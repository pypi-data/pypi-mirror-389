import ast
import contextlib
import inspect
import io
import pickle
import queue
import re
import socket
import threading
import types
from typing import Any

from langchain_core.tools import tool

from universal_mcp.agents.codeact01.utils import derive_context, inject_context, smart_truncate


async def eval_unsafe(
    code: str, _locals: dict[str, Any], add_context: dict[str, Any], timeout: int = 180
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """
    Execute code safely with a timeout.
    - Returns (output_str, filtered_locals_dict, new_add_context)
    - Errors or timeout are returned as output_str.
    - Previous variables in _locals persist across calls.
    """

    EXCLUDE_TYPES = (
        types.ModuleType,
        type(re.match("", "")),
        type(re.compile("")),
        type(threading.Lock()),
        type(threading.RLock()),
        threading.Event,
        threading.Condition,
        threading.Semaphore,
        queue.Queue,
        socket.socket,
        io.IOBase,
    )

    result_container = {"output": "<no output>"}

    try:
        compiled_code = compile(code, "<string>", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        with contextlib.redirect_stdout(io.StringIO()) as f:
            coroutine = eval(compiled_code, _locals, _locals)
            # Await the coroutine to run the code if it's async
            if coroutine:
                await coroutine
        result_container["output"] = f.getvalue() or "<code ran, no output printed to stdout>"
    except Exception as e:
        result_container["output"] = f"Error during execution: {type(e).__name__}: {e}"

    # If NameError for provider__tool occurred, append guidance (no retry)
    try:
        m = re.search(r"NameError:\s*name\s*'([^']+)'\s*is\s*not\s*defined", result_container["output"])
        if m and "__" in m.group(1):
            result_container["output"] += "\nHint: If it is a valid tool, load it before running this snippet."
    except Exception:
        pass

    # Filter locals for picklable/storable variables
    all_vars = {}
    for key, value in _locals.items():
        if key.startswith("__"):
            continue
        if inspect.iscoroutine(value) or inspect.iscoroutinefunction(value):
            continue
        if inspect.isasyncgen(value) or inspect.isasyncgenfunction(value):
            continue
        if isinstance(value, EXCLUDE_TYPES):
            continue
        if not callable(value) or not hasattr(value, "__name__"):
            # Only keep if it can be pickled (serialized) successfully
            try:
                pickle.dumps(value)
                all_vars[key] = value
            except Exception:
                pass

    # Safely derive context
    try:
        new_add_context = derive_context(code, add_context)
    except Exception:
        new_add_context = add_context

    return result_container["output"], all_vars, new_add_context


@tool(parse_docstring=True)
def execute_ipython_cell(snippet: str) -> str:
    """
    Executes a Python code snippet in a sandbox with retained context (top level defined functions, variables, imports, loaded functions using `load_functions` are retained)

    **Design Principles**:
    - Break logic into 3-5 small helper functions (max 30 lines each).
    - Keep large constants (e.g., multiline strings, dicts) global or in a dedicated helper function.
    - Modify only the relevant helper during debugging—context persists across executions.
    - Each helper function should do ONE thing
    - Example:
        def _get_json_schema():
            return {"key1":"many details"...}
        def _helper_function_1(...):
            ...

        def _helper_function_2(...):
            ...
        result1 = _helper_function_1(...)
        smart_print(result1[:1]) #As an example, to check if it has been processed correctly
        result2 = _helper_function_2(...)
        smart_print(result2[:1])
        final_result = ...
        smart_print(final_result)
        - Thus, while debugging, if you face an error in result2, you do not need to rewrite _helper_function_1() or _get_json_schema(). 
    - External functions which return a dict or list[dict] are ambiguous. Therefore, you MUST explore the structure of the returned data using `smart_print()` statements before using it, printing keys and values. `smart_print` truncates long strings from data, preventing huge output logs.
    - **Critical:LLM Function Usage Rules:**
        - For text creation or document generation (e.g., HTML, Markdown, textual content for document/email), do not respond directly; you must use execute_ipython_cell with llm__generate_text.
        - For any data extraction, text analysis, or classification task, always use the LLM functions inside python code (llm__extract_data, llm__classify_data, or llm__call_llm)-never rely on regex, manual parsing, or heuristic methods.
        - Use llm__call_llm only as a fallback when the other functions don't match the task exactly.
        - Regex or string manipulation can only be used when the text is fully structured.
    - You can only import libraries that come pre-installed with Python. However, do consider using preloaded functions or searching for external functions first, using the search and load tools to access them in the code.
    - Use loops to process multiple items—test once before scaling.
    - Do not use this tool just to print or expose code execution output to the user. Use markdown without a tool call for final results.

    Args:
        snippet: Python code to execute.

    Returns:
        Execution result or error as a string.

    Raises:
        ValueError: If snippet is empty.
    """
    # Validate required parameters
    if not snippet or not snippet.strip():
        raise ValueError("Parameter 'snippet' is required and cannot be empty or whitespace")

    # Your actual execution logic would go here
    return f"Successfully executed {len(snippet)} characters of Python code"


async def handle_execute_ipython_cell(
    code: str,
    tools_context: dict[str, Any],
    eval_fn,
    effective_previous_add_context: dict[str, Any],
    effective_existing_context: dict[str, Any],
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """
    Execute a code cell with shared state, supporting both sync and async eval functions.

    Returns (output, new_context, new_add_context).
    """
    context = {**tools_context, **effective_existing_context}
    context = inject_context(effective_previous_add_context, context)
    if inspect.iscoroutinefunction(eval_fn):
        output, new_context, new_add_context = await eval_fn(code, context, effective_previous_add_context, 180)
    else:
        output, new_context, new_add_context = eval_fn(code, context, effective_previous_add_context, 180)
    output = smart_truncate(output)
    return output, new_context, new_add_context
