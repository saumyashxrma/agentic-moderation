# Dev B — Infrastructure & Data Pipeline: Setup Log

**Project:** Multimodal AI Content Auto-Moderation API
**Scope owner:** Dev B (Infrastructure & Data Pipeline Lead)
**Environment:** Windows / PowerShell / VS Code / Docker Desktop with LocalStack Extension (LocalStack Pro)
**Project root:** `C:\Third_Eye\Project_LocalStack\agentic-moderation\pipeline`

## What this pipeline does

A client sends `POST /moderate/text` with a body like `{"type": "text", "content": "feeling bored today"}`.

1. An **Ingestion Lambda** checks Redis for a cached moderation flag on that content.
   - **Cache hit** → returns the flag immediately.
   - **Cache miss** → pushes the item onto an **SQS queue** with a UUID.
2. The SQS queue buffers items until either **20 messages** accumulate or **60 seconds** pass, then triggers a **Processor Lambda** with the whole batch.
3. The Processor Lambda (currently a stub) is where a teammate's LangGraph/AI moderation logic will eventually plug in, returning a flag for each item and writing it back to Redis + DynamoDB.

Everything below runs against **LocalStack** (emulated AWS) plus a plain **Redis** container — no real AWS account or costs involved.

---

## Final folder structure

```
pipeline/
├── docker-compose.yml
├── venv/                      # Python virtualenv
├── lambda_ingestion/
│   ├── handler.py             # Ingestion Lambda source
│   ├── requirements.txt       # redis
│   ├── test_local.py          # local test harness (no deploy needed)
│   ├── payload_miss.json      # sample cache-miss test payload
│   ├── payload_hit.json       # sample cache-hit test payload
│   ├── package/                # handler.py + installed deps, used for zipping
│   └── function.zip           # deployed to LocalStack Lambda
└── processor_lambda/
    ├── handler.py              # Processor Lambda stub (logs batches)
    └── function.zip
```

---

## Step 1 — Project folder & CLI tools

**Goal:** Set up an isolated Python environment and get `awslocal` (the LocalStack-aware AWS CLI wrapper) working.

```powershell
mkdir dev-b-pipeline
cd dev-b-pipeline
code .

python -m venv venv
.\venv\Scripts\Activate.ps1

pip install boto3 redis
pip show boto3 redis

deactivate
pip install --user awscli awscli-local
```

**Gotcha hit:** `awslocal` wasn't found after install — the install location (`...AppData\Roaming\Python\Python313\Scripts`) wasn't on PATH.

**Fix (permanent):** Added that folder to the Windows user `Path` environment variable via *System Environment Variables → Environment Variables → Path → New*, then reopened the terminal.

**Verification:**
```powershell
awslocal --version
awslocal sqs list-queues
```
Returned `{"QueueUrls": []}` — confirmed `awslocal` correctly reaches LocalStack at `localhost:4566`.

---

## Step 2 — Redis via Docker Compose

**Goal:** Run a local Redis container for the exact-match cache (used instead of AWS ElastiCache, which is a LocalStack Pro/Ultimate-only service).

**`docker-compose.yml`:**
```yaml
services:
  redis:
    image: redis:7-alpine
    container_name: moderation-redis
    ports:
      - "6379:6379"
    restart: unless-stopped
```

```powershell
docker compose up -d
docker ps
docker exec -it moderation-redis redis-cli ping
```
→ `PONG` confirmed Redis was reachable.

---

## Step 3 — Create the SQS queue

```powershell
awslocal sqs create-queue --queue-name moderation-text-queue
awslocal sqs list-queues
awslocal sqs get-queue-attributes --queue-url <QUEUE_URL> --attribute-names All
```

Also did a manual send/receive round-trip to prove the queue works before any Lambda touches it:
```powershell
awslocal sqs send-message --queue-url <QUEUE_URL> --message-body "test message"
awslocal sqs receive-message --queue-url <QUEUE_URL>
```

Confirmed visually in the LocalStack web app: **Resource Browser → SQS**.

---

## Step 4 — Ingestion Lambda logic (local testing, no deploy yet)

**`lambda_ingestion/handler.py`** — parses the request body, normalizes the content (`strip().lower()`), checks Redis, and either returns the cached flag or pushes to SQS with a UUID. Fails open (queues instead of crashing) if Redis is unreachable.

**`lambda_ingestion/test_local.py`** — imports `lambda_handler` directly and runs a cache-miss and cache-hit test without deploying anything.

