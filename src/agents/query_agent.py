import json
import sys
import pandas as pd
from src.clients.monday_client import MondayClient
from src.cleaning.cleaners import DataCleaner
from src.config import settings
from src.utils.exceptions import CustomException
from src.utils.logger import agent_log, api_trace_log

try:
    from openai import OpenAI
    _llm_client = OpenAI(
        api_key=settings.GROQ_API_KEY,
        base_url=settings.GROQ_BASE_URL,
    ) if settings.GROQ_API_KEY else None
except ImportError:
    _llm_client = None
    agent_log.warning("openai package not installed ")


SYSTEM_PROMPT = """You are a Business Intelligence assistant for a founder/executive.
You have access to live Monday.com board data.

Your job:
- Answer the user's question using ONLY the data provided.
- If values are missing or null, mention it clearly (e.g. "12 records have no deal value").
- Give a concise, executive-level answer with key numbers.
- Format currency as $XM or $XK. Use bullet points.
- If the data doesn't contain enough to answer, say so and suggest what's missing.
- For follow-up questions, use the conversation history.
"""


class QueryAgent:

    def __init__(self):
        try:
            self.monday  = MondayClient()
            self.cleaner = DataCleaner()
            self.history: list[dict] = []
            self.trace:   list[dict] = []

            self.work_orders_board = settings.WORK_ORDERS_BOARD_ID
            self.deals_board       = settings.DEALS_BOARD_ID

            agent_log.info(f"QueryAgent initialized — Groq model: {settings.GROQ_MODEL}")

        except Exception as e:
            raise CustomException("Failed initializing QueryAgent", sys) from e

    # ── Fetch one board (live, no cache) ──────────────────────────────────────

    def _fetch_board(self, board_id: str, label: str) -> pd.DataFrame:
        try:
            api_trace_log.info(f"[TRACE] Fetching {label} (board {board_id})")
            self.trace.append({
                "step":    f"Fetch {label}",
                "board_id": board_id,
                "status":  "started",
            })

            items = self.monday.get_board_items(board_id)
            df    = self.cleaner.normalize(items)

            null_count = int(df.isna().sum().sum())
            self.trace[-1].update({
                "status":     "done",
                "rows":       len(df),
                "columns":    list(df.columns),
                "null_cells": null_count,
            })

            agent_log.info(
                f"[TRACE] {label}: {len(df)} rows, {len(df.columns)} columns, "
                f"{null_count} null cells"
            )
            return df

        except Exception as e:
            self.trace[-1]["status"] = "error"
            raise CustomException(f"Error fetching {label}", sys) from e

    # ── Ask the LLM ───────────────────────────────────────────────────────────

    def _ask_llm(self, query: str, data: dict) -> str:
        if not _llm_client:
            return "Groq is not configured."

        context = {}
        for label, df in data.items():
            # 1. DROP JUNK: Drop columns that are 100% empty
            df = df.dropna(axis=1, how='all')
        
            cols_to_keep = [c for c in df.columns if not (
                c.startswith('_') or 
                'id' in c.lower() or 
                'hash' in c.lower() or 
                'pulse' in c.lower()
            )]
            df_filtered = df[cols_to_keep]

            total_rows = len(df_filtered)
            
            sample_size = min(total_rows, 15) 
            records_sample = df_filtered.head(sample_size).to_dict(orient="records")
            
            # 4. COMPRESS JSON: Remove nulls and convert to string
            clean_sample = [
                {k: v for k, v in r.items() if v is not None}
                for r in records_sample
            ]

            context[label] = {
                "board_summary": {
                    "total_records_live": total_rows,
                    "columns": list(df_filtered.columns),
                    "note": "The sample below is only the first 15 records."
                },
                "data_preview": clean_sample
            }

        # Construct messages with reduced history to save tokens
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for turn in self.history[-2:]: # Only last 2 messages for safety
            messages.append(turn)

        messages.append({
            "role": "user",
            "content": f"Query: {query}\n\nLive Data Context:\n{json.dumps(context, default=str)}"
        })

        try:
            self.trace.append({"step": f"Groq LLM ({settings.GROQ_MODEL})", "status": "started"})
            
            response = _llm_client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=messages,
                temperature=0.1, 
            )
            answer = response.choices[0].message.content
            self.trace[-1]["status"] = "done"
            return answer

        except Exception as e:
            # Fallback if still too large
            if "rate_limit_exceeded" in str(e).lower():
                return "The dataset is too large for the current AI tier. Please try a more specific question."
            raise CustomException("LLM call failed", sys) from e


    # ── Main entry point ──────────────────────────────────────────────────────

    def answer(self, query: str) -> dict:
        """
        Process one question. Live data fetch every time — no caching.
        Returns: {answer, trace, sources}
        """
        self.trace = []   

        try:
            agent_log.info(f"Query: {query[:80]}")

            data = {
                "work_orders": self._fetch_board(self.work_orders_board, "Work Orders"),
                "deals":       self._fetch_board(self.deals_board,       "Deals"),
            }

            answer = self._ask_llm(query, data)

            # Store for follow-up context
            self.history.append({"role": "user",      "content": query})
            self.history.append({"role": "assistant",  "content": answer})

            api_trace_log.info("Query processed successfully")

            return {
                "answer":  answer,
                "trace":   self.trace,
                "sources": ["Work Orders Board", "Deals Board"],
            }

        except Exception as e:
            raise CustomException("QueryAgent failed to answer", sys) from e

    def reset(self):
        self.history = []
        self.trace   = []