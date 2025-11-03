"""
Comprehensive tests for basic AIS tool adapters

Tests:
- create_ais_tool
- create_ais_tools
"""

import pytest
from ais_langchain.ais_tool import create_ais_tool, create_ais_tools, _format_result
from pydantic import BaseModel, Field


# Mock AIS Client
class MockAISClient:
    def __init__(self):
        self.capabilities = []
        self.responses = {}
        self.call_log = []

    def add_capability(self, name, description=None):
        """Add capability"""
        self.capabilities.append({"name": name, "description": description})

    def set_response(self, capability, response):
        """Set response for capability"""
        self.responses[capability] = response

    async def call(self, capability, params, options=None):
        """Mock call"""
        self.call_log.append({
            "capability": capability,
            "params": params,
            "options": options
        })

        if capability in self.responses:
            return self.responses[capability]

        raise Exception(f"No response configured for {capability}")

    def get_remote_capabilities(self):
        """Get capabilities"""
        return self.capabilities

    def get_call_count(self):
        """Get call count"""
        return len(self.call_log)


# ========================================================================
# CREATE AIS TOOL TESTS
# ========================================================================


class TestCreateAISTool:
    """Test create_ais_tool"""

    @pytest.mark.asyncio
    async def test_creates_tool_with_default_name(self):
        """Should create tool with default name"""
        client = MockAISClient()
        client.set_response("greet", {"message": "Hello!"})

        tool = create_ais_tool(client, "greet")

        assert tool is not None
        assert tool.name == "greet"

    @pytest.mark.asyncio
    async def test_creates_tool_with_custom_name(self):
        """Should create tool with custom name"""
        client = MockAISClient()
        client.set_response("greet", {"message": "Hello!"})

        tool = create_ais_tool(client, "greet", name="custom_name")

        assert tool.name == "custom_name"

    @pytest.mark.asyncio
    async def test_creates_tool_with_description(self):
        """Should create tool with description"""
        client = MockAISClient()
        client.set_response("greet", {"message": "Hello!"})

        tool = create_ais_tool(
            client,
            "greet",
            description="Greet the user"
        )

        assert tool.description == "Greet the user"

    @pytest.mark.asyncio
    async def test_creates_tool_with_default_description(self):
        """Should create tool with default description"""
        client = MockAISClient()
        client.set_response("greet", {"message": "Hello!"})

        tool = create_ais_tool(client, "greet")

        assert tool.description == "Call AIS capability: greet"

    @pytest.mark.asyncio
    async def test_calls_capability(self):
        """Should call AIS capability"""
        client = MockAISClient()
        client.set_response("greet", {"message": "Hello, World!"})

        tool = create_ais_tool(client, "greet")
        result = await tool.ainvoke({"params": {"name": "World"}})

        assert client.get_call_count() == 1
        assert "Hello, World!" in result

    @pytest.mark.asyncio
    async def test_passes_timeout_option(self):
        """Should pass timeout in options"""
        client = MockAISClient()
        client.set_response("slow", {"result": "done"})

        tool = create_ais_tool(client, "slow", timeout=5.0)
        await tool.ainvoke({"params": {}})

        assert client.call_log[0]["options"] == {"timeout": 5.0}

    @pytest.mark.asyncio
    async def test_handles_errors_gracefully(self):
        """Should handle errors and return error message"""
        client = MockAISClient()
        # No response configured, will raise error

        tool = create_ais_tool(client, "missing")
        result = await tool.ainvoke({"params": {}})

        assert "Error" in result
        assert "missing" in result

    @pytest.mark.asyncio
    async def test_with_custom_args_schema(self):
        """Should use custom args schema"""
        class CustomArgs(BaseModel):
            name: str = Field(description="User name")
            age: int = Field(description="User age")

        client = MockAISClient()
        client.set_response("greet", {"message": "Hello!"})

        tool = create_ais_tool(client, "greet", args_schema=CustomArgs)

        # Tool should have custom schema
        assert tool.args_schema == CustomArgs


# ========================================================================
# CREATE AIS TOOLS TESTS
# ========================================================================


