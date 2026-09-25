# Appendix D — Reproducibility

## D.1 Verifying this manuscript's numbers (recommended, read-only)

1. Read `backend/evaluation_out_real_llm_v1/results.json` (do not modify).
2. Recursively count `EV-*` records → expect **188**.
3. Tally by `surface` → intersection 55, hypothesis 50, gap 83.
4. Tally by `system` → keyword 41, embedding 36, llm_only 53, pipeline 58.
5. Count distinct `case_id` per system → keyword 12, embedding 12, llm_only 12, pipeline 8.
6. Read `failures[]` → 4 pipeline failures (verbatim in Appendix B / Table D).

## D.2 Re-running the experiment (separate, explicit step — NOT done here)

If a fresh run is ever desired, follow the repository README; note that:
- It will execute real rank/embedding/LLM calls and take significant time.
- Results will differ on network/LLM availability (the 4 recorded pipeline failures are
  network-dependent and may or may not recur).
- This manuscript intentionally does **not** re-run; it only reports the single authoritative run.
