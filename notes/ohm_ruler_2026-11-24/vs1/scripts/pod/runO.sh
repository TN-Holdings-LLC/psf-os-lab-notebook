#!/bin/bash
# Pod run (workplace VS, 2026-11-24, sono1): gpu/ohm_ruler_night.py plan B under ILLUSTRATIVE gate noise (never fitted).
# Tasks from /root/tasks.txt, one "p2 seed" per line; each writes two dry jobs (readout flip 0 and 0.02) and scores
# them. A progress line every minute.
log=/root/progress.txt; say() { echo "$(date -u +%FT%TZ) $*" >> $log; }
say setup start
mkdir -p /root/psfos /root/nb /root/w /root/work /root/out && tar xzf /root/psfos.tgz -C /root/psfos && tar xzf /root/nbslim.tgz -C /root/nb && tar xzf /root/B.tgz --no-same-owner -C /root/w
say untar rc=$?
python3 -m pip install -q --break-system-packages "qiskit==2.5.2" "qiskit-aer==0.18.0" "numpy==2.4.6" "scipy==1.17.1" > /root/pip.txt 2>&1
say pip done rc=$?
CPUS=0
if [ -f /sys/fs/cgroup/cpu.max ]; then CPUS=$(awk '{if ($1=="max") print 0; else printf "%d", $1/$2}' /sys/fs/cgroup/cpu.max); fi
if [ "$CPUS" = 0 ] && [ -f /sys/fs/cgroup/cpu/cpu.cfs_quota_us ]; then
  q=$(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us); p=$(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us); [ "$q" -gt 0 ] && CPUS=$((q / p)); fi
[ "$CPUS" -gt 0 ] || CPUS=8
say cpus $CPUS tasks $(wc -l < /root/tasks.txt)
export PYTHONPATH=/root/psfos OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
one() { p2=$1; s=$2; cd /root/nb
  python3 /root/w/vs_dry_noise.py /root/w/B /root/work --p2 $p2 --flips 0 0.02 --seed $s --skip _t4_ > /root/out/sim_p2${p2}_s$s.txt 2>&1
  for q in 0.0 0.02; do d=/root/work/p2${p2}_q${q}_s$s
    python3 gpu/ohm_ruler_night.py score $d /root/w/sealed/B_answers.json > /root/out/score_p2${p2}_q${q}_s$s.txt 2>&1
    cp $d/scores.json /root/out/scores_p2${p2}_q${q}_s$s.json 2>/dev/null; rm -rf "/root/work/p2${p2}_q${q}_s$s/job/circuits.qpy"; done; }
export -f one
( xargs -P $CPUS -L 1 bash -c 'one $0 $1' < /root/tasks.txt; say tasks done ) &
pid=$!; t0=$(date +%s)
while kill -0 $pid 2>/dev/null; do sleep 60; say "elapsed $(( $(date +%s) - t0 ))s scored $(ls /root/out/scores_*.json 2>/dev/null | wc -l) of $(( 2 * $(wc -l < /root/tasks.txt) )) load $(cut -d' ' -f1 /proc/loadavg)"; done
cd /root && tar czf /root/outO.tgz out; say all done
