#!/usr/bin/env python3
"""
MCP Server: mcp-cloud-ops

Read-only wrappers for aws, kubectl, helm and a search_context helper.
"""

import os
import re
import shlex
import subprocess
import logging
from pathlib import Path
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP


cloud_logger = logging.getLogger("mcp.cloud")
cloud_logger.setLevel(logging.INFO)


def configure_proxy_session():
    import requests
    session = requests.Session()
    http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
    https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    no_proxy = os.environ.get('NO_PROXY') or os.environ.get('no_proxy')
    if http_proxy or https_proxy:
        proxies = {}
        if http_proxy:
            proxies['http'] = http_proxy
        if https_proxy:
            proxies['https'] = https_proxy
        session.proxies.update(proxies)
        if no_proxy:
            session.trust_env = False
            session.proxies['no'] = no_proxy
    return session


def _parse_command(command: str) -> List[str]:
    operators = ['|', '&&', '||', ';']
    result: List[str] = []
    current_cmd = ''
    i = 0
    while i < len(command):
        for op in operators:
            if command[i:].startswith(op):
                if current_cmd.strip():
                    result.append(current_cmd.strip())
                current_cmd = ''
                i += len(op)
                break
        else:
            current_cmd += command[i]
            i += 1
    if current_cmd.strip():
        result.append(current_cmd.strip())
    return result


