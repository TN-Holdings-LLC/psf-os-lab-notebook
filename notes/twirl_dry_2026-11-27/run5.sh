#!/bin/bash
# Pod run (workplace VS, 2026-11-27): the fourth night's job (build4, 173 circuits) with a coherent CZ error and Pauli
# twirling of the mirrors (ILLUSTRATIVE, never fitted), t = 1, 3, scored by score4. Tasks in /root/tasks.txt:
#   TAG SEED ARGS...   (each run's folder and every file carry TAG, so no two runs share a name)
# Raw counts kept (gzip); everything packed to /root/out5.tgz at the end (read back by scp, then counted).
log=/root/progress.txt; say() { echo "$(date -u +%FT%TZ) $*" >> $log; }
say setup start
mkdir -p /root/psfos /root/nb /root/w /root/work /root/out/raw
tar xzf /root/psfos.tgz --no-same-owner -C /root/psfos && tar xzf /root/nbslim4.tgz --no-same-owner -C /root/nb && tar xzf /root/w5.tgz --no-same-owner -C /root/w
say untar rc=$?
python3 -m pip install -q --break-system-packages "qiskit==2.5.2" "qiskit-aer==0.17.2" "numpy==2.4.6" "scipy==1.17.1" > /root/pip.txt 2>&1
say pip rc=$? aer $(python3 -c "import qiskit_aer; print(qiskit_aer.__version__)")
CPUS=0
if [ -f /sys/fs/cgroup/cpu.max ]; then CPUS=$(awk '{if ($1=="max") print 0; else printf "%d", $1/$2}' /sys/fs/cgroup/cpu.max); fi
if [ "$CPUS" = 0 ] && [ -f /sys/fs/cgroup/cpu/cpu.cfs_quota_us ]; then
  q=$(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us); p=$(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us); [ "$q" -gt 0 ] && CPUS=$((q / p)); fi
[ "$CPUS" -gt 0 ] || CPUS=8
say cpus $CPUS tasks $(wc -l < /root/tasks.txt)
export PYTHONPATH=/root/psfos OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
one() { local tag=$1 s=$2 d; shift 2; cd /root/nb
  python3 /root/w/vs_dry5_twirl.py /root/w/or4 /root/work $tag --seed $s --flips 0 --skip _t4_ "$@" > /root/out/sim_${tag}_$s.txt 2>&1
  d=/root/work/${tag}_q0.0_s$s
  gzip -c $d/job/raw_counts.json > /root/out/raw/${tag}_q0.0_s$s.raw_counts.json.gz
  python3 gpu/ohm_ruler_night4.py score4 $d /root/w/or4_answers --tau 0.3 > /root/out/score4_${tag}_q0.0_s$s.txt 2>&1
  for f in scores3.json scores4.json qubits.csv; do cp $d/$f /root/out/${f%.*}_${tag}_q0.0_s$s.${f##*.} 2>/dev/null; done
  cp $d/job/submission.json /root/out/sub_${tag}_q0.0_s$s.json; rm -rf $d; echo x >> /root/done.txt; }
export -f one
( xargs -P $CPUS -L 1 bash -c 'one "$@"' _ < /root/tasks.txt; say tasks done ) &
t0=$(date +%s)
while [ $(jobs -r | wc -l) -gt 0 ]; do sleep 60; say "elapsed $(( $(date +%s) - t0 ))s done $(cat /root/done.txt 2>/dev/null | wc -l) of $(wc -l < /root/tasks.txt) load $(cut -d' ' -f1 /proc/loadavg)"; done
cd /root && tar czf /root/out5.tgz out; say "packed $(ls /root/out/scores4_*.json | wc -l) scores4"; say all done