Seeded a fake cached entry to test the hit path:
```powershell
docker exec -it moderation-redis redis-cli set "some cached phrase" "yellow"
```

**Gotcha 1 — missing AWS credentials:**
`boto3` calls (unlike `awslocal` CLI calls) don't auto-inject dummy credentials. Fixed by setting them manually per session:
```powershell
$env:AWS_ACCESS_KEY_ID = "test"
$env:AWS_SECRET_ACCESS_KEY = "test"
$env:AWS_DEFAULT_REGION = "us-east-1"
```

**Other required env vars for local testing:**
```powershell
$env:REDIS_HOST = "localhost"
$env:SQS_ENDPOINT_URL = "http://localhost.localstack.cloud:4566"
$env:QUEUE_URL = "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/moderation-text-queue"
```

**Run the test:**
```powershell
.\venv\Scripts\Activate.ps1
cd lambda_ingestion
python test_local.py
```
Both cache-miss (→ queued) and cache-hit (→ cached flag) paths worked correctly.

**Gotcha 2 — `awslocal` broke inside the active venv:**
`ModuleNotFoundError: No module named 'localstack_client'` — the venv's Python shadowed the global `awscli-local` install. Fixed by installing it into the venv too:
```powershell
pip install awscli awscli-local
```

Confirmed the queued message actually reached SQS:
```powershell
awslocal sqs receive-message --queue-url <QUEUE_URL>
```

---

## Step 5 — Package and deploy the Ingestion Lambda

**Goal:** Turn `handler.py` into a real Lambda function running inside LocalStack.

**Code fix required before deploying:** the original code hardcoded a `QUEUE_URL` env var. Since the Lambda's actual container can't resolve `localhost`-style URLs the same way the host machine can, this was replaced with a runtime lookup by queue *name*:
```python
QUEUE_NAME = os.environ.get("QUEUE_NAME", "moderation-text-queue")
_queue_url_cache = None

def get_queue_url():
    global _queue_url_cache
    if _queue_url_cache is None:
        _queue_url_cache = sqs_client.get_queue_url(QueueName=QUEUE_NAME)["QueueUrl"]
    return _queue_url_cache
```
And the `send_message` call was updated to use `QueueUrl=get_queue_url()`.

**Package the dependencies (Lambda's runtime doesn't include `redis` by default):**
```powershell
mkdir package
pip install -r requirements.txt -t package
Copy-Item handler.py package\
cd package
Compress-Archive -Path .\* -DestinationPath ..\function.zip -Force
cd ..
```

**Deploy:**
```powershell
awslocal lambda create-function `
  --function-name ingestion-lambda `
  --runtime python3.12 `
  --handler handler.lambda_handler `
  --zip-file fileb://function.zip `
  --role arn:aws:iam::000000000000:role/lambda-role `
  --environment "Variables={REDIS_HOST=host.docker.internal,QUEUE_NAME=moderation-text-queue}"
```

`host.docker.internal` is Docker Desktop's special DNS name letting any container reach services on the host machine — this is how the Lambda's own container reaches the `moderation-redis` container's published port.

**Gotcha 1 — `--cli-binary-format` flag not recognized:**
Turned out the machine has **AWS CLI v1** installed, not v2 — that flag is v2-only and isn't needed on v1.

**Gotcha 2 — PowerShell mangled inline JSON payloads:**
Passing `--payload '{"type":"text",...}'` inline caused `Runtime.UnmarshalError` because PowerShell stripped the embedded double quotes before the string reached the CLI. **Fix:** write payloads to files and reference them with `file://`:
```powershell
awslocal lambda invoke --function-name ingestion-lambda --payload file://payload_miss.json output.json
awslocal lambda invoke --function-name ingestion-lambda --payload file://payload_hit.json output2.json
Get-Content output.json
Get-Content output2.json
```

**Gotcha 3 — the code fix from earlier hadn't actually been applied before zipping:**
First deploy still had the old `QUEUE_URL = os.environ.get("QUEUE_URL")` logic, which was `None` since only `QUEUE_NAME` was set — causing every miss-path request to fail with a 500. Fixed by actually editing `handler.py`, then re-zipping and updating:
```powershell
Copy-Item handler.py package\ -Force
cd package
Compress-Archive -Path .\* -DestinationPath ..\function.zip -Force
cd ..
awslocal lambda update-function-code --function-name ingestion-lambda --zip-file fileb://function.zip
```

