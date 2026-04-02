# 📋 NaijaTax AI: 72-Hour Sprint Task Board

**Project:** NaijaTax AI (Agentic Tax Copilot)
**Architecture:** LangGraph + Local MCP Server + Playwright Dynamic Browser Injection
**Timeline:** 3 Days
**Team Size:** 6 Engineers (Divided into 3 Pods)

---

## 🛠️ Pod A: Tools & Browser Automation (MCP Server)
**Focus:** Building deterministic local tools, including the self-healing Playwright browser controllers, and exposing them via the Model Context Protocol.

### Task A1: Document Parser & PII Scrubber (`parse_and_scrub`)
* **Description:** Build the Python logic to extract text from Nigerian bank statement PDFs using `PyMuPDF` or `Camelot`. Pipe the extracted text through a regex-based PII scrubber that automatically masks 10-digit NUBANs, 11-digit BVNs, and phone numbers before returning the string.
* **Deliverable:** A robust extraction function that fails gracefully with an `UnreadablePDFError` if the document is invalid.

### Task A2: Tax Law Knowledge Base (`query_tax_law`)
* **Description:** Initialize a local ChromaDB instance containing the text of the latest Nigerian Finance Acts. Write a retrieval tool that accepts natural language search terms and returns the most relevant legal text chunks to ground the LLM's calculations.
* **Deliverable:** A functional local RAG retrieval tool.

### Task A3: Playwright Auto-Launcher (`launch_firs_portal`)
* **Description:** Use `playwright.sync_api` to build a tool that launches a persistent, *visible* (`headless=False`) Google Chrome context and navigates to the FIRS TaxPromax URL. Store the active page session in a global variable so subsequent tools can access the live window.
* **Deliverable:** A script that successfully opens a browser on the user's screen ready for human login.

### Task A4: Semantic DOM Mapper (`map_active_form`)
* **Description:** Build the "Self-Healing" vision tool. Use Playwright to execute a Javascript snippet that finds all visible `<input>` and `<select>` tags on the active page, pairs them with their associated human-readable `<label>`, and returns a clean, minified JSON array of the form structure.
* **Deliverable:** A tool that gives the LLM a lightweight, real-time map of the FIRS UI.

### Task A5: Dynamic Form Injector (`dynamic_inject`)
* **Description:** Build a tool that accepts a CSS selector and a value, then uses the active Playwright session to inject that value directly into the live webpage. Include a Javascript evaluation to highlight the filled field in light green (`#e8f5e9`) so the user sees exactly what the AI touched.
* **Deliverable:** A tool that allows the LLM to type safely into the live FIRS browser window.

### Task A6: Expose the MCP Server
* **Description:** Wrap the tools from A1 through A5 using the OpenAI SDK's MCP server implementation. Ensure the server runs locally on a stable port so Pod B can connect their LangGraph agents to it.
* **Deliverable:** A running `server.py` file.

### Task A7: The "TaxPromax" Rosetta Stone Dictionary
* **Description:** While Task A4 dynamically maps the active browser form, the LLM still needs to know what those fields mean in a Nigerian context. Create a static JSON dictionary (`pit_dictionary.json`) under the MCP server package (e.g. `mcp_server/data/`). The dictionary must define standard Nigerian tax terms and abbreviations so agents can cross-reference them during the injection phase.
* **Required keys to map (minimum):** `TIN`, `PAYE`, `NHF`, `NHIS`, `CRA`, `WHT` (each with human-readable definitions and optional synonyms / Form A label hints).
* **Deliverable:** A static JSON reference file the Sidekick agent can load to resolve TaxPromax acronyms when matching live DOM labels to Pydantic fields.

---

## 🧠 Pod B: Agentic Core & Orchestration (LangGraph)
**Focus:** Defining state, engineering prompts, and orchestrating the multi-agent workflow.

### Task B1: Define Global State & Data Schemas
* **Description:** Create `state.py` to define the LangGraph `TypedDict` (memory). Create `schemas.py` using Pydantic to strictly type filing-oriented profiles and outputs (see **B6** for the full `NigerianPITProfile` model and **`TaxLiabilityReport`**) so agent outputs are predictable.
* **Deliverable:** The central data contracts that Pod A and Pod C will use to integrate their work.

