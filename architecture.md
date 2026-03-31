# NaijaTax AI: System Architecture

This document is the technical North Star for the 6-member squad during the sprint. It defines the boundaries of the tech stack and the repository structure so **Pod A** (tools and browser), **Pod B** (orchestration), and **Pod C** (UX) can work concurrently with minimal merge friction.

---

## 1. System overview

NaijaTax AI is a local, privacy-first multi-agent system designed to assist Nigerian users with filing their taxes under the new tax rules. To bypass the fragility of automating government websites (CAPTCHAs, timeouts), the **target** design uses a **shared browser session**: the human handles authentication in a persistent Chrome window while LangGraph acts as an over-the-shoulder copilot—reading the DOM and injecting calculations in real time.

**What exists in this repo today:** a **Streamlit/gradio** app (`ui/`), a **LangGraph** package (`agentic_core/`), a **FastMCP** server (`mcp_server/`) with tool modules including `tax_rag.py` and `browser_tools.py` (stubs returning `not_configured` until wired), shared **utils**, and **Docker Compose** wiring Streamlit/gradio, MCP, and a LangGraph HTTP service. **Full Chroma-backed RAG**, **Playwright CDP** live attach to Chrome, and the end-to-end TaxPromax loop remain **sprint targets**—land them in small PRs and update this file when they ship.

---

## 2. Architecture and data flow

The diagram below shows the user, Streamlit or Gradio, the LangGraph state machine, MCP tools, persistent Chrome, and (target) vector retrieval.

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'fontSize': '15px', 'fontFamily': 'ui-sans-serif, system-ui, sans-serif', 'primaryTextColor': '#111827', 'secondaryTextColor': '#111827', 'tertiaryTextColor': '#111827', 'lineColor': '#374151', 'textColor': '#111827', 'mainBkg': '#ffffff', 'edgeLabelBackground': '#f3f4f6'}}}%%
flowchart TD
    classDef user fill:#fce4ec,stroke:#880e4f,stroke-width:3px,color:#1a1a1a;
    classDef ui fill:#b3e5fc,stroke:#01579b,stroke-width:3px,color:#0d1b2a;
    classDef graph fill:#c8e6c9,stroke:#1b5e20,stroke-width:3px,color:#102a16;
    classDef mcp fill:#ffe0b2,stroke:#e65100,stroke-width:3px,color:#3e2723;
    classDef db fill:#e1bee7,stroke:#4a148c,stroke-width:3px,color:#311b4a;
    classDef browser fill:#ffcdd2,stroke:#b71c1c,stroke-width:3px,color:#3e0d0d;

    User((👤 User)):::user <-->|Uploads Docs and Chats| UI[💻 Streamlit/gradio Interface<br/>Chat and State Viewer]:::ui
    User <-->|Handles Login/CAPTCHA<br/>Clicks Final Submit| Chrome[🌐 Persistent Chrome<br/>FIRS TaxPromax]:::browser

    subgraph ac["Agentic Core (LangGraph)"]
        Guardian[🛡️ Guardian Agent<br/>Doc Parsing and PII]:::graph
        Strategist[🧠 Strategist Agent<br/>Tax RAG and Math]:::graph
        Sidekick[🤝 Sidekick Agent<br/>Browser Copilot]:::graph

        Guardian -->|Clean Data Profile| Strategist
        Strategist -->|Verified Tax Report| Sidekick
        Sidekick <-->|HITL Pause and Resume| UI
    end

    UI <-->|Triggers Execution| Guardian

    subgraph lmcp["Local MCP Server"]
        PII[PII Scrubber Tool]:::mcp
        RAG[Tax Law Vector DB]:::db
        Playwright[Playwright CDP Controller]:::mcp
    end

    Guardian -.->|Sanitizes Text| PII
    Strategist -.->|Queries Finance Act| RAG
    Sidekick -.->|Injects and Reads DOM| Playwright
    Playwright <-->|Connects via port 9222| Chrome

    style ac fill:#e8f5e9,stroke:#1b5e20,stroke-width:3px,color:#0d2818;
    style lmcp fill:#fff3e0,stroke:#e65100,stroke-width:3px,color:#3e2723;