**Gotcha 4 — SQS endpoint also needed fixing for the same class of reason:**
The default `SQS_ENDPOINT_URL` (`http://localhost.localstack.cloud:4566`) doesn't resolve correctly from inside the Lambda's own container. Fixed via a configuration update:
```powershell
awslocal lambda update-function-configuration `
  --function-name ingestion-lambda `
  --environment "Variables={REDIS_HOST=host.docker.internal,QUEUE_NAME=moderation-text-queue,SQS_ENDPOINT_URL=http://host.docker.internal:4566}"
```

**Gotcha 5 — reading Lambda logs:**
`awslocal logs tail ...` doesn't exist in CLI v1. Used the v1-compatible approach instead:
```powershell
awslocal logs describe-log-streams --log-group-name /aws/lambda/ingestion-lambda --order-by LastEventTime --descending
awslocal logs get-log-events --log-group-name /aws/lambda/ingestion-lambda --log-stream-name '<STREAM_NAME_WITH_$LATEST>'
```
Note: log stream names contain `$LATEST` — **must use single quotes** in PowerShell, or `$LATEST` gets interpreted as an (empty) variable and corrupts the name.

**Final verified result:** both cache-miss (→ 202, queued) and cache-hit (→ 200, cached flag) worked correctly through the real deployed Lambda, and the queued message was confirmed present in SQS.

---

## Step 6 — Wire up API Gateway

**Goal:** Make the Ingestion Lambda reachable over plain HTTP instead of only via `awslocal lambda invoke`.

```powershell
$API_ID = awslocal apigateway create-rest-api --name "moderation-api" --query "id" --output text

$ROOT_ID = awslocal apigateway get-resources --rest-api-id $API_ID --query "items[?path=='/'].id" --output text

$MODERATE_ID = awslocal apigateway create-resource --rest-api-id $API_ID --parent-id $ROOT_ID --path-part moderate --query "id" --output text

$TEXT_ID = awslocal apigateway create-resource --rest-api-id $API_ID --parent-id $MODERATE_ID --path-part text --query "id" --output text

awslocal apigateway put-method --rest-api-id $API_ID --resource-id $TEXT_ID --http-method POST --authorization-type NONE

$LAMBDA_ARN = "arn:aws:lambda:us-east-1:000000000000:function:ingestion-lambda"
$INTEGRATION_URI = "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations"

awslocal apigateway put-integration `
  --rest-api-id $API_ID `
  --resource-id $TEXT_ID `
  --http-method POST `
  --type AWS_PROXY `
  --integration-http-method POST `
  --uri $INTEGRATION_URI

awslocal lambda add-permission `
  --function-name ingestion-lambda `
  --statement-id apigateway-invoke `
  --action lambda:InvokeFunction `
  --principal apigateway.amazonaws.com `
  --source-arn "arn:aws:execute-api:us-east-1:000000000000:$API_ID/*/POST/moderate/text"

awslocal apigateway create-deployment --rest-api-id $API_ID --stage-name local
```

`AWS_PROXY` integration hands the raw HTTP request straight to the Lambda as its `event`, matching how `handler.py` already parses `event["body"]`.

**Test using `Invoke-RestMethod`** (avoids the same quote-mangling issue seen with `lambda invoke`):
```powershell
$body = '{"type":"text","content":"feeling bored today"}'
Invoke-RestMethod -Uri "http://localhost:4566/restapis/$API_ID/local/_user_request_/moderate/text" -Method POST -Body $body -ContentType "application/json"
```

Both the miss path (→ queued) and hit path (→ cached, `flag: yellow`) worked correctly over real HTTP.

`_user_request_` in the URL is LocalStack's convention for hitting a deployed stage via the edge port — not a typo.

**Note:** `$API_ID` and related variables only persist for the current terminal session — need to be noted down or re-fetched (`awslocal apigateway get-rest-apis --query "items[?name=='moderation-api'].id" --output text`) in future sessions.

---

## Step 7 — SQS → Processor Lambda batching trigger

**Goal:** This is where the "batch of 20 OR 60 seconds" rule actually lives.

**`processor_lambda/handler.py`** — a stub that logs every record in the batch it receives (no external dependencies needed):
```python
import json

