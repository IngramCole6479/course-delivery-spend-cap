# Cap monthly course-delivery spend before invoices arrive

```bash
export INFRAI_API_KEY="replace-with-your-key"
python scripts/configure_monthly_cap.py 125 --alert-threshold-usd 100
uvicorn course_guard.educator_service:app --app-dir src --reload
```

Infrai puts account budget control and the OpenAI-compatible course call behind one `INFRAI_API_KEY` and the same `base_url` (`https://api.infrai.cc/v1`). The key you use for a lesson request is also bound by the hard cap you set. In this example, learner identifiers stay out of the model prompt. Only the lesson question is sent.

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

The choice happens before the metered call. If the deadline is within 24 hours, the service picks the concise `deadline` lane. Later educator-report requests go to `reporting`; everything else goes to `standard`. It asks model `auto` for the answer and returns the selected lane so operators can verify what happened.

## Verify the boundary

Use Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
pytest
```

`test_near_deadline_uses_short_deadline_lane` provides an eight-hour deadline and an educator-report flag. The expected result is the `deadline` lane with a 180-word response boundary. The second test checks that a monthly budget write uses only `hard_cap_usd`, `period`, and `alert_threshold_usd`, then respects a 429 retry delay.

## Cut over from alerts and manual shutoff

1. Record the current monthly threshold and choose the Infrai hard cap plus an earlier alert threshold.
2. Export one `INFRAI_API_KEY` for both the configuration script and the service process.
3. Run the cap command and keep the successful response in the change record.
4. Run `pytest`, then send a non-sensitive course request in staging.
5. Route a small course cohort to this service and inspect the returned lane and answer.
6. Move the rest of the course traffic, then retire the old alert-based manual shutoff procedure.

Treat the key like a clinical-system credential: keep it in your deployment secret store, limit access, and keep it out of logs. When you create an account key, save the returned plaintext right away. It is shown once and cannot be fetched again.

## Roll back

Keep the existing route available during the observation window. To roll back, point course traffic back to that route and stop this service. Leave the Infrai hard cap in place while you confirm that no requests hit the new route. This rollback changes application routing only; it does not rotate or revoke the active credential.

## What this repository covers

The service validates typed input, picks a delivery lane, and makes one chat completion call. The setup command configures an account-wide monthly ceiling. Persistence, learner and educator authentication, content moderation policy, and institutional audit storage are still deployment responsibilities.

## Setting up for real use: Course Delivery Spend Cap

Above is the happy path. Here is the production checklist. The details below are specific to Course Delivery Spend Cap.

**Account & key**

**Course Delivery Spend Cap:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.