"""
Test URL elicitation functionality
"""

import pytest
from mcp.shared.memory import create_connected_server_and_client_session
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession
from mcp.types import ElicitRequestParams, ElicitResult
from mcp.shared.exceptions import ElicitationRequiredError


@pytest.mark.anyio
async def test_url_elicitation_basic():
    """Test basic URL elicitation functionality."""
    mcp = FastMCP(name="TestURLServer")
    
    @mcp.tool(description="Test URL elicitation")
    async def test_url_tool(ctx: Context[ServerSession, None]) -> str:
        result = await ctx.elicit_url(
            message="Please visit this test URL",
            url="https://example.com/test",
            elicitationId="test-123",
        )
        
        if result.action == "accept":
            return "URL elicitation accepted"
        elif result.action == "decline":
            return "URL elicitation declined"
        else:
            return "URL elicitation cancelled"
    
    # Mock elicitation callback that accepts URL elicitations
    async def mock_elicitation_callback(context, params: ElicitRequestParams):
        if params.mode == "url":
            return ElicitResult(action="accept")
        else:
            return ElicitResult(action="decline")
    
    async with create_connected_server_and_client_session(
        mcp._mcp_server, elicitation_callback=mock_elicitation_callback
    ) as client_session:
        await client_session.initialize()
        
        result = await client_session.call_tool("test_url_tool", {})
        assert len(result.content) == 1
        assert result.content[0].text == "URL elicitation accepted"


@pytest.mark.anyio
async def test_elicitation_required_error():
    """Test ElicitationRequiredError functionality."""
    mcp = FastMCP(name="TestErrorServer")
    
    @mcp.tool(description="Test elicitation required error")
    async def test_error_tool(ctx: Context[ServerSession, None]) -> str:
        from mcp.types import ElicitRequestParams
        
        elicitation_params = ElicitRequestParams(
            mode="url",
            message="This tool requires authorization",
            elicitationId="error-test-123",
            url="https://auth.example.com/authorize",
        )
        
        raise ElicitationRequiredError([elicit_params])
    
    # Mock elicitation callback
    async def mock_elicitation_callback(context, params: ElicitRequestParams):
        return ElicitResult(action="accept")
    
    async with create_connected_server_and_client_session(
        mcp._mcp_server, elicitation_callback=mock_elicitation_callback
    ) as client_session:
        await client_session.initialize()
        
        # The tool should raise ElicitationRequiredError
        with pytest.raises(ElicitationRequiredError) as exc_info:
            await client_session.call_tool("test_error_tool", {})
        
        # Verify the error contains the elicitation
        assert len(exc_info.value.elicitations) == 1
        assert exc_info.value.elicitations[0].mode == "url"
        assert exc_info.value.elicitations[0].elicitationId == "error-test-123"


@pytest.mark.anyio
async def test_form_vs_url_elicitation():
    """Test that both form and URL elicitation modes work."""
    mcp = FastMCP(name="TestBothModesServer")
    
    from pydantic import BaseModel, Field
    
    class TestSchema(BaseModel):
        name: str = Field(description="Test name")
    
    @mcp.tool(description="Test both modes")
    async def test_both_modes(ctx: Context[ServerSession, None]) -> str:
        # Test form elicitation
        form_result = await ctx.elicit(
            message="Please provide your name",
            schema=TestSchema,
        )
        
        # Test URL elicitation
        url_result = await ctx.elicit_url(
            message="Please visit this URL",
            url="https://example.com/test",
            elicitationId="both-test-123",
        )
        
        return f"Form: {form_result.action}, URL: {url_result.action}"
    
    # Mock elicitation callback that handles both modes
    async def mock_elicitation_callback(context, params: ElicitRequestParams):
        return ElicitResult(action="accept", content={"name": "Test User"} if params.mode == "form" else None)
    
    async with create_connected_server_and_client_session(
        mcp._mcp_server, elicitation_callback=mock_elicitation_callback
    ) as client_session:
        await client_session.initialize()
        
        result = await client_session.call_tool("test_both_modes", {})
        assert len(result.content) == 1
        assert "Form: accept" in result.content[0].text
        assert "URL: accept" in result.content[0].text
