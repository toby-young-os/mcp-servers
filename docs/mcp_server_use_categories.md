# MCP Server Use Categories

This document summarizes the four primary categories of Model Context
Protocol (MCP) server usage patterns, along with examples, protocol
behavior, and model roles. It also includes extended categories for
advanced use cases.

## Quick Links to Local Examples

- [Capability Discovery (`math-capability-registry`)](categories/capability_discovery.md)
- [Data-Providing (`math-data-provider`)](categories/data_provider.md)
- [Prompt-Returning (`math-prompt-helper`)](categories/prompt_helper.md)
- [Autonomous Reasoning (`math-autonomous-reasoner`)](categories/autonomous_reasoner.md)

---

## 🌟 Overview

MCP servers can serve very different roles depending on whether they
expose capabilities, provide structured data, co-reason with the
model, or run autonomous reasoning on their own. This taxonomy helps
identify what kind of interaction each server supports and what the
model should do next.

---

## 🧭 1. Capability Discovery / Tool Registration

**Purpose:** Advertise what the server can do.  

- The server exposes a manifest of tools, schemas, and endpoint
  definitions (what methods exist, what parameters they take, what
  they return).
- Enables the model (or client) to **dynamically discover** and reason
  about new tools at runtime—e.g., “browse,” “query,” or “summarize.”
- **Returns:** Purely **structured metadata** (no model prompts or
    user data)
- **Typical MCP behavior:** `GET /manifest` or equivalent.

**Example servers:**  
- The default OpenAI MCP manifest endpoint  
- Any registry service exposing available tool definitions

**Model responsibility:** Learn available tools and update its planner.

---

## 📊 2. Data-Providing / Context-Enriching Calls

**Purpose:** Serve structured **data** directly.  

- The model asks for information; the server retrieves and returns
  structured results.
- Examples: “fetch user history,” “get chart data,” “search a
  database,” etc.
- **Returns:** **Structured data** only—ready for the model to reason
    over.
- **Typical MCP behavior:** `POST /tools/<tool_name>/execute`
    returning JSON.

**Example servers:**  
- ChromaDB MCP (semantic vector search)  
- SQL or analytics MCP returning metrics or rows

**Model responsibility:** Use the data in reasoning or planning the next action.

---

## 💬 3. Prompt-Returning / Co-Reasoning Calls

**Purpose:** Collaborate with the model in generating reasoning steps.  

- The server returns **data plus a suggested prompt** that guides how
  to use that data in the next model call.
- Useful in multi-stage reasoning chains or co-processing workflows.
- Allows the server to encode procedural knowledge while the model
  remains stateless.
- **Returns:** **Data + prompt**, sometimes wrapped in a “run model”
    or “template” instruction.
- **Typical MCP behavior:** Same as a data call, but includes a
    `prompt_template` or `next_action` field.

**Example servers:**  
- Document summarization helper MCP  
- Chart-explainer or QA assistant that formats retrieved results into a reasoning prompt

**Model responsibility:** Use the returned prompt as the next input to continue reasoning.

---

## 🧠 4. Autonomous / Server-Side Reasoning

**Purpose:** Perform LLM inference *inside* the server itself.  

- The client delegates reasoning to the server (e.g., for specialized
  inference, summarization, or code execution).
- Some servers include their own local or fine-tuned model runtimes.
- **Returns:** The **final answer** or structured output—no further
    prompting needed.
- **Typical MCP behavior:** `POST /run_model` or a similar inference
    endpoint.

**Example servers:**  
- Local summarization or reasoning engine MCP  
- Code execution MCP running internal inference pipelines

**Model responsibility:** Delegate entirely; no follow-up reasoning required.

---

## 🔄 Hybrid / Transitional Servers
Some MCP servers blend categories. For example:
- A data-providing server that sometimes emits prompt templates when ambiguity exists.
- A summarizer that usually returns prompts but occasionally provides direct answers.

In such cases, the client should inspect the returned fields (e.g.,
presence of a `prompt` or `answer`) to decide whether to continue
reasoning or stop.

---

## 🧩 Extended Categories

### ⚡ 5. Event-Driven / Subscription Servers

**Purpose:** Provide **push-based** or **streaming** updates rather than pull-based requests.  

- Instead of the model querying for data, the server streams events or
  changes (e.g., file updates, new messages, telemetry).
- Supports **reactive agents** that stay in sync with changing state.
- Typically implemented using **WebSocket** or **SSE (Server-Sent
  Events)** channels.
- **Returns:** Incremental updates or event payloads.

**Example servers:**  
- MCP notification or change-tracking server for live contexts  
- Realtime telemetry feed or live data stream MCP

**Model responsibility:** Listen and respond to updates; no explicit query loop.

🟢 *Why it matters:* Enables persistent context and real-time reactivity.

---

### 🧱 6. State-Management / Memory Servers

**Purpose:** Store or recall long-term structured context on behalf of the model.  

- Acts like an external working memory, holding user sessions, prior
  outputs, or long-term embeddings.
- Distinct from “data-providing” servers in that **the data originates
  from the model’s own history** rather than an external source.
- **Returns:** Stored or retrieved memory objects, often with metadata
    or relevance scores.

**Example servers:**  
- Memory or conversation-history MCP (e.g., vector memory manager)  
- State persistence layer for multi-turn toolchains

**Model responsibility:** Write or read memory context to maintain continuity across sessions.

🟢 *Why it matters:* Defines how MCP servers can support **stateful cognition** or long-lived agentic behavior.

---

## 🧮 Summary Table

| # | Category | Returns | Model Role | Next Step | Example |
|---|-----------|----------|-------------|------------|----------|
| 1 | Discovery | Capabilities & schemas | Learn available tools | Update planner | Manifest endpoint |
| 2 | Data-only | Structured results | Use in reasoning | Produce next action or response | ChromaDB MCP |
| 3 | Data + prompt | Data + prompt template | Continue reasoning | Run LLM with prompt | Summarizer MCP |
| 4 | Autonomous reasoning | Final result | None (delegated) | Output directly | Local LLM server |
| 5 | Event-driven | Streaming payloads | React to updates | Adjust context or state | Telemetry MCP |
| 6 | State-management | Memory objects | Maintain continuity | Read/write state | Memory MCP |

---

### ✅ Key Takeaway

Understanding these categories helps design agents that can flexibly
coordinate with different MCP servers—from static capability discovery
to full autonomous reasoning, streaming updates, and long-term memory
management.
