# Team Setup Guide (Windows)

## Prerequisites
- Python 3.10+
- Docker Desktop
- AWS SAM CLI
- Git for Windows

## Setup
1. Clone the repo
2. Create a virtual environment: `python -m venv .venv`
3. Activate it: `.venv\Scripts\activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Start local services: `docker-compose up -d`

## Branch Workflow
- Pull latest: `git checkout main && git pull`
- New branch: `git checkout -b feature/name`
- Commit: `git add . && git commit -m "message"`
- Push: `git push origin feature/name`
- Open a Pull Request on GitHub

## Ownership
- Dev A: `src/ingestion/`, `src/agents/`
- Dev B: `src/processor/`, `template.yaml`, `docker-compose.yml`