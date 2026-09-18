# Onboarding Guide: Set Up & Test the Moderation Pipeline From Scratch

This guide takes you from **zero installed tools** to a **working, tested pipeline** after cloning this repo. Follow it in order — later steps assume earlier ones are done.

**What you'll end up with:** a local HTTP endpoint (`POST /moderate/text`) backed by a Redis cache, an SQS queue, and two Lambda functions, all running inside LocalStack (an AWS emulator) on your machine. No AWS account, no real cloud costs.

**Platform:** these instructions assume **Windows with WSL2**. If you're on macOS/Linux, skip the WSL steps — Docker Desktop's Linux container backend works natively.

---

## Part 1 — Install prerequisites

### 1.1 Install WSL2 + Ubuntu

Docker Desktop on Windows needs WSL2 as its backend. Open **PowerShell as Administrator** and run:

```powershell
wsl --install
```

This installs WSL2 and Ubuntu by default. **Restart your machine** when prompted.

After restart, Ubuntu should launch automatically to finish setup — it'll ask you to create a Linux username and password (these are separate from your Windows login; pick anything memorable).

**Verify:**
```powershell
wsl --status
```
Should show WSL version 2 and Ubuntu as your default distro.

### 1.2 Install Docker Desktop

1. Download Docker Desktop for Windows from [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/).
2. Run the installer. When prompted, make sure **"Use WSL 2 instead of Hyper-V"** is checked (it's the default on modern installs).
3. Once installed, launch Docker Desktop. Wait for the whale icon in your system tray to show it's running (not "starting...").
4. Go to **Settings → Resources → WSL Integration** and make sure integration with your Ubuntu distro is **enabled**.

**Verify** (in PowerShell or a new terminal):
```powershell
docker --version
docker ps
```
`docker ps` should return an empty table with headers, no errors.

### 1.3 Install Python

If you don't already have Python 3.11+ installed, get it from [python.org/downloads](https://www.python.org/downloads/). During install, **check "Add Python to PATH"**.

**Verify:**
```powershell
python --version
```

### 1.4 Install VS Code (or your preferred editor)

From [code.visualstudio.com](https://code.visualstudio.com/) if not already installed. The **Python extension** (by Microsoft) is worth installing for interpreter selection and linting.

### 1.5 Install Git (if not already installed)

From [git-scm.com](https://git-scm.com/downloads). Verify with:
```powershell
git --version
```

---

## Part 2 — Install and configure the LocalStack Docker Desktop Extension

### 2.1 Install the extension

1. Open Docker Desktop.
2. Go to the **Extensions** tab (left sidebar) → **Browse**.
3. Search for **"LocalStack"** and click **Install** on the official LocalStack extension.

### 2.2 Sign in and get your API key

LocalStack's extension needs an API key tied to a (free) LocalStack account to start.

1. Open the LocalStack extension inside Docker Desktop — it opens the LocalStack web application.
2. **Sign up / log in** (a free account is enough to get started; some features shown in the Resource Browser like ElastiCache require a paid Ultimate tier, but everything this pipeline uses — API Gateway, SQS, Lambda, S3, DynamoDB — is on the free "Base" tier).
3. Once logged in, navigate to **Profiles** (usually in the left sidebar or account menu).
4. Find your **API key** and copy it.

### 2.3 Add the API key in Docker Desktop

1. In Docker Desktop, go to the **LocalStack extension's Configuration tab** (sometimes labeled "Config" or found via the extension's settings icon).
2. Create a **new configuration** and paste your API key into it.
3. Save.

### 2.4 Start LocalStack

1. Back in the LocalStack extension panel, click **Start**.
2. Wait for the status indicator to turn green / show "Running". This spins up the `localstack-main` container, which emulates AWS services on `localhost:4566`.

**Verify** (in PowerShell):
```powershell
docker ps
```
You should see a container named something like `localstack-main` with status `Up ... (healthy)`.

---

## Part 3 — Clone the repo and set up your Python environment

### 3.1 Clone the repo

```powershell
cd C:\
mkdir Projects
cd Projects
git clone <YOUR_REPO_URL>
cd <repo-folder-name>\pipeline
code .
```

Adjust the path to wherever you keep your projects — `C:\Projects` is just an example.

### 3.2 Create and activate a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Your terminal prompt should now show `(venv)` at the start.

> If PowerShell blocks the activation script with an execution-policy error, run this once (as your normal user, not admin):
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```
> Then retry activation.

### 3.3 Install Python dependencies

```powershell
pip install boto3 redis awscli awscli-local
```

Installing `awscli`/`awscli-local` **inside the venv** (not just globally) avoids a known issue where the `awslocal` command fails with `ModuleNotFoundError: No module named 'localstack_client'` when the venv is active.

**Verify:**
```powershell
awslocal --version
```

### 3.4 Confirm `awslocal` reaches LocalStack

```powershell
awslocal sqs list-queues
```
Should return `{"QueueUrls": []}` with no errors — confirms LocalStack (started in Part 2) is reachable.

### 3.5 Set dummy AWS credentials for this session

Some direct `boto3` calls (used by the Lambda code, and by some deploy scripts) require *some* AWS credentials to be present, even though LocalStack doesn't check them for validity:

```powershell
$env:AWS_ACCESS_KEY_ID = "test"
$env:AWS_SECRET_ACCESS_KEY = "test"
$env:AWS_DEFAULT_REGION = "us-east-1"
```

> **Note:** These environment variables only last for the current terminal session. You'll need to re-run this block (and the ones in 3.3 activation) every time you open a fresh terminal to work on this project.

---

## Part 4 — Start Redis

The repo includes a `docker-compose.yml` in the `pipeline/` folder that defines the Redis cache container.

```powershell
cd C:\Projects\<repo-folder-name>\pipeline
docker compose up -d
```

**Verify:**
```powershell
docker ps
docker exec -it moderation-redis redis-cli ping
```
Should return `PONG`.

---

## Part 5 — Recreate the AWS resources in LocalStack

> **Important:** LocalStack's emulated AWS resources (queues, functions, API Gateway) are **not** stored in Git — they only exist inside the running LocalStack container's memory/state. Since this is a fresh LocalStack instance, you need to recreate the queue, both Lambda functions, and the API Gateway from scratch using the code already in the repo.

### 5.1 Create the SQS queue

```powershell
awslocal sqs create-queue --queue-name moderation-text-queue
```

Save the returned `QueueUrl` — you'll need it below. It'll look like:
```
http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/moderation-text-queue
```

**Verify:**
```powershell
awslocal sqs list-queues
```

### 5.2 Package and deploy the Ingestion Lambda

```powershell
cd lambda_ingestion
mkdir package
pip install -r requirements.txt -t package
Copy-Item handler.py package\ -Force
cd package
Compress-Archive -Path .\* -DestinationPath ..\function.zip -Force
cd ..
```

```powershell
awslocal lambda create-function `
  --function-name ingestion-lambda `
  --runtime python3.12 `
  --handler handler.lambda_handler `
  --zip-file fileb://function.zip `
  --role arn:aws:iam::000000000000:role/lambda-role `
  --environment "Variables={REDIS_HOST=host.docker.internal,QUEUE_NAME=moderation-text-queue,SQS_ENDPOINT_URL=http://host.docker.internal:4566}"
```

`host.docker.internal` is Docker Desktop's special DNS name that lets any container reach services published on your host machine (Redis on 6379, LocalStack's edge port on 4566) — this is required because the Lambda runs in its own separate container.

**Verify:**
```powershell
awslocal lambda list-functions --query "Functions[].FunctionName" --output text
```
Should include `ingestion-lambda`.

### 5.3 Test the Ingestion Lambda directly (before wiring up HTTP)

The repo includes sample payload files. From the `lambda_ingestion` folder:

```powershell
awslocal lambda invoke --function-name ingestion-lambda --payload file://payload_miss.json output.json
Get-Content output.json
```
Expected: `statusCode: 202`, `"source": "queued"`.

```powershell
awslocal lambda invoke --function-name ingestion-lambda --payload file://payload_hit.json output2.json
Get-Content output2.json
```
This one will show `"source": "queued"` too on a **fresh** LocalStack instance, since nothing is cached yet — that's expected. To actually test the cache-hit path, seed Redis first:
```powershell
docker exec -it moderation-redis redis-cli set "some cached phrase" "yellow"
awslocal lambda invoke --function-name ingestion-lambda --payload file://payload_hit.json output2.json
Get-Content output2.json
```
Now expect: `statusCode: 200`, `"source": "cache"`, `"flag": "yellow"`.

> **Windows note:** always pass payloads via `--payload file://payload.json` rather than inline JSON strings — PowerShell mangles embedded quotes in single-quoted inline arguments and causes a `Runtime.UnmarshalError`.

### 5.4 Deploy the Processor Lambda (stub)

```powershell
cd ..\processor_lambda
Compress-Archive -Path .\handler.py -DestinationPath .\function.zip -Force

awslocal lambda create-function `
  --function-name processor-lambda `
  --runtime python3.12 `
  --handler handler.lambda_handler `
  --zip-file fileb://function.zip `
  --role arn:aws:iam::000000000000:role/lambda-role
```

### 5.5 Connect the queue to the Processor Lambda with the batching rule

```powershell
$QUEUE_URL = "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/moderation-text-queue"
$QUEUE_ARN = awslocal sqs get-queue-attributes --queue-url $QUEUE_URL --attribute-names QueueArn --query "Attributes.QueueArn" --output text

awslocal lambda create-event-source-mapping `
  --function-name processor-lambda `
  --event-source-arn $QUEUE_ARN `
  --batch-size 20 `
  --maximum-batching-window-in-seconds 60
```

**Verify:**
```powershell
awslocal lambda list-event-source-mappings --function-name processor-lambda
```
Check `"State": "Enabled"`.

### 5.6 Wire up API Gateway

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

> **Save `$API_ID` somewhere** (write it down, or echo it: `$API_ID`) — you'll need it for every test request, and it only persists for the current terminal session.

---

## Part 6 — Test the full pipeline with a real API request

### 6.1 Send a cache-miss request

```powershell
$body = '{"type":"text","content":"feeling bored today"}'
Invoke-RestMethod -Uri "http://localhost:4566/restapis/$API_ID/local/_user_request_/moderate/text" -Method POST -Body $body -ContentType "application/json"
```

**Expected output:**
```
source id                                   content              status
------ --                                   -------              ------
queued <some-uuid>                          feeling bored today  pending
```

### 6.2 Send a cache-hit request

Since you already seeded `"some cached phrase" → "yellow"` in Redis (Part 5.3), test that path via HTTP too:

```powershell
$bodyHit = '{"type":"text","content":"some cached phrase"}'
Invoke-RestMethod -Uri "http://localhost:4566/restapis/$API_ID/local/_user_request_/moderate/text" -Method POST -Body $bodyHit -ContentType "application/json"
```

**Expected output:**
```
source content            flag
------ -------            ----
cache  some cached phrase yellow
```

### 6.3 Confirm the message reached SQS

```powershell
awslocal sqs receive-message --queue-url $QUEUE_URL
```
Should show the `"feeling bored today"` message body (JSON with `id`, `type`, `content`).

### 6.4 Confirm the batching trigger fires

Wait about 60–90 seconds after sending step 6.1's request (LocalStack's batch window polling isn't perfectly instant), then check the Processor Lambda's logs:

```powershell
awslocal logs describe-log-streams --log-group-name /aws/lambda/processor-lambda --order-by LastEventTime --descending
```

Copy the most recent `logStreamName` from the output, then (**use single quotes** — the name contains `$LATEST`, which PowerShell will otherwise try to interpret as a variable and corrupt):

```powershell
awslocal logs get-log-events --log-group-name /aws/lambda/processor-lambda --log-stream-name '<PASTE_STREAM_NAME_HERE>'
```

You should see log lines like:
```
Processor Lambda triggered with a batch of 1 message(s).
  - id=<uuid> type=text content='feeling bored today'
```

### 6.5 Visual confirmation in the LocalStack web app

Open the LocalStack extension in Docker Desktop → **Resource Browser**:
- **SQS** → `moderation-text-queue` should exist, message count back to `0` after the batch was consumed
- **Lambda** → both `ingestion-lambda` and `processor-lambda` should be listed
- **API Gateway** → `moderation-api` with the `/moderate/text` resource

---

## Troubleshooting quick reference

| Symptom | Likely cause | Fix |
|---|---|---|
| `awslocal` command not found | Not on PATH | Reinstall inside the venv (`pip install awscli awscli-local`), or add the global install's Scripts folder to PATH |
| `Unable to locate credentials` | Missing dummy AWS creds for direct `boto3` calls | Re-run the Part 3.5 env var block |
| `ModuleNotFoundError: localstack_client` | `awscli-local` only installed globally, not in active venv | `pip install awscli awscli-local` while venv is active |
| `Runtime.UnmarshalError` on `lambda invoke` | Inline JSON payload quotes stripped by PowerShell | Use `--payload file://payload.json` instead |
| Lambda times out / can't reach Redis or SQS | Using `localhost` instead of `host.docker.internal` in Lambda env vars | Redeploy/update with `host.docker.internal` for `REDIS_HOST` and `SQS_ENDPOINT_URL` |
| `awslocal logs tail` / `--cli-binary-format` unrecognized | Machine has AWS CLI v1, not v2 | Use `describe-log-streams` + `get-log-events`; drop v2-only flags |
| Log stream lookup fails (`ResourceNotFoundException`) | `$LATEST` in the stream name gets mangled by double quotes | Always single-quote log stream names |
| LocalStack extension won't start | Invalid/missing API key, or not signed in | Re-check Part 2.2–2.3, confirm the key was pasted correctly into the Docker Desktop configuration |

---

## Recap: full command sequence (copy-paste block)

For reference, here's every setup command back-to-back once prerequisites (Parts 1–2) are done, assuming you're starting a fresh terminal in the `pipeline/` folder:

```powershell
# Environment
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install boto3 redis awscli awscli-local
$env:AWS_ACCESS_KEY_ID = "test"
$env:AWS_SECRET_ACCESS_KEY = "test"
$env:AWS_DEFAULT_REGION = "us-east-1"

# Redis
docker compose up -d

# SQS
awslocal sqs create-queue --queue-name moderation-text-queue

# Ingestion Lambda
cd lambda_ingestion
mkdir package
pip install -r requirements.txt -t package
Copy-Item handler.py package\ -Force
cd package
Compress-Archive -Path .\* -DestinationPath ..\function.zip -Force
cd ..
awslocal lambda create-function --function-name ingestion-lambda --runtime python3.12 --handler handler.lambda_handler --zip-file fileb://function.zip --role arn:aws:iam::000000000000:role/lambda-role --environment "Variables={REDIS_HOST=host.docker.internal,QUEUE_NAME=moderation-text-queue,SQS_ENDPOINT_URL=http://host.docker.internal:4566}"

# Processor Lambda
cd ..\processor_lambda
Compress-Archive -Path .\handler.py -DestinationPath .\function.zip -Force
awslocal lambda create-function --function-name processor-lambda --runtime python3.12 --handler handler.lambda_handler --zip-file fileb://function.zip --role arn:aws:iam::000000000000:role/lambda-role

$QUEUE_URL = "http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/moderation-text-queue"
$QUEUE_ARN = awslocal sqs get-queue-attributes --queue-url $QUEUE_URL --attribute-names QueueArn --query "Attributes.QueueArn" --output text
awslocal lambda create-event-source-mapping --function-name processor-lambda --event-source-arn $QUEUE_ARN --batch-size 20 --maximum-batching-window-in-seconds 60

# API Gateway
cd ..
$API_ID = awslocal apigateway create-rest-api --name "moderation-api" --query "id" --output text
$ROOT_ID = awslocal apigateway get-resources --rest-api-id $API_ID --query "items[?path=='/'].id" --output text
$MODERATE_ID = awslocal apigateway create-resource --rest-api-id $API_ID --parent-id $ROOT_ID --path-part moderate --query "id" --output text
$TEXT_ID = awslocal apigateway create-resource --rest-api-id $API_ID --parent-id $MODERATE_ID --path-part text --query "id" --output text
awslocal apigateway put-method --rest-api-id $API_ID --resource-id $TEXT_ID --http-method POST --authorization-type NONE
$LAMBDA_ARN = "arn:aws:lambda:us-east-1:000000000000:function:ingestion-lambda"
$INTEGRATION_URI = "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations"
awslocal apigateway put-integration --rest-api-id $API_ID --resource-id $TEXT_ID --http-method POST --type AWS_PROXY --integration-http-method POST --uri $INTEGRATION_URI
awslocal lambda add-permission --function-name ingestion-lambda --statement-id apigateway-invoke --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:us-east-1:000000000000:$API_ID/*/POST/moderate/text"
awslocal apigateway create-deployment --rest-api-id $API_ID --stage-name local

# Test
$body = '{"type":"text","content":"feeling bored today"}'
Invoke-RestMethod -Uri "http://localhost:4566/restapis/$API_ID/local/_user_request_/moderate/text" -Method POST -Body $body -ContentType "application/json"
```

> **Tip:** this whole block would make a great `setup.ps1` script for the repo — worth considering as a follow-up so new teammates don't have to run this manually at all.
