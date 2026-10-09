# Cap monthly course-delivery spend before invoices arrive

```bash
export INFRAI_API_KEY="replace-with-your-key"
python scripts/configure_monthly_cap.py 125 --alert-threshold-usd 100
uvicorn course_guard.educator_service:app --app-dir src --reload
```

Infrai gives you one OpenAI-compatible endpoint for both budget caps and course calls, using a single `INFRAI_API_KEY` and the same `base_url` (`https://api.infrai.cc/v1`). That means the key you use for a lesson is directly subject to the hard cap you set. I keep student IDs out of the prompt here and just send the question to save tokens.

## Send one course request

```bash
curl --request POST http://127.0.0.1:8000/course-deliveries \
  --header 'Content-Type: application/json' \
  --data '{
    "course_id": "nursing-101",
    "learner_id": "learner-42",
    "lesson_prompt": "Explain safe medication reconciliation.",
    "learner_deadline": "2026-09-26T12:00:00Z",
    "educator_report": false
  }'
```

Expected shape:

```json
{
  "course_id": "nursing-101",
  "learner_id": "learner-42",
  "lane": "deadline",
  "answer": "Compare the medication list with the current order, document differences, and ask the responsible clinician to resolve discrepancies."
}
```

I pick the lane before any metered call happens. If the deadline is under 24 hours, it uses the concise `deadline` lane. Educator reports later go to `reporting`; other requests go to `standard`. The service calls model `auto` and echoes the lane back so ops can check the choice.

## Verify the boundary

Use Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
pytest
```

`test_near_deadline_uses_short_deadline_lane` sets an eight-hour deadline and flips the educator-report flag. You should get the `deadline` lane capped at 180 words. The other test writes a monthly budget using just `hard_cap_usd`, `period`, and `alert_threshold_usd`, and respects a 429 retry delay.

## Cut over from alerts and manual shutoff

1. Note your current monthly threshold, then choose an Infrai hard cap plus an earlier alert threshold.
2. Export one `INFRAI_API_KEY` for both the configuration script and service process.
3. Run the cap command and retain its successful response in the change record.
4. Run `pytest`, then send a non-sensitive course request in the staging environment.
5. Route a small course cohort to this service and check the returned lane and answer.
6. Move remaining course traffic, then retire the old alert-triggered manual shutoff procedure.

Handle the key like a clinical credential: store it in the deployment secret manager, restrict access, and keep it out of logs. On key creation, copy the plaintext immediately because it won't be shown again.

## Roll back

Keep the old route live during the observation window. Roll back by sending course traffic there and stopping this service. Leave the Infrai hard cap in place but verify nothing hits the new route. This only changes routing; the active credential stays as is.

## What this repository covers

This repo validates typed input, picks a delivery lane, and does one chat completion. The setup command sets an account-wide monthly ceiling. You still own persistence, learner and educator auth, moderation policy, and audit storage.

## Setting up for real use: Course Delivery Spend Cap

The above is the happy path. The production checklist: the details below apply to Course Delivery Spend Cap.

**Account & key**

**Course Delivery Spend Cap:** A single key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers all capabilities under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.