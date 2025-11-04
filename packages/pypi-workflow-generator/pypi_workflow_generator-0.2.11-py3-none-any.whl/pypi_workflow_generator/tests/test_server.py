"""
Tests for MCP server functionality.
"""

import os
import pytest
from pypi_workflow_generator.server import MCPServer

@pytest.mark.asyncio
async def test_list_tools():
    """Test that list_tools returns correct tool definitions."""
    server = MCPServer()
    result = await server.handle_list_tools()

    assert "tools" in result
    assert len(result["tools"]) == 4

    tool_names = [tool["name"] for tool in result["tools"]]
    assert "generate_workflow" in tool_names
    assert "initialize_project" in tool_names
    assert "create_release" in tool_names
    assert "generate_release_workflow" in tool_names

    # Verify each tool has required fields
    for tool in result["tools"]:
        assert "name" in tool
        assert "description" in tool
        assert "inputSchema" in tool
        assert "type" in tool["inputSchema"]
        assert "properties" in tool["inputSchema"]


@pytest.mark.asyncio
async def test_list_tools_schema_validation():
    """Test that tool schemas are properly defined."""
    server = MCPServer()
    result = await server.handle_list_tools()

    # Check generate_workflow schema
    gen_tool = next(t for t in result["tools"] if t["name"] == "generate_workflow")
    assert "python_version" in gen_tool["inputSchema"]["properties"]
    assert "output_filename" in gen_tool["inputSchema"]["properties"]
    assert "release_on_main_push" in gen_tool["inputSchema"]["properties"]
    assert gen_tool["inputSchema"]["required"] == []

    # Check initialize_project schema
    init_tool = next(t for t in result["tools"] if t["name"] == "initialize_project")
    assert "package_name" in init_tool["inputSchema"]["properties"]
    assert "author" in init_tool["inputSchema"]["properties"]
    assert "author_email" in init_tool["inputSchema"]["properties"]
    assert set(init_tool["inputSchema"]["required"]) == {
        "package_name", "author", "author_email", "description", "url", "command_name"
    }

    # Check create_release schema
    release_tool = next(t for t in result["tools"] if t["name"] == "create_release")
    assert "version" in release_tool["inputSchema"]["properties"]
    assert release_tool["inputSchema"]["required"] == ["version"]


@pytest.mark.asyncio
async def test_call_tool_generate_workflow(tmp_path):
    """Test calling generate_workflow tool via MCP."""
    server = MCPServer()

    # Change to temp directory
    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Create dummy project files (required for workflow generation)
        (tmp_path / "pyproject.toml").write_text("[build-system]\n")
        (tmp_path / "setup.py").write_text("from setuptools import setup\nsetup()")

        result = await server.handle_call_tool(
            "generate_workflow",
            {
                "python_version": "3.11",
                "output_filename": "test-workflow.yml"
            }
        )

        assert "content" in result
        assert len(result["content"]) > 0
        assert result["content"][0]["type"] == "text"
        assert "Successfully generated" in result["content"][0]["text"]
        assert result.get("isError") == False

        # Verify file was created
        workflow_path = tmp_path / ".github" / "workflows" / "test-workflow.yml"
        assert workflow_path.exists()

        # Verify content has correct Python version
        content = workflow_path.read_text()
        assert "3.11" in content

    finally:
        os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_call_tool_generate_workflow_with_options(tmp_path):
    """Test calling generate_workflow with custom options."""
    server = MCPServer()

    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Create dummy project files (required for workflow generation)
        (tmp_path / "pyproject.toml").write_text("[build-system]\n")
        (tmp_path / "setup.py").write_text("from setuptools import setup\nsetup()")

        result = await server.handle_call_tool(
            "generate_workflow",
            {
                "python_version": "3.10",
                "output_filename": "custom.yml",
                "release_on_main_push": True,
                "test_path": "tests/",
                "verbose_publish": True
            }
        )

        assert result.get("isError") == False
        assert "Successfully generated" in result["content"][0]["text"]

        workflow_path = tmp_path / ".github" / "workflows" / "custom.yml"
        assert workflow_path.exists()

        content = workflow_path.read_text()
        assert "3.10" in content
        assert "push:" in content  # Should have main push trigger

    finally:
        os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_call_tool_initialize_project(tmp_path):
    """Test calling initialize_project tool via MCP."""
    server = MCPServer()

    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        result = await server.handle_call_tool(
            "initialize_project",
            {
                "package_name": "test-package",
                "author": "Test Author",
                "author_email": "test@example.com",
                "description": "A test package",
                "url": "https://github.com/test/test-package",
                "command_name": "test-cmd"
            }
        )

        assert "content" in result
        assert result.get("isError") == False
        assert "Successfully initialized project" in result["content"][0]["text"]

        # Verify files were created
        assert (tmp_path / "pyproject.toml").exists()
        assert (tmp_path / "setup.py").exists()

        # Verify content
        setup_content = (tmp_path / "setup.py").read_text()
        assert "test-package" in setup_content
        assert "Test Author" in setup_content
        assert "test@example.com" in setup_content
        assert "test-cmd" in setup_content

    finally:
        os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_call_tool_initialize_project_missing_args():
    """Test that initialize_project fails with missing required arguments."""
    server = MCPServer()

    result = await server.handle_call_tool(
        "initialize_project",
        {
            "package_name": "test-package"
            # Missing other required fields
        }
    )

    # Should return an error
    assert result.get("isError") == True
    assert "content" in result


