#!/bin/bash
# The noiseless cells of the grid (p2 0, readout flips 0 and 0.02, plan B t = 1, 3, 10 seeds), run on the desk
# (workplace VS, 2026-11-24, sono2; author The Architect): the pod's last ten tasks were queued behind the slow
# damping runs, so they were run here instead (2.5 min with 6 processes). Same seeds as the pod grid.
#   B=<plan B build>  ANS=<sealed answers, never printed>  NB=<notebook at ohm-ruler-next-2026-11-24>  OUT=<folder>
#   PYTHONPATH=<psf-os 0.3.3> bash g0_local.sh
one() { s=$1; python vs_dry_noise2.py $B $OUT/work --p2 0 --flips 0 0.02 --seed $s --skip _t4_
  for q in 0.0 0.02; do d=$OUT/work/p20.0_q${q}_s$s
    (cd $NB && python gpu/ohm_ruler_night.py score $d $ANS && python gpu/ohm_ruler_night2.py score2 $d $ANS) > /dev/null
    cp $d/scores.json $OUT/scores_p20.0_q${q}_s$s.json; cp $d/scores2.json $OUT/scores2_p20.0_q${q}_s$s.json; done; }
export -f one; export B ANS NB OUT
for i in $(seq 1 10); do echo $((100000000 * i + 1)); done | xargs -P 6 -I{} bash -c 'one {}'
