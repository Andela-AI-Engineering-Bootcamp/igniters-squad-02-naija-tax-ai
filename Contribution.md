```markdown
# 🤝 Contributing to NaijaTax AI

First off, thank you for considering contributing to NaijaTax AI! 

This project was born out of an Agentic AI Engineering Bootcamp with the goal of helping Nigerian citizens navigate the complexities of the new tax laws using autonomous agents. Whether you are fixing a bug, adding a new MCP tool, or improving our LangGraph state machine, your help is welcome.

This document outlines the process for getting your local environment set up, branching, and submitting your first Pull Request (PR).

---

## 🛠️ 1. Prerequisites

Before you begin, ensure you have the following installed on your machine:
* **Python 3.10+**
* **Git**
* **Docker & Docker Compose** (Highly recommended to avoid local environment issues)
* **Google Chrome** (Required for the Playwright automation)
* An active **OpenAI API Key**

---

## 💻 2. Local Environment Setup

You can run this project either via Docker or fully locally. 

### Step 1: Fork and Clone
1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```bash
   git clone [https://github.com/YOUR-USERNAME/naijatax-ai.git](https://github.com/YOUR-USERNAME/naijatax-ai.git)
   cd naijatax-ai
```

1. Add the upstream repository so you can sync changes:
  ```bash
   git remote add upstream [https://github.com/ORIGINAL-ORG/naijatax-ai.git](https://github.com/ORIGINAL-ORG/naijatax-ai.git)
  ```

### Step 2: Environment Variables

Copy the template file to create your local `.env`:

```bash
cp .env.example .env
```

Open `.env` and add your `OPENAI_API_KEY`.

### Step 3: Installation (Local Route)

If you prefer not to use Docker, set up your Python virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

**Crucial Playwright Step:** Because our Sidekick Agent uses Playwright to interact with the FIRS portal, you must install the local browser binaries:

```bash
playwright install chrome
```

---

## 🏗️ 3. Understanding the Architecture

Before writing code, familiarize yourself with our 3-Pod architecture. Please ensure your contributions go to the correct directory:

- `**/mcp_server**`: Contains deterministic Python tools (PDF parsing, PII scrubbing, Playwright DOM injection). No LLM logic goes here.
- `**/agent_core**`: Contains our LangGraph state machine (`state.py`) and agent nodes (Guardian, Strategist, Sidekick). 
- `**/frontend**`: Contains the Streamlit UI and our mathematical guardrails.

---

## 🌿 4. Branching Strategy

We use a strict branching model. **Never commit directly to `main` or `staging`.**

Create a new branch from `staging` for your work:

```bash
git fetch upstream
git checkout staging
git pull upstream staging
git checkout -b feature/short-description
```

**Naming Conventions:**

- `feature/` - For new MCP tools, agent nodes, or UI components.
- `fix/` - For bug fixes or prompt tuning.
- `docs/` - For updates to the README or architecture docs.

---

## 🧪 5. Development Workflow & Testing

1. **Make your changes:** Keep your functions modular. If you add a new MCP tool, ensure it returns a clear string or JSON dictionary.
2. **Run the MCP Server:** Test your tools independently first.
  ```bash
   python mcp_server/server.py
  ```
3. **Run the UI & Graph:** In a separate terminal, launch the Streamlit app.
  ```bash
   streamlit run frontend/app.py
  ```
4. **Test the HITL Breakpoints:** Ensure that any changes to the agents do not bypass the Human-In-The-Loop approval gates in the UI.

---

## 🚀 6. Submitting Your Pull Request

Once your feature is complete and working locally:

1. **Format your code:** We recommend using `black` for Python formatting.
  ```bash
   black .
  ```
2. **Commit your changes** using Conventional Commits:
  ```bash
   git commit -m "feat(mcp): added self-healing DOM mapper tool"
  ```
3. **Push to your fork:**
  ```bash
   git push origin feature/short-description
  ```
4. **Open a PR:** Go to the original repository on GitHub and click "New Pull Request".
  - Set the base branch to `staging`.
  - Fill out the provided PR template, explaining *why* the change was made and how to test it.

### The Review Process

A core squad member will review your PR within 24 hours. We may request changes, particularly if the logic interferes with our Guardrails or PII scrubbers. Once approved, we will squash and merge your branch into `staging`.

---

## ❓ Getting Help

If you are stuck on a LangGraph state issue or Playwright locator, don't spin your wheels! Open an issue with the tag `help wanted` or drop a message in our squad Discord channel.

Happy building! 🇳🇬🤖

