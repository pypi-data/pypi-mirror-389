import asyncio
import base64
from collections import defaultdict
from pathlib import Path
from typing import Annotated, Any

from langchain_core.tools import tool
from pydantic import Field
from universal_mcp.agentr.client import AgentrClient
from universal_mcp.agentr.registry import AgentrRegistry
from universal_mcp.applications.markitdown.app import MarkitdownApp
from universal_mcp.types import ToolFormat
from langgraph.types import StreamWriter

from universal_mcp.agents.codeact01.prompts import build_tool_definitions
import uuid


def enter_agent_builder_mode():
    """Call this function to enter agent builder mode. Agent builder mode is when the user wants to store a repeated task as a script with some inputs for the future."""
    return


def create_meta_tools(tool_registry: AgentrRegistry) -> dict[str, Any]:
    """Create the meta tools for searching and loading tools"""

    @tool
    async def search_functions(
        queries: Annotated[
            list[list[str]] | None,
            Field(
                description="A list of query lists. Each inner list contains one or more search terms that will be used together to find relevant tools."
            ),
        ] = None,
        app_ids: Annotated[
            list[str] | None,
            Field(description="The ID or list of IDs (common names) of specific applications to search within."),
        ] = None,
    ) -> str:
        """
        Searches for relevant functions based on queries and/or applications. This function
        operates in three powerful modes with support for multi-query searches:

        1.  **Global Search** (`queries` only as List[List[str]]):
            - Searches all functions across all applications.
            - Supports multiple independent searches in parallel.
            - Each inner list represents a separate search query.

            Examples:
            - Single global search:
              `search_functions(queries=[["create presentation"]])`

            - Multiple independent global searches:
              `search_functions(queries=[["send email"], ["schedule meeting"]])`

            - Multi-term search for comprehensive results:
              `search_functions(queries=[["send email", "draft email", "compose email"]])`

        2.  **App Discovery** (`app_ids` only as List[str]):
            - Returns ALL available functions for one or more specific applications.
            - Use this to explore the complete capability set of an application.

            Examples:
            - Single app discovery:
              `search_functions(app_ids=["Gmail"])`

            - Multiple app discovery:
              `search_functions(app_ids=["Gmail", "Google Calendar", "Slack"])`

        3.  **Scoped Search** (`queries` as List[List[str]] and `app_ids` as List[str]):
            - Performs targeted searches within specific applications in parallel.
            - The number of app_ids must match the number of inner query lists.
            - Each query list is searched within its corresponding app_id.
            - Supports multiple search terms per app for comprehensive discovery.

            Examples:
            - Basic scoped search (one query per app):
              `search_functions(queries=[["find email"], ["share file"]], app_ids=["Gmail", "Google_Drive"])`

            - Multi-term scoped search (multiple queries per app):
              `search_functions(
                  queries=[
                      ["send email", "draft email", "compose email", "reply to email"],
                      ["create event", "schedule meeting", "find free time"],
                      ["upload file", "share file", "create folder", "search files"]
                  ],
                  app_ids=["Gmail", "Google Calendar", "Google_Drive"]
              )`

            - Mixed complexity (some apps with single query, others with multiple):
              `search_functions(
                  queries=[
                      ["list messages"],
                      ["create event", "delete event", "update event"]
                  ],
                  app_ids=["Gmail", "Google Calendar"]
              )`

        **Pro Tips:**
        - Use multiple search terms in a single query list to cast a wider net and discover related functionality
        - Multi-term searches are more efficient than separate calls
        - Scoped searches return more focused results than global searches
        - The function returns connection status for each app (connected vs NOT connected)
        - All searches within a single call execute in parallel for maximum efficiency

        **Parameters:**
        - `queries` (List[List[str]], optional): A list of query lists. Each inner list contains one or more
          search terms that will be used together to find relevant tools.
        - `app_ids` (List[str], optional): A list of application IDs to search within or discover.

        **Returns:**
        - A structured response containing:
          - Matched tools with their descriptions
          - Connection status for each app
          - Recommendations for which tools to load next
        """
        registry = tool_registry

        TOOL_THRESHOLD = 0.75
        APP_THRESHOLD = 0.7

        # --- Helper Functions for Different Search Modes ---

        async def _handle_global_search(queries: list[str]) -> list[list[dict[str, Any]]]:
            """Performs a broad search across all apps to find relevant tools and apps."""
            # 1. Perform initial broad searches for tools and apps concurrently.
            initial_tool_tasks = [registry.search_tools(query=q, distance_threshold=TOOL_THRESHOLD) for q in queries]
            app_search_tasks = [registry.search_apps(query=q, distance_threshold=APP_THRESHOLD) for q in queries]

            initial_tool_results, app_search_results = await asyncio.gather(
                asyncio.gather(*initial_tool_tasks), asyncio.gather(*app_search_tasks)
            )

            # 2. Create a prioritized list of app IDs for the final search.
            app_ids_from_apps = {app["id"] for result_list in app_search_results for app in result_list}
            prioritized_app_id_list = list(app_ids_from_apps)

            app_ids_from_tools = {tool["app_id"] for result_list in initial_tool_results for tool in result_list}
            for tool_app_id in app_ids_from_tools:
                if tool_app_id not in app_ids_from_apps:
                    prioritized_app_id_list.append(tool_app_id)

            if not prioritized_app_id_list:
                return []

            # 3. Perform the final, comprehensive tool search across the prioritized apps.
            final_tool_search_tasks = [
                registry.search_tools(query=query, app_id=app_id_to_search, distance_threshold=TOOL_THRESHOLD)
                for app_id_to_search in prioritized_app_id_list
                for query in queries
            ]
            return await asyncio.gather(*final_tool_search_tasks)

        async def _handle_scoped_search(app_ids: list[str], queries: list[list[str]]) -> list[list[dict[str, Any]]]:
            """Performs targeted searches for specific queries within specific applications."""
            if len(app_ids) != len(queries):
                raise ValueError("The number of app_ids must match the number of query lists.")

            tasks = []
            for app_id, query_list in zip(app_ids, queries):
                for query in query_list:
                    # Create a search task for each query in the list for the corresponding app
                    tasks.append(registry.search_tools(query=query, app_id=app_id, distance_threshold=TOOL_THRESHOLD))

            return await asyncio.gather(*tasks)

        async def _handle_app_discovery(app_ids: list[str]) -> list[list[dict[str, Any]]]:
            """Fetches all tools for a list of applications."""
            tasks = [registry.search_tools(query="", app_id=app_id, limit=20) for app_id in app_ids]
            return await asyncio.gather(*tasks)

        # --- Helper Functions for Structuring and Formatting Results ---

        def _format_response(structured_results: list[dict[str, Any]]) -> str:
            """Builds the final, user-facing formatted string response from structured data."""
            if not structured_results:
                return "No relevant functions were found."

            result_parts = []
            apps_in_results = {app["app_id"] for app in structured_results}
            connected_apps_in_results = {
                app["app_id"] for app in structured_results if app["connection_status"] == "connected"
            }

            for app in structured_results:
                app_id = app["app_id"]
                app_status = "connected" if app["connection_status"] == "connected" else "NOT connected"
                result_parts.append(f"Tools from {app_id} (status: {app_status} by user):")

                for tool in app["tools"]:
                    result_parts.append(f" - {tool['id']}: {tool['description']}")
                result_parts.append("")  # Empty line for readability

            # Add summary connection status messages
            if not connected_apps_in_results and len(apps_in_results) > 1:
                result_parts.append(
                    "Connection Status: None of the apps in the results are connected. "
                    "You must ask the user to choose the application."
                )
            elif len(connected_apps_in_results) > 1:
                connected_list = ", ".join(sorted(list(connected_apps_in_results)))
                result_parts.append(
                    f"Connection Status: Multiple apps are connected ({connected_list}). "
                    "You must ask the user to select which application they want to use."
                )

            result_parts.append("Call load_functions to select the required functions only.")
            if 0 <= len(connected_apps_in_results) < len(apps_in_results):
                result_parts.append(
                    "Unconnected app functions can also be loaded if asked for by the user, they will generate a connection link"
                    "but prefer connected ones. Ask the user to choose the app if none of the "
                    "relevant apps are connected."
                )

            return "\n".join(result_parts)

        def _structure_tool_results(
            raw_tool_lists: list[list[dict[str, Any]]], connected_app_ids: set[str]
        ) -> list[dict[str, Any]]:
            """
            Converts raw search results into a structured format, handling duplicates,
            cleaning descriptions, and adding connection status.
            """
            aggregated_tools = defaultdict(dict)
            # Use a list to maintain the order of apps as they are found.
            ordered_app_ids = []

            for tool_list in raw_tool_lists:
                for tool in tool_list:
                    app_id = tool.get("app_id", "unknown")
                    tool_id = tool.get("id")

                    if not tool_id:
                        continue

                    if app_id not in aggregated_tools:
                        ordered_app_ids.append(app_id)

                    if tool_id not in aggregated_tools[app_id]:
                        aggregated_tools[app_id][tool_id] = {
                            "id": tool_id,
                            "description": _clean_tool_description(tool.get("description", "")),
                        }

            # Build the final results list respecting the discovery order.
            found_tools_result = []
            for app_id in ordered_app_ids:
                if app_id in aggregated_tools and aggregated_tools[app_id]:
                    found_tools_result.append(
                        {
                            "app_id": app_id,
                            "connection_status": "connected" if app_id in connected_app_ids else "not_connected",
                            "tools": list(aggregated_tools[app_id].values()),
                        }
                    )
            return found_tools_result

        def _clean_tool_description(description: str) -> str:
            """Consistently formats tool descriptions by removing implementation details."""
            return description.split("Context:")[0].strip()

        # Main Function Logic

        if not queries and not app_ids:
            raise ValueError("You must provide 'queries', 'app_ids', or both.")

        # --- Initialization and Input Normalization ---
        connections = await registry.list_connected_apps()
        connected_app_ids = {connection["app_id"] for connection in connections}

        canonical_app_ids = []
        if app_ids:
            # Concurrently search for all provided app names
            app_search_tasks = [
                registry.search_apps(query=app_name, distance_threshold=APP_THRESHOLD) for app_name in app_ids
            ]
            app_search_results = await asyncio.gather(*app_search_tasks)

            # Process results and build the list of canonical IDs, handling not found errors
            for app_name, result_list in zip(app_ids, app_search_results):
                if not result_list:
                    raise ValueError(f"Application '{app_name}' could not be found.")
                # Assume the first result is the correct one
                canonical_app_ids.append(result_list[0]["id"])

        # --- Mode Dispatching ---
        raw_results = []

        if canonical_app_ids and queries:
            raw_results = await _handle_scoped_search(canonical_app_ids, queries)
        elif canonical_app_ids:
            raw_results = await _handle_app_discovery(canonical_app_ids)
        elif queries:
            # Flatten list of lists to list of strings for global search
            flat_queries = (
                [q for sublist in queries for q in sublist] if queries and not isinstance(queries[0], str) else queries
            )
            raw_results = await _handle_global_search(flat_queries)

        # --- Structuring and Formatting ---
        structured_data = _structure_tool_results(raw_results, connected_app_ids)
        return _format_response(structured_data)

    @tool
    async def load_functions(tool_ids: list[str]) -> str:
        """
        Loads specified functions and returns their Python signatures and docstrings.
        This makes the functions available for use inside the 'execute_ipython_cell' tool.
        The agent MUST use the returned information to understand how to call the functions correctly.

        Args:
            tool_ids: A list of function IDs in the format 'app__function'. Example: ['google_mail__send_email']

        Returns:
            A string containing the signatures and docstrings of the successfully loaded functions,
            ready for the agent to use in its code.
        """
        if not tool_ids:
            return "No tool IDs provided to load."

        # Step 1: Validate which tools are usable and get login links for others.
        valid_tools, unconnected_links = await get_valid_tools(tool_ids=tool_ids, registry=tool_registry)

        if not valid_tools:
            response_string = "Error: None of the provided tool IDs could be validated or loaded."
            return response_string, {}, [], ""

        # Step 2: Export the schemas of the valid tools.
        await tool_registry.load_tools(valid_tools)
        exported_tools = await tool_registry.export_tools(
            valid_tools, ToolFormat.NATIVE
        )  # Get definition for only the new tools

        # Step 3: Build the informational string for the agent.
        tool_definitions, new_tools_context = build_tool_definitions(exported_tools)

        result_parts = [
            f"Successfully loaded {len(exported_tools)} functions. They are now available for use inside `execute_ipython_cell`:",
            "\n".join(tool_definitions),
        ]

        response_string = "\n\n".join(result_parts)
        unconnected_links = "\n".join(unconnected_links)

        return response_string, new_tools_context, valid_tools, unconnected_links

    async def web_search(query: str) -> dict:
        """
        Get an LLM answer to a question informed by Exa search results. Useful when you need information from a wide range of real-time sources on the web. Do not use this when you need to access contents of a specific webpage.

        This tool performs an Exa `/answer` request, which:
        1. Provides a **direct answer** for factual queries (e.g., "What is the capital of France?" → "Paris")
        2. Generates a **summary with citations** for open-ended questions
        (e.g., "What is the state of AI in healthcare?" → A detailed summary with source links)

        Args:
            query (str): The question or topic to answer.
        Returns:
            dict: A structured response containing only:
                - answer (str): Generated answer
                - citations (list[dict]): List of cited sources
        """
        await tool_registry.export_tools(["exa__answer"], ToolFormat.LANGCHAIN)
        response = await tool_registry.call_tool("exa__answer", {"query": query, "text": True})

        # Extract only desired fields
        return {
            "answer": response.get("answer"),
            "citations": response.get("citations", []),
        }

    async def read_file(uri: str) -> str:
        """
        Asynchronously reads a local file or uri and returns the content as a markdown string.

        This tool aims to extract the main text content from various sources.
        It automatically prepends 'file://' to the input string if it appears
        to be a local path without a specified scheme (like http, https, data, file).

        Args:
            uri (str): The URI pointing to the resource or a local file path.
                       Supported schemes:
                       - http:// or https:// (Web pages, feeds, APIs)
                       - file:// (Local or accessible network files)
                       - data: (Embedded data)

        Returns:
            A string containing the markdown representation of the content at the specified URI

        Raises:
            ValueError: If the URI is invalid, empty, or uses an unsupported scheme
                        after automatic prefixing.

        Tags:
            convert, markdown, async, uri, transform, document, important
        """
        markitdown = MarkitdownApp()
        response = await markitdown.convert_to_markdown(uri)
        return response

    def save_file(file_name: str, content: str) -> dict:
        """
        Saves a file to the local filesystem.

        Args:
            file_name (str): The name of the file to save.
            content (str): The content to save to the file.

        Returns:
            dict: A dictionary containing the result of the save operation with the following fields:
                - status (str): "success" if the save succeeded, "error" otherwise.
                - message (str): A message returned by the server, typically indicating success or providing error details.
        """
        with Path(file_name).open("w") as f:
            f.write(content)

        return {
            "status": "success",
            "message": f"File {file_name} saved successfully",
            "file_path": Path(file_name).absolute(),
        }

    def upload_file(file_name: str, mime_type: str, base64_data: str) -> dict:
        """
        Uploads a file to the server.

        Args:
            file_name (str): The name of the file to upload.
            mime_type (str): The MIME type of the file.
            base64_data (str): The file content encoded as a base64 string.

        Returns:
            dict: A dictionary containing the result of the upload operation with the following fields:
                - status (str): "success" if the upload succeeded, "error" otherwise.
                - message (str): A message returned by the server, typically indicating success or providing error details.
                - signed_url (str or None): The signed URL to access the uploaded file if successful, None otherwise.
        """
        client: AgentrClient = tool_registry.client
        bytes_data = base64.b64decode(base64_data)
        response = client._upload_file(file_name, mime_type, bytes_data)
        if response.get("status") != "success":
            return {
                "status": "error",
                "message": response.get("message"),
                "signed_url": None,
            }
        return {
            "status": "success",
            "message": response.get("message"),
            "signed_url": response.get("signed_url"),
        }

    return {
        "search_functions": search_functions,
        "load_functions": load_functions,
        "web_search": web_search,
        "read_file": read_file,
        "upload_file": upload_file,
        "save_file": save_file,
    }