@pytest.mark.asyncio
async def test_call_tool_create_release():
    """Test calling create_release tool via MCP."""
    server = MCPServer()

    # Note: This will fail in a non-git repo, but we can test the call structure
    result = await server.handle_call_tool(
        "create_release",
        {
            "version": "v1.0.0"
        }
    )

    # Should have content (either success or error message)
    assert "content" in result
    assert "isError" in result


@pytest.mark.asyncio
async def test_call_tool_unknown():
    """Test calling unknown tool returns error."""
    server = MCPServer()

    result = await server.handle_call_tool("unknown_tool", {})

    assert result.get("isError") == True
    assert "Unknown tool" in result["content"][0]["text"]


@pytest.mark.asyncio
async def test_handle_request_list_tools():
    """Test handling a full JSON-RPC request for tools/list."""
    server = MCPServer()

    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }

    response = await server.handle_request(request)

    assert "tools" in response
    assert len(response["tools"]) == 4


@pytest.mark.asyncio
async def test_handle_request_call_tool():
    """Test handling a full JSON-RPC request for tools/call."""
    server = MCPServer()

    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "generate_workflow",
            "arguments": {
                "python_version": "3.11"
            }
        }
    }

    response = await server.handle_request(request)

    assert "content" in response


@pytest.mark.asyncio
async def test_handle_request_unknown_method():
    """Test handling unknown method returns error."""
    server = MCPServer()

    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "unknown/method",
        "params": {}
    }

    response = await server.handle_request(request)

    assert "error" in response
    assert response["error"]["code"] == -32601
    assert "Method not found" in response["error"]["message"]


def test_mcp_server_imports():
    """Test that MCP server can be imported successfully."""
    from pypi_workflow_generator.server import MCPServer, main

    assert MCPServer is not None
    assert main is not None
    assert callable(main)


@pytest.mark.asyncio
async def test_call_tool_generate_release_workflow(tmp_path):
    """Test calling generate_release_workflow tool via MCP."""
    server = MCPServer()

    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        result = await server.handle_call_tool(
            "generate_release_workflow",
            {}
        )

        assert "content" in result
        assert result.get("isError") == False
        assert "Successfully generated" in result["content"][0]["text"]

        workflow_path = tmp_path / ".github" / "workflows" / "create-release.yml"
        assert workflow_path.exists()

        content = workflow_path.read_text()
        assert "workflow_dispatch" in content
        assert "Create GitHub Release" in content

    finally:
        os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_call_tool_generate_release_workflow_custom_filename(tmp_path):
    """Test release workflow with custom filename via MCP."""
    server = MCPServer()

    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        result = await server.handle_call_tool(
            "generate_release_workflow",
            {"output_filename": "custom-release.yml"}
        )

        assert result.get("isError") == False

        workflow_path = tmp_path / ".github" / "workflows" / "custom-release.yml"
        assert workflow_path.exists()

    finally:
        os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_generate_workflow_includes_release_via_mcp(tmp_path):
    """Test that generate_workflow MCP tool creates both workflows by default."""
    server = MCPServer()

    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Create dummy project files
        (tmp_path / "pyproject.toml").write_text("[build-system]\n")
        (tmp_path / "setup.py").write_text("from setuptools import setup\nsetup()")

        result = await server.handle_call_tool(
            "generate_workflow",
            {"python_version": "3.11"}
        )

        assert result.get("isError") == False

        # Both workflows should exist
        assert (tmp_path / ".github" / "workflows" / "pypi-publish.yml").exists()
        assert (tmp_path / ".github" / "workflows" / "create-release.yml").exists()

    finally:
        os.chdir(original_cwd)
