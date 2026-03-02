# Agentic BI: AI Insights for Monday.com

An intelligent Business Intelligence (BI) assistant that connects directly to **Monday.com** boards to provide live, executive-level analytics. Built with **Llama 3.3-70B** via Groq, it translates natural language questions into data-driven insights.

## Key Features

* **🔌 MCP Integration:** Built on the **Model Context Protocol**, exposing Monday.com data as standardized tools for LLMs.
* **Live Monday.com Integration:** Real-time fetching of items across multiple boards (Work Orders & Deals) using GraphQL.
* **Context Compression Engine:** An optimized pipeline that handles large datasets (hundreds of rows) within the strict **12,000 TPM** limits of the Groq Free Tier.
* **Data Resilience:** Automatically cleans and normalizes raw responses into structured DataFrames, handling 800+ null cells and complex currency types.
* **Traceability:** Visible "Action Trace" for every query, showing the raw data stats and LLM steps.

---

## Technical Architecture

1. **MCP Server:** Implements standardized tools (`get_board_data`, `get_workspace_data`) for structured data retrieval.
2. **Monday Client:** A custom GraphQL client with **pagination (cursors)** to ensure 100% of board data is fetched.
3. **Data Cleaner:** Uses `pandas` to flatten nested JSON and perform type-casting (Currency, Dates, Numbers).
4. **Query Agent:** The "Brain" that coordinates fetching, data sampling, and LLM communication.
5. **Backend:** Flask (Python) handles session-based agents and API routing to the frontend.

### Solving the "413: Request Too Large" Challenge

Standard LLMs struggle with large tables. To solve the token limit, this agent uses **Context Compression**:

* **Metadata Summary:** It calculates total row counts and data gaps locally.
* **Column Pruning:** Technical IDs and internal hashes are stripped to save tokens.
* **Smart Sampling:** Only a representative sample of records is sent, while the LLM is provided with **total aggregates** to maintain BI accuracy.

---

## Source Code Structure

```text
.
├── src/                        # Core Logic
│   ├── agents/                 # LLM Orchestration
│   ├── cleaning/               # Data Normalization
│   ├── clients/                # Monday.com API Client
│   ├── mcp/                    # MCP Server & Tool Definitions
│   └── utils/                  # Loggers & Exceptions
├── Frontend/                   # UI Assets (HTML/CSS/JS)
├── app.py                      # Flask Entry Point
├── .env.example                # Template for environment variables
├── readme.md                   # Project Documentation
└── requirements.txt            # Dependencies

```

---

## Setup & Installation

### 1. Prerequisites

* Python 3.9+
* Monday.com API Key
* Groq API Key

### 2. Environment Configuration

Create a `.env` file in the root directory (use `.env.example` as a template):

```env
MONDAY_API_KEY=your_key
GROQ_API_KEY=your_key
WORK_ORDERS_BOARD_ID=5026914816
DEALS_BOARD_ID=5026914653

```

### 3. Installation

```bash
pip install -r requirements.txt
python app.py

```

---

## Testing Queries

1. "List all deals in the Mining sector."
2. "How many work orders are currently marked as 'Completed'?"
3. "What is the total revenue currently in the Deals board?"

---

## Decision Log (Quick Summary)

* **Standardization:** Implemented **MCP** to ensure tool portability and structured LLM tool-calling.
* **Performance:** Used `requests.Session()` to reduce API latency by ~20% via TCP reuse.
* **Integrity:** Implemented a regex-based cleaning pipeline to convert "Null Tokens" (TBD, -, None) into standard formats, preventing LLM hallucinations.
