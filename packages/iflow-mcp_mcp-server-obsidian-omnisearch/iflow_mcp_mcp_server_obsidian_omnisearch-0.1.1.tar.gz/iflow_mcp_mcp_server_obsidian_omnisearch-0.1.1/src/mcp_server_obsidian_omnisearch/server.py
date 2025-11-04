import asyncio
import sys
from urllib.parse import quote
import requests
import os
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from pydantic import BaseModel

class SearchArgs(BaseModel):
    query: str

class ReadNoteArgs(BaseModel):
    filepath: str

def serve(obsidian_vault_path: str):
    server = Server("obsidian-omnisearch")

    @server.list_tools()
    async def list_tools():
        return [
            Tool(
                name="obsidian_notes_search",
                description="Search Obsidian notes and return absolute paths to the matching notes. The returned paths can be used with the read_note tool to view the note contents.",
                inputSchema=SearchArgs.model_json_schema()
            ),
            Tool(
                name="read_note",
                description="Read and return the contents of an Obsidian note file.",
                inputSchema=ReadNoteArgs.model_json_schema()
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        if name == "obsidian_notes_search":
            args = SearchArgs(**arguments)
            try:
                search_url = "http://localhost:51361/search?q={query}"
                response = requests.get(search_url.format(query=quote(args.query)))
                response.raise_for_status()
                json_response = response.json()
                sorted_results = sorted(
                    json_response, key=lambda x: x["score"], reverse=True
                )
                results = [
                    f"<title>{item['basename']}</title>\n"
                    f"<excerpt>{item['excerpt']}</excerpt>\n"
                    f"<score>{item['score']}</score>\n"
                    f"<filepath>{os.path.join(obsidian_vault_path, item['path'].lstrip('/'))}</filepath>"
                    for item in sorted_results
                ]
                return [TextContent(type="text", text="\n\n".join(results))]
            except Exception:
                return [TextContent(type="text", text="No results found")]
        
        elif name == "read_note":
            args = ReadNoteArgs(**arguments)
            try:
                with open(args.filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                return [TextContent(type="text", text=content)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error reading file: {str(e)}")]
        
        else:
            raise ValueError(f"Unknown tool: {name}")

    return server

async def main():
    if len(sys.argv) != 2:
        print("Usage: mcp-server-obsidian-omnisearch <obsidian_vault_path>", file=sys.stderr)
        sys.exit(1)
    
    obsidian_vault_path = sys.argv[1]
    server = serve(obsidian_vault_path)
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

def main_sync():
    asyncio.run(main())

if __name__ == "__main__":
    main_sync()
