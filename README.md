# AlgoQX Studio

The Operating System for Enterprise AI.

AlgoQX Studio is a production-grade AI engineering platform designed to inspect, build, evaluate, and secure LLM-powered applications. It features 10 core modules providing tokenizers, prompt engineering comparison environments, RAG studio indices, LangGraph multi-agent visual builders, and privacy guardrails.

## Features

- **LLM Explorer**: Tokenizer tracking, context window gauge indicators, and high-dimensional embeddings space visualizations.
- **Prompt Lab**: Side-by-side comparison of prompt strategies (zero-shot, few-shot, CoT, etc.) analyzing latency, cost, and output consistency.
- **RAG Studio**: Custom loaders (PDF, DOCX, TXT), FAISS vector store creation, and hallucination and groundedness evaluation metrics.
- **Agent Builder**: Graph builder using node connections (Planner, Researcher, Retriever, Reasoner, Writer, Reviewer) backed by LangGraph execution loops.
- **Model Context Protocol (MCP)**: Dynamic tool discovery and transport connection compared against REST API endpoints.
- **Application Builder**: Automatic code generation for FastAPI backends, Streamlit frontends, and OpenAPI/Swagger schemas.
- **Security Center**: Scanner checking prompts for injections, jailbreaks, system leaks, and OWASP Top 10 vulnerabilities metrics.
- **Privacy Center**: Pre-inference PII masking (Aadhaar, PAN, Emails, Credit Cards, API Keys) using redact, hash, or mask strategies.
- **Observability**: Trace logs mapping execution steps, timings, cost totals, and replay actions.
- **Analytics**: Historical dashboards graphing platform traffic, latency variations, model shares, and costs.

## Technical Architecture

- **Backend**: FastAPI, Async SQLAlchemy, SQLite, OpenAI Python SDK.
- **Frontend**: Streamlit, Plotly, custom CSS themes.
- **Vector Space**: FAISS, sentence-transformers (BAAI/bge-small-en-v1.5).
- **Package Manager**: Astral uv.

## Getting Started

### Local Setup (using uv)

1. Create a virtual environment and sync dependencies:
   ```bash
   uv venv
   # On Windows
   .venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate
   
   uv pip install -e .
   ```

2. Copy configuration environment:
   ```bash
   cp .env.example .env
   ```

3. Launch backend API server:
   ```bash
   python -m backend.main
   ```

4. Launch Streamlit UI frontend:
   ```bash
   streamlit run frontend/app.py
   ```

### Docker Compose Deployment

Ensure you have Docker and Docker Compose installed:

```bash
docker-compose build
docker-compose up -d
```

Access the API documentation at `http://localhost:8000/docs` and the user interface at `http://localhost:8501`.
