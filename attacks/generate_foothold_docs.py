import os
import httpx
from openai import OpenAI
import os
import re
import json
import anthropic
import subprocess
from pathlib import Path


GENERATED_PROMPT_TXT = 'generate_func_comments_prompt3.txt'
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"

def GenerateFuncDocwithGPT(model):
    if os.path.exists(f'func_doc_{model}.json'):
        print('already generated func docs')
        return
    # Create a custom HTTP client
    http_client = httpx.Client()

    # Create OpenAI client instance with the custom HTTP client
    api_key = os.environ.get(OPENAI_API_KEY_ENV)
    if not api_key:
        raise RuntimeError(f"{OPENAI_API_KEY_ENV} is not set")
    client = OpenAI(api_key=api_key, http_client=http_client)

    with open(GENERATED_PROMPT_TXT, 'r') as f:
        prompt = f.read()

    # Send request
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful coding assistant. You will be asked to write Python-style function docstrings."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1000,
        timeout=60
    )

    response = response.choices[0].message.content

    # with open('func-comments-gpt-4o-response.txt', 'r') as f:
    #     response = f.read()
    match = re.search(r"\[\s*{.*?}\s*\]", response, re.DOTALL)
    data = None
    if match:
        json_str = match.group(0)
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            print("ERROR: JSON parsing failure:", e)
    else:
        print("ERROR: JSON array not found")

    with open(f'func_doc_{model}.json', 'w') as f:
        json.dump(data, f)


def GenerateFuncDocwithClaude(model):
    if os.path.exists(f'func_doc_{model}.json'):
        print('already generated func docs')
        return
    # Create a custom HTTP client
    http_client = httpx.Client()

    # Create Claude client instance with the custom HTTP client
    api_key = os.environ.get(ANTHROPIC_API_KEY_ENV)
    if not api_key:
        raise RuntimeError(f"{ANTHROPIC_API_KEY_ENV} is not set")
    client = anthropic.Anthropic(api_key=api_key, http_client=http_client)

    with open(GENERATED_PROMPT_TXT, 'r') as f:
        prompt = f.read()

    # Send request
    response = client.messages.create(
        model=model,
        messages=[
        {"role": "user", "content": "You are a helpful coding assistant. You will be asked to write Python-style function docstrings."},
        {"role": "user", "content": prompt}
    ],
        temperature=0.7,
        max_tokens=2048,
        timeout=60
    )

    response = response.content[0].text
    # print(response)
    match = re.search(r"\[\s*\{.*?\}\s*\]", response, re.DOTALL)
    data = None
    if match:
        json_str = match.group(0)
        print('----------------------')
        print(json_str)
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            print("ERROR:", e)
    else:
        print("ERROR")

    with open(f'func_doc_{model}.json', 'w') as f:
        json.dump(data, f)

def run(cmd, cwd=None):
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True, cwd=cwd)

def config_tool_env(model):
    # Step 1: uv init
    if not os.path.exists(os.path.join(f'tools_{model}', 'pyproject.toml')):
        run(f"uv init tools_{model}")
    project_dir = Path(f'tools_{model}').resolve()
    run("uv venv", cwd=project_dir)
    run("uv add mcp anthropic python-dotenv", cwd=project_dir)

    # Step 5: Remove main.py
    main_file = project_dir / "main.py"
    if main_file.exists():
        print(f"Removing {main_file}")
        main_file.unlink()


def generate_funcs_using_docs(model, path):
    with open(f'func_doc_{model}.json', 'r') as f:
        data = json.load(f)

    with open(f'func_templates.txt') as f:
        func_template = f.read()

    # os.makedirs(path, exist_ok=True)
    config_tool_env(model)

    i = 0
    for d in data:
        func_data = func_template.replace('[$FuncName]', d['function name']).replace('[$Docs]', d['function docstring'].strip('\"'))
        with open(os.path.join(path, f'{model}-t{i}.py'), 'w') as f: 
            f.write(func_data)
        generate_a_func_config(model, path, f'{model}-t{i}.py')
        i += 1

def generate_a_func_config(model, dire, fpath):
    with open('config_templates.txt', 'r') as f:
        config_template = f.read()
    absolute_path = Path(dire).resolve()

    data = config_template.replace('[$TOOL_DIR]', str(absolute_path)).replace('[$TOOL_FILE]', fpath)

    with open(os.path.join(dire, fpath.replace('.py', '_config.json')), 'w') as f:
        f.write(data)


def generate_funcs(model):
    if 'claude' in model:
        GenerateFuncDocwithClaude(model)
    if 'gpt' in model:
        GenerateFuncDocwithGPT(model)
    
    save_dirs = f'tools_{model}'
    generate_funcs_using_docs(model, save_dirs)


if __name__ == '__main__':
    generate_funcs("gpt-4o")