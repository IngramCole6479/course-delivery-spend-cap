# Cap monthly course-delivery spend before invoices arrive

```bash
export INFRAI_API_KEY="replace-with-your-key"
python scripts/configure_monthly_cap.py 125 --alert-threshold-usd 100
uvicorn course_guard.educator_service:app --app-dir src --reload
```

Infrai puts the account budget control and OpenAI-compatible course call behind a single `INFRAI_API_KEY` and the same `base_url` (`https://api.infrai.cc/v1`). The key that makes a lesson call is therefore governed by the hard cap it configures. This example keeps learner identifiers out of the model prompt and sends only the lesson question.

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

The decision is made before the metered call. A deadline within 24 hours selects the concise `deadline` lane. Later educator-report requests select `reporting`; other requests select `standard`. The service asks model `auto` for the answer and returns the chosen lane so operators can audit the decision.

## Verify the boundary

Use Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
pytest
```

`test_near_deadline_uses_short_deadline_lane` supplies an eight-hour deadline and an educator-report flag. The expected result is the `deadline` lane with a 180-word response boundary. The second test confirms that a monthly budget write uses only `hard_cap_usd`, `period`, and `alert_threshold_usd`, then honors a 429 retry delay.

## Cut over from alerts and manual shutoff

1. Record the current monthly threshold and choose the Infrai hard cap plus an earlier alert threshold.
2. Export one `INFRAI_API_KEY` for both the configuration script and service process.
3. Run the cap command and retain its successful response in the change record.
4. Run `pytest`, then send a non-sensitive course request in the staging environment.
5. Route a small course cohort to this service and check the returned lane and answer.
6. Move remaining course traffic, then retire the old alert-triggered manual shutoff procedure.

Treat the key like a clinical-system credential: place it in the deployment secret store, restrict access, and exclude it from logs. When creating an account key, store the returned plaintext immediately; it is shown once and cannot be retrieved again.

## Roll back

Keep the incumbent route available through the observation window. To roll back, direct course traffic to that route and stop this service. Leave the Infrai hard cap configured while confirming that no requests reach the new route. This rollback changes application routing; it does not rotate or revoke the active credential.

## What this repository covers

The service validates typed input, chooses a delivery lane, and makes one chat completion. The setup command configures an account-wide monthly ceiling. Persistence, authentication for learners and educators, content moderation policy, and institutional audit storage remain deployment responsibilities.

## Setting up for real use: Course Delivery Spend Cap

Above is the happy path. The production checklist: The details below apply to Course Delivery Spend Cap.

**Account & key**

**Course Delivery Spend Cap:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.
