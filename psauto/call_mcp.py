"""Call this project's stdio MCP server with JSON arguments from a file."""

import argparse
import asyncio
from datetime import timedelta
import json
from pathlib import Path
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def call(tool, arguments, config):
    server = StdioServerParameters(command=sys.executable,
                                   args=[str(Path(__file__).with_name('mcp_server.py')), '--config', str(config)])
    async with stdio_client(server) as streams:
        async with ClientSession(*streams, read_timeout_seconds=timedelta(minutes=30)) as session:
            await session.initialize()
            if tool == 'list':
                return (await session.list_tools()).model_dump(mode='json')
            result = await session.call_tool(tool, arguments)
            if result.structuredContent is not None:
                return {'isError': result.isError, **result.structuredContent}
            for block in result.content:
                if block.type == 'text':
                    try:
                        return {'isError': result.isError, **json.loads(block.text)}
                    except (ValueError, TypeError):
                        return {'isError': result.isError, 'message': block.text}
            return {'isError': result.isError}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tool', choices=['list', 'create_field', 'create_record', 'create_ae', 'save_project'])
    parser.add_argument('--arguments', help='UTF-8 JSON file; code is never put in shell command text')
    parser.add_argument('--config', default=str(Path(__file__).with_name('config.json')))
    parser.add_argument('--result', help='Optional JSON result file')
    args = parser.parse_args()
    arguments = json.loads(Path(args.arguments).read_text(encoding='utf-8')) if args.arguments else {}
    result = asyncio.run(call(args.tool, arguments, Path(args.config).resolve()))
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.result:
        output = Path(args.result)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding='utf-8')
    print(rendered)
    return 0 if args.tool == 'list' or result.get('success') else 1


if __name__ == '__main__':
    raise SystemExit(main())