```

**Current vs target:** `mcp_server` today exposes deterministic tools such as PII scrubbing and bank PDF parsing (`pii_scrubber`, `bank_parser`). Chroma RAG and Playwright browser tools in the diagram are the intended extensions. The compiled agent pipeline in code is `guardian → strategist → sidekick` (see [`agentic_core/graph.py`](agentic_core/graph.py)).

---

## 3. Tech stack

- **Orchestration:** **LangGraph** — cyclic graphs and `interrupt`-style flows for Human-in-the-Loop (HITL) gates.
- **Agentic intelligence:** **OpenAI SDK** — reasoning and classification; configure keys via `.env` (see [`.env.example`](.env.example)).
- **Tooling layer:** **Model Context Protocol (MCP)** — decouples Python tool execution from ad-hoc LLM prompts; keeps sensitive work local.
- **Browser automation (target):** **Playwright (Python)** — attach to user-launched Chrome via Chrome DevTools Protocol (CDP), e.g. port 9222, to read and inject into the live FIRS portal without relying on headless-only flows.
- **Knowledge base (target):** **ChromaDB** — local vector store for Nigerian Finance Act text to reduce bracket and rate hallucinations.
- **Frontend:** **Streamlit/Gradio** — fast chat and upload UX in `ui/`.

**Runtime:** [`docker-compose.yml`](docker-compose.yml) runs **Streamlit/gradio**, the **MCP** service, and a **LangGraph** HTTP service. Add a dedicated vector DB service (or embed Chroma) when `tax_rag` lands.

---

## 4. Repository layout

Structure matches **this repository as it exists today**. Sprint additions appear inline with a *(planned)* note so Pods can align before files exist.

```text
Naija_tax_ai/
├── .env.example                 # OPENAI_API_KEY and related config
├── .gitignore
├── docker-compose.yml           # Streamlit/Gradio, MCP, LangGraph services
├── Dockerfile
├── README.md
├── architecture.md              # This document
├── architecture.png             # Optional slide/export asset
├── requirements.txt
│
├── mcp_server/                  # POD A: tools and browser automation
│   ├── __init__.py
│   ├── server.py                # MCP server and tool routing
│   └── tools/
│       ├── __init__.py
│       ├── pii_scrubber.py      # Regex masking for BVN, NUBAN, phone-like patterns
│       ├── bank_parser.py       # Bank PDF and table extraction
│       ├── tax_rag.py           # Chroma queries for Nigerian tax law (stub until collection wired)
│       └── browser_tools.py     # Playwright CDP attach and DOM helpers (stub until wired)
│
├── agentic_core/                # POD B: multi-agent orchestration
│   ├── state.py                 # Shared LangGraph state
│   ├── schemas.py               # Pydantic validation
│   ├── graph.py                 # Graph compile, edges, breakpoints
│   └── nodes/
│       ├── guardian_node.py     # Intake and privacy
│       ├── strategist_node.py   # Tax reasoning and RAG calls (when wired)
│       └── sidekick_node.py     # User comms and browser copilot hooks
│
├── ui/                          # POD C: Streamlit/Gradio UX
│   ├── app.py
│   └── components/
│       ├── chat_interface.py
│       ├── file_uploader.py
│       └── status_panel.py      # (planned) Rich LangGraph state panel
│
└── utils/                       # Shared guardrails and plumbing
    ├── exceptions.py
    ├── guardrails.py
    └── logger.py
```

### Module responsibilities

- **`mcp_server/`** — Deterministic I/O: tools return strings or JSON. **Do not** embed LLM prompts here.
- **`agentic_core/`** — Owns state and control flow. Agents should call MCP tools for heavy or sensitive logic instead of duplicating it.
- **`ui/`** — Assume the backend can fail; handle empty states gracefully. The final FIRS **Submit** must remain a **human** action unless product policy explicitly changes.

---

## 5. Related assets

- [`README.md`](README.md) — setup, agents, MCP tool table, guardrails.
- [`architecture.png`](architecture.png) — optional visual for decks if kept in sync with this file.
