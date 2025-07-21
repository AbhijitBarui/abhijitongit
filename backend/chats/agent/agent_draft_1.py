import os
import re
import json
import logging
from typing import Any, Dict, List

import requests
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_community.vectorstores import FAISS

# === Configuration ===
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
EXTERNAL_API_URL = os.getenv(
    "EXTERNAL_API_URL",
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
)
EXTERNAL_API_KEY = os.getenv("EXTERNAL_LLM_API_KEY")
MCP_BASE_URL = os.getenv("MCP_BASE_URL", "http://127.0.0.1:5000/mcp")

# === Logging ===
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# === Models & Vector DB Setup ===
embedding_model = OllamaEmbeddings(model="nomic-embed-text")
llm_local = OllamaLLM(model="llama3")
vector_db = FAISS.load_local("faiss_db", embedding_model, allow_dangerous_deserialization=True)

# === JSON-RPC Helper for MCP ===
def call_mcp(request_obj: Dict[str, Any]) -> Any:
    try:
        res = requests.post(MCP_BASE_URL, json=request_obj)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        logger.error(f"MCP request failed: {e}")
        return {"error": str(e)}


def initialize_mcp_session() -> None:
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "agent-pipeline", "version": "1.0.0"}
        }
    }
    call_mcp(init_req)

# === 1) Local Ollama Model Call ===
def prompt_ollama_model(prompt: str) -> str:
    payload = {"model": "mistral:latest", "prompt": prompt, "stream": False}
    try:
        res = requests.post(OLLAMA_URL, json=payload)
        res.raise_for_status()
        return res.json().get("response", "")
    except Exception as e:
        logger.error(f"Error calling Ollama: {e}")
        return ""

# === 2) External LLM Call (e.g., Gemini) ===
def prompt_external_model(prompt: str) -> str:
    if not EXTERNAL_API_KEY:
        logger.warning("No external API key set.")
        return ""
    headers = {"Content-Type": "application/json", "X-goog-api-key": EXTERNAL_API_KEY}
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(EXTERNAL_API_URL, headers=headers, json=body)
        res.raise_for_status()
        data = res.json()
        candidates = data.get("candidates", [])
        if candidates:
            return candidates[0].get("content", "")
    except Exception as e:
        logger.error(f"Error calling external LLM: {e}")
    return ""

# === 3) Intent Parsing ===
VALID_FLOWS = {"Simple greetings", "RAG Vector DB", "MCP DB Toolbox"}

def validate_intent_results(intent: Any) -> Dict[str, Any]:
    if not isinstance(intent, dict):
        return {"flow": "Simple greetings", "tool": "", "parameters": {}}
    flow = intent.get("flow")
    if flow not in VALID_FLOWS:
        return {"flow": "Simple greetings", "tool": "", "parameters": {}}
    params = intent.get("parameters") or {}
    if not isinstance(params, dict):
        params = {}
    return {"flow": flow, "tool": intent.get("tool", ""), "parameters": params}


def fetch_intent(user_prompt: str) -> Dict[str, Any]:
    classification_prompt = f"""
You are an intent classification assistant.

Available flows/tools:

1. Simple greetings: Respond to greetings like "hi" or "hello".
2. RAG Vector DB: Retrieve portfolio and project information.
3. MCP DB Toolbox: Query the Postgres database. Tools include:
   - list-tasks
   - get-tasks-by-user (requires email)
   - get-tasks-due-today (no parameters)
   - get-tasks-by-date (requires date)
   - create-task
   - update-task-status

User message:
"{user_prompt}"

Return EXACTLY JSON:

{{
  "flow": "flow-name",
  "tool": "tool-name or empty if N/A",
  "parameters": {{
    // extracted parameters
  }}
}}

If no match, return:
{{
  "flow": "Simple greetings",
  "tool": "",
  "parameters": {{}}
}}
"""
    raw = prompt_ollama_model(classification_prompt)
    if not raw.strip() and EXTERNAL_API_KEY:
        raw = prompt_external_model(classification_prompt)
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    try:
        intent = json.loads(match.group(0)) if match else {}
    except:
        intent = {}
    return validate_intent_results(intent)

# === 4) RAG Flow ===
def prompt_to_vector(user_prompt: str) -> List[float]:
    return embedding_model.embed_query(user_prompt)