### Task B2: The Guardian Agent Node (Intake)
* **Description:** Write the node that invokes the `parse_and_scrub` tool. If the document is read successfully, it formats the data into the Pydantic schema. If there's an ambiguity (e.g., "Is this deposit a gift?"), it updates the state to trigger a routing pause for human clarification.
* **Deliverable:** A functional intake node that outputs clean JSON.

### Task B3: The Strategist Agent Node (Calculation)
* **Description:** Write the node that takes the clean JSON, invokes the `query_tax_law` RAG tool, and calculates the final Personal Income Tax liability. The prompt must force the LLM to cite the legal section it used to calculate deductions like the Consolidated Relief Allowance (CRA).
* **Deliverable:** A node that deterministically calculates Nigerian tax math.

### Task B4: The Sidekick Agent Node (Browser Copilot)
* **Description:** Write the node that manages the browser interaction. It must sequentially: 1) Invoke `launch_firs_portal`, 2) Wait for human login, 3) Invoke `map_active_form` to read the UI, 4) Match its calculations to the human labels, and 5) Invoke `dynamic_inject` to fill the form.
* **Deliverable:** The agent that translates calculated data into physical, self-healing browser actions.

### Task B5: Graph Compilation & HITL Breakpoints
* **Description:** Wire the Guardian, Strategist, and Sidekick nodes together in `graph.py`. Insert LangGraph `interrupt` breakpoints before the browser launches and *before* the user is told to click the final submit button.
* **Deliverable:** The compiled, runnable LangGraph state machine.

### Task B6: Comprehensive PIT Pydantic Schema (`schemas.py`)
* **Description:** Extend `schemas.py` with a **`NigerianPITProfile`** model that includes mandatory and optional fields needed for Nigerian Personal Income Tax (Form A / Finance Act–aligned filing), not just what a bank statement provides. Use clear defaults (e.g. `0.0`) and `Optional[...]` where the user may genuinely have no value (e.g. TIN). Cover identity (TIN), income sources (salary, trade, dividends, rent), statutory reliefs (pension, NHF, NHIS, life assurance), and taxes already paid (PAYE, WHT credits).
* **Deliverable:** A strictly typed structure so agents know which variables are required for calculation and injection, and which still need user input.

### Task B7: The "Missing Context" Interview Loop (Guardian Agent)
* **Description:** A bank statement shows income flows but usually **not** life assurance, NHIS, NHF, or full pension detail. After parsing the PDF into `NigerianPITProfile`, the Guardian must detect empty or unknown tax-reducing fields and trigger a LangGraph interrupt to ask the user (e.g. whether they wish to declare life assurance or NHIS premiums to reduce liability). Merge answers into state before the Strategist runs.
* **Deliverable:** An interview step that proactively hunts for legal deductions before calculation.

---

## 🖥️ Pod C: User Experience & Guardrails (Streamlit)
**Focus:** Building the "Command Center" UI where the human interacts with the Sidekick.

### Task C1: Streamlit Command Center Foundation
* **Description:** Build the main Streamlit UI (`app.py`). Include a secure file uploader for the bank statements and a clear visual dashboard that will display the extracted `Gross Income`, `CRA`, and `Tax Payable` once the LangGraph state updates.
* **Deliverable:** The base UI layout and file-staging mechanism.

### Task C2: The Sidekick Chat Interface
* **Description:** Implement the interactive `st.chat_message` interface. This is where the Sidekick agent will explain its calculations, cite the Nigerian tax law, and give the user instructions on what to do in the Chrome browser.
* **Deliverable:** A fluid, conversational UI tied to the LangGraph output stream.

### Task C3: State Synchronization & Execution Triggers
* **Description:** Build the Streamlit widgets that push the LangGraph state forward. When the graph pauses at a HITL breakpoint, display clear action buttons (e.g., "Launch Browser", "Inject Form Data") that the user must click to resume the agent's execution.
* **Deliverable:** The UI bridges that allow the human to safely control the LangGraph execution flow.

### Task C4: Safety Middleware (The Math Guardrail)
* **Description:** Before the Streamlit app renders the final tax numbers calculated by Pod B, write a strict Python utility function that manually recalculates the math based on the hardcoded FIRS tax brackets. If the LLM hallucinated the math, the UI must catch it and display a warning instead of letting the Sidekick proceed.
* **Deliverable:** A silent safety net in `utils/guardrails.py` protecting the user from AI arithmetic errors.