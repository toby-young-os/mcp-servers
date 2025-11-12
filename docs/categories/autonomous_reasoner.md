# Autonomous Reasoning Server

**Category:** Autonomous / Server-Side Reasoning

This server delegates math word problems to OpenAI, returning both `reasoning_steps` and the final answer so clients can surface the result directly. OpenAI credentials (`OPENAI_API_KEY`) are required.

## Quick Demo

```bash
fastmcp-math-chat --server autonomous --no-planner --show-json
```

Ask “What is the result of doubling 7 and then subtracting 3?” to see the OpenAI-produced reasoning trace.

## Sample Request and Response

Request:

```json
{
  "problem": "If you double 3 and add 1, what do you get?"
}
```

Response:

```json
{
  "problem": "If you double 3 and add 1, what do you get?",
  "reasoning_steps": [
    "Double 3 to get 6",
    "Add 1 to get 7"
  ],
  "final_answer": "7",
  "model": "gpt-4.1-mini",
  "source": "openai"
}
```
