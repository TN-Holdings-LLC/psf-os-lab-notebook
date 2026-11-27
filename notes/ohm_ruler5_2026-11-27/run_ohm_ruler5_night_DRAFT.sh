#!/bin/bash
# The fifth Ohm ruler night, the device part only (a DRAFT by the workplace, 2026-11-27; author The Architect).
# Written in the form of the record files of 2026-11-26 (build.txt, check.txt, pick.txt, device.txt, score.txt,
# versions.txt); the workplace has not seen home's run_ohm_ruler4_night_2026-11-26.sh, so home compares the two before
# use. VPN OFF. No git command here: the declaration is pushed and the clone made before this script (VPN ON), and the
# clone is checked out at the declaring commit by hand.
#
#   NB=~/or_nb PSFOS=~/psf-os ANS=/path/to/ohm_ruler_answers_L9.json OUT=/path/to/or5_night_YYYY-MM-DD \
#     bash run_ohm_ruler5_night_DRAFT.sh
#
# NB: the notebook clone at the declaring commit; PSFOS: psf-os 0.3.3 (e652257); ANS: the sealed 9-pair answers
# (sha256 e581df9d...), kept outside the notebook; OUT: a new folder for this night (refused if it exists).
set -euo pipefail
: "${NB:?set NB}" "${PSFOS:?set PSFOS}" "${ANS:?set ANS}" "${OUT:?set OUT}"
[ -e "$OUT" ] && { echo "STOP: $OUT exists"; exit 1; }
echo "e581df9d4fbb99ca219f3beb1e3efbf6b2d34be0477d32fc7bf51071207497ac  $ANS" | sha256sum -c - \
  || { echo "STOP: the sealed answers' sha256 differs"; exit 1; }
mkdir -p "$OUT"
cd "$NB"
export PYTHONPATH="$PSFOS:$NB" TOQB_DIR="$NB"
python -c "import psf_os; assert psf_os.__version__ == '0.3.3', psf_os.__version__; print('psf-os', psf_os.__version__)"
pip list 2>/dev/null | grep -E '^(numpy|qiskit|qiskit-aer|qiskit-ibm-runtime) ' > "$OUT/versions.txt"
python --version >> "$OUT/versions.txt"

# The declared procedure, word for word (prereg "Device procedure"), OUT -> $OUT, ANSWERS_SEALED -> $ANS
python gpu/daily_fetch.py "$OUT/fetch_in"
python gpu/ohm_ruler_night.py pick "$OUT/fetch_in/queue.json" | tee "$OUT/pick.txt"
DEV=$(cut -d' ' -f1 "$OUT/pick.txt")
echo "$DEV" > "$OUT/device.txt"
python gpu/ohm_ruler_night5.py build5 "$OUT/fetch_in/$DEV/dev" "$OUT/or5" "$ANS" "$OUT/or5_answers" --pairs-t 1:7 3:7 4:9 \
  2>&1 | tee "$OUT/build.txt"
python gpu/ohm_ruler_night5.py check5 "$OUT/or5" "$OUT/or5_answers" 2>&1 | tee "$OUT/check.txt"
grep -q "^ALL (declared check, string mirrors, readout) PASS" "$OUT/check.txt" \
  || { echo "STOP: check5 is not ALL PASS: no run"; exit 1; }
python -m psf_os submit --job "$OUT/or5/job"
python -m psf_os collect --job "$OUT/or5/job" --wait-min 20
python gpu/ohm_ruler_night5.py score5 "$OUT/or5" "$OUT/or5_answers" --tau 0.3 2>&1 | tee "$OUT/score.txt"
cp "$OUT/or5/qubits.csv" "$OUT/qubits.csv"
echo "done: $OUT (copy into results/<night>/ at home, as 11-26)"
