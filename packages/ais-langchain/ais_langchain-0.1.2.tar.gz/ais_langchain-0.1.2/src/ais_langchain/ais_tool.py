"""
Basic AIS Tool Adapters for LangChain

Simple integration for quick start with AIS Protocol agents in LangChain.
"""

import json
from typing import Any, Dict, List, Optional, Type

from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, Field, create_model


# Note: AISClient type hint - users will import from @ais-protocol/core
class AISClient:
    """Type stub for AIS client."""

    async def call(
        self, capability: str, params: Any, options: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Call capability."""
        ...

    def server_capabilities(self) -> List[Any]:
        """Get server capabilities."""
        ...


def create_ais_tool(
    client: Any,  # AISClient from @ais-protocol/core
    capability: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    args_schema: Optional[Type[BaseModel]] = None,
    timeout: Optional[float] = None,
) -> StructuredTool:
    """
    Create a basic LangChain tool from an AIS capability.

    Args:
        client: AIS client instance
        capability: Capability name to invoke
        name: Tool name (defaults to capability name)
        description: Tool description
        args_schema: Pydantic model for arguments
        timeout: Call timeout in seconds

    Returns:
        LangChain StructuredTool

    Example:
        ```python
        from ais_protocol import AISClient
        from ais_langchain import create_ais_tool
        from pydantic import BaseModel, Field

        class CalculateArgs(BaseModel):
            operation: str = Field(description="Operation: add, subtract, multiply, divide")
            a: float = Field(description="First operand")
            b: float = Field(description="Second operand")

        client = AISClient(agent_id="agent://example.com/client")
        await client.connect("http://localhost:8000")

        calculator = create_ais_tool(
            client=client,
            capability="calculate",
            description="Perform mathematical calculations",
            args_schema=CalculateArgs
        )
        ```
    """
    tool_name = name or capability
    tool_description = description or f"Call AIS capability: {capability}"

    # Create default args schema if not provided
    if args_schema is None:
        args_schema = create_model(
            f"{capability}_args",
            params=(
                Dict[str, Any],
                Field(
                    default_factory=dict,
                    description="Parameters for the capability",
                ),
            ),
        )

    async def _call_capability(**kwargs: Any) -> str:
        """Internal function to call AIS capability."""
        try:
            # Prepare parameters
            params = kwargs

            # Call capability
            options = {"timeout": timeout} if timeout else None
            result = await client.call(capability, params, options)

            # Convert result to string
            return _format_result(result)

        except Exception as error:
            return f"Error calling AIS capability '{capability}': {str(error)}"

    # Create structured tool
    tool = StructuredTool(
        name=tool_name,
        description=tool_description,
        args_schema=args_schema,
        coroutine=_call_capability,
    )

    return tool


def create_ais_tools(
    client: Any,  # AISClient from @ais-protocol/core
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
    prefix: str = "",
    timeout: Optional[float] = None,
) -> List[StructuredTool]:
    """
    Auto-generate LangChain tools from all AIS agent capabilities.

    Args:
        client: AIS client instance
        include: Only include these capabilities (None = all)
        exclude: Exclude these capabilities
        prefix: Prefix for tool names
        timeout: Default timeout for all tools

    Returns:
        List of LangChain tools

    Example:
        ```python
        from ais_protocol import AISClient
        from ais_langchain import create_ais_tools

        client = AISClient(agent_id="agent://example.com/client")
        await client.connect("http://localhost:8000")

        # Create tools from all capabilities
        tools = create_ais_tools(client)

        # Or filter specific capabilities
        tools = create_ais_tools(
            client,
            include=["calculate", "process_text"],
            prefix="ais_"
        )
        ```
    """
    capabilities = client.server_capabilities()
    tools: List[StructuredTool] = []

    for cap in capabilities:
        # Get capability name
        if isinstance(cap, str):
            cap_name = cap
            cap_desc = None
        elif isinstance(cap, dict):
            cap_name = cap.get("name", "")
            cap_desc = cap.get("description")
        else:
            # Capability object with .name attribute
            cap_name = getattr(cap, "name", str(cap))
            cap_desc = getattr(cap, "description", None)

        # Apply filters
        if include and cap_name not in include:
            continue
        if exclude and cap_name in exclude:
            continue

        # Create tool
        tool_name = f"{prefix}{cap_name}" if prefix else cap_name
        tool = create_ais_tool(
            client=client,
            capability=cap_name,
            name=tool_name,
            description=cap_desc,
            timeout=timeout,
        )
        tools.append(tool)

    return tools


def _format_result(result: Any) -> str:
    """
    Format capability result as string for LangChain.

    Args:
        result: Capability result

    Returns:
        Formatted string
    """
    if isinstance(result, str):
        return result

    if isinstance(result, dict):
        # Check for common result fields
        if "result" in result:
            return str(result["result"])
        if "message" in result:
            return str(result["message"])
        if "text" in result:
            return str(result["text"])
        if "output" in result:
            return str(result["output"])

        # Pretty print JSON
        return json.dumps(result, indent=2)

    if isinstance(result, (list, tuple)):
        return json.dumps(result, indent=2)

    # Default: convert to string
    return str(result)
