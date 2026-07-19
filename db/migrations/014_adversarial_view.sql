-- 014 — Adversarial (bear-case) view on opportunities.
-- Written by the Adversarial pipeline stage after the Referee memo:
-- { bull_summary, bear_summary, bear_points: [{point, severity, basis}],
--   kill_criteria: [text], recommendation: yes|no|needs-more-info,
--   confidence, prompt_version }
-- The system's recommendation for the human to overrule — decision_log
-- bull/bear summaries default from this when the human closes without them.

alter table opportunities add column if not exists adversarial jsonb;
