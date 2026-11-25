# Lyftr AI — LLM Chatbot with Key Failover and Response Caching

Production-grade, highly resilient full-stack LLM Chat application built with FastAPI, LiteLLM, SQLite, React, Vite, and Tailwind CSS. Features automatic multi-key failover with sequential retries, deterministic response caching, multi-turn session persistence, and comprehensive request metadata tracking.

---

## 1. Live URLs

- **GitHub Repository**: [https://github.com/Amncodes/lyftr-ai](https://github.com/Amncodes/lyftr-ai)
- **Frontend Application (Vercel)**: `https://lyftr-ai-chat.vercel.app` *(Pending manual domain binding / provider deployment)*
- **Backend API Gateway (Render)**: `https://lyftr-ai-backend.onrender.com` *(Configured via `render.yaml`)*
- **Local Development**:
  - Frontend: [http://localhost:3000](http://localhost:3000)
  - Backend: [http://localhost:8000](http://localhost:8000)
  - Health Check: [http://localhost:8000/health](http://localhost:8000/health)

---

## 2. Run locally: with Docker and without

### Environment Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Ensure your `.env` contains:

```env
LLM_API_KEYS=your_key_1,your_key_2
LLM_MODEL=openai/gpt-4o-mini
LLM_PROVIDER=openai
LLM_API_BASE=
DATABASE_URL=sqlite:////data/app.db
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
ENABLE_FAILURE_SIMULATION=true
LITELLM_CACHE_ENABLED=true
VITE_API_BASE_URL=http://localhost:8000
```

---

### Option A: Running with Docker & Docker Compose (Recommended)

Requires Docker & Docker Compose installed.

1. **Start both Backend and Frontend**:
   ```bash
   make up
   ```
   *Or with Docker Compose directly:*
   ```bash
   docker compose up -d --build
   ```

2. **View Live Container Logs**:
   ```bash
   make logs
   ```

3. **Stop Containers**:
   ```bash
   make down
   ```

The backend starts at `http://localhost:8000` and the frontend at `http://localhost:3000`. The SQLite database persists across container restarts via the `lyftr_data` named Docker volume mounted at `/data`.

---

### Option B: Running Locally without Docker

#### 1. Backend Setup (Python 3.11+)

```bash
# Navigate to backend directory
cd backend

# Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend test suite
pytest tests/ -v

# Start FastAPI development server
PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend Setup (Node.js 18+)

```bash
# In a new terminal, navigate to frontend directory
cd frontend

# Install npm dependencies
npm install

# Run Vite development server
npm run dev
# Or build and preview production build on port 3000:
npm run build && npm run preview -- --port 3000 --host
```

---

## 3. Design decisions: key fallback, caching, SQLite session storage

### Architecture Overview

```
                      ┌─────────────────────────────────────────┐
                      │          React SPA (Port 3000)          │
                      │  Tailwind CSS + Lucide Icons + Vite     │
                      └────────────────────┬────────────────────┘
                                           │ HTTP REST (JSON)
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │       FastAPI Gateway (Port 8000)       │
                      │ ├── /health                             │
                      │ ├── /chat                               │
                      │ └── /sessions/{session_id}/messages     │
                      └────┬───────────────┬────────────────────┘
                           │               │
            ┌──────────────┴──────┐        └──────────────┐
            ▼                     ▼                       ▼
┌───────────────────────┐ ┌───────────────┐ ┌───────────────────────────┐
│ LiteLLM Response Cache│ │ LiteLLM Router│ │      SQLite Database      │
│  - Exact Cache Key    │ │  Key Pool:    │ │  - Messages table         │
│  - Input/Output Tokens│ │  [key_1,      │ │  - JSON metadata storage  │
│  - Zero Fallback Meta │ │   key_2, ...] │ │  - Session isolation      │
└───────────────────────┘ └───────┬───────┘ └───────────────────────────┘
                                  ▼
                      ┌───────────────────────┐
                      │ External LLM Provider │
                      │ OpenAI / Anthropic /  │
                      │ Gemini / Mistral / etc│
                      └───────────────────────┘
```

### 1. Key Fallback & Multi-Key Resilience
- **Configurable Pool**: Keys are parsed from `LLM_API_KEYS` into an ordered list mapped to sanitized internal identifiers (`key_1`, `key_2`, ..., `key_N`).
- **No Secret Leakage**: Raw secret tokens are never exposed to frontend clients, API payloads, or standard application logs.
- **Sequential Fallback**: When an active key encounters rate limits (HTTP 429), quota exhaustion, connection timeouts, or provider 5xx outages, the gateway increments `fallback_attempts` and seamlessly transitions to the next available key in the pool.
- **Fail-Safe Exhaustion**: If all configured keys fail, the gateway returns HTTP 503 `{"detail": "all providers unavailable"}` and prevents corrupt or empty records from polluting database history.
- **Simulation Hook**: When `ENABLE_FAILURE_SIMULATION=true`, the `X-Simulate-Failure` header can simulate 429, 500, 502, or 503 errors per-key (`key_1=429`) or globally (`*=429`), isolating test effects strictly to that single request.

### 2. Deterministic Response Caching (LiteLLM Built-in Cache)
- **Granular Compound Key**: Built-in LiteLLM caching differentiates:
  - Configured model identifier (`LLM_MODEL`).
  - Active system prompt.
  - Complete prior conversation turn history.
  - New user message content.
- **Cross-Session Cache Hits**: Submitting the same initial prompt in two distinct sessions produces an instant cache hit on the second request.
- **Cache Hit Contract Compliance**:
  - `resolution_source` is set to `LLM_CACHE`.
  - `key_id` is set to `null`.
  - `fallback_attempts` is set to `0`.
  - Original prompt and completion token counts are preserved.
  - Latency drops to sub-10ms (significantly lower than live inference).

### 3. SQLite Session Storage & Isolation
- **Direct Local Persistence**: Uses SQLite without external database dependencies (no Redis or PostgreSQL required).
- **History Isolation**: Messages are queried strictly by `session_id` ordered by message `id ASC`.
- **System Prompt Secrecy**: Custom system instructions are used solely as runtime LLM context and are never exposed via `/sessions/{session_id}/messages`.
- **Atomic Persistence**: Records are committed only upon verified successful responses, preserving database integrity.

---

## 4. Verification: how to see failover, cache hits and per-message token usage

### A. Health Endpoint Verification

```bash
curl -X GET http://localhost:8000/health
```

Expected output:
```json
{
  "status": "ok",
  "keys_configured": 2,
  "cache_enabled": true
}
```

---

### B. Failover Demonstration using `curl`

#### 1. Key Failover from `key_1` to `key_2` (HTTP 429 simulation)
```bash
curl -i -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-Simulate-Failure: key_1=429" \
  -d '{
    "session_id": "s-test-failover",
    "message": "What is the capital of France?"
  }'
```
Response exhibits:
- `"resolution_source": "LIVE_INFERENCE"`
- `"key_id": "key_2"`
- `"fallback_attempts": 1`

#### 2. All Keys Exhausted Failover (HTTP 503)
```bash
curl -i -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-Simulate-Failure: key_1=429,key_2=500" \
  -d '{
    "session_id": "s-test-all-fail",
    "message": "Hello"
  }'
```
Response status: `HTTP/1.1 503 Service Unavailable`
```json
{
  "detail": "all providers unavailable"
}
```

Verify that the failed request was **not** saved to history:
```bash
curl -i -X GET http://localhost:8000/sessions/s-test-all-fail/messages
```
Returns `HTTP/1.1 404 Not Found`.

---

### C. Cache Demonstration using `curl`

#### Step 1: Initial Prompt in Session 1 (Miss / Live Inference)
```bash
curl -i -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "s-session-alpha",
    "message": "Explain quantum computing in one sentence."
  }'
```
Response metadata contains:
```json
"metadata": {
  "resolution_source": "LIVE_INFERENCE",
  "model": "openai/gpt-4o-mini",
  "latency_ms": 782,
  "input_tokens": 16,
  "output_tokens": 24,
  "key_id": "key_1",
  "fallback_attempts": 0
}
```

#### Step 2: Identical Prompt in a NEW Session 2 (Cache Hit)
```bash
curl -i -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "s-session-beta",
    "message": "Explain quantum computing in one sentence."
  }'
