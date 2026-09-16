```markdown
# 🛠️ Setup Guide — Agentic Moderation API

**Read this top to bottom before asking for help.** It contains everything you need to get the project running on your machine.

---

## 📋 Prerequisites

Install these **before** cloning the repo.

| Tool | Version | Download Link |
| :--- | :--- | :--- |
| **Python** | 3.10 or higher | https://www.python.org/downloads/ |
| **Docker Desktop** | Latest | https://www.docker.com/products/docker-desktop/ |
| **AWS SAM CLI** | Latest | https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html |
| **Git for Windows** | Latest | https://git-scm.com/downloads |

**Verify each is installed** by opening a fresh Command Prompt and running:

```cmd
python --version
docker --version
sam --version
git --version
```

Each should print a version number. If any says "not recognized," reinstall that tool.

**Critical:** Docker Desktop must be **running** (green whale icon in the system tray) before you proceed. If Docker isn't running, every `docker` command will fail with "cannot connect to the Docker daemon."

---

## 📥 Step 1: Clone the Repository

Open **Command Prompt** (`Win + R` → type `cmd` → Enter). Run:

```cmd
cd %USERPROFILE%\Documents
git clone https://github.com/YOUR_USERNAME/moderation-api-hackathon.git
cd moderation-api-hackathon
```

> Replace `YOUR_USERNAME` with the actual GitHub username of the repo owner. Ask the team lead if unsure.

You should now be inside the project folder. Verify:

```cmd
dir
```

You should see: `README.md`, `CONTRIBUTING.md`, `SETUP.md`, `docker-compose.yml`, `requirements.txt`, `.env.example`, `src\`, `docs\`, `tests\`.

---

## 🐍 Step 2: Create the Python Virtual Environment

**Why a virtual environment:** It isolates this project's Python packages from every other Python project on your machine. Without it, package versions conflict across projects and "it works on my machine" bugs multiply.

Still in the project folder, run **one command at a time**:

```cmd
python -m venv .venv
```

Wait for it to finish (takes 10–30 seconds). Then activate it:

```cmd
.venv\Scripts\activate
```

**You should now see `(.venv)` at the start of your prompt**, like this:

```
(.venv) D:\...\moderation-api-hackathon>
```

If you don't see it, the activation failed. **Do not proceed** — every subsequent command will install packages globally instead of into the project. Tell the team lead.

**If you're using PowerShell instead of cmd**, the activation command is:

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks it with an execution policy error, run this first:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

---

## 📦 Step 3: Install Python Dependencies

With the venv active (you see `(.venv)` in the prompt), run:

```cmd
python -m pip install --upgrade pip
```

Then install the project's dependencies:

```cmd
pip install -r requirements.txt
```

This installs: FastAPI, uvicorn, boto3, redis, Pillow, ImageHash, requests, python-dotenv, **Strands Agents**, pytest, httpx.

**Takes 2–5 minutes.** You'll see a lot of output. Ignore the "Requirement already satisfied" lines — that's normal.

**When it finishes, verify every critical package imports correctly:**

```cmd
python -c "import fastapi; print('fastapi OK')"
```

```cmd
python -c "import boto3; print('boto3 OK')"
```

```cmd
python -c "import redis; print('redis OK')"
```

```cmd
python -c "import PIL; print('Pillow OK')"
```

```cmd
python -c "import imagehash; print('ImageHash OK')"
```

```cmd
python -c "import strands; print('Strands OK')"
```

**Each should print `OK`.** If any raises an error, paste the exact error into the team chat before proceeding.

---

## 🔧 Step 4: Create Your `.env` File

The repo ships with `.env.example` — a template. You need to copy it to `.env` to activate it.

```cmd
copy .env.example .env
```

**Why:** `.env` is gitignored (it may contain secrets later), so it doesn't come with the clone. `.env.example` is the committed template. The copy is your personal working config.

Verify:

```cmd
type .env
```

You should see:

```
AWS_ENDPOINT_URL=http://localhost:4566
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
REDIS_HOST=localhost
REDIS_PORT=6379
TEXT_QUEUE_NAME=moderation-text-queue
IMAGE_QUEUE_NAME=moderation-image-queue
S3_BUCKET_NAME=moderation-images
...
```

**If `AWS_ENDPOINT_URL` is missing or commented out, stop.** The app will try to hit real AWS and fail with `InvalidClientTokenId`. Tell the team lead.

---

## 🐳 Step 5: Start the Docker Services

**Ensure Docker Desktop is running first.** Then:

```cmd
docker-compose up -d
```

Wait ~10 seconds, then verify:

```cmd
docker ps
```

**Expected:** Two containers listed, both `Up`:

```
CONTAINER ID   IMAGE                              ...   NAMES
xxxxxxxxxxxx   valkey/valkey:latest               ...   valkey
xxxxxxxxxxxx   localstack/localstack:3.8.1        ...   localstack
```

**If `localstack` is missing:** It crashed on startup. Check why:

```cmd
docker logs localstack
```

The most common cause is a wrong LocalStack image tag. Confirm your `docker-compose.yml` says `localstack/localstack:3.8.1` and **not** `latest`. The `latest` tag now points to the Pro version which requires a license.

**Fix if needed:**

```cmd
docker-compose down --remove-orphans
docker-compose up -d
timeout /t 20 /nobreak >nul
docker ps
```

**If you see a warning about "orphan containers (minio)":** That's harmless — it's a leftover from an earlier setup. Clean it up once with:

```cmd
docker-compose down --remove-orphans
```

---

## 🧪 Step 6: Verify LocalStack Is Healthy

```cmd
curl http://localhost:4566/_localstack/health
```

You should get JSON containing `"sqs": "available"`, `"s3": "available"`, and `"edition": "community"`.

**If you get a connection error:** LocalStack isn't running. Go back to Step 5.

---

## 📮 Step 7: Create the SQS Queues and S3 Bucket

LocalStack starts **empty** — no queues, no buckets. You must create them once per LocalStack restart.

**Run each command separately.** Do not paste them all at once — Command Prompt joins multiple pasted lines into one command and breaks them.

### Command 1: Text queue

```cmd
docker exec -it localstack bash -c "awslocal sqs create-queue --queue-name moderation-text-queue"
```

Wait for output. Should show a `QueueUrl`.

### Command 2: Image queue

```cmd
docker exec -it localstack bash -c "awslocal sqs create-queue --queue-name moderation-image-queue"
```

Wait for output.

### Command 3: S3 bucket

```cmd
docker exec -it localstack bash -c "awslocal s3 mb s3://moderation-images"
```

Wait for output. Should say `make_bucket: moderation-images`.

### Verify

```cmd
docker exec -it localstack bash -c "awslocal sqs list-queues"
```

Expected: both queue URLs listed.

```cmd
docker exec -it localstack bash -c "awslocal s3 ls"
```

Expected: `moderation-images` listed.

### Verify Valkey

```cmd
docker exec -it valkey valkey-cli ping
```

Expected: `PONG`.

---

## 🚀 Step 8: Start the API

In your **first** Command Prompt window (with the venv active):

```cmd
uvicorn src.ingestion.app:app --reload --port 8000
```

You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Leave this window running.** It's your live server.

---

## ✅ Step 9: Test the API

Open a **second** Command Prompt window (do **not** close the first). From any folder:

### Health check

```cmd
curl http://localhost:8000/health
```

**Expected:** `{"api":"ok","cache":true}`

### Send a moderation request

```cmd
curl -X POST http://localhost:8000/moderate/text -H "Content-Type: application/json" -d "{\"text\":\"hello world\"}"
```

**Expected:** `{"request_id":"<uuid>","status":"queued","flag":null}`

### Confirm the message landed in SQS

```cmd
docker exec -it localstack bash -c "awslocal sqs get-queue-attributes --queue-url http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/moderation-text-queue --attribute-names ApproximateNumberOfMessages"
```

**Expected:** `"ApproximateNumberOfMessages": "1"`.

**If all three pass, your environment is fully working.** Reply with "setup done" in the team chat.

---

## 🔁 Daily Workflow

**Every morning (or after every restart):**

```cmd
cd %USERPROFILE%\Documents\moderation-api-hackathon
.venv\Scripts\activate
docker-compose up -d
timeout /t 15 /nobreak >nul
docker exec -it localstack bash -c "awslocal sqs create-queue --queue-name moderation-text-queue"
docker exec -it localstack bash -c "awslocal sqs create-queue --queue-name moderation-image-queue"
docker exec -it localstack bash -c "awslocal s3 mb s3://moderation-images"
```

**Why re-create queues each restart:** LocalStack runs with `PERSISTENCE=0` for a clean state, so queues don't survive restarts. This is intentional for testing but means you re-run these commands each session.

**Then start working:**

```cmd
uvicorn src.ingestion.app:app --reload --port 8000
```

---

## 🌿 Git Workflow

**Pull the latest `main` every morning:**

```cmd
git checkout main
git pull origin main
```

**Create a branch for your feature:**

```cmd
git checkout -b feature/your-feature-name
```

**Work, then commit:**

```cmd
git add .
git commit -m "Clear description of what changed"
git push origin feature/your-feature-name
```

**Open a Pull Request** on GitHub. Tag your teammate for review. Merge when it's reviewed.

**After merge, clean up:**

```cmd
git checkout main
git pull origin main
git branch -d feature/your-feature-name
```

**Never push directly to `main`.** Always use a feature branch and a PR.

---

## 👥 Ownership

| Role | Owns | Primary Files |
| :--- | :--- | :--- |
| **Dev A** | Application & Agentic AI | `src/ingestion/`, `src/agents/` |
| **Dev B** | Infrastructure & Pipeline | `src/processor/`, `docker/`, `template.yaml` |
| **Team Lead** | Ideation, demo, README, docs | `docs/`, `README.md` |

**Rule:** Don't edit files outside your ownership without asking in the team chat first. Reduces merge conflicts.

---

## 🔧 Common Problems & Fixes

| Symptom | Cause | Fix |
| :--- | :--- | :--- |
| `ERROR: Error loading ASGI app` | Missing or empty file in `src/` | Run `dir src /s /b`, ensure all files exist and have content |
| `InvalidClientTokenId` | boto3 hitting real AWS | Check `.env` has `AWS_ENDPOINT_URL=http://localhost:4566` |
| `QueueDoesNotExist` | Queue not created in LocalStack | Re-run Step 7 |
| `ConnectionRefusedError` on port 6379 | Valkey container down | `docker ps`, then `docker-compose up -d` |
| `docker: cannot connect to daemon` | Docker Desktop not running | Start Docker Desktop, wait for green icon |
| `localstack` container missing from `docker ps` | Wrong image tag | Ensure `docker-compose.yml` uses `3.8.1`, not `latest` |
| `docker: pull access denied` | Network or image issue | Check internet, then `docker-compose pull` |
| `ERROR: ResolutionImpossible` on `pip install` | Conflicting package versions | Delete `.venv`, recreate with `python -m venv .venv`, then `pip install -r requirements.txt` |
| Webhook never receives data | Processor not implemented yet | Expected — Dev B's job |
| `ModuleNotFoundError: No module named 'src'` | Running Python from wrong folder | `cd` to project root, ensure `.venv` is active |

