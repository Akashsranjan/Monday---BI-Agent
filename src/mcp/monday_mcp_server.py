from mcp.server import Server
from mcp.types import TextContent

from src.clients.monday_client import MondayClient
from src.cleaning.cleaners import DataCleaner
from src.mcp.schemas import (
    BOARD_QUERY,
    MULTI_BOARD_QUERY,
    WORKSPACE_BOARDS_QUERY
)


client = MondayClient()
cleaner = DataCleaner()
server = Server("monday-mcp-server")


# ---------------------------------------------
# Fetch single board
# ---------------------------------------------
@server.tool(
    name="get_board_data",
    description="Fetch and clean one Monday.com board by board_id."
)
def get_board_data(board_id: str):
    result = client.run_query(
        BOARD_QUERY,
        {"board_id": int(board_id)}
    )

    items = result["data"]["boards"][0]["items"]
    df = cleaner.normalize(items)
    return TextContent(text=df.to_json(orient="records"))


# ---------------------------------------------
# Fetch multiple boards by ID
# ---------------------------------------------
@server.tool(
    name="get_multiple_boards",
    description="Fetch & merge data from multiple Monday.com boards."
)
def get_multiple_boards(board_ids: list):

    result = client.run_query(
        MULTI_BOARD_QUERY,
        {"board_ids": [int(x) for x in board_ids]}
    )

    boards = result["data"]["boards"]
    all_items = []

    for board in boards:
        all_items.extend(board["items"])

    df = cleaner.normalize(all_items)
    return TextContent(text=df.to_json(orient="records"))


# ---------------------------------------------
# Fetch data from multiple workspaces
# ---------------------------------------------
@server.tool(
    name="get_workspace_data",
    description="Fetch all boards and items inside one or more workspaces."
)
def get_workspace_data(workspace_ids: list):

    result = client.run_query(
        WORKSPACE_BOARDS_QUERY,
        {"workspace_ids": [int(x) for x in workspace_ids]}
    )

    boards = result["data"]["boards"]
    all_items = []

    for board in boards:
        all_items.extend(board["items"])

    df = cleaner.normalize(all_items)
    return TextContent(text=df.to_json(orient="records"))


# ---------------------------------------------
# Start the server
# ---------------------------------------------
if __name__ == "__main__":
    server.run()