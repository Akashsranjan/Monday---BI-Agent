# Fetch a single board by ID with paginated items
BOARD_QUERY = """
query ($board_id: [ID!], $cursor: String) {
  boards(ids: $board_id) {
    id
    name
    workspace {
      id
      name
    }
    items_page(limit: 200, cursor: $cursor) {
      cursor
      items {
        id
        name
        column_values {
          id
          text
          value
          type
        }
      }
    }
  }
}
"""

# Fetch multiple boards by IDs
MULTI_BOARD_QUERY = """
query ($board_ids: [ID!], $cursor: String) {
  boards(ids: $board_ids) {
    id
    name
    workspace {
      id
      name
    }
    items_page(limit: 200, cursor: $cursor) {
      cursor
      items {
        id
        name
        column_values {
          id
          text
          value
          type
        }
      }
    }
  }
}
"""

# Fetch all boards inside one or more workspaces
WORKSPACE_BOARDS_QUERY = """
query ($workspace_ids: [ID!]) {
  boards(workspace_ids: $workspace_ids, limit: 50) {
    id
    name
    workspace {
      id
      name
    }
    items_page(limit: 200) {
      cursor
      items {
        id
        name
        column_values {
          id
          text
          value
          type
        }
      }
    }
  }
}
"""

# Lightweight board list query (no items)
LIST_BOARDS_QUERY = """
query {
  boards(limit: 50, order_by: created_at) {
    id
    name
    workspace {
      id
      name
    }
    board_kind
    state
    updated_at
  }
}
"""

# Search items by column value
SEARCH_ITEMS_QUERY = """
query ($board_id: [ID!], $column_id: String!, $column_value: String!) {
  items_by_column_values(
    board_id: $board_id,
    column_id: $column_id,
    column_value: $column_value
  ) {
    id
    name
    board {
      id
      name
    }
    column_values {
      id
      text
      value
      type
    }
  }
}
"""