class TestCreateAISTools:
    """Test create_ais_tools"""

    @pytest.mark.asyncio
    async def test_creates_tools_from_capabilities(self):
        """Should create tools from all capabilities"""
        client = MockAISClient()
        client.add_capability("calculate", "Perform calculations")
        client.add_capability("translate", "Translate text")
        client.add_capability("summarize", "Summarize text")

        tools = create_ais_tools(client)

        assert len(tools) == 3
        tool_names = [t.name for t in tools]
        assert "calculate" in tool_names
        assert "translate" in tool_names
        assert "summarize" in tool_names

    @pytest.mark.asyncio
    async def test_filters_with_include(self):
        """Should only include specified capabilities"""
        client = MockAISClient()
        client.add_capability("calculate")
        client.add_capability("translate")
        client.add_capability("summarize")

        tools = create_ais_tools(client, include=["calculate", "translate"])

        assert len(tools) == 2
        tool_names = [t.name for t in tools]
        assert "calculate" in tool_names
        assert "translate" in tool_names
        assert "summarize" not in tool_names

    @pytest.mark.asyncio
    async def test_filters_with_exclude(self):
        """Should exclude specified capabilities"""
        client = MockAISClient()
        client.add_capability("calculate")
        client.add_capability("translate")
        client.add_capability("summarize")

        tools = create_ais_tools(client, exclude=["summarize"])

        assert len(tools) == 2
        tool_names = [t.name for t in tools]
        assert "calculate" in tool_names
        assert "translate" in tool_names
        assert "summarize" not in tool_names

    @pytest.mark.asyncio
    async def test_adds_prefix_to_names(self):
        """Should add prefix to tool names"""
        client = MockAISClient()
        client.add_capability("calculate")
        client.add_capability("translate")

        tools = create_ais_tools(client, prefix="ais_")

        assert len(tools) == 2
        tool_names = [t.name for t in tools]
        assert "ais_calculate" in tool_names
        assert "ais_translate" in tool_names

    @pytest.mark.asyncio
    async def test_uses_capability_descriptions(self):
        """Should use capability descriptions"""
        client = MockAISClient()
        client.add_capability("calculate", "Perform math calculations")

        tools = create_ais_tools(client)

        assert len(tools) == 1
        assert tools[0].description == "Perform math calculations"

    @pytest.mark.asyncio
    async def test_handles_string_capabilities(self):
        """Should handle capabilities as strings"""
        client = MockAISClient()
        # Return string capabilities instead of dicts
        client.capabilities = ["calculate", "translate"]

        tools = create_ais_tools(client)

        assert len(tools) == 2
        tool_names = [t.name for t in tools]
        assert "calculate" in tool_names
        assert "translate" in tool_names

    @pytest.mark.asyncio
    async def test_passes_timeout_to_tools(self):
        """Should pass timeout to all tools"""
        client = MockAISClient()
        client.add_capability("test")
        client.set_response("test", {"result": "done"})

        tools = create_ais_tools(client, timeout=5.0)

        # Invoke tool to verify timeout is passed
        await tools[0].ainvoke({"params": {}})
        assert client.call_log[0]["options"] == {"timeout": 5.0}


# ========================================================================
# FORMAT RESULT TESTS
# ========================================================================


class TestFormatResult:
    """Test _format_result"""

    def test_formats_string(self):
        """Should return string as-is"""
        result = _format_result("hello")
        assert result == "hello"

    def test_formats_dict_with_result_field(self):
        """Should extract 'result' field"""
        result = _format_result({"result": 42, "other": "data"})
        assert result == "42"

    def test_formats_dict_with_message_field(self):
        """Should extract 'message' field"""
        result = _format_result({"message": "Hello!", "other": "data"})
        assert result == "Hello!"

    def test_formats_dict_with_text_field(self):
        """Should extract 'text' field"""
        result = _format_result({"text": "Some text", "other": "data"})
        assert result == "Some text"

    def test_formats_dict_with_output_field(self):
        """Should extract 'output' field"""
        result = _format_result({"output": "Output data", "other": "data"})
        assert result == "Output data"

    def test_formats_dict_as_json(self):
        """Should format dict as JSON if no known fields"""
        result = _format_result({"key": "value", "num": 42})
        assert "key" in result
        assert "value" in result
        assert "42" in result

    def test_formats_list_as_json(self):
        """Should format list as JSON"""
        result = _format_result([1, 2, 3])
        assert "1" in result
        assert "2" in result
        assert "3" in result

    def test_formats_number(self):
        """Should convert number to string"""
        result = _format_result(42)
        assert result == "42"

    def test_formats_boolean(self):
        """Should convert boolean to string"""
        result = _format_result(True)
        assert result == "True"