def lambda_handler(event, context):
    records = event.get("Records", [])
    print(f"Processor Lambda triggered with a batch of {len(records)} message(s).")

    parsed_items = []
    for record in records:
        try:
            body = json.loads(record["body"])
            parsed_items.append(body)
            print(f"  - id={body.get('id')} type={body.get('type')} content={body.get('content')!r}")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  - Failed to parse record: {e} | raw body: {record.get('body')}")

    print(f"Batch summary: {json.dumps(parsed_items, indent=2)}")
    return {"batchSize": len(records), "processedIds": [item.get("id") for item in parsed_items]}
```

**Deploy:**
```powershell
Compress-Archive -Path .\handler.py -DestinationPath .\function.zip -Force

awslocal lambda create-function `
  --function-name processor-lambda `
  --runtime python3.12 `
  --handler handler.lambda_handler `
  --zip-file fileb://function.zip `
  --role arn:aws:iam::000000000000:role/lambda-role
```

**Connect it to the queue with the batching rule:**
```powershell
$QUEUE_URL = "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/moderation-text-queue"
$QUEUE_ARN = awslocal sqs get-queue-attributes --queue-url $QUEUE_URL --attribute-names QueueArn --query "Attributes.QueueArn" --output text

awslocal lambda create-event-source-mapping `
  --function-name processor-lambda `
  --event-source-arn $QUEUE_ARN `
  --batch-size 20 `
  --maximum-batching-window-in-seconds 60
```

**Test:** sent a message via the API Gateway endpoint, waited ~60 seconds, then checked the Processor Lambda's logs:
```powershell
awslocal logs describe-log-streams --log-group-name /aws/lambda/processor-lambda --order-by LastEventTime --descending
awslocal logs get-log-events --log-group-name /aws/lambda/processor-lambda --log-stream-name '<STREAM_NAME>'
```

Log output confirmed the Lambda received a **batch** (not one-at-a-time invocations) after the time window elapsed, with correctly parsed `id`/`type`/`content` for each item.

**Note on a transient duplicate-message observation:** a couple of stale test messages (leftover from earlier manual `receive-message` testing, which doesn't auto-delete) appeared in two consecutive batches before finally clearing. Verified this wasn't a systemic problem by purging the queue and re-testing with a single fresh message:
```powershell
awslocal sqs purge-queue --queue-url $QUEUE_URL
```
The following batch showed exactly one message with the correct ID — confirming the event source mapping correctly deletes messages after a successful batch invocation under normal conditions.

---

## Step 8 — Full end-to-end verification

Already proven across Steps 5–7 via `Invoke-RestMethod` → API Gateway → Ingestion Lambda → Redis/SQS → batching trigger → Processor Lambda logs. No separate work needed — this step was validating the whole chain, which the step 6 and step 7 tests already exercised together.

---

## Recurring gotchas worth remembering

| Issue | Cause | Fix |
|---|---|---|
| `awslocal` not found | Install location not on PATH | Add `...Roaming\Python\PythonXXX\Scripts` to PATH permanently |
| `Unable to locate credentials` | Direct `boto3` calls need dummy AWS creds | Set `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_DEFAULT_REGION` env vars |
| `ModuleNotFoundError: localstack_client` inside venv | `awscli-local` only installed globally, not in venv | `pip install awscli awscli-local` inside the venv too |
| Inline JSON payloads corrupted (`Runtime.UnmarshalError`) | PowerShell strips embedded quotes from single-quoted strings passed to external `.exe`s | Use `--payload file://payload.json` instead of inline JSON |
| Redis/SQS unreachable from inside a deployed Lambda | `localhost`-style hostnames resolve to the Lambda's own container, not the host machine | Use `host.docker.internal` for any service published on the host |
| `awslocal logs tail` / `--cli-binary-format` not recognized | Machine has AWS CLI **v1**, not v2 | Use v1-compatible commands (`describe-log-streams` + `get-log-events`) and drop v2-only flags |
| Log stream name lookups fail (`ResourceNotFoundException`) | Log stream names contain `$LATEST`; double-quoting in PowerShell tries to interpolate it as a variable | Always **single-quote** log stream names |

---

## What's next

- Hand off `processor_lambda/handler.py` to the teammate building the LangGraph/AI moderation logic — the batch shape (`event["Records"]`, each with a JSON body containing `id`, `type`, `content`) is now a stable, tested contract.
- Add a Redis TTL (30 days per the original plan) once results are written back to the cache.
- Consider scripting steps 1–7 into a single `setup.ps1` or a SAM `template.yaml` for easier teardown/rebuild.
- The image-upload pipeline (S3 → pHash → Redis → Image SQS queue) is a separate, not-yet-started piece of work using the same patterns.