def create_agent_builder_tools() -> dict[str, Any]:
    """Create tools for agent plan and code creation, saving, modifying"""
    @tool
    async def create_agent_plan(steps: list[str]):
        """ Call this tool to create a draft of a reusable agent plan, that will be used to create a corresponding Python script in the next step if approved by the user in conversation.
            Args:
                steps (list[str]):- A list of strings. Each string is a step in the agent plan, obeying the following rules-

            Rules:
            - Do NOT include the searching or loading of functions for applications. Assume that the functions have already been loaded.
            - The plan is a sequence of steps corresponding to the key logical steps taken to achieve the user's task in the conversation history, without focusing on technical specifics.
            - Identify user-provided information as variables that should become the main agent input parameters using `variable_name` syntax, enclosed by backticks `...`. Intermediate variables should be highlighted using italics, i.e. *...*, NEVER `...`
            - Keep the logic generic and reusable. Avoid hardcoding any names/constants. However, do try to keep them as variables with defaults, especially if used in the conversation history. They should be represented as `variable_name(default = default_value)`.
            - Have a human-friendly plan and inputs format. That is, it must not use internal IDs or keys used by APIs as either inputs or outputs to the overall plan; using them internally is okay.
            - Be as concise as possible, especially for internal processing steps.
            - For steps where the assistant's intelligence was used outside of the code to infer/decide/analyse something, replace it with the use of *llm__* functions in the plan if required.

            Example Conversation History:
            User Message: "Create an image using Gemini for Marvel Cinematic Universe in comic style"
            Code snippet: image_result = await google_gemini__generate_image(prompt=prompt)
            Assistant Message: "The image has been successfully generated [image_result]."
            User Message: "Save the image in my OneDrive"
            Code snippet: image_data = base64.b64decode(image_result['data'])
                temp_file_path = tempfile.mktemp(suffix='.png')
                with open(temp_file_path, 'wb') as f:
                    f.write(image_data)
                # Upload the image to OneDrive with a descriptive filename
                onedrive_filename = "Marvel_Cinematic_Universe_Comic_Style.png"

                print(f"Uploading to OneDrive as: {onedrive_filename}")

                # Upload to OneDrive root folder
                upload_result = onedrive__upload_file(
                    file_path=temp_file_path,
                    parent_id='root',
                    file_name=onedrive_filename
                )

            Generated Steps:
            "steps": [
                "Generate an image using Gemini model with `image_prompt` and `style(default = 'comic')`",
                "Upload the obtained image to OneDrive using `onedrive_filename(default = 'generated_image.png')` and `onedrive_parent_folder(default = 'root')`",
                "Return confirmation of upload including file name and destination path, and link to the upload"
            ]
            Note that internal variables like upload_result, image_result are not highlighted in the plan, and intermediate processing details are skipped.
            Now create a plan based on the conversation history. Do not include any other text or explanation in your response. Just the JSON object.
        """
        return steps
    @tool
    async def modify_agent_plan(modifications: list[str]):
        """ Call this tool to modify a plan created using create_agent_plan.
            Args:
                steps (list[str]):- A list of strings. Each string can be one of the following-
                - <nochange> carries the corresponding step from the most recently created plan using create_agent_plan.
                - <new>content</new> adds a step to the previous plan, shifting the further steps of the plan one step ahead.
                - <modify>content</modify> rewrites an entire step and replaces it with content.
                - <delete> deletes the corresponding step.
            Follow the same rules for steps as create_agent_plan.
            You must call this before save_agent_code if there is any change requested by the user to the plan.
        """
        return modifications
    @tool
    async def save_agent_code(agent_name: str, agent_description: str, python_code: str):
        """
            Call this tool to save reusable Python code for the agent.
            Args:
                -agent_name: 3-6 words, Title Case, no punctuation except hyphens if needed
                -agent_description: Single sentence, <= 140 characters, clearly states what the agent does
                -python_code(str): The python code in string form, obeying the following rules-
            It should be granular, reusable Python code for an agent based on the final confirmed plan and the conversation history (user messages, assistant messages, and code executions).
            Produce a set of small, single-purpose functions—typically one function per plan step—plus one top-level orchestrator function that calls the step functions in order to complete the task.

            Rules-
            - Do NOT include the searching and loading of functions. Assume required functions have already been loaded. Include imports you need.
            - Your response must be **ONLY Python code**. No markdown or explanations.
            - Define multiple top-level functions:
            1) One small, clear function for each plan step (as granular as practical), with an underscore as the first character in its name.
            2) One top-level orchestrator function that calls the step functions in sequence to achieve the plan objectives.
            - The orchestrator function's parameters **must exactly match the external variables** in the agent plan (the ones marked with backticks `` `variable_name` ``). Provide defaults exactly as specified in the plan when present. Variables in italics (i.e. enclosed in *...*) are internal and must not be orchestrator parameters.
            - The orchestrator function MUST be declared with `def` or `async def` and be directly runnable with a single Python command (e.g., `image_generator(...)`). If it is async, assume the caller will `await` it.
            - NEVER use asyncio or asyncio.run(). The code is executed in a ipython environment, so using await is enough.
            - Step functions should accept only the inputs they need, return explicit outputs, and pass intermediate results forward via return values—not globals.
            - Name functions in snake_case derived from their purpose/step. Use keyword arguments in calls; avoid positional-only calls.
            - Keep the code self-contained and executable. Put imports at the top of the code. Do not nest functions unless strictly necessary.
            - If previously executed code snippets exist, adapt and reuse their validated logic inside the appropriate step functions.
            - Do not print the final output; return it from the orchestrator.

            Example:

            If the plan has:

            "steps": [
            "Receive creative description as image_prompt",
            "Generate image using Gemini with style(default = 'comic')",
            "Save temporary image internally as *temp_file_path*",
            "Upload *temp_file_path* to OneDrive folder onedrive_parent_folder(default = 'root')"
            ]

            Then the functions should look like:

            ```python
            from typing import Dict

            def _generate_image(image_prompt: str, style: str = "comic") -> Dict:
                # previously validated code to call Gemini
                ...

            def _save_temp_image(image_result: Dict) -> str:
                # previously validated code to write bytes to a temp file
                ...

            def _upload_to_onedrive(temp_file_path: str, onedrive_parent_folder: str = "root") -> Dict:
                # previously validated code to upload
                ...

            def image_generator(image_prompt: str, style: str = "comic", onedrive_parent_folder: str = "root") -> Dict:
                image_result = generate_image(image_prompt=image_prompt, style=style)
                temp_file_path = save_temp_image(image_result=image_result)
                upload_result = upload_to_onedrive(temp_file_path=temp_file_path, onedrive_parent_folder=onedrive_parent_folder)
                return upload_result
            ```

            Use this convention consistently to generate the final agent
            """
        return agent_name, agent_description, python_code
    return {
        "create_agent_plan": create_agent_plan,
        "save_agent_code": save_agent_code,
        "modify_agent_plan": modify_agent_plan,
    }



