#!/bin/bash
# Pod run (workplace VS, 2026-11-27): the fourth night's job (build4, 173 circuits) with a coherent CZ error and Pauli
# twirling of the mirrors (ILLUSTRATIVE, never fitted), t = 1, 3, scored by score4. Tasks in /root/tasksb.txt:
#   TAG SEED ARGS...   (each run's folder and every file carry TAG, so no two runs share a name)
# Raw counts kept (gzip); everything packed to /root/out5b.tgz at the end (read back by scp, then counted).
log=/root/progressb.txt; say() { echo "$(date -u +%FT%TZ) $*" >> $log; }
say setup start
mkdir -p /root/psfos /root/nb /root/w /root/workb /root/outb/raw
CPUS=0
if [ -f /sys/fs/cgroup/cpu.max ]; then CPUS=$(awk '{if ($1=="max") print 0; else printf "%d", $1/$2}' /sys/fs/cgroup/cpu.max); fi
if [ "$CPUS" = 0 ] && [ -f /sys/fs/cgroup/cpu/cpu.cfs_quota_us ]; then
  q=$(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us); p=$(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us); [ "$q" -gt 0 ] && CPUS=$((q / p)); fi
CPUS=6
say cpus $CPUS tasks $(wc -l < /root/tasksb.txt)
export PYTHONPATH=/root/psfos OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
one() { local tag=$1 s=$2 d; shift 2; cd /root/nb
  python3 /root/w/vs_dry5_twirl.py /root/w/or4 /root/workb $tag --seed $s --flips 0 --skip _t4_ "$@" > /root/outb/sim_${tag}_$s.txt 2>&1
  d=/root/workb/${tag}_q0.0_s$s
  gzip -c $d/job/raw_counts.json > /root/outb/raw/${tag}_q0.0_s$s.raw_counts.json.gz
  python3 gpu/ohm_ruler_night4.py score4 $d /root/w/or4_answers --tau 0.3 > /root/outb/score4_${tag}_q0.0_s$s.txt 2>&1
  for f in scores3.json scores4.json qubits.csv; do cp $d/$f /root/outb/${f%.*}_${tag}_q0.0_s$s.${f##*.} 2>/dev/null; done
  cp $d/job/submission.json /root/outb/sub_${tag}_q0.0_s$s.json; rm -rf $d; echo x >> /root/doneb.txt; }
export -f one
( xargs -P $CPUS -L 1 bash -c 'one "$@"' _ < /root/tasksb.txt; say tasks done ) &
t0=$(date +%s)
while [ $(jobs -r | wc -l) -gt 0 ]; do sleep 60; say "elapsed $(( $(date +%s) - t0 ))s done $(cat /root/doneb.txt 2>/dev/null | wc -l) of $(wc -l < /root/tasksb.txt) load $(cut -d' ' -f1 /proc/loadavg)"; done
cd /root && tar czf /root/out5b.tgz outb; say "packed $(ls /root/outb/scores4_*.json | wc -l) scores4"; say all done
