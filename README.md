# AI Tool Gateway

⚠️ **Project Status: Under Construction**

This project is currently under active development.

The architecture, endpoints, and integrations may change frequently while the system is being built and stabilized. Documentation may not always reflect the latest internal changes.

Until the first stable release is published, the repository should be considered **experimental** and **not production ready**.

Use at your own discretion.
___


> Self-hosted Ollama, tool, archon, git gateway — without relying on GPT-style SaaS APIs. 

AI Tool Gateway combines **local language models and external tool integrations** behind a simple HTTP interface.  
Instead of sending prompts to proprietary APIs, requests are routed through a lightweight gateway that can call models, search knowledge bases, execute code, or perform web queries.

The system integrates several open components:

- **Ollama** — local LLM runtime
- **Archon** — knowledge search and RAG
- **Open Interpreter** — code execution environment - *Uncertain role in project*
- **git** - project base

Together these provide a **small powerful foundation** for building AI-driven systems that remain fully under your control.

The design philosophy is straightforward:

- keep the architecture simple
- avoid vendor lock-in
- make tools composable
- expose everything through clean HTTP endpoints


---

## Overview

The gateway acts as a controller between:

- a user
- a language model
- tool services

The user sends a message to the `/chat` endpoint.  
The model processes the message and may request tool execution.  
The gateway then calls the appropriate service and returns the results.

This architecture allows a model to access capabilities such as:

- knowledge search
- RAG queries
- web search
- code execution

without embedding these capabilities directly inside the model.
___
## Setup
```bash
git clone git@github.com:Isak-Landin/tool-ai-gateway.git
```

### Automatic setup
> **Ensure you have docker (with docker compose) installed**
> ```bash
> cd ./tool-ai-gateway
> chmod +x ./run_application.sh
> bash ./run_application.sh
> ```
  
### Manual setup from project root
>```bash
>cat "TODO"
>```
___

## Architecture

The application combines several independent systems:

### Ollama
Provides the local LLM runtime.

The gateway forwards chat requests to Ollama using its native chat API.  
Ollama runs locally/remote server and allows the system to operate without external model providers.

### Archon
Provides knowledge retrieval functionality.

Archon is responsible for:

- searching indexed sources
- performing RAG queries
- returning document chunks or summaries

The gateway exposes passthrough endpoints which forward queries to Archon.


### Open Interpreter
Provides code execution capabilities.

When the model determines that code should be executed to solve a task, Open Interpreter provides a controlled execution environment.


---

## System Flow

Typical request flow:

1. User sends message to `/chat`
2. Gateway forwards the message to the model
3. Model determines whether a tool is needed
4. Gateway executes the requested tool
5. Tool result is returned to the model
6. Model produces final response
7. Gateway returns response to the user


---

## Example Endpoints

The gateway exposes a small set of endpoints for interaction and tool execution.


### Chat

POST `/chat`

Main interface used to communicate with the system.

Example:
```bash
curl -X POST http://localhost:4100/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello"}'
```

Example tool-triggering message:
```bash
curl -X POST http://localhost:4100/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Search Archon for docmost and summarize it"}'
```

---
## Archon
> **Built-in No Manual execution needed - TESTING ONLY**
### Archon Search


GET `/archon_search`

Searches indexed knowledge sources through Archon.

Example:
```bash
curl "http://localhost:4100/archon_search?q=docmost"
```
  

With parameters:

```bash
curl "http://localhost:4100/archon_search?q=docmost&source=&match_count=5&return_mode=chunks"
```

---

### Archon RAG Query

POST `/archon_rag_query`

Performs a RAG query against the Archon knowledge index.

Example:
```bash
curl -X POST http://localhost:4100/archon_rag_query \
  -H "Content-Type: application/json" \
  -d '{"query":"What is Docmost?","source":"","match_count":5,"return_mode":"chunks"}'
```

---

### Web Search

GET `/web_search`

Performs a simple web search.

Example:

```bash
curl "http://localhost:4100/web_search?q=ollama"
```

---

## Why This Exists

Modern AI workflows often depend heavily on proprietary APIs.  
This project demonstrates a minimal architecture for building an alternative using open components.

Benefits include:

- Controlled model execution
- No **MUST-HAVE** dependency on GPT/Claude APIs
- Pre-integrated web search, archon
- Modular architecture
- Simple HTTP integration
- Code focused model


---

## Goals

The design priorities of AI Tool Gateway are:

- Simplicity
- Modularity
- Easy integration with external tools
- Minimal orchestration logic


---

## Future Extensions

Possible future improvements include:

- additional tool integrations
- improved tool routing logic
- authentication and access control
- structured tool schemas
- UI for interacting with the gateway
- persistent conversation storage


---
## Ongoing Documentation
[File Structure](https://docs.isaklandin.com/share/fdwgh9qhko/p/file-structure-and-roles-1p7Tp5BxEU)  
[DB Tables](https://docs.isaklandin.com/share/ofnogq5ovo/p/tables-mBux5sqtSl)  
[Current Notes](https://docs.isaklandin.com/share/1bn72iiy2i/p/current-todo-notes-SFWp3rW5fS)
___

## License
[**GNU GENERAL PUBLIC LICENSE**](https://www.gnu.org/licenses/gpl-3.0.en.html#license-text) - *Version 3, 29 June 2007*