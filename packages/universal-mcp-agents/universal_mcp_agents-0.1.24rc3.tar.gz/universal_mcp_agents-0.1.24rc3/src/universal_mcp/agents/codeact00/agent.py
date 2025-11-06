import copy
import json
import re
import uuid
from typing import Literal, cast

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import START, StateGraph
from langgraph.types import Command, RetryPolicy, StreamWriter
from universal_mcp.tools.registry import ToolRegistry
from universal_mcp.types import ToolFormat

from universal_mcp.agents.base import BaseAgent
from universal_mcp.agents.codeact00.llm_tool import smart_print
from universal_mcp.agents.codeact00.prompts import (
    AGENT_BUILDER_GENERATING_PROMPT,
    AGENT_BUILDER_META_PROMPT,
    AGENT_BUILDER_PLANNING_PROMPT,
    AGENT_BUILDER_PLANNER_PROMPT,
    AGENT_BUILDER_PLAN_PATCH_PROMPT,
    AGENT_BUILDER_CODE_PATCH_PROMPT,
    build_tool_definitions,
    create_default_prompt,
)
from universal_mcp.agents.codeact00.sandbox import eval_unsafe, execute_ipython_cell, handle_execute_ipython_cell
from universal_mcp.agents.codeact00.state import (
    AgentBuilderCode,
    AgentBuilderMeta,
    AgentBuilderPlan,
    AgentBuilderPatch,
    CodeActState,
)
from universal_mcp.agents.codeact00.tools import (
    create_meta_tools,
    enter_agent_builder_mode,
    finalize_planning,
    cancel_planning,
)
from universal_mcp.agents.codeact00.utils import (
    build_anthropic_cache_message,
    extract_plan_parameters,
    get_connected_apps_string,
    strip_thinking,
    apply_patch_or_use_proposed,
)
from universal_mcp.agents.llm import load_chat_model
from universal_mcp.agents.utils import convert_tool_ids_to_dict, filter_retry_on, get_message_text


