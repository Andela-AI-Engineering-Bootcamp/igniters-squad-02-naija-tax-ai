# Naija Tax AI

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic_Orchestration-orange.svg)](https://python.langchain.com/docs/langgraph/)
[![MCP](https://img.shields.io/badge/MCP-Enabled-green.svg)](https://modelcontextprotocol.io/)

Privacy-aware Nigerian tax assistance built during a 72-hour sprint as the Agentic AI Engineering Bootcamp capstone. The system helps users work through newly introduced tax rules by combining bank-statement ingestion, PII-safe processing, and a **Human-in-the-Loop (HITL)** flow before any simulated filing step.

**Stack:** **Streamlit** (`ui/`) for uploads, chat, and confirmations; **LangGraph** (`agentic_core/`) orchestrating three logical agents; a local **MCP server** (`mcp_server/`); shared guardrails in `utils/` (exceptions, PII-safe logging).

---

## Architecture

Orchestration uses **LangGraph** with a linear `guardian → strategist → sidekick` graph.

### Agents

1. **Guardian (intake & privacy)** — Only path that should touch raw uploads; scrubs PII before downstream agents see content.
2. **Strategist (tax & law)** — Produces structured tax drafts. The repo currently ships a **placeholder**; wire in LLM + retrieval over official FIRS/NTA sources for production.
3. **Sidekick (filing / HITL)** — Presents figures for explicit user confirmation before a simulated filing step.

### MCP server

Custom **FastMCP** server (`mcp_server/`) exposes tools used by the agents:

| Tool | Role |
|------|------|
| `scrub_pii` | Masks BVN/NUBAN-like sequences in text (see `mcp_server/tools/pii_scrubber.py`). |
| `parse_bank_pdf` | Extracts tables (Camelot) or page text (PyMuPDF) from bank PDFs (`mcp_server/tools/bank_parser.py`). |

Implementation modules are also referred to as `pii_scrubber` and `bank_parser` in squad ownership below.

### Diagram

Add an architecture image (e.g. `architecture.png`) in the repo root and link it here when available.

---

## Guardrails & safety

- **Validation:** Pydantic schemas on structured financial/tax payloads.
- **PII:** Regex-based masking so sensitive banking identifiers are not echoed into LLM context without scrubbing.
- **HITL:** LangGraph interrupts / UI steps so users confirm calculated figures before filing simulation.
- **Degraded input:** Unreadable PDFs should fall back to manual income entry instead of hard-failing (wire in `utils` guardrails as you extend nodes).

---

## Setup

### Prerequisites

- **Docker** and **Docker Compose** (recommended for one-command parity), or **Python 3.10+** for local runs
- **OpenAI API key** (and any other keys in `.env.example`)

### Docker (recommended)

From the repo root:

1. `cp .env.example .env` and set `OPENAI_API_KEY` (and any other required variables).
2. Build and run:

   ```bash
   docker compose build
   docker compose up
   ```

   (`docker-compose` works if your install still uses the hyphenated plugin.)

**Services:**

| Service | URL / notes |
|---------|-------------|
| Streamlit UI | http://localhost:8501 |
| MCP (SSE) | http://localhost:8000 |
| LangGraph API | http://localhost:8001 — `GET /health`, demo `POST /invoke` |

All services share the same `Dockerfile` so dependencies and OS libraries stay aligned.

### Local (Python)

1. Create a venv and install deps:

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. `cp .env.example .env` and fill secrets.

3. Run the UI from the repo root with `PYTHONPATH` set:

   ```bash
   export PYTHONPATH=$(pwd)
   streamlit run ui/app.py
   ```

4. In separate terminals (same `PYTHONPATH` and venv):

   ```bash
   python -m mcp_server.server
   python -m agentic_core.graph
   ```

---

## Squad contributions

| Pod | Area | Ownership |
|-----|------|-----------|
| **POD A** | `mcp_server/` | MCP tools: `pii_scrubber`, `bank_parser`, server wiring |
| **POD B** | `agentic_core/` | LangGraph state, schemas, nodes (Guardian / Strategist / Sidekick), `graph.py` |
| **POD C** | `ui/` | Streamlit app, file upload, chat & HITL components |
| **Shared** | `utils/` | Guardrails, exceptions, PII-safe logging |

_Update with real names and sprint notes as you deliver._

---

## Disclaimer

This repository is for learning and prototyping. **It is not legal or tax advice.** Use official FIRS / NTA sources and professional review before any real filing.