async def get_valid_tools(tool_ids: list[str], registry: AgentrRegistry) -> tuple[list[str], list[str]]:
    """For a given list of tool_ids, validates the tools and returns a list of links for the apps that have not been logged in"""
    correct, incorrect = [], []
    connections = await registry.list_connected_apps()
    connected_apps = {connection["app_id"] for connection in connections}
    unconnected = set()
    unconnected_links = []
    app_tool_list: dict[str, set[str]] = {}

    # Group tool_ids by app for fewer registry calls
    app_to_tools: dict[str, list[tuple[str, str]]] = {}
    for tool_id in tool_ids:
        if "__" not in tool_id:
            incorrect.append(tool_id)
            continue
        app, tool_name = tool_id.split("__", 1)
        app_to_tools.setdefault(app, []).append((tool_id, tool_name))

    # Fetch all apps concurrently
    async def fetch_tools(app: str):
        try:
            tools_dict = await registry.list_tools(app)
            return app, {tool_unit["name"] for tool_unit in tools_dict}
        except Exception:
            return app, None

    results = await asyncio.gather(*(fetch_tools(app) for app in app_to_tools))

    # Build map of available tools per app
    for app, tools in results:
        if tools is not None:
            app_tool_list[app] = tools

    # Validate tool_ids
    for app, tool_entries in app_to_tools.items():
        available = app_tool_list.get(app)
        if available is None:
            incorrect.extend(tool_id for tool_id, _ in tool_entries)
            continue
        if app not in connected_apps and app not in unconnected:
            unconnected.add(app)
            text = await registry.authorise_app(app_id=app)
            start = text.find(":") + 1
            end = text.find(". R", start)
            url = text[start:end].strip()
            markdown_link = f"[Connect to {app.capitalize()}]({url})"
            unconnected_links.append(markdown_link)
        for tool_id, tool_name in tool_entries:
            if tool_name in available:
                correct.append(tool_id)
            else:
                incorrect.append(tool_id)

    return correct, unconnected_links
