#!/bin/bash
# Pod run (workplace VS, 2026-11-24, sono2): the ohm ruler dry runs under ILLUSTRATIVE noise (never fitted), scored by
# the declared tool (score) and the next night's candidate (score2). Tasks from /root/tasks.txt, one per line:
#   S SEED I N   one shard of the t = 4 circuits (p2 0.01), saved to /root/mem/SEED
#   G P2 SEED    plan B t = 1, 3 at gate noise P2, readout flips 0 and 0.02
#   A G SEED     plan B t = 1, 3 at amplitude damping G (no depolarizing), flip 0
# After the tasks, every seed with shards is merged (flip 0) and scored. A progress line every minute.
log=/root/progress.txt; say() { echo "$(date -u +%FT%TZ) $*" >> $log; }
say setup start
mkdir -p /root/psfos /root/nb /root/w /root/work /root/out /root/mem && tar xzf /root/psfos.tgz --no-same-owner -C /root/psfos && tar xzf /root/nbslim2.tgz --no-same-owner -C /root/nb && tar xzf /root/B.tgz --no-same-owner -C /root/w && cp /root/vs_dry_noise2.py /root/w/
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
sc() { d=$1; tag=$(basename $d); cd /root/nb
  python3 gpu/ohm_ruler_night.py score $d /root/w/sealed/B_answers.json > /root/out/score_$tag.txt 2>&1
  python3 gpu/ohm_ruler_night2.py score2 $d /root/w/sealed/B_answers.json > /root/out/score2_$tag.txt 2>&1
  cp $d/scores.json /root/out/scores_$tag.json 2>/dev/null; cp $d/scores2.json /root/out/scores2_$tag.json 2>/dev/null
  rm -f $d/job/circuits.qpy; }
one() { k=$1; cd /root/nb; D=/root/w/vs_dry_noise2.py
  case $k in
    S) python3 $D /root/w/B /root/work --p2 0.01 --seed $2 --skip _t1_ _t3_ --shard $3 $4 --mem-dir /root/mem/$2 > /root/out/shard_$2_$3.txt 2>&1 ;;
    G) python3 $D /root/w/B /root/work --p2 $2 --flips 0 0.02 --seed $3 --skip _t4_ > /root/out/sim_G_$2_$3.txt 2>&1
       for q in 0.0 0.02; do sc /root/work/p2$2_q${q}_s$3; done ;;
    A) python3 $D /root/w/B /root/work --p2 0 --damp $2 --flips 0 --seed $3 --skip _t4_ > /root/out/sim_A_$2_$3.txt 2>&1
       sc /root/work/p20.0_g$2_q0.0_s$3 ;;
  esac; echo done >> /root/done.txt; }
export -f one sc
( xargs -P $CPUS -L 1 bash -c 'one $0 $1 $2 $3' < /root/tasks.txt; say tasks done
  for m in /root/mem/*; do [ -d $m ] || continue; s=$(basename $m)
    ( cd /root/nb; python3 /root/w/vs_dry_noise2.py /root/w/B /root/work --p2 0.01 --flips 0 --seed $s --skip _t1_ _t3_ --merge --mem-dir $m > /root/out/merge_$s.txt 2>&1; sc /root/work/p20.01_q0.0_s$s ) &
  done; wait; say merged ) &
pid=$!; t0=$(date +%s)
while kill -0 $pid 2>/dev/null; do sleep 60; say "elapsed $(( $(date +%s) - t0 ))s done $(wc -l < /root/done.txt 2>/dev/null || echo 0) of $(wc -l < /root/tasks.txt) scores $(ls /root/out/scores_*.json 2>/dev/null | wc -l) load $(cut -d' ' -f1 /proc/loadavg)"; done
cd /root && tar czf /root/out2.tgz out; say all done
