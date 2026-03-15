# AI Tool Gateway

⚠️ **Project Status: Under Construction**

This project is currently under active development.

The architecture, endpoints, and integrations may change frequently while the system is being built and stabilized. Documentation may not always reflect the latest internal changes.

Until the first stable release is published, the repository should be considered **experimental** and **not production ready**.

Use at your own discretion.

___


> Self-hosted Ollama + tool + Archon + git gateway — without relying on GPT-style SaaS APIs.

AI Tool Gateway exposes a **minimal HTTP backend** that connects:

- a **UI**
- a **local language model**
- **tool execution services**
- **project repositories**
- **persistent conversation state**

The gateway allows a language model to interact with tools without giving the model direct access to system resources.

Instead of embedding capabilities directly into the model, the gateway controls all execution through a deterministic backend layer.

The system currently integrates:

- **Ollama** — local LLM runtime
- **Archon** — knowledge search / RAG
- **git** — project repository access
- **PostgreSQL** — persistent state

Open Interpreter previously appeared in early design notes but **is not part of the current MVP architecture**.

The design philosophy remains intentionally simple:

- keep architecture minimal
- avoid vendor lock-in
- expose clean HTTP interfaces
- isolate model from system execution
- maintain deterministic backend control

---

# Overview

The gateway acts as a controller between:

- a **user interface**
- a **language model**
- **backend tool services**

A request to the system flows through several layers:

1. UI sends request to `/chat`
2. Gateway resolves the project context
3. Gateway binds a runtime handle
4. Conversation history and file context are loaded
5. The model is invoked through Ollama
6. The model may request a tool
7. Gateway validates and executes the tool
8. Tool results are returned to the model
9. Model produces a final response
10. Gateway returns the response to the UI

Important rule:

The **model never executes tools directly**.

The model can only **request tool calls**.  
The backend decides whether the request is honored.

---

# Setup

Clone the repository:

```bash
git clone git@github.com:Isak-Landin/tool-ai-gateway.git