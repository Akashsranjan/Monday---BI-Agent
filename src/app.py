import uuid
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request

from src.agents.query_agent import QueryAgent
from src.config import settings
from src.utils.logger import app_log

app = Flask(
    __name__,
    template_folder="Frontend/templates",
    static_folder="Frontend/static",
)

_sessions: dict[str, QueryAgent] = {}
MAX_SESSIONS = 50


def _get_agent(session_id: str) -> QueryAgent:
    """Fetch or create an agent tied to a browser session."""
    if session_id not in _sessions:
        if len(_sessions) >= MAX_SESSIONS:
            del _sessions[next(iter(_sessions))]
        _sessions[session_id] = QueryAgent()
        app_log.info(f"[Session] New session created: {session_id[:8]}")
    return _sessions[session_id]


@app.get("/")
def index():
    return render_template("index.html")



@app.post("/api/query")
def query():
    body       = request.get_json(force=True, silent=True) or {}
    message    = (body.get("message") or "").strip()
    session_id = body.get("session_id") or str(uuid.uuid4())

    if not message:
        return jsonify({"error": "message is required"}), 400

    agent = _get_agent(session_id)

    try:
        # answer() is synchronous — no asyncio.run() needed
        result = agent.answer(message)

        return jsonify({
            "session_id":   session_id,
            "answer":       result["answer"],
            "trace":        result["trace"],
            "data_quality": result.get("data_quality"),
            "sources":      result.get("sources", []),
            "timestamp":    datetime.now(timezone.utc).isoformat(),
        })

    except Exception as e:
        app_log.exception("Agent failed to answer query")
        return jsonify({"error": "Agent failed", "details": str(e)}), 500



if __name__ == "__main__":
    app_log.info(f"Starting BI Agent on port {settings.PORT}")
    app.run(host="0.0.0.0", port=settings.PORT, debug=settings.DEBUG)
