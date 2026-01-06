import subprocess
import time
import psutil
import pyautogui
import shutil
import os
import yaml
import json
clientConfig = {"claude-desktop": "~/.config/Claude/claude_desktop_config.json",
                "librechat": "~/LibreChat/librechat.yaml"}

def apply_attack_tool_config(client, generating_model, tool_path, other_tools_scale=0):
    tool_directory = f'tools_{generating_model}'
    if client == 'claude-desktop':
        if other_tools_scale == 0:
            if 'shadow_func' not in tool_path:
                template_file = f'{tool_directory}/claude_template_config_small.txt'
            else:
                template_file = f'{tool_directory}/claude_template_config_small(contain_fetch).txt'
        elif other_tools_scale == 1:
            if 'shadow_func' not in tool_path:
                template_file = f'{tool_directory}/claude_template_config_medium.txt'
            else:
                template_file = f'{tool_directory}/claude_template_config_medium(contain_fetch).txt'
        else:
            if 'shadow_func' not in tool_path:
                template_file = f'{tool_directory}/claude_template_config_large.txt'
            else:
                template_file = f'{tool_directory}/claude_template_config_large(contain_fetch).txt'
        with open(template_file, 'r') as f:
            data = f.read()
        print(f'apply {tool_directory}/{tool_path} on {client}')
        data = data.replace('[$TOOL_DIRECTORY$]', os.path.abspath(tool_directory)).replace('[$TOOL_FPATH$]', tool_path)
        clientConfigPath = clientConfig[client]
        clientConfigPath = os.path.expanduser(clientConfigPath)
        with open(clientConfigPath, 'w') as f:
            f.write(data)
        return json.loads(data)
    if client == 'librechat':
        if other_tools_scale == 0:
            if 'shadow_func' not in tool_path:
                template_file = f'{tool_directory}/librechat_template_config_small.txt'
            else:
                template_file = f'{tool_directory}/librechat_template_config_small(contain_fetch).txt'
        elif other_tools_scale == 1:
            if 'shadow_func' not in tool_path:
                template_file = f'{tool_directory}/librechat_template_config_medium.txt'
            else:
                template_file = f'{tool_directory}/librechat_template_config_medium(contain_fetch).txt'
        else:
            if 'shadow_func' not in tool_path:
                template_file = f'{tool_directory}/librechat_template_config_large.txt'
            else:
                template_file = f'{tool_directory}/librechat_template_config_large(contain_fetch).txt'
        with open(template_file, 'r') as f:
            data = f.read()
        print(f'apply {tool_directory}/{tool_path} with scale {other_tools_scale} on {client}')
        data = data.replace('[$TOOL_DIRECTORY$]', os.path.abspath(tool_directory)).replace('[$TOOL_FPATH$]', tool_path)
        clientConfigPath = clientConfig[client]
        clientConfigPath = os.path.expanduser(clientConfigPath)
        with open(clientConfigPath, 'w') as f:
            f.write(data)
        return yaml.safe_load(data)


def get_attack_tools(tool_generated_from_model, t=0, enhanced=False):
    tool_paths = []
    if t==0:
        t = 'pre_func'
    elif t == 1:
        t = 'post_func'
    else:
        t = 'shadow_func'
    if enhanced:
        t = 'enhanced_' + t
    for f in os.listdir(os.path.join(f'tools_{tool_generated_from_model}', t)):
        if not f.endswith('.py'):
            continue
        fpath = os.path.join(t, f)
        tool_paths.append(fpath)
    return tool_paths


if __name__ == '__main__':
    client = 'librechat'
    attack_model = 'claude-sonnet-4'
    scale = 1
    attack_method = 1
    t = get_attack_tools(attack_model, attack_method, enhanced=True)[0]
    print(t)
    config = apply_attack_tool_config(client, attack_model, t, other_tools_scale=scale)
    print(len(config['mcpServers']))