```
Response metadata reflects instant cache retrieval:
```json
"metadata": {
  "resolution_source": "LLM_CACHE",
  "model": "openai/gpt-4o-mini",
  "latency_ms": 2,
  "input_tokens": 16,
  "output_tokens": 24,
  "key_id": null,
  "fallback_attempts": 0
}
```
Notice:
1. `resolution_source` is `LLM_CACHE`.
2. `key_id` is `null`.
3. `fallback_attempts` is `0`.
4. `latency_ms` is orders of magnitude lower.
5. Per-message token usage (`input_tokens`, `output_tokens`) accurately mirrors the cached generation.

---

### D. Automated Pytest Test Suite

Run all 17 automated verification tests:

```bash
make test
```
Or directly:
```bash
cd backend && pytest tests/ -v
```

Verified Test Scenarios:
1. `test_health.py::test_health_endpoint_healthy`
2. `test_health.py::test_health_endpoint_db_failure`
3. `test_health.py::test_health_endpoint_no_keys`
4. `test_chat.py::test_successful_chat_response`
5. `test_chat.py::test_missing_message_validation`
6. `test_chat.py::test_empty_message_validation`
7. `test_chat.py::test_message_exceeding_4000_chars`
8. `test_chat.py::test_correct_per_request_token_metadata`
9. `test_chat.py::test_multi_turn_conversation_context`
10. `test_failover.py::test_key_1_failure_with_key_2_fallback`
11. `test_failover.py::test_all_keys_failing_returns_503`
12. `test_failover.py::test_simulated_failures_not_stored_in_history`
13. `test_cache.py::test_cache_first_request_live_and_second_request_cache_hit`
14. `test_cache.py::test_different_message_does_not_reuse_cache`
15. `test_sessions.py::test_unknown_session_returns_404`
16. `test_sessions.py::test_session_history_retrieval_and_isolation`
17. `test_sessions.py::test_system_prompt_never_exposed_in_history`

---

## 5. Setup Used: editor and AI tools

- **Development Platform**: macOS (Darwin 24.1.0, Apple Silicon)
- **Primary Runtime**: Python 3.14 / 3.11, Node.js v25.8, npm 11.11
- **AI Pairing / Agent System**: Google Antigravity Agentic Assistant powered by Gemini 3.8 Flash
- **Codebase Tools**: Vite, TypeScript Compiler, Pytest, LiteLLM SDK, Uvicorn, SQLAlchemy ORM

---

## 6. Bonus features

1. **Interactive Failure Simulation Controls**: The frontend sidebar includes an intuitive dropdown to set `X-Simulate-Failure` headers on the fly (`key_1=429`, `key_1=500`, `key_1=429,key_2=500`, `*=429`), enabling instant manual verification of failover from the UI.
2. **Real-Time Health Polling**: The frontend continuously tracks `/health` status and shows active keys count and caching state in real time.
3. **Custom System Prompt Drawer**: Easily customize assistant behavior per session via an accordion settings panel (`data-testid="system-prompt-input"`), strictly isolated from public history.
4. **One-Click Prompt Suggestions**: Interactive starter prompts on the welcome screen that instantly demonstrate single-turn inference, multi-turn memory, and caching.
5. **Multi-Stage Docker & Cloud-Ready Artifacts**:
   - `render.yaml` for 1-click Docker backend deployment with persistent disk.
   - `vercel.json` with SPA routing configuration for Vercel edge deployment.
