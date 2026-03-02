import json
import re
import warnings
from typing import Any

import pandas as pd

from src.utils.logger import app_log

NULL_TOKENS = {"", " ", "null", "none", "n/a", "na", "nan", "-", "--", "tbd"}


class DataCleaner:

    def normalize(self, items: list) -> pd.DataFrame:
        if not items:
            app_log.warning("DataCleaner: empty items list")
            return pd.DataFrame()

        app_log.info(f"DataCleaner: normalizing {len(items)} items")

        rows = [self._flatten(item) for item in items]
        df   = pd.DataFrame(rows)

        for col in df.columns:
            df[col] = df[col].apply(self._clean_cell)

        # Drop columns that are entirely empty
        df = df.dropna(axis=1, how="all")

        app_log.info(f"DataCleaner: {df.shape[0]} rows x {df.shape[1]} cols")
        return df

    @staticmethod
    def _flatten(item: dict) -> dict:
        """
        Monday item → flat dict.
        Uses column_value title as key.
        """
        row: dict[str, Any] = {
            "_item_id": item.get("id"),
            "name":     item.get("name", ""),
        }
        for cv in item.get("column_values", []):
            title = (cv.get("title") or cv.get("id") or "col").strip()
            text  = cv.get("text", "")
            if not text:
                raw = cv.get("value")
                if raw:
                    try:
                        parsed = json.loads(raw)
                        text = (parsed.get("date") or parsed.get("text") or str(parsed)
                                if isinstance(parsed, dict) else str(parsed))
                    except Exception:
                        text = str(raw)
            row[title] = text
        return row

    @staticmethod
    def _clean_cell(val: Any) -> Any:
        if val is None:
            return None
        s = str(val).strip()
        if s.lower() in NULL_TOKENS:
            return None

        num = re.sub(r"[$€£,\s]", "", s)
        m = re.match(r"^([\d.]+)([KkMmBb])$", num)
        if m:
            return float(m.group(1)) * {"K": 1e3, "M": 1e6, "B": 1e9}[m.group(2).upper()]
        try:
            return float(num) if "." in num else int(num)
        except (ValueError, TypeError):
            pass
        # Date
        try:
            from dateutil import parser as dp
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                return dp.parse(s).strftime("%Y-%m-%d")
        except Exception:
            pass
        return s