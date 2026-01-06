import os
import httpx
from openai import OpenAI
import os
import re
import json
import anthropic
import subprocess
from pathlib import Path


GENERATED_PROMPT_TXT = 'generate_trigger_prompts.txt'
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"

def capture_json_objects(text):
    stack = []
    result = []
    start_indices = []
    
    for i, c in enumerate(text):
        if c == '{':
            if not stack:
                # Record the position of the outermost '{'
                start_indices.append(i)
            stack.append(i)
        elif c == '}':
            if stack:
                stack.pop()
                if not stack and start_indices:
                    # Matched one maximum outermost '{}'
                    start = start_indices.pop()
                    result.append(text[start:i+1])
    try:
        data = json.loads(result[0])
    except json.JSONDecodeError as e:
        print("ERROR: JSON parsing failed:", e)
    return data



def extract_json(response):
    match = re.search(r"{.*?}", response, re.DOTALL)
    data = None
    if match:
        json_str = match.group(0)
        print(json_str)
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            print("ERROR: JSON parsing failed:", e)
    else:
        print("ERROR: No JSON object content found")
    return data

def GenerateTriggerwithGPT(tool, model):
    trigger_path = f'tool_triggers/{tool}_triggers.json'
    pre_trigger_path = f'tool_triggers/{tool}_pre_triggers.json'

    if os.path.exists(trigger_path):
        print('already generated trigger prompts')
        return
    # Create a custom HTTP client
    http_client = httpx.Client()

    # Create OpenAI client instance with the custom HTTP client
    api_key = os.environ.get(OPENAI_API_KEY_ENV)
    if not api_key:
        raise RuntimeError(f"{OPENAI_API_KEY_ENV} is not set")
    client = OpenAI(api_key=api_key, http_client=http_client)

    with open(f'tool_docs/{tool}.json', 'r') as f:
        toolDocs = f.read()

    with open('generate_trigger_prompts.txt', 'r') as f:
        GENERATED_PROMPT_TXT = f.read()

    prompt = GENERATED_PROMPT_TXT.replace('[$Tool_Docs$]', toolDocs)

    # print(prompt)

    # Send request
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=8000,
        timeout=60
    )

    response = response.choices[0].message.content

    with open('test_response.txt', 'w') as f:
        print('test .....')
        f.write(response)

    data = capture_json_objects(response)
    print(data)
    if data is not None:
        with open(trigger_path, 'w') as f:
            json.dump(data['trigger_prompts'], f)
        with open(pre_trigger_path, 'w') as f:
            json.dump(data['prerequisite_prompts'], f)


if __name__ == '__main__':
    # GenerateTriggerwithGPT("sqlite", "gpt-4.1")
    root_dir = 'tool_docs'
    tools = []
    for t in os.listdir(root_dir):
        if t.endswith('.json'):
            t = t[:-5]
            tools.append(t)
    for t in tools:
        print(f'------generate trigger prompts for {t}-------')
        GenerateTriggerwithGPT(t, "gpt-4.1")
