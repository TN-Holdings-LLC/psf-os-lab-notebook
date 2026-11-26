# The order in which IBM ran the 11-25 job's pubs (read 2026-11-26, no new job, no charge)

`spans_dc3bju5h_2026-11-25.json`, from the runtime's execution spans of job dc3bju5hdvas73bni4og (ibm_fez, 169 pubs;
`fetch_execution_spans.py`, run by the owner with VPN OFF):

- two spans: pubs 0 to 99 from 10:36:41.46 to 10:37:11.72 UTC, then pubs 100 to 168 from 10:37:30.83 to 10:37:52.74.
- So the device ran the pubs in the job's index order, in two blocks about 19 s apart. In psf-os 0.3.3's build the
  sentinel is pubs 0 to 3 and the order is the record files' (the workplace VS, 2026-11-26); a readout pair placed
  first and last would therefore sit at the two ends of the run, about 70 s apart.
- What the spans do not say: the order inside a block (the span gives the block's start and stop only).