class CodeActPlaybookAgent(BaseAgent):
    def __init__(
        self,
        name: str,
        instructions: str,
        model: str,
        memory: BaseCheckpointSaver | None = None,
        registry: ToolRegistry | None = None,
        agent_builder_registry: object | None = None,
        sandbox_timeout: int = 20,
        **kwargs,
    ):
        super().__init__(
            name=name,
            instructions=instructions,
            model=model,
            memory=memory,
            **kwargs,
        )
        self.model_instance = load_chat_model(model)
        self.agent_builder_model_instance = load_chat_model("anthropic:claude-sonnet-4-5-20250929", thinking=False, disable_streaming = True, tags=("quiet",))
        self.registry = registry
        self.agent_builder_registry = agent_builder_registry
        self.agent = agent_builder_registry.get_agent() if agent_builder_registry else None

        self.tools_config = self.agent.tools if self.agent else {}
        self.eval_fn = eval_unsafe
        self.sandbox_timeout = sandbox_timeout
        self.default_tools_config = {
            "llm": ["generate_text", "classify_data", "extract_data", "call_llm"],
        }
        self.final_instructions = ""
        self.tools_context = {}
        self.eval_mode = kwargs.get("eval_mode", False)

    async def _build_graph(self):  # noqa: PLR0915
        """Build the graph for the CodeAct Playbook Agent."""
        meta_tools = create_meta_tools(self.registry)
        self.additional_tools = [
            smart_print,
            meta_tools["web_search"],
            meta_tools["read_file"],
            meta_tools["save_file"],
            meta_tools["upload_file"],
        ]

        if self.tools_config:
            await self.registry.load_tools(self.tools_config)  # Load provided tools
        if self.default_tools_config:
            await self.registry.load_tools(self.default_tools_config)  # Load default tools

        async def call_model(state: CodeActState) -> Command[Literal["execute_tools"]]:
            """This node now only ever binds the four meta-tools to the LLM."""
            messages = build_anthropic_cache_message(self.final_instructions) + state["messages"]

            agent_facing_tools = [
                execute_ipython_cell,
                enter_agent_builder_mode,
                meta_tools["search_functions"],
                meta_tools["load_functions"],
            ]

            if isinstance(self.model_instance, ChatAnthropic):
                model_with_tools = self.model_instance.bind_tools(
                    tools=agent_facing_tools,
                    tool_choice="auto",
                    cache_control={"type": "ephemeral", "ttl": "1h"},
                )
                if isinstance(messages[-1].content, str):
                    pass
                else:
                    last = copy.deepcopy(messages[-1])
                    last.content[-1]["cache_control"] = {"type": "ephemeral", "ttl": "5m"}
                    messages[-1] = last
            else:
                model_with_tools = self.model_instance.bind_tools(
                    tools=agent_facing_tools,
                    tool_choice="auto",
                )
            response = cast(AIMessage, await model_with_tools.ainvoke(messages))
            if response.tool_calls:
                return Command(goto="execute_tools", update={"messages": [response]})
            else:
                return Command(update={"messages": [response], "model_with_tools": model_with_tools})

        async def execute_tools(state: CodeActState) -> Command[Literal["call_model", "agent_builder"]]:
            """Execute tool calls"""
            last_message = state["messages"][-1]
            tool_calls = last_message.tool_calls if isinstance(last_message, AIMessage) else []

            tool_messages = []
            new_tool_ids = []
            tool_result = ""
            ask_user = False
            ai_msg = ""
            effective_previous_add_context = state.get("add_context", {})
            effective_existing_context = state.get("context", {})
            # logging.info(f"Initial new_tool_ids_for_context: {new_tool_ids_for_context}")

            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                try:
                    if tool_name == "enter_agent_builder_mode":
                        tool_message = ToolMessage(
                            content=json.dumps("Entered Agent Builder Mode."),
                            name=tool_call["name"],
                            tool_call_id=tool_call["id"],
                        )
                        return Command(
                            goto="agent_builder",
                            update={
                                "agent_builder_mode": "planning",
                                "messages": [tool_message],
                            },  # Entered Agent Builder mode
                        )
                    elif tool_name == "execute_ipython_cell":
                        code = tool_call["args"]["snippet"]
                        output, new_context, new_add_context = await handle_execute_ipython_cell(
                            code,
                            self.tools_context,  # Uses the dynamically updated context
                            self.eval_fn,
                            effective_previous_add_context,
                            effective_existing_context,
                        )
                        effective_existing_context = new_context
                        effective_previous_add_context = new_add_context
                        tool_result = output
                    elif tool_name == "load_functions":
                        # The tool now does all the work of validation and formatting.
                        tool_result, new_context_for_sandbox, valid_tools, unconnected_links = await meta_tools[
                            "load_functions"
                        ].ainvoke(tool_args)
                        # We still need to update the sandbox context for `execute_ipython_cell`
                        new_tool_ids.extend(valid_tools)
                        if new_tool_ids:
                            self.tools_context.update(new_context_for_sandbox)
                        if unconnected_links:
                            ask_user = True
                            ai_msg = f"Please login to the following app(s) using the following links and let me know in order to proceed:\n {unconnected_links} "

                    elif tool_name == "search_functions":
                        tool_result = await meta_tools["search_functions"].ainvoke(tool_args)
                    else:
                        raise Exception(
                            f"Unexpected tool call: {tool_call['name']}. "
                            "tool calls must be one of 'enter_agent_builder_mode', 'execute_ipython_cell', 'load_functions', or 'search_functions'. For using functions, call them in code using 'execute_ipython_cell'."
                        )
                except Exception as e:
                    tool_result = str(e)

                tool_message = ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
                tool_messages.append(tool_message)

            if ask_user:
                tool_messages.append(AIMessage(content=ai_msg))
                return Command(
                    update={
                        "messages": tool_messages,
                        "selected_tool_ids": new_tool_ids,
                        "context": effective_existing_context,
                        "add_context": effective_previous_add_context,
                    }
                )

            return Command(
                goto="call_model",
                update={
                    "messages": tool_messages,
                    "selected_tool_ids": new_tool_ids,
                    "context": effective_existing_context,
                    "add_context": effective_previous_add_context,
                },
            )

        async def agent_builder(state: CodeActState, writer: StreamWriter) -> Command[Literal["call_model"]]:
            agent_builder_mode = state.get("agent_builder_mode")
            if agent_builder_mode == "planning":
                planner_instructions = self.instructions + AGENT_BUILDER_PLANNER_PROMPT + self.preloaded_defs
                existing_plan_steps = None
                if self.agent and getattr(self.agent, "instructions", None):
                    existing_plan_steps = self.agent.instructions.get("plan")

                messages = [{"role": "system", "content": planner_instructions}]
                if existing_plan_steps:
                    plan_block = "\n".join(str(s) for s in existing_plan_steps)
                    messages.append({
                        "role": "system",
                        "content": f"Existing plan steps:\n{plan_block}"
                    })
                messages += state["messages"]

                # Bind planning tool so the builder can decide when to finalize
                model_with_tools = self.model_instance.bind_tools(
                    tools=[finalize_planning, cancel_planning],
                    tool_choice="auto",
                )
                response = cast(AIMessage, await model_with_tools.ainvoke(messages))

                if response.tool_calls:
                    # If exit was requested, route back to main agent
                    for tc in response.tool_calls:
                        if tc.get("name") == "cancel_planning":
                            return Command(goto="call_model", update={"agent_builder_mode": "inactive"})

                    plan_id = str(uuid.uuid4())
                    writer({"type": "custom", id: plan_id, "name": "planning", "data": {"update": bool(self.agent)}})

                    existing_plan_steps = None
                    if self.agent and getattr(self.agent, "instructions", None):
                        existing_plan_steps = self.agent.instructions.get("plan")
                    if not existing_plan_steps:
                        existing_plan_steps = state.get("plan")

                    if existing_plan_steps:
                        current_plan_text = "\n".join(str(s) for s in (existing_plan_steps or []))
                        plan_patch_instructions = self.instructions + "\n" + AGENT_BUILDER_PLAN_PATCH_PROMPT + self.preloaded_defs
                        base_messages = [{"role": "system", "content": plan_patch_instructions}] + strip_thinking(state["messages"])
                        base_messages.append(HumanMessage(content=f"Current plan (one step per line):\n{current_plan_text}"))
                        model_with_structured_output = self.agent_builder_model_instance.with_structured_output(AgentBuilderPatch)
                        patch_response = await model_with_structured_output.ainvoke(base_messages)
                        proposed_text = cast(AgentBuilderPatch, patch_response).patch
                        updated_plan_text = apply_patch_or_use_proposed(current_plan_text, proposed_text)
                        plan_steps = [line for line in updated_plan_text.splitlines() if line.strip()]
                        plan = AgentBuilderPlan(steps=plan_steps)
                    else:
                        model_with_structured_output = self.agent_builder_model_instance.with_structured_output(
                            AgentBuilderPlan
                        )
                        structured_plan_instructions = self.instructions + AGENT_BUILDER_PLANNING_PROMPT + self.preloaded_defs
                        so_base_messages = [{"role": "system", "content": structured_plan_instructions}] + strip_thinking(
                            state["messages"]
                        )
                        so_response = await model_with_structured_output.ainvoke(
                            so_base_messages
                        )
                        plan = cast(AgentBuilderPlan, so_response)

                    writer({"type": "custom", id: plan_id, "name": "planning", "data": {"plan": plan.steps}})
                    ai_msg = AIMessage(
                        content=json.dumps(plan.model_dump()),
                        additional_kwargs={
                            "type": "planning",
                            "plan": plan.steps,
                            "update": bool(self.agent),
                        },
                        metadata={"tags": ("quiet")}
                    )

                    if self.eval_mode:
                        mock_user_message = HumanMessage(content="yes, this is great")
                        return Command(
                            goto="agent_builder",
                            update={
                                "messages": [ai_msg, mock_user_message],
                                "agent_builder_mode": "generating",
                                "plan": plan.steps,
                            },
                        )

                    return Command(
                        update={
                            "messages": [ai_msg],
                            "agent_builder_mode": "confirming",
                            "plan": plan.steps,
                        }
                    )

                # The builder is asking clarifying questions. Stay in planning mode.
                return Command(update={"messages": [response]})

            elif agent_builder_mode == "confirming":
                # Deterministic routing based on three exact button inputs from UI
                user_text = ""
                for m in reversed(state["messages"]):
                    try:
                        if getattr(m, "type", "") in {"human", "user"}:
                            user_text = (get_message_text(m) or "").strip()
                            if user_text:
                                break
                    except Exception:
                        continue

                t = user_text.lower()
                if t == "yes, this is great":
                    self.meta_id = str(uuid.uuid4())
                    name, description = None, None
                    if self.agent:
                        # Update flow: use existing name/description and do not re-generate
                        name = getattr(self.agent, "name", None)
                        description = getattr(self.agent, "description", None)
                        writer(
                            {
                                "type": "custom",
                                id: self.meta_id,
                                "name": "generating",
                                "data": {
                                    "update": True,
                                    "name": name,
                                    "description": description,
                                },
                            }
                        )
                    else:
                        writer({"type": "custom", id: self.meta_id, "name": "generating", "data": {"update": False}})

                        meta_instructions = self.instructions + AGENT_BUILDER_META_PROMPT
                        messages = [{"role": "system", "content": meta_instructions}] + strip_thinking(state["messages"])

                        model_with_structured_output = self.agent_builder_model_instance.with_structured_output(
                            AgentBuilderMeta
                        )
                        meta_response = await model_with_structured_output.ainvoke(messages)
                        meta = cast(AgentBuilderMeta, meta_response)
                        name, description = meta.name, meta.description

                        # Emit intermediary UI update with created name/description
                        writer(
                            {
                                "type": "custom",
                                id: self.meta_id,
                                "name": "generating",
                                "data": {"update": False, "name": name, "description": description},
                            }
                        )

                    return Command(
                        goto="agent_builder",
                        update={
                            "agent_builder_mode": "generating",
                            "agent_name": name,
                            "agent_description": description,
                        },
                    )
                if t == "i would like to modify the plan":
                    prompt_ai = AIMessage(
                        content="What would you like to change about the plan? Let me know and I'll update the plan accordingly.",
                    )
                    return Command(update={"agent_builder_mode": "planning", "messages": [prompt_ai]})
                if t == "let's do something else":
                    return Command(goto="call_model", update={"agent_builder_mode": "inactive"})

                # Fallback safe default
                return Command(goto="call_model", update={"agent_builder_mode": "inactive"})

            elif agent_builder_mode == "generating":
                existing_code = None
                if self.agent and getattr(self.agent, "instructions", None):
                    existing_code = self.agent.instructions.get("script")
    
                if existing_code:
                    generating_instructions = self.instructions + AGENT_BUILDER_CODE_PATCH_PROMPT + self.preloaded_defs
                    messages = [{"role": "system", "content": generating_instructions}] + strip_thinking(state["messages"])
                    if state.get("plan"):
                        plan_text = "\n".join(str(s) for s in state["plan"])
                        messages.append(HumanMessage(content=f"Confirmed plan (one step per line):\n{plan_text}"))
                    messages.append(HumanMessage(content=f"Current code to update:\n```python\n{existing_code}\n```"))
                    model_with_structured_output = self.agent_builder_model_instance.with_structured_output(AgentBuilderPatch)
                    ai_resp = await model_with_structured_output.ainvoke(messages)
                    proposed = cast(AgentBuilderPatch, ai_resp).patch
                    func_code = apply_patch_or_use_proposed(existing_code, proposed)
                else:
                    generating_instructions = self.instructions + AGENT_BUILDER_GENERATING_PROMPT + self.preloaded_defs
                    messages = [{"role": "system", "content": generating_instructions}] + strip_thinking(state["messages"])
                    model_with_structured_output = self.agent_builder_model_instance.with_structured_output(
                        AgentBuilderCode
                    )
                    response = await model_with_structured_output.ainvoke(messages)
                    func_code = cast(AgentBuilderCode, response).code

                # Extract function name (handle both regular and async functions)
                match = re.search(r"^\s*(?:async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", func_code, re.MULTILINE)
                if match:
                    function_name = match.group(1)
                else:
                    function_name = "generated_agent"

                # Use generated metadata if available
                final_name = state.get("agent_name") or function_name
                final_description = state.get("agent_description") or f"Generated agent: {function_name}"
                add_context = state.get("add_context", {})
                if "functions" not in add_context:
                    add_context["functions"] = []
                add_context["functions"].append(func_code)

                # Save or update an Agent using the helper registry
                try:
                    if not self.agent_builder_registry:
                        raise ValueError("AgentBuilder registry is not configured")

                    plan_params = extract_plan_parameters(state["plan"])

                    # Build instructions payload embedding the plan and function code
                    instructions_payload = {
                        "plan": state["plan"],
                        "script": func_code,
                        "params": plan_params,
                    }

                    # Convert tool ids list to dict
                    tool_dict = convert_tool_ids_to_dict(state["selected_tool_ids"])

                    res = self.agent_builder_registry.upsert_agent(
                        name=final_name,
                        description=final_description,
                        instructions=instructions_payload,
                        tools=tool_dict,
                    )
                except Exception:
                    # In case of error, add the code to the exit message content

                    mock_exit_tool_call = {"name": "exit_agent_builder_mode", "args": {}, "id": "exit_builder_1"}

                    # Create a minimal assistant message to maintain flow
                    mock_assistant_message = AIMessage(
                        content=json.dumps({"code": func_code}),
                        tool_calls=[mock_exit_tool_call],
                        additional_kwargs={
                            "type": "generating",
                            "id": "ignore",
                            "update": bool(self.agent),
                            "name": final_name.replace(" ", "_"),
                            "description": final_description,
                        },
                        metadata={"tags": ("quiet")}
                    )
                    mock_exit_tool_response = ToolMessage(
                        content=json.dumps(
                            f"An error occurred. Displaying the function code:\n\n{func_code}\nFinal Name: {final_name}\nDescription: {final_description}"
                        ),
                        name="exit_agent_builder_mode",
                        tool_call_id="exit_builder_1",
                    )
                    if self.eval_mode:
                        human_msg = HumanMessage(content="Call the generated agent function (without redeclaring it) and check whether it works as expected")
                        return Command(goto="call_model", update={"messages": [mock_assistant_message, mock_exit_tool_response, human_msg], "agent_builder_mode": "normal", "add_context": add_context})
                    else:
                        return Command(update={"messages": [mock_assistant_message, mock_exit_tool_response], "agent_builder_mode": "normal", "add_context": add_context})

                writer(
                    {
                        "type": "custom",
                        id: self.meta_id,
                        "name": "generating",
                        "data": {
                            "id": str(res.id),
                            "update": bool(self.agent),
                            "name": final_name,
                            "description": final_description,
                            "add_context": add_context,
                        },
                    }
                )
                mock_exit_tool_call = {"name": "exit_agent_builder_mode", "args": {}, "id": "exit_builder_1"}
                mock_assistant_message = AIMessage(
                    content=json.dumps({"code": func_code}),
                    tool_calls=[mock_exit_tool_call],
                    additional_kwargs={
                        "type": "generating",
                        "id": str(res.id),
                        "update": bool(self.agent),
                        "name": final_name.replace(" ", "_"),
                        "description": final_description,
                    },
                    metadata={"tags": ("quiet")}
                )

                mock_exit_tool_response = ToolMessage(
                    content=json.dumps(
                        "Exited Agent Builder Mode. Enter this mode again if you need to modify the saved agent."
                    ),
                    name="exit_agent_builder_mode",
                    tool_call_id="exit_builder_1",
                )

                return Command(
                    update={
                        "messages": [mock_assistant_message, mock_exit_tool_response],
                        "agent_builder_mode": "normal",
                        "add_context": add_context,
                    }
                )

        async def route_entry(state: CodeActState) -> Command[Literal["call_model", "agent_builder", "execute_tools"]]:
            """Route to either normal mode or agent builder creation"""
            pre_tools = await self.registry.export_tools(format=ToolFormat.NATIVE)

            # Create the initial system prompt and tools_context in one go
            self.final_instructions, self.tools_context = create_default_prompt(
                pre_tools,
                self.additional_tools,
                self.instructions,
                await get_connected_apps_string(self.registry),
                self.agent,
                is_initial_prompt=True,
            )
            self.preloaded_defs, _ = build_tool_definitions(pre_tools)
            self.preloaded_defs = "\n".join(self.preloaded_defs)
            await self.registry.load_tools(state["selected_tool_ids"])
            exported_tools = await self.registry.export_tools(
                state["selected_tool_ids"], ToolFormat.NATIVE
            )  # Get definition for only the new tools
            _, loaded_tools_context = build_tool_definitions(exported_tools)
            self.tools_context.update(loaded_tools_context)

            if (
                len(state["messages"]) == 1 and self.agent
            ):  # Inject the agent's script function into add_context for execution
                script = self.agent.instructions.get("script")
                add_context = {"functions": [script]}
                return Command(goto="call_model", update={"add_context": add_context})

            if state.get("agent_builder_mode") in ["planning", "confirming", "generating"]:
                return Command(goto="agent_builder")
            return Command(goto="call_model")

        agent = StateGraph(state_schema=CodeActState)
        agent.add_node(call_model, retry_policy=RetryPolicy(max_attempts=3, retry_on=filter_retry_on))
        agent.add_node(agent_builder)
        agent.add_node(execute_tools)
        agent.add_node(route_entry)
        agent.add_edge(START, "route_entry")
        return agent.compile(checkpointer=self.memory)
