# 🏗️ Multimodal AI Content Auto-Moderation API

## 🛠️ Tech Stack

**Core Infrastructure (Local Environment)**
*   **LocalStack:** Emulates AWS services locally without an AWS account or cloud costs.
    *   **API Gateway:** Receives text payloads.
    *   **S3:** Handles local image uploads.
    *   **SQS:** Buffers incoming requests and handles micro-batching.
    *   **Lambda:** Serverless compute for Ingestion and Processing scripts.
    *   **DynamoDB:** Stores the final moderation results locally.
*   **Docker / Docker Compose:** Orchestrates LocalStack and Redis containers.

**Caching & Storage**
*   **Redis:** Local Docker container acting as an exact-match cache for normalized text strings and image pHashes.

**AI & Orchestration**
*   **LangGraph:** Orchestrates the multi-agent state machine (Tone, Policy, and Supervisor agents) to allow advanced routing and parallel execution.
*   **Gemini API (gemini-1.5-flash):** The multimodal foundational model powering the reasoning agents.
*   **Python:** The core language for Lambda functions and LangGraph scripts.

---

## 🔄 Project Flow

1.  **Ingestion:** A client sends a POST request with text to the LocalStack API Gateway OR uploads an image to the LocalStack S3 bucket.
2.  **Cache Check:** This action triggers the **Ingestion Lambda**, which normalizes the text or calculates the image pHash. It checks the local **Redis** cache.
    *   *Cache Hit:* The process stops.
    *   *Cache Miss:* The payload is packaged and pushed to the **LocalStack SQS Queue**.
3.  **Batching:** The SQS Queue holds the messages until the configured batch size (e.g., 10-20 items) or time window (60-300 seconds) is reached.
4.  **Processing:** SQS triggers the **Processor Lambda**, which pulls the batch and fetches any required images from S3.
5.  **AI Evaluation:** The batch is routed through **LangGraph**, where the multi-agent setup (Tone Agent and Policy Agent) evaluates the content using the **Gemini API**. A Supervisor Agent synthesizes the final moderation flag (Green, Yellow, or Red).
6.  **Resolution:** The Processor Lambda caches the new results in Redis and writes the final structured output to the **LocalStack DynamoDB** table.

---

## 🤝 Team Split

### 🧠 Dev A — Application & Agentic AI Lead
*Owns the "brain" and business logic—everything that processes the text, orchestrates the AI, and decides the moderation result.*

| Responsibility | Details |
| :--- | :--- |
| **Ingestion Lambda Logic** | Write the Python code to handle request validation, UUID generation, and extracting payloads from API Gateway or S3. |
| **Normalization & Caching** | Write functions to clean text, hash images, and check the Redis container for exact matches. |
| **LangGraph Orchestration** | Build the 3-agent pipeline (Tone, Policy, Supervisor) and define the strict `State` object for advanced routing. |
| **Gemini API Integration** | Write system prompts and configure the integration to route LangGraph nodes to the Gemini 1.5 Flash model. |
| **DynamoDB Formatting** | Ensure the final LangGraph output is formatted as a strict JSON dictionary matching the required database schema. |

### 🛠️ Dev B — Infrastructure & Data Pipeline Lead
*Owns the "plumbing"—everything that provisions resources, moves data, and stores the final result.*

| Responsibility | Details |
| :--- | :--- |
| **LocalStack & Docker** | Configure `docker-compose.yml` to spin up LocalStack (API Gateway, S3, SQS, Lambda, DynamoDB) alongside Redis. |
| **AWS SAM Template** | Write `template.yaml` to define the infrastructure-as-code for Lambdas, SQS queues, API Gateway, and DynamoDB. |
| **SQS Event Triggers** | Set up batch sizes and time windows for the Text and Image queues, mapping them as triggers to the Processor Lambda. |
| **LocalStack S3 Config** | Configure the S3 Bucket in the SAM template to handle local image uploads and trigger the Ingestion Lambda. |
| **Processor Lambda (Data)** | Build the Python shell that polls SQS, fetches images from S3, passes the batch to Dev A's LangGraph app, and writes results to DynamoDB. |