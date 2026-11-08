"""
The agent loop: sends the task to Claude, runs the tools it asks for, and traces every step in Phoenix.
"""

import json
from pathlib import Path

import anthropic
from mcp import Client

from ops_world import fresh_world
from ops_tools import build_server

# Caps the loop so a confused agent can't call tools forever and run up cost.
MAX_STEPS = 12
# Output limit per model call. Thinking tokens count toward it too.
MAX_TOKENS = 8000
BASE_PROMPT = Path("prompts/base_system_prompt.txt").read_text()

client = anthropic.Anthropic()


# MCP and the Anthropic API describe tools in slightly different formats; this converts one to the other.
def to_claude_tools(mcp_tools):
    return [
        {"name": t.name, "description": t.description, "input_schema": t.input_schema}
        for t in mcp_tools
    ]


# Cache tokens count toward Haiku's 100K price tier, so the prompt size includes them.
def prompt_size(usage):
    return (
        usage.input_tokens
        + (usage.cache_read_input_tokens or 0)
        + (usage.cache_creation_input_tokens or 0)
    )


async def run_agent(task, model, tracer, system_prompt=BASE_PROMPT, overrides=None, metadata=None, log_tools="full"):
    world = fresh_world(overrides)
    messages = [{"role": "user", "content": task}]
    calls = []
    final_text = ""
    stop_reason = None

    # Manual spans: auto-instrumentation only captures the model calls, not the loop or the tools.
    with tracer.start_as_current_span("agent_run", openinference_span_kind="agent") as agent_span:
        agent_span.set_input(task)
        agent_span.set_attribute("metadata", json.dumps({"model": model, **(metadata or {})}))

        async with Client(build_server(world, log_tools)) as mcp_client:
            tools = to_claude_tools((await mcp_client.list_tools()).tools)

            for step in range(MAX_STEPS):
                response = client.messages.create(
                    model=model,
                    max_tokens=MAX_TOKENS,
                    system=system_prompt,
                    tools=tools,
                    messages=messages,
                )
                calls.append({
                    "prompt_tokens": prompt_size(response.usage),
                    "output_tokens": response.usage.output_tokens,
                })
                stop_reason = response.stop_reason
                # Send the reply back unchanged; the API needs its thinking and tool_use blocks exactly as they were.
                messages.append({"role": "assistant", "content": response.content})

                # No more tool calls means the model is done, and its text is the final answer.
                if response.stop_reason != "tool_use":
                    final_text = "".join(b.text for b in response.content if b.type == "text")
                    break

                results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue
                    with tracer.start_as_current_span(block.name, openinference_span_kind="tool") as tool_span:
                        tool_span.set_tool(name=block.name, parameters=block.input)
                        tool_span.set_input(block.input)
                        result = await mcp_client.call_tool(block.name, block.input)
                        text = result.content[0].text
                        tool_span.set_output(text)
                    # tool_use_id links each result to the call that asked for it, since the model can call several tools at once.
                    results.append({"type": "tool_result", "tool_use_id": block.id, "content": text})
                messages.append({"role": "user", "content": results})

        agent_span.set_output(final_text)

    return {
        "task": task,
        "model": model,
        "final_text": final_text,
        "stop_reason": stop_reason,
        # True if the loop ran out of steps while the model still wanted to use tools.
        "hit_step_limit": stop_reason == "tool_use",
        "world": world,
        "actions": world["actions"],
        "calls": calls,
    }