# Appendix D: Reproducibility Information

This appendix summarizes the artifacts and procedures that support verifying the analysis reported in
this paper. It complements Section 9.

## D.1 Verifying the reported numbers (read-only)

The counts reported in this paper can be verified by a read-only inspection of the recorded evaluation
outputs maintained in the ResearchCollision repository:

1. Recursively enumerate all recorded evidence records; expect 188.
2. Tally by surface; expect intersection 55, hypothesis 50, gap 83.
3. Tally by system; expect keyword 41, embedding 36, llm_only 53, pipeline 58.
4. Count the distinct cases per system; expect keyword 12, embedding 12, llm_only 12, pipeline 8.
5. Inspect the recorded failure list; expect the four pipeline failures listed in Appendix C
   and in Table D of Section 6.

## D.2 Re-running the experiment (explicit, separate step — not performed)

Re-running the experiment is possible, but this paper intentionally does not do so; it reports a
single authoritative execution. A fresh run would:

- execute real retrieval and language-model calls and take considerable time;
- produce results that may differ with network and provider availability (the four recorded pipeline
  failures are network-dependent and may or may not recur), because remote language-model sampling is
  not guaranteed deterministic.

Manuscript reproduction is fully script-based: the PDF, HTML preview, figures, and all tables in this
paper are derived by read-only parsing of the recorded evaluation outputs, and no experiment is
re-executed during manuscript preparation.