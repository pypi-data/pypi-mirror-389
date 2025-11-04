import pytest

from sema4ai_docint.agent_server_client.transport.http import HTTPTransport
from sema4ai_docint.services.persistence.file import AgentServerChatFileAccessor


@pytest.mark.asyncio
class TestAgentServerFileAccessor:
    async def test_file_crud_operations(self, agent_server_cli, agent_id, thread_id):
        api_url = f"http://localhost:{agent_server_cli.get_http_port()}/api/v2/"
        transport = HTTPTransport(agent_id=agent_id, api_url=api_url)
        transport.connect()

        accessor = AgentServerChatFileAccessor(thread_id=thread_id, transport=transport)

        # List the files
        files = await accessor.list()
        assert len(files) == 0, "Expected no files in the thread"

        # Write a file
        await accessor.write_text("test_file.txt", b"Hello, world!")

        # List the files again
        files = await accessor.list()
        assert len(files) == 1, "Expected one file in the thread"
        assert files[0] == "test_file.txt", "Expected file to be named test_file.txt"

        # Read the file
        content = await accessor.read_text("test_file.txt")
        assert content == b"Hello, world!", "Expected file content to be 'Hello, world!'"
