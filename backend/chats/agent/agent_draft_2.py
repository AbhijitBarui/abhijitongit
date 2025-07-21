import os
import re
import json
import logging
from typing import Any, Dict, Optional, List

import requests
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_community.vectorstores import FAISS

from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# === Configuration ===
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
EXTERNAL_API_URL = os.getenv("EXTERNAL_API_URL", "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent")
EXTERNAL_API_KEY = os.getenv("EXTERNAL_LLM_API_KEY")
MCP_BASE_URL = os.getenv("MCP_BASE_URL", "http://127.0.0.1:5000/mcp")

# === Logging ===
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# === Models & Vector DB Setup ===
embedding_model = OllamaEmbeddings(model="nomic-embed-text")
llm_local = OllamaLLM(model="llama3")
# Pre-build your FAISS index and store under `faiss_db`
vector_db = FAISS.load_local("faiss_db", embedding_model, allow_dangerous_deserialization=True)

# === 1) Local Ollama Model Call ===
def prompt_ollama_model(prompt: str) -> str:
    payload = {"model": "mistral:latest", "prompt": prompt, "stream": False}
    try:
        res = requests.post(OLLAMA_URL, json=payload)
        res.raise_for_status()
        data = res.json()
        return data.get("response", "")
    except Exception as e:
        logger.error(f"Error calling Ollama: {e}")
        return ""

# === 2) External LLM Call (e.g., Gemini) ===
def prompt_external_model(prompt: str) -> str:
    if not EXTERNAL_API_KEY:
        logger.warning("No external API key set, skipping external model call.")
        return ""
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": EXTERNAL_API_KEY
    }
    body = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        res = requests.post(EXTERNAL_API_URL, headers=headers, json=body)
        res.raise_for_status()
        data = res.json()
        # adjust based on actual Gemini response shape
        candidates = data.get("candidates", [])
        if candidates:
            return candidates[0].get("content", "")
        return ""
    except Exception as e:
        logger.error(f"Error calling external LLM: {e}")
        return ""

# === 3) Validate Intent Structure ===
VALID_FLOWS = {"mcp", "rag", "simple"}

def validate_intent_results(intent: Any) -> Dict[str, Any]:
    if not isinstance(intent, dict):
        return {"flow": "simple", "message": "Sorry, I didn't understand your request."}
    flow = intent.get("flow")
    if flow not in VALID_FLOWS:
        return {"flow": "simple", "message": "Sorry, I couldn't classify your request."}
    return intent

# === 4) Fetch Intent from LLM ===
def fetch_intent(user_prompt: str) -> Dict[str, Any]:
    # Craft a prompt for intent parsing
    parser_prompt = f"""
You are an intent parser. Given a user message, return JSON with keys:
- flow: one of 'mcp', 'rag', or 'simple'
- tool: (if flow=='mcp') name of MCP tool to invoke
- args: (if flow=='mcp') arguments object for the tool
Example output: {{"flow":"mcp","tool":"get-tasks-by-user","args":{{"email":"user@example.com"}}}}
User message: {user_prompt}
"""
    # Try local first, then external if available
    raw = prompt_ollama_model(parser_prompt)
    if not raw.strip() and EXTERNAL_API_KEY:
        raw = prompt_external_model(parser_prompt)
    try:
        intent = json.loads(re.search(r"\{.*\}", raw, re.DOTALL).group(0))
    except Exception:
        intent = {"flow": "simple", "message": "Sorry, I couldn't parse your intent."}
    return validate_intent_results(intent)

# === 5) RAG Path ===
def prompt_to_vector(user_prompt: str) -> List[float]:
    return embedding_model.embed_query(user_prompt)

def vector_matching(prompt_vector: List[float]) -> List[Any]:
    return vector_db.similarity_search_by_vector(prompt_vector, k=5)

def rag_path(user_prompt: str, intent_results: Dict[str, Any]) -> str:
    vec = prompt_to_vector(user_prompt)
    docs = vector_matching(vec)
    context = "\n---\n".join([d.page_content for d in docs])
    return f"Here is some context from relevant documents:\n{context}\n\nAnswer the user: {user_prompt}" 

# === 6) Simple Reply Path ===
def simple_reply_path(user_prompt: str, intent_results: Dict[str, Any]) -> str:
    return user_prompt  # echo back to LLM for direct answer

# === 7) MCP Tool Invocation ===
ALLOWED_TOOLS = {"create-task": ["title", "due_date"],
                 "update-task-status": ["task_id", "status"],
                 "get-tasks-by-user": ["email"],
                 # add your tool definitions here
                }

def validate_requested_tool(intent: Dict[str, Any]) -> bool:
    tool = intent.get("tool")
    return tool in ALLOWED_TOOLS

def validate_tool_parameters(intent: Dict[str, Any]) -> bool:
    tool = intent.get("tool")
    args = intent.get("args", {}) or {}
    required = ALLOWED_TOOLS.get(tool, [])
    return all(param in args for param in required)

def mcp_tool_run(intent: Dict[str, Any]) -> Any:
    tool = intent.get("tool")
    args = intent.get("args", {})
    try:
        res = requests.post(
            f"{MCP_BASE_URL}/tools/{tool}/invoke",
            json={"args": args},
            timeout=10
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        logger.error(f"MCP tool error: {e}")
        return {"error": str(e)}

def mcp_path(user_prompt: str, intent_results: Dict[str, Any]) -> str:
    if not validate_requested_tool(intent_results):
        return "Sorry, I can't perform that action."
    if not validate_tool_parameters(intent_results):
        return "Missing parameters for the requested operation."
    data = mcp_tool_run(intent_results)
    return f"Tool '{intent_results['tool']}' returned:\n{json.dumps(data, indent=2)}\nPlease explain this to the user."

# === 8) Flow Selector ===
def select_flow(user_prompt: str, intent_results: Dict[str, Any]) -> str:
    flow = intent_results.get("flow")
    if flow == "rag":
        return rag_path(user_prompt, intent_results)
    elif flow == "mcp":
        return mcp_path(user_prompt, intent_results)
    else:
        return simple_reply_path(user_prompt, intent_results)

# === 9) Validate Output ===
def validate_user_output(output: str) -> str:
    if not output or len(output) < 3:
        return "(Generated response was too short; here's what I have:)\n" + output
    return output

# === 10) Generate Final Output ===
def generate_output(output_llm_prompt: str) -> str:
    # Prefer local LLM, fallback to external
    result = prompt_ollama_model(output_llm_prompt)
    if not result.strip() and EXTERNAL_API_KEY:
        result = prompt_external_model(output_llm_prompt)
    return validate_user_output(result)

# === 11) Main Handler ===
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
