## imports

## functions

# use Ollama model and fetch results using crafted prompt
def prompt_ollama_model(prompt):
    # hit ollama API
    # return obtained results
    pass

# use API LLM and fetch results using crafted prompt
def prompt_external_model(prompt):
    # hit external LLM API with api key e.g. gemini
#     e.g.:
#     curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent" \
#   -H 'Content-Type: application/json' \
#   -H 'X-goog-api-key: API_KEY_HERE' \
#   -X POST \
#   -d '{
#     "contents": [
#       {
#         "parts": [
#           {
#             "text": "Explain how AI works in a few words"
#           }
#         ]
#       }
#     ]
#   }'
    # return obtained results
    pass

# validate intent results returned - structure wise:
def validate_intent_results(intent_results):
    # check structure and type of return: check whether our logic can understand which path to follow, 
    # and if we are given a path, whether we have enough parameters to follow that path to the end
    # return actual value if okay, otherwise return a simple reply value which tells user their request was not clear enough
    pass

# fetch intent from LLM via prompt
def fetch_intent(user_prompt):
    # fetch data required for prompt
    # functions here

    # prepare prompt
    prompt = f'' # replace later

    # send prompt via ollama or external LLM and get intent results
    intent_results = prompt_external_model(prompt)
    intent_results = prompt_ollama_model(prompt)

    # validate intent results structure
    validated_intent_results = validate_intent_results(intent_results)

    # return the response 
    return validated_intent_results 

# prompt to vector embedding
def prompt_to_vector(user_prompt):
    pass

# vector matching in vector DB
def vector_matching(prompt_vector):
    pass

# follow the process of RAG implementation: 
# from Prompt vector conversion to packaging of 
# promptvector and matching vectors from vector db
def rag_path(user_prompt, intent_results):
    # convert prompt to vector
    prompt_vector = prompt_to_vector(user_prompt)
    # perform cosine match with this embedded vector in vector db and get matching vector converted datasets
    results = vector_matching(prompt_vector)
    # bundle up the matching datasets and prompt for Output LLM prompt
    output_llm_prompt = f'' # edit later
    return output_llm_prompt

# follow process of simple reply generation: 
# userprompt + simple generation intent result = Output LLM Prompt in return
def simple_reply_path(user_prompt, intent_results):
    output_llm_prompt = f'' # edit later
    return output_llm_prompt

# check if requested tool from Intent output exists or not
def validate_requested_tool(intent_results):
    pass

# check if we have all necessary parameters to run the requested tool or not
def validate_tool_parameters(intent_results):
    pass

# run mcp tool and obtain results
def mcp_tool_run(intent_results):
    # add logic here
    pass

# from intent results, identify which tool to be used
# check if tool exists
# check if tool's required parameters are present or nah; if not, generate simple reply prompt saying ambiguous prompt
# ask MCP to run the tool with necessary parameters and return the data
# bundle up returned data with user prompt for Output LLM Prompt
def mcp_path(user_prompt, intent_results):
    if validate_requested_tool(intent_results):
        if validate_tool_parameters(intent_results):
            mcp_data = mcp_tool_run(intent_results)

    output_llm_prompt = f'' # edit later
    return output_llm_prompt

# decide flow and get output llm prompt based on intent
def select_flow(user_prompt, intent_results):
    # llm returned intent results will be able to tell this fnc
    # which path to follow:
    output_llm_prompt = ''
    if intent_results == 1: # change later
        # path 1: RAG 
        output_llm_prompt = rag_path(user_prompt, intent_results)
    elif intent_results == 2: # change later
        # path 2: MCP
        output_llm_prompt = mcp_path(user_prompt, intent_results)
    elif intent_results == 3: # change later
        # path 3: Simple reply
        output_llm_prompt = simple_reply_path(user_prompt, intent_results)
    return output_llm_prompt

# validate the output of user output LLM
def validate_user_output(output_llm_results):
    # check if output is eligible for user output quality; if not send whatever we got for now, with a flag
    return output_llm_results

# generate user output after flow generates output llm prompt
def generate_output(output_llm_prompt):
    # send prompt via ollama or external LLM and get intent results
    output_llm_results = prompt_external_model(output_llm_prompt)
    output_llm_results = prompt_ollama_model(output_llm_prompt)

    # validate intent results structure
    validated_user_output = validate_user_output(output_llm_results)

    # return the response 
    return validated_user_output 
