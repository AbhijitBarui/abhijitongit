
import openai
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv
import os
load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

response = client.chat.completions.create(
    model="moonshotai/kimi-k2-instruct",

    messages=[
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "Write a Python function to reverse a string."}
    ]
)

print(response.choices[0].message.content)
