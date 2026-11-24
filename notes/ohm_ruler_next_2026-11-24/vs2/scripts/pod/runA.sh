#!/bin/bash
# Pod run (workplace VS, 2026-11-24, sono2): plan B t = 1, 3 under ILLUSTRATIVE amplitude damping (never fitted), on the
# GPU (statevector trajectories), three runs at a time; scored by score and score2.
log=/root/progressA.txt; say() { echo "$(date -u +%FT%TZ) $*" >> $log; }
export PYTHONPATH=/root/psfos OMP_NUM_THREADS=2
sc() { d=$1; tag=$(basename $d); cd /root/nb
  python3 gpu/ohm_ruler_night.py score $d /root/w/sealed/B_answers.json > /root/outA/score_$tag.txt 2>&1
  python3 gpu/ohm_ruler_night2.py score2 $d /root/w/sealed/B_answers.json > /root/outA/score2_$tag.txt 2>&1
  cp $d/scores.json /root/outA/scores_$tag.json 2>/dev/null; cp $d/scores2.json /root/outA/scores2_$tag.json 2>/dev/null; }
one() { g=$1; s=$2; cd /root/nb
  python3 /root/w/vs_dry_noise2.py /root/w/B /root/workA --p2 0 --damp $g --flips 0 --seed $s --skip _t4_ --gpu > /root/outA/sim_A_${g}_$s.txt 2>&1
  sc /root/workA/p20.0_g${g}_q0.0_s$s; echo done >> /root/doneA.txt; }
export -f one sc
mkdir -p /root/outA /root/workA; rm -rf /root/workA/*; say start
( for g in 0.005 0.01; do for i in 1 2 3 4 5; do echo "$g $((100000000*i+1))"; done; done | xargs -P 3 -L 1 bash -c 'one $0 $1'; say tasks done ) &
pid=$!; t0=$(date +%s)
while kill -0 $pid 2>/dev/null; do sleep 60; say "elapsed $(( $(date +%s) - t0 ))s done $(wc -l < /root/doneA.txt 2>/dev/null || echo 0) of 10"; done
cd /root && tar czf /root/outA.tgz outA; say all done
