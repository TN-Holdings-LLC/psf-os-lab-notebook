# Paper 10, version 1: Zenodo input (DRAFT, workplace 2026-11-19; the form of notes/paper9/ZENODO.md)

Not uploaded. Every `[...]` is filled at home when the paper is final; nothing else is expected to change.

- Upload: `TN-Holdings_Paper10_v1_Decisions-No-Correction-Can-Reach.pdf` (the same bytes as `notes/paper10_ff/paper10_v1.pdf`,
  built from `notes/paper10_ff/paper10.tex` at [commit]).
- Title: Decisions No Correction of the Uncontrolled Circuit Can Reach: Real-Time Control on IBM Heron, Declared Before
  the Data
- Creator: TN Holdings (no personal name; no e-mail in the record).
- Resource type: Publication / Preprint. Language: English. Date: [date of upload].
- Description: the abstract of the PDF, pasted as plain text from the .tex (not copied from the PDF: ligatures and
  spaces break, as with paper 4), with the `\pending` places of the 11-19 night filled.
- Keywords: quantum computing; IBM Heron r2; dynamic circuits; mid-circuit measurement; feed-forward; real-time
  control; correction ceiling; pre-registration; reproducibility; repeat-until-success; iterative phase estimation;
  repetition code.
- Related identifiers:
  - is supplemented by https://github.com/TN-Holdings-LLC/psf-os-lab-notebook (commit [commit]);
  - is supplemented by doi:10.5281/zenodo.[psf-os 0.2 version DOI] (psf-os [number]); the concept DOI
    10.5281/zenodo.24211404 resolves to the latest release;
  - continues doi:10.5281/zenodo.24278888 (paper 9).
- Licence: as papers 1-9.

## Checks before upload (as for paper 9)

- The PDF's numbers against the records (the workplace VS's number check, as `VS_NUMBER_CHECK_2026-11-19.md`), and no
  `[PENDING` left: `pdftotext paper10_v1.pdf - | grep -c PENDING` gives 0.
- The description field matched to the final abstract.
- The paper's author line holds a contact address (`\author{TN Holdings\\ contact: ...}`, as in the draft from home);
  whether it stays in the PDF is the owner's choice; the Zenodo record itself carries none.
