from datetime import timedelta
import json
from pathlib import Path
import sys
import tempfile
import unittest

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_stdio_tools_and_validation_without_browser(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / 'config.json'
            config.write_text(json.dumps({'jumpserver_url': 'http://127.0.0.1:9', 'display_selector': '#missing'}), encoding='utf-8')
            server = Path(__file__).resolve().parents[1] / 'mcp_server.py'
            params = StdioServerParameters(command=sys.executable, args=[str(server), '--config', str(config)])
            async with stdio_client(params) as streams:
                async with ClientSession(*streams, read_timeout_seconds=timedelta(seconds=30)) as client:
                    await client.initialize()
                    listed = await client.list_tools()
                    tools = {tool.name: tool for tool in listed.tools}
                    self.assertEqual(set(tools), {'create_field', 'create_record', 'create_ae'})
                    step = tools['create_ae'].inputSchema['$defs']['AEStep']['properties']
                    self.assertEqual(set(step['type']['enum']), {'SQL', 'PeopleCode'})
                    self.assertEqual(step['code']['type'], 'string')
                    invalid_name = await client.call_tool('create_field', {'name': 'BAD', 'long_name': 'x', 'short_name': 'x'})
                    self.assertTrue(invalid_name.isError)
                    invalid_type = await client.call_tool('create_ae', {'name': 'GM_TEST', 'steps': [{'type': 'Do Select', 'code': 'x'}]})
                    self.assertTrue(invalid_type.isError)
            self.assertFalse((Path(directory) / 'out').exists(), 'Invalid MCP parameters must not start automation')
