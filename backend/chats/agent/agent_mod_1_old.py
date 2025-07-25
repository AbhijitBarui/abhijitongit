## IMPORTS
import os
import re
import json
import logging
import time
from functools import wraps
from typing import Any, Dict, Optional, List
import requests
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_community.vectorstores import FAISS
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

## CONFIGURATION
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
EXTERNAL_API_URL = os.getenv(
    "EXTERNAL_API_URL",
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
)
EXTERNAL_API_KEY = os.getenv("EXTERNAL_LLM_API_KEY")
MCP_BASE_URL = os.getenv("MCP_BASE_URL", "http://127.0.0.1:5000/mcp")

## LOGGING
# logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
# logger = logging.getLogger(__name__)

LOG_DIR = "logs"
LOG_FILE = "agent_logs.txt"
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("agent_timer")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(os.path.join(LOG_DIR, LOG_FILE))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(file_handler)

## MODELS VECTOR DB SETUP
embedding_model = OllamaEmbeddings(model="nomic-embed-text")
llm_local = OllamaLLM(model="llama3")
# Pre-build your FAISS index and store under `faiss_db`
vector_db = FAISS.load_local("faiss_db", embedding_model, allow_dangerous_deserialization=True)



## FUNCTIONS

# LOG DECORATOR

def timeit(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        result = fn(*args, **kwargs)
        elapsed = time.perf_counter() - t0
        logger.info(f"{fn.__name__} took {elapsed:.3f}s")
        return result
    return wrapper

# FIND USER INTENT

# use Ollama model and fetch results using crafted prompt 
@timeit
def prompt_ollama_model(prompt: str) -> str:
    payload = {"model": "mistral:latest", "prompt": prompt, "stream": False}
    try:
        res = requests.post(OLLAMA_URL, json=payload)
        res.raise_for_status()
        return res.json().get("response", "")
    except Exception as e:
        logger.error(f"Error calling Ollama: {e}")
        return ""

@timeit
# use API LLM and fetch results using crafted prompt
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

# validate intent results returned - structure wise:
VALID_FLOWS = {"Simple greetings", "RAG Vector DB", "MCP DB Toolbox"}

@timeit
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

@timeit
# fetch intent from LLM via prompt
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
    # raw = prompt_ollama_model(classification_prompt)
    # if not raw.strip() and EXTERNAL_API_KEY:
    #     raw = prompt_external_model(classification_prompt)
    raw = prompt_external_model(classification_prompt)
    if not isinstance(raw, str):
            raw = json.dumps(raw)
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    try:
        intent = json.loads(match.group(0)) if match else {}
    except:
        intent = {}
    
    logger.info(f"[INTENT] User: {user_prompt} → Intent: {intent}")
    return validate_intent_results(intent)



# VECTOR RAG PROCESSES

# prompt to vector embedding
@timeit
def prompt_to_vector(user_prompt: str) -> List[float]:
    return embedding_model.embed_query(user_prompt)

# vector matching in vector DB
@timeit
def vector_matching(prompt_vector: List[float]) -> List[Any]:
    return vector_db.similarity_search_by_vector(prompt_vector, k=5)

# follow the process of RAG implementation: 
# from Prompt vector conversion to packaging of 
# promptvector and matching vectors from vector db
@timeit
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



# SIMPLE REPLY PROCESS

# follow process of simple reply generation: 
# userprompt + simple generation intent result = Output LLM Prompt in return
@timeit
def simple_reply_path(user_prompt: str, intent_results: Dict[str, Any]) -> str:
    return f"""
You are a friendly assistant.

The user said: "{user_prompt}"

Respond with a warm and welcoming greeting.
"""



# MCP PROCESSES
ALLOWED_TOOLS = {
    "create-event": ["summary", "start_time", "end_time", "attendees"],
    "list-events": ["date"],
    "update-event": ["event_id", "summary", "start_time", "end_time"],
    "delete-event": ["event_id"],
}

# check if requested tool from Intent output exists or not
@timeit
def validate_requested_tool(intent: Dict[str, Any]) -> bool:
    return intent.get("tool") in ALLOWED_TOOLS

# check if we have all necessary parameters to run the requested tool or not
@timeit
def validate_tool_parameters(intent: Dict[str, Any]) -> bool:
    req = ALLOWED_TOOLS.get(intent.get("tool"), [])
    return all(p in intent.get("parameters", {}) for p in req)

@timeit
def call_mcp(request_obj: Dict[str, Any]) -> Any:
    try:
        res = requests.post(MCP_BASE_URL, json=request_obj)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        logger.error(f"MCP request failed: {e}")
        return {"error": str(e)}

@timeit
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

# run mcp tool and obtain results
@timeit
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

# from intent results, identify which tool to be used
# check if tool exists
# check if tool's required parameters are present or nah; if not, generate simple reply prompt saying ambiguous prompt
# ask MCP to run the tool with necessary parameters and return the data
# bundle up returned data with user prompt for Output LLM Prompt
@timeit
def mcp_path(user_prompt: str, intent_results: Dict[str, Any]) -> str:
    initialize_mcp_session()
    tool = intent_results["tool"]
    params = intent_results["parameters"]
    if not validate_requested_tool(intent_results):
        return "Sorry, I can't perform that action."
    if not validate_tool_parameters(intent_results):
        return "Missing parameters for the requested operation."
    data = mcp_tool_run(intent_results)
    # Calendar-specific formatting
    if tool == "create-event":
        event_id = data.get("id")
        return f"Scheduled event (ID: {event_id}) '{params.get('summary')}' from {params.get('start_time')} to {params.get('end_time')} with attendees {params.get('attendees')}"  
    if tool == "list-events":
        items = [f"- {evt.get('summary')} at {evt.get('start_time')}" for evt in (data or [])]
        list_str = "\n".join(items)
        return f"Here are your events on {params.get('date')}:\n{list_str}"
    if tool == "update-event":
        return f"Updated event ID {params.get('event_id')} successfully."
    if tool == "delete-event":
        return f"Deleted event ID {params.get('event_id')} successfully."
    return ""



# USE INTENT CHOOSE FLOW

# decide flow and get output llm prompt based on intent
@timeit
@timeit
def select_flow(user_prompt: str, intent_results: Dict[str, Any]) -> str:
    flow = intent_results.get("flow")
    if flow == "RAG Vector DB":
        prompt = rag_path(user_prompt, intent_results)
    elif flow == "MCP DB Toolbox":
        prompt = mcp_path(user_prompt, intent_results)
    else:
        prompt = simple_reply_path(user_prompt, intent_results)

    logger.info(f"[FLOW] Flow selected: {flow}\nGenerated LLM Prompt:\n{prompt.strip()}")
    return prompt



# VALIDATE AND SEND OUTPUT TO USER

# validate the output of user output LLM
@timeit
def validate_user_output(output: str) -> str:
    if not output or len(output.split()) < 3:
        return "(Generated response was too short; here's what I have:)\n" + output
    return output

# generate user output after flow generates output llm prompt
@timeit
def generate_output(output_llm_prompt: str) -> str:
    result = prompt_external_model(output_llm_prompt)
    # If we got back a dict (full JSON response), unwrap the text:
    if isinstance(result, dict):
        # Ollama/Gemini style: a list of parts with 'text'
        parts = result.get("parts")
        if isinstance(parts, list):
            # concatenate all the text chunks
            result = "".join(p.get("text", "") for p in parts)
        # fallback for other shapes:
        else:
            # maybe they nested under "response"
            resp = result.get("response")
            if isinstance(resp, str):
                result = resp
            elif isinstance(resp, dict) and "content" in resp:
                result = resp["content"]
            else:
                # last resort: stringify the whole thing
                result = json.dumps(result)
    logger.info(f"[OUTPUT] Final response to user:\n{result.strip()}")
    return validate_user_output(result)

# main fnc
@timeit
def handle_user_message(user_prompt: str) -> str:
    intent = fetch_intent(user_prompt)
    llm_prompt = select_flow(user_prompt, intent)
    reply = generate_output(llm_prompt)
    logger.info(f"[SUMMARY] User: {user_prompt}\nBot: {reply.strip()}")
    return reply

# 
if __name__ == "__main__":
    while True:
        user_in = input("You: ")
        if user_in.lower() in {"exit", "quit"}:
            break
        reply = handle_user_message(user_in)
        print(f"Bot: {reply}\n")