---

## 🧭 How the Pieces Fit Together

```
┌─────────────────────────────────────────────────────────────┐
│  Your Laptop                                                 │
│                                                              │
│  ┌───────────────────────┐    ┌──────────────────────────┐  │
│  │  Python venv (.venv)  │    │  Docker: valkey          │  │
│  │  FastAPI (port 8000)  │───▶│  port 6379               │  │
│  │  Strands agents       │    │  Cache flags             │  │
│  │  Processor (Dev B)    │    └──────────────────────────┘  │
│  │                       │                                   │
│  │                       │    ┌──────────────────────────┐  │
│  │                       │───▶│  Docker: localstack      │  │
│  └───────────────────────┘    │  port 4566               │  │
│                                │  Fakes SQS + S3          │  │
│                                └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**In words:** Your Python code runs on Windows. It talks to Valkey for caching and LocalStack for SQS/S3. Everything is local, free, and identical to production — only the endpoint URLs will change when you deploy.

---

## 🎯 Where to Start Coding

Once your environment is verified working:

**Dev A** — Open `src/agents/orchestrator.py`. Test the Strands supervisor:

```cmd
python -c "from src.agents.orchestrator import build_supervisor; sup = build_supervisor(); print(sup('You are an idiot'))"
```

Get it returning a real flag. Then wire it into `src/processor/handler.py::process_batch`.

**Dev B** — Open `src/processor/handler.py`. Make `process_batch` pull from SQS, invoke the supervisor, write to Valkey, and POST to webhook. Test with:

```cmd
docker exec -it localstack bash -c "awslocal sqs send-message --queue-url http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/moderation-text-queue --message-body '{\"request_id\":\"test-1\",\"text\":\"hello\"}'"
```

**Team Lead** — Draft `docs/demo-script.md`. Outline the 3-minute demo video: problem, solution, live demo, AWS fit, what you learned.

---

## 📚 Reference Commands

**Docker:**

```cmd
docker ps                                  # list running containers
docker logs localstack                     # see LocalStack logs
docker logs -f localstack                  # follow logs live
docker-compose down                        # stop everything
docker-compose up -d                       # start everything
docker-compose down --remove-orphans       # clean stop (removes stale containers)
```

**LocalStack inspection:**

```cmd
docker exec -it localstack bash -c "awslocal sqs list-queues"
docker exec -it localstack bash -c "awslocal s3 ls"
docker exec -it localstack bash -c "awslocal sqs get-queue-attributes --queue-url <URL> --attribute-names All"
```

**Valkey inspection:**

```cmd
docker exec -it valkey valkey-cli ping
docker exec -it valkey valkey-cli KEYS "*"
docker exec -it valkey valkey-cli GET "text:<hash>"
```

**API:**

```cmd
curl http://localhost:8000/health
curl http://localhost:8000/docs                # interactive API docs in browser
```

---

