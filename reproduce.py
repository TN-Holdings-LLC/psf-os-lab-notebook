"""Re-score the committed device results from their committed raw counts, without IBM, and compare with the
committed scores.json files. Every scorer is run unchanged on a copy (the committed files are not touched).

usage (from the TOQB root, with psf-os installed or on PYTHONPATH):
    python reproduce.py [--psf-os PATH_TO_PSF_OS_CHECKOUT] [NAME ...]

Prints one line per result: SAME (every number equal to 1e-9), DIFFERENT (the first differing key), or FAILED.

--gate-hash: also rebuild the circuits of the run2d results (practice and daily) from their committed device record and
user circuits with the psf-os on the path, and compare psf_os.gatehash of every compiled circuit (user, floor, mirror,
sentinel; the job's circuits.qpy) with the committed ones: GATES SAME / GATES DIFFERENT. The gate hash does not depend
on Qiskit's QPY format (QPY bytes do).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))

# name: (result folder, folders to copy, scorer command with {T} = the copy's root, scores file in the copy[, rev])
# rev (optional): the commit whose gpu/ scorer made the committed scores.json, where the scorer has gained keys since
# (it is taken from `git archive rev gpu` into the temporary folder; needs the git history).
RESULTS = {
    "p6-fez-2026-11-04": ("results/p6-device-2026-11-04", ["V"], ["gpu/p6_score.py", "{T}"], "scores.json"),
    "p6-marrakesh-2026-11-04": ("results/p6-marrakesh-2026-11-04", ["V"], ["gpu/p6_score.py", "{T}"], "scores.json"),
    "os2d-fez-2026-11-04": ("results/os2d-2026-11-04", ["V"],
                            ["gpu/os2d_score.py", "{T}/V/job", "{T}/V/runs",
                             "results/p6-answers-2026-11-04/answers_cpu.json", "{T}/scores.json"], "scores.json"),
    "corr-fez-2026-11-04": ("results/corr-2026-11-04", ["V"], ["gpu/corr_score.py", "{T}"], "scores.json"),
    "corr-marrakesh-2026-11-04": ("results/corr-marrakesh-2026-11-04", ["V"], ["gpu/corr_score.py", "{T}"],
                                  "scores.json"),
    "practice-marrakesh-2026-11-04": ("results/practice-2026-11-04", ["run", "circuits"],
                                      ["gpu/practice_score.py", "{T}/run", "{T}/circuits/answers.json"],
                                      "run/scores.json"),
    "practice-fez-2026-11-04": ("results/practice-fez-2026-11-04", ["run", "circuits"],
                                ["gpu/practice_score.py", "{T}/run", "{T}/circuits/answers.json"], "run/scores.json"),
    "daily-2026-11-05-marrakesh": ("results/daily/2026-11-05", ["ibm_marrakesh", "answers.json"],
                                   ["gpu/daily_score.py", "{T}/ibm_marrakesh/run", "{T}/answers.json"],
                                   "ibm_marrakesh/run/scores.json"),
    "daily-2026-11-05-fez": ("results/daily/2026-11-05", ["ibm_fez", "answers.json"],
                             ["gpu/daily_score.py", "{T}/ibm_fez/run", "{T}/answers.json"], "ibm_fez/run/scores.json"),
    # added 2026-11-08 for paper 7 (the 11-06 run is FX-A alone, scored with its answers_by_tag.json)
    "daily-2026-11-06-marrakesh": ("results/daily/2026-11-06", ["ibm_marrakesh"],
                                   ["gpu/daily_score.py", "{T}/ibm_marrakesh/run", "{T}/ibm_marrakesh/answers_by_tag.json"],
                                   "ibm_marrakesh/run/scores.json"),
    "daily-2026-11-07-fez": ("results/daily/2026-11-07", ["ibm_fez", "answers.json"],
                             ["gpu/daily_score.py", "{T}/ibm_fez/run", "{T}/answers.json"], "ibm_fez/run/scores.json"),
    "daily-2026-11-14-marrakesh": ("results/daily/2026-11-14", ["ibm_marrakesh", "answers.json"],
                             ["gpu/daily_score.py", "{T}/ibm_marrakesh/run", "{T}/answers.json"], "ibm_marrakesh/run/scores.json"),
    "daily-2026-11-14-fez": ("results/daily/2026-11-14", ["ibm_fez", "answers.json"],
                             ["gpu/daily_score.py", "{T}/ibm_fez/run", "{T}/answers.json"], "ibm_fez/run/scores.json"),
    "daily-2026-11-15-marrakesh": ("results/daily/2026-11-15", ["ibm_marrakesh", "answers.json"],
                             ["gpu/daily_score.py", "{T}/ibm_marrakesh/run", "{T}/answers.json"], "ibm_marrakesh/run/scores.json"),
    "daily-2026-11-16-marrakesh": ("results/daily/2026-11-16", ["ibm_marrakesh", "answers.json"],
                             ["gpu/daily_score.py", "{T}/ibm_marrakesh/run", "{T}/answers.json"], "ibm_marrakesh/run/scores.json"),
    "daily-2026-11-16-kingston": ("results/daily/2026-11-16", ["ibm_kingston", "answers.json"],
                             ["gpu/daily_score.py", "{T}/ibm_kingston/run", "{T}/answers.json"], "ibm_kingston/run/scores.json"),
    "du51-kingston-2026-11-07": ("results/du51-2026-11-07", ["ibm_kingston", "answers"],
                                 ["gpu/du51_score.py", "{T}/ibm_kingston/run", "{T}/answers/answers.json"],
                                 "ibm_kingston/run/scores.json"),
    "du71-kingston-2026-11-07": ("results/du71-2026-11-07", ["ibm_kingston", "answers"],
                                 ["gpu/du51_score.py", "{T}/ibm_kingston/run", "{T}/answers/answers.json"],
                                 "ibm_kingston/run/scores.json"),
    # added 2026-11-10 at the workplace for paper 8 (handover 11-09 item 3); same rule: the declared scorer, unchanged
    "physA-4x4x3-fez-2026-11-07": ("results/os3d-physA-2026-11-07", ["j1_4x4x3", "answers"],
                                   ["gpu/os3d_v31_score.py", "{T}/j1_4x4x3", "{T}/answers/answers_4x4x3.json", "top"],
                                   "j1_4x4x3/scores.json"),
    "physA-4x2x2-fez-2026-11-07": ("results/os3d-physA-2026-11-07", ["j2_4x2x2", "answers"],
                                   ["gpu/os3d_v31_score.py", "{T}/j2_4x2x2", "{T}/answers/answers_4x2x2.json", "top"],
                                   "j2_4x2x2/scores.json"),
    "heisB-fez-2026-11-08": ("results/os3d-heisB-2026-11-08", ["fez", "answers"],
                             ["gpu/heis3d_score.py", "{T}/fez", "{T}/answers/heis_answers_fez.json"], "fez/scores.json", "9eaf26c"),
    "heisE-marrakesh-2026-11-08": ("results/os3d-heisE-2026-11-08", ["marrakesh", "answers"],
                                   ["gpu/heis3d_score.py", "{T}/marrakesh", "{T}/answers/heis_answers_E_marrakesh.json"],
                                   "marrakesh/scores.json", "bc38d2c"),
    "heisE-kingston-2026-11-08": ("results/os3d-heisE-kingston-2026-11-08", ["kingston", "answers"],
                                  ["gpu/heis3d_score.py", "{T}/kingston", "{T}/answers/heis_answers_Ek.json"],
                                  "kingston/scores.json", "bc38d2c"),
    "du91-marrakesh-2026-11-09": ("results/du91-2026-11-09", ["ibm_marrakesh", "answers"],
                                  ["gpu/du51_score.py", "{T}/ibm_marrakesh/run", "{T}/answers/du91_answers_marrakesh.json"],
                                  "ibm_marrakesh/run/scores.json"),
    "schw-marrakesh-2026-11-09": ("results/schw-2026-11-09", ["ibm_marrakesh", "answers"],
                                  ["gpu/schw_score.py", "{T}/ibm_marrakesh", "{T}/answers/schw_answers_marrakesh.json"],
                                  "ibm_marrakesh/scores.json"),
    "lc3d-marrakesh-2026-11-09": ("results/lc3d-2026-11-09", ["ibm_marrakesh", "answers"],
                                  ["gpu/lc3d_score.py", "{T}/ibm_marrakesh", "{T}/answers/lc_answers_marrakesh.json"],
                                  "ibm_marrakesh/scores.json"),
    # added 2026-11-10 for paper 8: the N = 91 second run (ruler in every job) and the Ising line against fold
    "du91r-fez-2026-11-10": ("results/night-2026-11-10/du91r", ["ibm_fez", "answers"],
                             ["gpu/du91r_score.py", "{T}/ibm_fez", "{T}/answers/du91r_fez.json"],
                             "ibm_fez/scores.json"),
    "isingL-fez-2026-11-10": ("results/night-2026-11-10/isingL", ["ibm_fez", "answers"],
                              ["gpu/isingL_score.py", "{T}/ibm_fez", "{T}/answers/isingL_fez.json"],
                              "ibm_fez/scores.json"),
    "utility-fez-2026-11-10": ("results/utility-2026-11-10", ["ibm_fez", "answers"],
                               ["gpu/utility_score.py", "{T}/ibm_fez", "{T}/answers/answers_ibm_fez.json"],
                               "ibm_fez/scores.json"),
    "utility-depth-fez-2026-11-11": ("results/utility-depth-2026-11-11", ["ibm_fez", "answers"],
                                     ["gpu/utility_score.py", "{T}/ibm_fez", "{T}/answers/answers.json"],
                                     "ibm_fez/scores.json"),
    "hubbard-fez-2026-11-11": ("results/hubbard-2026-11-11", ["ibm_fez", "answers"],
                               ["gpu/hub_score.py", "{T}/ibm_fez", "{T}/answers/hub_ibm_fez_ans.json"],
                               "ibm_fez/scores.json"),
    "hubbard-big-fez-2026-11-11": ("results/hubbard-big-2026-11-11", ["ibm_fez", "answers"],
                                   ["gpu/hub_score.py", "{T}/ibm_fez", "{T}/answers/hubB_ibm_fez_ans.json"],
                                   "ibm_fez/scores.json"),
    "hub-dt-fez-2026-11-12": ("results/hub-dt-2026-11-12", ["ibm_fez", "answers"],
                              ["gpu/hub_score.py", "{T}/ibm_fez", "{T}/answers/dt_ibm_fez_ans_circuit.json"],
                              "ibm_fez/scores.json"),
    "ohm-fez-2026-11-12": ("results/ohm-2026-11-12", ["ibm_fez", "answers"],
                           ["gpu/ohm_score.py", "{T}/ibm_fez", "{T}/answers/ohm_ibm_fez_ans.json"],
                           "ibm_fez/scores.json"),
    "ohm-kingston-2026-11-12": ("results/ohm-kingston-2026-11-12", ["ibm_kingston", "answers"],
                                ["gpu/ohm_score.py", "{T}/ibm_kingston", "{T}/answers/ohm_ibm_kingston_ans.json"],
                                "ibm_kingston/scores.json"),
    "xx91-fez-2026-11-12": ("results/xx91-2026-11-12", ["ibm_fez", "answers"],
                            ["gpu/hub_score.py", "{T}/ibm_fez", "{T}/answers/xx91_ibm_fez_ans.json"],
                            "ibm_fez/scores.json"),
    "twin-2026-11-13-xx": ("results/twin-2026-11-13", ["ibm_marrakesh_xx", "answers"],
        ["gpu/twin_score.py", "{T}/ibm_marrakesh_xx", "{T}/answers/xx_xx_ans.json", "{T}/answers/xx_xx_ans_twin.json"],
        "ibm_marrakesh_xx/twin_scores.json"),
    "twin-2026-11-13-hub": ("results/twin-2026-11-13", ["ibm_marrakesh_hub", "answers"],
        ["gpu/twin_score.py", "{T}/ibm_marrakesh_hub", "{T}/answers/hub_hub_ans.json", "{T}/answers/hub_hub_ans_twin.json"],
        "ibm_marrakesh_hub/twin_scores.json"),
    "full-floor-2026-11-13-floor": ("results/full-floor-2026-11-13", ["ibm_marrakesh_floor", "answers"],
        ["gpu/full_floor.py", "score", "{T}/ibm_marrakesh_floor", "{T}/answers/floor_floor_ans.json"],
        "ibm_marrakesh_floor/full_floor.json"),
    "full-floor-2026-11-14-floor": ("results/full-floor-2026-11-14", ["ibm_marrakesh_floor", "answers"],
        ["gpu/full_floor.py", "score", "{T}/ibm_marrakesh_floor", "{T}/answers/floor_floor_ans.json"],
        "ibm_marrakesh_floor/full_floor.json"),
    "xxsize-2026-11-14-marrakesh-n33": ("results/xxsize-2026-11-14-marrakesh", ["ibm_marrakesh_n33", "answers"],
        ["gpu/hub_score.py", "{T}/ibm_marrakesh_n33", "{T}/answers/n33_n33_ans.json"],
        "ibm_marrakesh_n33/scores.json"),
    "xxsize-2026-11-14-marrakesh-n81": ("results/xxsize-2026-11-14-marrakesh", ["ibm_marrakesh_n81", "answers"],
        ["gpu/hub_score.py", "{T}/ibm_marrakesh_n81", "{T}/answers/n81_n81_ans.json"],
        "ibm_marrakesh_n81/scores.json"),
    "xxsize-2026-11-14-fez-n33": ("results/xxsize-2026-11-14-fez", ["ibm_fez_n33", "answers"],
        ["gpu/hub_score.py", "{T}/ibm_fez_n33", "{T}/answers/n33_n33_ans.json"],
        "ibm_fez_n33/scores.json"),
    "xxsize-2026-11-14-fez-n81": ("results/xxsize-2026-11-14-fez", ["ibm_fez_n81", "answers"],
        ["gpu/hub_score.py", "{T}/ibm_fez_n81", "{T}/answers/n81_n81_ans.json"],
        "ibm_fez_n81/scores.json"),
    "xxcone-2026-11-14-n33": ("results/xxcone-2026-11-14", ["ibm_marrakesh_n33", "answers"],
        ["gpu/hub_score.py", "{T}/ibm_marrakesh_n33", "{T}/answers/n33_n33_ans.json"],
        "ibm_marrakesh_n33/scores.json"),
    "xxcone-2026-11-14-n81": ("results/xxcone-2026-11-14", ["ibm_marrakesh_n81", "answers"],
        ["gpu/hub_score.py", "{T}/ibm_marrakesh_n81", "{T}/answers/n81_n81_ans.json"],
        "ibm_marrakesh_n81/scores.json"),
    "full-floor-2026-11-15-floor": ("results/full-floor-2026-11-15", ["ibm_marrakesh_floor", "answers"],
        ["gpu/full_floor.py", "score", "{T}/ibm_marrakesh_floor", "{T}/answers/floor_floor_ans.json"],
        "ibm_marrakesh_floor/full_floor.json"),
    "full-floor-2026-11-16-floor": ("results/full-floor-2026-11-16", ["ibm_marrakesh_floor", "answers"],
        ["gpu/full_floor.py", "score", "{T}/ibm_marrakesh_floor", "{T}/answers/floor_floor_ans.json"],
        "ibm_marrakesh_floor/full_floor.json"),
    # needs psf-os at the branch feedforward-2026-11-16 (--psf-os PATH to that checkout): psf_os.feedforward
    "feedforward-2026-11-16": ("results/feedforward-2026-11-16", ["job", "runs", "build.json"],
        ["gpu/ff_night.py", "score", "{T}"], "ff_scores.json"),
    # needs psf-os at the branch feedforward-2026-11-16 (--psf-os PATH to that checkout): psf_os.feedforward
    "rus-neuron-2026-11-16": ("results/rus-neuron-2026-11-16", ["job", "runs", "build.json"],
        ["gpu/rus_night.py", "score", "{T}"], "rus_scores.json"),
    # needs psf-os at the branch feedforward-2026-11-16 (--psf-os PATH to that checkout): psf_os.feedforward
    "wait-diag-2026-11-16": ("results/wait-diag-2026-11-16", ["job", "runs", "build.json"],
        ["gpu/wait_night.py", "score", "{T}"], "wait_scores.json"),
    # needs psf-os at the branch feedforward-2026-11-16 (--psf-os PATH to that checkout): psf_os.feedforward
    "ctrl-diag-2026-11-16": ("results/ctrl-diag-2026-11-16", ["job", "runs", "build.json"],
        ["gpu/ctrl_night.py", "score", "{T}"], "ctrl_scores.json"),
    # needs psf-os at the branch feedforward-2026-11-16 (--psf-os PATH to that checkout): psf_os.feedforward
    "rus-neuron2-2026-11-16": ("results/rus-neuron2-2026-11-16", ["job", "runs", "build.json"],
        ["gpu/rus2_night.py", "score", "{T}"], "rus2_scores.json"),
    # needs psf-os at the branch feedforward-2026-11-16 (--psf-os PATH to that checkout): psf_os.feedforward
    "rus-neuron3-2026-11-16": ("results/rus-neuron3-2026-11-16", ["job", "runs", "build.json"],
        ["gpu/rus3_night.py", "score", "{T}"], "rus3_scores.json"),
    # needs psf-os at the branch feedforward-2026-11-16 (--psf-os PATH to that checkout): psf_os.feedforward
    "rus-neuron3-kingston-2026-11-16": ("results/rus-neuron3-kingston-2026-11-16", ["job", "runs", "build.json"],
        ["gpu/rus3_night.py", "score", "{T}"], "rus3_scores.json"),
    # needs psf-os at the branch feedforward-2026-11-16, 301ac01 or later (--psf-os PATH)
    "ff-night-2026-11-17-coh": ("results/ff-night-2026-11-17/coh", ["job", "runs", "build.json"],
        ["gpu/coh_night.py", "score", "{T}"], "coh_scores.json"),
    # needs psf-os at the branch feedforward-2026-11-16, 301ac01 or later (--psf-os PATH)
    "ff-night-2026-11-17-compound": ("results/ff-night-2026-11-17/compound", ["job", "runs", "build.json"],
        ["gpu/compound_night.py", "score", "{T}"], "compound_scores.json"),
    # needs psf-os at the branch feedforward-2026-11-16, 301ac01 or later (--psf-os PATH)
    "ff-night-2026-11-17-apps": ("results/ff-night-2026-11-17/apps", ["job", "runs", "build.json"],
        ["gpu/apps_night.py", "score", "{T}"], "apps_scores.json"),
    # needs psf-os at the branch feedforward-2026-11-16, 301ac01 or later (--psf-os PATH)
    "ff-night-2026-11-17-early": ("results/ff-night-2026-11-17/early", ["job", "runs", "build.json"],
        ["gpu/early_night.py", "score", "{T}", "--rd", "results/ff-night-2026-11-17/compound"], "early_scores.json"),
    # needs psf-os at the branch feedforward-2026-11-16, 301ac01 or later (--psf-os PATH)
    "ff-night2-2026-11-17-coh2": ("results/ff-night2-2026-11-17/coh2", ["job", "runs", "build.json"],
        ["gpu/coh2_night.py", "score", "{T}"], "coh2_scores.json"),
    # needs psf-os at the branch feedforward-2026-11-16, 301ac01 or later (--psf-os PATH)
    "ff-night2-2026-11-17-early2": ("results/ff-night2-2026-11-17/early2", ["job", "runs", "build.json"],
        ["gpu/early2_night.py", "score", "{T}"], "early2_scores.json"),
    # needs psf-os at the branch feedforward-2026-11-16, 301ac01 or later (--psf-os PATH)
    "ff-night2-2026-11-17-apps2": ("results/ff-night2-2026-11-17/apps2", ["job", "runs", "build.json"],
        ["gpu/apps2_night.py", "score", "{T}"], "apps2_scores.json"),
    # needs psf-os at the branch feedforward-2026-11-16, 301ac01 or later (--psf-os PATH)
    "os-night-2026-11-17-dw": ("results/os-night-2026-11-17/dw", ["job", "runs", "build.json"],
        ["gpu/wait_night.py", "score", "{T}"], "wait_scores.json"),
    "os-night-2026-11-17-dc": ("results/os-night-2026-11-17/dc", ["job", "runs", "build.json"],
        ["gpu/ctrl_night.py", "score", "{T}"], "ctrl_scores.json"),
    "os-night-2026-11-17-main": ("results/os-night-2026-11-17/main", ["job", "runs", "build.json", "rule.json"],
        ["gpu/os_night.py", "score", "{T}"], "os_scores.json"),
    # needs psf-os at the branch feedforward-2026-11-16, 301ac01 or later (--psf-os PATH)
    "balanced-night-2026-11-17": ("results/balanced-night-2026-11-17", ["job", "runs", "build.json"],
        ["gpu/balanced_night.py", "score", "{T}"], "balanced_scores.json"),
    # needs psf-os at the branch feedforward-2026-11-16, 0f57c76 or later (bundled items) (--psf-os PATH)
    "packing-night-2026-11-17": ("results/packing-night-2026-11-17", ["packed", "single1", "plan.json"],
        ["gpu/packing_night.py", "score", "{T}"], "packing_scores.json"),
    # 2026-11-18 (psf-os at the branch feedforward-2026-11-16, 0f57c76 or later; --psf-os PATH)
    "balanced-repeat-2026-11-18": ("results/balanced-repeat-2026-11-18", ["job", "runs", "build.json"],
        ["gpu/balanced_night.py", "score", "{T}"], "balanced_scores.json"),
    "parallel-night-2026-11-18": ("results/parallel-night-2026-11-18", ["pa", "pb", "plan.json"],
        ["gpu/parallel_night.py", "score", "{T}"], "parallel_scores.json"),
    "timing-night-2026-11-18": ("results/timing-night-2026-11-18", ["tmA", "tmB", "dt.json"],
        ["gpu/timing_night.py", "score", "{T}/tmA", "{T}/tmB", "--dt-file", "{T}/dt.json"], "tmA/timing_scores.json"),
    "os2-night-2026-11-18-dw": ("results/os2-night-2026-11-18/dw", ["job", "runs", "build.json"],
        ["gpu/wait_night.py", "score", "{T}"], "wait_scores.json"),
    "os2-night-2026-11-18-dc": ("results/os2-night-2026-11-18/dc", ["job", "runs", "build.json"],
        ["gpu/ctrl_night.py", "score", "{T}"], "ctrl_scores.json"),
    "os2-night-2026-11-18-r1": ("results/os2-night-2026-11-18/r1", ["job", "runs", "build.json", "rule.json"],
        ["gpu/os2_night.py", "score", "{T}"], "round_scores.json"),
    "loop-night-2026-11-19-dw": ("results/loop-night-2026-11-19/dw", ["job", "runs", "build.json"],
        ["gpu/wait_night.py", "score", "{T}"], "wait_scores.json"),
    "loop-night-2026-11-19-dc": ("results/loop-night-2026-11-19/dc", ["job", "runs", "build.json"],
        ["gpu/ctrl_night.py", "score", "{T}"], "ctrl_scores.json"),
    "loop-night-2026-11-19-r1": ("results/loop-night-2026-11-19/r1", ["job", "runs", "build.json", "rule.json"],
        ["gpu/os3_night.py", "score", "{T}"], "round_scores.json"),
    "loop-night-2026-11-19-r2": ("results/loop-night-2026-11-19/r2", ["job", "runs", "build.json", "rule.json"],
        ["gpu/os3_night.py", "score", "{T}"], "round_scores.json"),
    "loop-night-2026-11-19-r3": ("results/loop-night-2026-11-19/r3", ["job", "runs", "build.json", "rule.json"],
        ["gpu/os3_night.py", "score", "{T}"], "round_scores.json"),
    "loop-paired-night-2026-11-20-dw": ("results/loop-paired-night-2026-11-20/dw", ["job", "runs", "build.json"],
        ["gpu/wait_night.py", "score", "{T}"], "wait_scores.json"),
    "loop-paired-night-2026-11-20-dc": ("results/loop-paired-night-2026-11-20/dc", ["job", "runs", "build.json"],
        ["gpu/ctrl_night.py", "score", "{T}"], "ctrl_scores.json"),
    "weekend-shared-night-2026-11-21-A": ("results/weekend-shared-night-2026-11-21/A", ["job0", "shared.json"],
        ["gpu/weekend_shared_night.py", "score", "{T}"], "scores/A/repcode4_scores.json"),
    "weekend-shared-night-2026-11-21-B": ("results/weekend-shared-night-2026-11-21/BC", ["job0", "job1", "shared.json"],
        ["gpu/weekend_shared_night.py", "score", "{T}"], "scores/B/qpe_long_scores.json"),
    "weekend-shared-night-2026-11-21-C": ("results/weekend-shared-night-2026-11-21/BC", ["job0", "job1", "shared.json"],
        ["gpu/weekend_shared_night.py", "score", "{T}"], "scores/C/park_scores.json"),
    "qpe-parked-night-2026-11-21": ("results/qpe-parked-night-2026-11-21/qp", ["job0", "job1", "plan.json"],
        ["gpu/qpe_parked_night.py", "score", "{T}"], "parked_scores.json"),
    "rus-fence-night-2026-11-21": ("results/rus-fence-night-2026-11-21/rf", ["job0", "plan.json"],
        ["gpu/rus_fence_night.py", "score", "{T}"], "rusfence_scores.json"),
    "likely-park-night-2026-11-22": ("results/likely-park-night-2026-11-22/lp", ["job0", "plan.json"],
        ["gpu/likely_park_night.py", "score", "{T}"], "likely_scores.json"),
    "qpe-n78-night-2026-11-22": ("results/qpe-n78-night-2026-11-22/qn", ["job0", "plan.json"],
        ["gpu/qpe_long_parked_night.py", "score", "{T}"], "qpe78_scores.json"),
    "ipe-branch-cost-night-2026-11-22": ("results/ipe-branch-cost-night-2026-11-22/bc", ["job0", "plan.json"],
        ["gpu/ipe_branch_cost_night.py", "score", "{T}"], "branch_scores.json"),
    "interfere-night-2026-11-19": ("results/interfere-night-2026-11-19", ["job", "runs", "plan.json"],
        ["gpu/interfere_night.py", "score", "{T}"], "interfere_scores.json", "404daf9f"),
    "repcode-night-2026-11-19": ("results/repcode-night-2026-11-19", ["job", "runs", "build.json", "part.json"],
        ["gpu/repcode_night.py", "score", "{T}"], "repcode_scores.json", "404daf9f"),
    "qpe-repro-night-2026-11-19": ("results/qpe-repro-night-2026-11-19", ["qA", "qB"],
        ["gpu/qpe_repro_night.py", "score", "{T}/qA", "{T}/qB"], "qA/qpe_scores.json"),
    "decoy-night-2026-11-20": ("results/decoy-night-2026-11-20", ["job", "runs", "plan.json"],
        ["gpu/decoy_night.py", "score", "{T}"], "decoy_scores.json"),
    "loopvar-night-2026-11-20": ("results/loopvar-night-2026-11-20", ["V1", "V2", "V3", "plan.json"],
        ["gpu/loopvar_night.py", "score", "{T}"], "loopvar_scores.json"),
    "ohm-window-night-2026-11-23": ("results/ohm-window-night-2026-11-23", ["ow", "answers"],
        ["gpu/ohm_window_night.py", "score", "{T}/ow", "{T}/answers/ohm_window_answers_by_label.json"],
        "ow/scores.json"),
    "ohm-ruler-night-2026-11-24": ("results/ohm-ruler-night-2026-11-24", ["or", "answers"],
        ["gpu/ohm_ruler_night.py", "score", "{T}/or", "{T}/answers/ohm_ruler_answers_by_label.json"],
        "or/scores.json"),
    "ohm-ruler3-night-2026-11-25": ("results/ohm-ruler3-night-2026-11-25", ["or3", "answers"],
        ["gpu/ohm_ruler_night3.py", "score3", "{T}/or3", "{T}/answers/ohm_ruler3_answers_by_label.json",
         "--tau", "0.3"],
        "or3/scores3.json"),
}


def first_difference(a, b, path=""):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                return f"{path}/{k} missing on one side"
            d = first_difference(a[k], b[k], f"{path}/{k}")
            if d:
                return d
        return None
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return f"{path} length {len(a)} != {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            d = first_difference(x, y, f"{path}[{i}]")
            if d:
                return d
        return None
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return None if abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b)) else f"{path}: {a} != {b}"
    return None if a == b else f"{path}: {a!r} != {b!r}"


# run2d results: (run folder, device record folder, user circuits folder)
REBUILD = {
    "practice-marrakesh-2026-11-04": ("results/practice-2026-11-04/run", "results/practice-2026-11-04/dev",
                                      "results/practice-2026-11-04/circuits"),
    "practice-fez-2026-11-04": ("results/practice-fez-2026-11-04/run", "results/practice-fez-2026-11-04/dev",
                                "results/practice-fez-2026-11-04/circuits"),
    "daily-2026-11-05-marrakesh": ("results/daily/2026-11-05/ibm_marrakesh/run",
                                   "results/daily/2026-11-05/ibm_marrakesh/dev", "results/daily/2026-11-05/circuits"),
    "daily-2026-11-05-fez": ("results/daily/2026-11-05/ibm_fez/run", "results/daily/2026-11-05/ibm_fez/dev",
                             "results/daily/2026-11-05/circuits"),
}


def gate_check(name):
    """Rebuild one run2d result and compare gate hashes; (ok, message)."""
    from psf_os import device as Dv
    from psf_os import gatehash as G
    from psf_os import user2d as U
    run, dev_dir, circ = (os.path.join(ROOT, p) for p in REBUILD[name])
    rep = json.load(open(os.path.join(run, "report.json")))
    man = json.load(open(os.path.join(run, "job", "manifest.json")))
    items = [(t, U.load(os.path.join(circ, f"{t}.qpy"))) for t in rep["tags"]]
    with tempfile.TemporaryDirectory() as t:
        U.build_batch(Dv.Device.load(dev_dir), items, t, shots=man["shots"], max_seconds=10 ** 6)
        old = G.qpy_hash(os.path.join(run, "job", "circuits.qpy"))
        new = G.qpy_hash(os.path.join(t, "job", "circuits.qpy"))
        per = sorted(f for f in os.listdir(os.path.join(run, "runs")) if f.endswith(".qpy"))
        bad = [f for f in per if G.qpy_hash(os.path.join(run, "runs", f)) != G.qpy_hash(os.path.join(t, "runs", f))]
    ok = old == new and not bad
    return ok, (f"GATES SAME ({old['circuits']} circuits, {old['gate_sha256'][:12]})" if ok else
                f"GATES DIFFERENT (job {old['gate_sha256'][:12]} vs {new['gate_sha256'][:12]}; records {bad})")


def _ignore(folder, names):
    """Leave out the committed scores, and raw_counts.json where the committed raw_counts.json.gz is beside it (older
    records commit the .gz only; the plain file there is a local, untracked copy). Records from 2026-11-06 on commit
    raw_counts.json itself, which is then the input."""
    out = {"scores.json", "scores3.json"} & set(names)
    if "raw_counts.json.gz" in names:
        out.add("raw_counts.json")
    return out


def copy_result(src, parts, dst):
    for p in parts:
        s = os.path.join(ROOT, src, p)
        if os.path.isdir(s):
            shutil.copytree(s, os.path.join(dst, p), ignore=_ignore)
        else:
            shutil.copy(s, os.path.join(dst, p))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--psf-os", default=None, help="a psf-os checkout to put first on PYTHONPATH")
    ap.add_argument("--gate-hash", action="store_true", help="also rebuild the run2d results' circuits and compare gates")
    ap.add_argument("names", nargs="*")
    a = ap.parse_args()
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(p for p in (a.psf_os, ROOT, env.get("PYTHONPATH")) if p)
    names = a.names or list(RESULTS)
    bad = 0
    for name in names:
        src, parts, cmd, scores, *rev = RESULTS[name]
        with tempfile.TemporaryDirectory() as t:
            copy_result(src, parts, t)
            if rev:  # the scorer as it was when the committed scores were made
                # gpu/ and the notes' Python modules at rev, laid out as in the notebook (scorers that add notes/
                # folders to sys.path relative to their own file find them)
                rt = os.path.join(t, "_at_rev")
                os.makedirs(rt)
                arc = subprocess.run(["git", "archive", rev[0], "gpu", ":(glob)notes/**/*.py"], cwd=ROOT,
                                     capture_output=True, check=True)
                subprocess.run(["tar", "-x", "-C", rt], input=arc.stdout, check=True)
                cmd = [os.path.join(rt, cmd[0])] + cmd[1:]
            run = subprocess.run([sys.executable] + [c.replace("{T}", t) for c in cmd], cwd=ROOT, env=env,
                                 capture_output=True, text=True)
            if run.returncode != 0:
                print(f"{name:32} FAILED: {run.stderr.strip().splitlines()[-1] if run.stderr.strip() else run.returncode}")
                bad += 1
                continue
            new = json.load(open(os.path.join(t, scores)))
            old = json.load(open(os.path.join(ROOT, src, scores)))
            d = first_difference(json.loads(json.dumps(old)), json.loads(json.dumps(new)))
            print(f"{name:32} " + ("SAME" if d is None else f"DIFFERENT at {d}"))
            bad += d is not None
    print(f"{len(names) - bad} of {len(names)} reproduced")
    if a.gate_hash:
        if a.psf_os:
            sys.path.insert(0, a.psf_os)
        gbad = 0
        gnames = [n for n in names if n in REBUILD]
        for name in gnames:
            try:
                ok, msg = gate_check(name)
            except Exception as e:  # noqa: BLE001
                ok, msg = False, f"FAILED: {e}"
            print(f"{name:32} {msg}")
            gbad += not ok
        print(f"{len(gnames) - gbad} of {len(gnames)} rebuilt with the same gates")
        bad += gbad
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
