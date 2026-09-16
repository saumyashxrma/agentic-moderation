# agentic-moderation
Cost-effective, multi-agent content moderation API built on AWS open-source stack
# 🛡️ Agentic Moderation API

A cost-effective, context-aware content moderation API built on the AWS open-source stack.

## 🎯 The Problem
Content moderation is expensive and slow. Calling an LLM for every piece of content is prohibitively costly, and free solutions lack context-awareness.

## 💡 Our Solution
A multi-agent system that combines exact-match caching (via text normalization and perceptual hashing) with micro-batched LLM processing, dramatically reducing costs while maintaining accuracy.

## 🏗️ Architecture
Client → Ingestion API → Cache Check → SQS Queue → Processor Lambda → Multi-Agent Pipeline → Webhook
                                    (Cache Hit → Instant Return)

## ☁️ AWS Services & Tools Used
- **Strands Agents SDK**: Multi-agent orchestration
- **AWS SAM + LocalStack**: Local serverless development
- **Amazon Bedrock**: Foundation model access (Ship It track)
- **Amazon SQS**: Asynchronous micro-batching

## 🚀 Getting Started
See `CONTRIBUTING.md` for full setup instructions.

## 📄 License
MIT