def vector_matching(prompt_vector: List[float]) -> List[Any]:
    return vector_db.similarity_search_by_vector(prompt_vector, k=5)

def rag_path(user_prompt: str, intent_results: Dict[str, Any]) -> str:
    vec = prompt_to_vector(user_prompt)
    docs = vector_matching(vec)
    items = [f"{i+1}. {d.page_content}" for i, d in enumerate(docs)]
    list_str = "\n".join(items)
    return f"""
You are an AI assistant who provides information about your portfolio and past work.

Here are relevant projects retrieved from your portfolio database:
{list_str}

User's question:
"{user_prompt}"

Summarize these examples and answer the user's question in a concise, friendly way.
"""

# === 5) Simple Greetings Flow ===
def simple_reply_path(user_prompt: str, intent_results: Dict[str, Any]) -> str:
    return f"""
You are a friendly assistant.

The user said: "{user_prompt}"

Respond with a warm and welcoming greeting.
"""

# === 6) MCP DB Toolbox Flow ===
ALLOWED_TOOLS = {
    "list-tasks": [],
    "get-tasks-by-user": ["email"],
    "get-tasks-due-today": [],
    "get-tasks-by-date": ["date"],
    "create-task": ["title", "due_date"],
    "update-task-status": ["task_id", "status"],
}

def validate_requested_tool(intent: Dict[str, Any]) -> bool:
    return intent.get("tool") in ALLOWED_TOOLS

def validate_tool_parameters(intent: Dict[str, Any]) -> bool:
    req = ALLOWED_TOOLS.get(intent.get("tool"), [])
    return all(p in intent.get("parameters", {}) for p in req)

def mcp_tool_run(intent: Dict[str, Any]) -> Any:
    rpc = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": intent["tool"],
            "arguments": intent["parameters"],
            "_meta": {"progressToken": 1}
        }
    }
    return call_mcp(rpc)

def mcp_path(user_prompt: str, intent_results: Dict[str, Any]) -> str:
    initialize_mcp_session()
    if not validate_requested_tool(intent_results):
        return "Sorry, I can't perform that action."
    if not validate_tool_parameters(intent_results):
        return "Missing parameters for the requested operation."
    data = mcp_tool_run(intent_results)
    items: List[str] = []
    if isinstance(data, list):
        for item in data:
            title = item.get("title") or item.get("name") or json.dumps(item)
            items.append(f"- {title}")
    else:
        items.append(f"- {data}")
    header = "According to the database, here are the results"
    tool = intent_results["tool"]
    params = intent_results["parameters"]
    if tool == "get-tasks-due-today":
        header = "According to the database, here are tasks due today"
    elif tool == "get-tasks-by-date":
        header = f"According to the database, here are tasks due on {params.get('date')}"
    elif tool == "get-tasks-by-user":
        header = f"According to the database, here are tasks for {params.get('email')}"
    list_str = "\n".join(items)
    return f"""
You are an assistant helping the user manage their tasks.

{header}:
{list_str}

User's question:
"{user_prompt}"

Provide a clear summary for the user.
"""

# === 7) Flow Selector ===
def select_flow(user_prompt: str, intent_results: Dict[str, Any]) -> str:
    flow = intent_results.get("flow")
    if flow == "RAG Vector DB":
        return rag_path(user_prompt, intent_results)
    if flow == "MCP DB Toolbox":
        return mcp_path(user_prompt, intent_results)
    return simple_reply_path(user_prompt, intent_results)

# === 8) Validate & Generate Output ===
def validate_user_output(output: str) -> str:
    if not output or len(output.split()) < 3:
        return "(Generated response was too short; here's what I have:)\n" + output
    return output

def generate_output(output_llm_prompt: str) -> str:
    result = prompt_ollama_model(output_llm_prompt)
    if not result.strip() and EXTERNAL_API_KEY:
        result = prompt_external_model(output_llm_prompt)
    return validate_user_output(result)

# === 9) Main Handler ===
def handle_user_message(user_prompt: str) -> str:
    intent = fetch_intent(user_prompt)
    llm_prompt = select_flow(user_prompt, intent)
    return generate_output(llm_prompt)

# === Run as Script ===
if __name__ == "__main__":
    while True:
        user_in = input("You: ")
        if user_in.lower() in {"exit", "quit"}:
            break
        reply = handle_user_message(user_in)
        print(f"Bot: {reply}\n")
