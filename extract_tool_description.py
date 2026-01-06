import asyncio
from mcp import ClientSession, StdioServerParameters
import json
from mcp.client.stdio import stdio_client

async def run_and_extract_tool_doc(command, args=None, env=None, save_path='tool_description.json'):
    server_params = StdioServerParameters(
        command=command,
        args=args,
        env=env
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            response = await session.list_tools()
            print(response)
            tool_json = {'numTool': len(response.tools), 'tools': [ {'function_name': t.name, 'description': t.description, 'input_schema': t.inputSchema} for t in response.tools]}
            with open(save_path, 'w') as f:
                json.dump(tool_json, f)
    await asyncio.sleep(2) 

def main():
    config = None
    with open('claude_desktop_config.json', 'r') as f:
        config = json.load(f)
    for name, c in config['mcpServers'].items():
        print(name)
        command = c.get('command', None)
        args = c.get('args', [])
        env = c.get('env', None)
        print(f'----------extracting tool docs from {name}------------')
        asyncio.run(run_and_extract_tool_doc(command, args, env, f'tool_docs/{name}.json'))


if __name__ == "__main__":
    main()