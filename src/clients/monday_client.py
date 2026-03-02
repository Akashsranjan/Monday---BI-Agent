import sys
import time
import uuid

import requests

from src.config import settings
from src.utils.logger import api_trace_log, app_log
from src.utils.exceptions import CustomException


class MondayClient:

    def __init__(self):
        try:
            self.api_key = settings.MONDAY_API_KEY
            self.url     = settings.MONDAY_API_URL

            if not self.api_key:
                raise CustomException("Missing MONDAY_API_KEY in environment", sys)

            # Session reuses TCP connection — faster than reconnecting each call
            self._session = requests.Session()
            self._session.headers.update({
                "Authorization": self.api_key,
                "Content-Type":  "application/json",
                "API-Version":   "2024-01",
            })
            app_log.info("MondayClient initialized")

        except Exception as e:
            raise CustomException("Failed to initialize MondayClient", sys) from e

    def run_query(self, query: str, variables: dict = None) -> dict:
        """Execute one GraphQL query. Returns the full response dict."""
        call_id   = str(uuid.uuid4())[:8]
        variables = variables or {}

        api_trace_log.info(f"[{call_id}] Executing Monday API query")
        api_trace_log.debug(f"[{call_id}] variables={variables}")

        t0 = time.time()
        try:
            response = self._session.post(
                self.url,
                json={"query": query, "variables": variables},
                timeout=30,
            )
            ms = round((time.time() - t0) * 1000, 1)
            api_trace_log.info(f"[{call_id}] HTTP {response.status_code} in {ms}ms")

            if response.status_code != 200:
                raise CustomException(
                    f"Non-200 status code: {response.text[:300]}", sys
                )

            json_data = response.json()
            api_trace_log.debug(f"[{call_id}] Response: {str(json_data)[:200]}")

            if "errors" in json_data:
                raise CustomException(
                    f"GraphQL errors: {json_data['errors']}", sys
                )

            return json_data

        except CustomException:
            raise
        except Exception as e:
            raise CustomException("Monday API query execution failed", sys) from e

    def paginate_board(self, board_id: str) -> list:
        """
        Fetch ALL items from a board by following cursor pages.
        Monday returns max 200 items per page — this loops until done.
        Returns a flat list of raw item dicts.
        """
        from src.mcp.schemas import BOARD_QUERY

        all_items = []
        cursor    = None
        page      = 1

        while True:
            # board_id MUST be a list of strings — GraphQL type is [ID!]!
            variables = {"board_id": [str(board_id)]}
            if cursor:
                variables["cursor"] = cursor

            api_trace_log.info(f"Board {board_id} — fetching page {page}")

            try:
                data = self.run_query(BOARD_QUERY, variables)
            except Exception as e:
                raise CustomException(
                    f"Failed fetching board {board_id} page {page}", sys
                ) from e

            boards = data.get("data", {}).get("boards", [])
            if not boards:
                break

            # items are nested inside items_page — NOT directly on boards[0]
            page_data = boards[0].get("items_page", {})
            items     = page_data.get("items", [])
            all_items.extend(items)

            api_trace_log.info(
                f"Board {board_id} page {page}: "
                f"{len(items)} items (total: {len(all_items)})"
            )

            cursor = page_data.get("cursor")
            if not cursor:
                break
            page += 1

        app_log.info(f"Board {board_id}: {len(all_items)} total items fetched")
        return all_items

    def get_board_items(self, board_id) -> list:
        """Alias for paginate_board — kept for compatibility with query_agent."""
        try:
            return self.paginate_board(str(board_id))
        except Exception as e:
            raise CustomException(
                f"Failed to fetch board {board_id}", sys
            ) from e