def _validate_and_run(command: str, tool_name: str, allowed: List[str], disallowed_opts: List[str], cmd_index: int) -> Dict[str, Any]:
    try:
        full_command = f"{tool_name} {command}" if not command.strip().startswith(tool_name) else command
        for sub_cmd in _parse_command(full_command):
            parts = shlex.split(sub_cmd)
            tool_index = -1
            for i, part in enumerate(parts):
                if part == tool_name:
                    tool_index = i
                    break
            if tool_index == -1:
                continue
            validate_index = tool_index + 1 + cmd_index
            if validate_index >= len(parts):
                raise ValueError(f"Invalid {tool_name} command: missing required parts")
            verb = parts[validate_index]
            if not any(verb.startswith(a) for a in allowed):
                raise ValueError(f"Only read-only {tool_name} verbs allowed: {', '.join(allowed)}")
            if any(opt in parts for opt in disallowed_opts):
                raise ValueError(f"Disallowed options detected: {', '.join(disallowed_opts)}")

        proc = subprocess.Popen(full_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = proc.communicate()
        # Cas d'erreur: Exit code != 0
        if proc.returncode != 0:
            # Si stderr est vide, c'est probablement un grep/pipe sans résultat, pas une vraie erreur
            if not err.strip():
                return {"output": "Command executed successfully but returned no output."}
            # Sinon, c'est une vraie erreur
            return {"error": f"Error running {tool_name} command: {err}"}

        # Cas de succès: Exit code == 0
        # Cas 1: stdout non vide → output normal
        if out.strip():
            return {"output": out}
        # Cas 3: stdout vide, stderr non vide → messages informatifs (comme "No resources found")
        if err.strip():
            return {"output": err}
        # Cas 2: stdout vide, stderr vide → message informatif
        return {"output": "Command executed successfully but returned no output."}
    except Exception as e:
        return {"error": f"Error executing {tool_name} command: {str(e)}"}


def create_server() -> FastMCP:
    mcp = FastMCP("mcp-cloud-ops")

    @mcp.tool()
    def aws(command: str) -> str:
        """Execute a read-only AWS CLI command. Requires --profile."""
        if not command:
            return "No AWS command provided"
        if "--profile" not in command:
            return "Error: The --profile option is required to specify which AWS profile to use. Format: '<service> <action> [parameters] --profile <profile_name>'"
        res = _validate_and_run(
            command,
            tool_name="aws",
            allowed=[
                'analyze', 'check', 'describe', 'estimate', 'export',
                'filter', 'generate', 'get', 'help', 'list', 'lookup',
                'ls', 'preview', 'scan', 'search', 'show',
                'summarize', 'test', 'validate', 'view'
            ],
            disallowed_opts=[],
            cmd_index=1,
        )
        return res.get('output') if 'output' in res else res.get('error', 'Unknown error')

    @mcp.tool()
    def kubectl(command: str) -> str:
        """Execute a read-only kubectl command. Requires --context."""
        if not command:
            return "No kubectl command provided"
        if "--context" not in command:
            return "Error: The --context option is required to specify which cluster to use. Format: '<command> [parameters] --context <context_name>'"
        res = _validate_and_run(
            command,
            tool_name="kubectl",
            allowed=['api-resources', 'api-versions', 'cluster-info', 'describe', 'explain', 'get', 'logs', 'top', 'version', 'config'],
            disallowed_opts=['--kubeconfig', '--as', '--as-group', '--token'],
            cmd_index=0,
        )
        return res.get('output') if 'output' in res else res.get('error', 'Unknown error')

    @mcp.tool()
    def helm(command: str) -> str:
        """Execute a read-only Helm command. Requires --kube-context."""
        if not command:
            return "No Helm command provided"
        if "--kube-context" not in command:
            return "Error: The --kube-context option is required to specify which cluster to use. Format: '<command> [parameters] --kube-context <context_name>'"
        res = _validate_and_run(
            command,
            tool_name="helm",
            allowed=['dependency', 'env', 'get', 'history', 'inspect', 'lint', 'list', 'search', 'show', 'status', 'template', 'verify', 'version'],
            disallowed_opts=['--kubeconfig'],
            cmd_index=0,
        )
        return res.get('output') if 'output' in res else res.get('error', 'Unknown error')

    @mcp.tool()
    def search_context(command: str) -> str:
        """Search matching AWS profiles and kubectl contexts by substring(s)."""
        # List profiles
        profiles_res = _validate_and_run("configure list-profiles", "aws", [
            'analyze', 'check', 'describe', 'estimate', 'export', 'filter', 'generate', 'get', 'help', 'list', 'lookup', 'ls', 'preview', 'scan', 'search', 'show', 'summarize', 'test', 'validate', 'view'
        ], [], 1)
        if 'error' in profiles_res:
            return f"Failed to get AWS profiles: {profiles_res['error']}"
        profiles = [p.strip() for p in (profiles_res.get('output') or '').strip().split('\n') if p.strip()]

        search_term = (command or '').strip()
        if search_term:
            words = search_term.lower().split()
            filtered_profiles: List[str] = []
            for w in words:
                filtered_profiles.extend([p for p in profiles if w in p.lower()])
            profiles = list(dict.fromkeys(filtered_profiles)) or profiles

        # Regions for filtered profiles (best-effort)
        region_map = {}
        for p in profiles:
            region_res = _validate_and_run(f"configure get region --profile {p}", "aws", [
                'analyze', 'check', 'describe', 'estimate', 'export', 'filter', 'generate', 'get', 'help', 'list', 'lookup', 'ls', 'preview', 'scan', 'search', 'show', 'summarize', 'test', 'validate', 'view'
            ], [], 1)
            region_map[p] = (region_res.get('output') or '').strip()

        # kubectl contexts
        kube_res = _validate_and_run("config get-contexts", "kubectl", ['api-resources', 'api-versions', 'cluster-info', 'describe', 'explain', 'get', 'logs', 'top', 'version', 'config'], ['--kubeconfig', '--as', '--as-group', '--token'], 0)
        if 'error' in kube_res:
            return f"Failed to get kubectl contexts: {kube_res['error']}"
        lines = (kube_res.get('output') or '').strip().split('\n')
        contexts: List[str] = []
        for line in lines[1:] if len(lines) > 1 else []:
            m = re.search(r'arn:aws[^:]*:eks:[^:]+:[^:]+:cluster/[^/]+-[^-]+(?:\s|$)', line)
            if m:
                contexts.append(m.group(0).strip())

        if search_term:
            words = search_term.lower().split()
            filtered_contexts: List[str] = []
            for w in words:
                filtered_contexts.extend([c for c in contexts if w in c.lower()])
            contexts = list(dict.fromkeys(filtered_contexts)) or contexts

        return str({
            'aws_profiles': profiles,
            'aws_default_region': region_map,
            'kubectl_contexts': contexts,
        })

    return mcp


if __name__ == "__main__":
    create_server().run()

def main():
    create_server().run()

