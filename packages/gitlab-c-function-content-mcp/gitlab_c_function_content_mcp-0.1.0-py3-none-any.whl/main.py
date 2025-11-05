#!/usr/bin/env python3

import os
import urllib

import requests
from mcp.server.fastmcp import FastMCP
from tree_sitter import Language, Parser
import tree_sitter_c as tsc


# Environment variables
gitlab_base_url = os.getenv('GITLAB_BASE_URL', 'https://sonicgit.eng.sonicwall.com/api/v4')
gitlab_repo = os.getenv('GITLAB_PROJECT_REPO_ID', 'sonicos/sonicosv')
gitlab_branch = os.getenv('GITLAB_PROJECT_BRANCH', 'MASTER/sonicosx/7.3.1/master')
gitlab_token = os.getenv('GITLAB_TOKEN')

mcp = FastMCP(name="Gitlab C Function Content MCP")


class TscParse():
    def __init__(self, code=''):
        C_LANGUAGE = Language(tsc.language())
        parser = Parser(language=C_LANGUAGE)
        tree = parser.parse(code.encode('utf-8'))
        self.code = code
        self.root_node = tree.root_node

    def print(self):
        self.print_node(self.root_node)

    def _print_node(self, node, indent=0):
        if node.type == '\n':
            return
        print('  ' * indent + f'{node.type} [{node.start_point}-{node.end_point}]')
        for child in node.children:
            self._print_node(child, indent + 1)

    def get_function(self, func_name):
        return self._find_function(self.root_node, func_name)

    def _match_function_name(self, node, func_name):
        declarator = node.child_by_field_name('declarator')
        if declarator is None:
            return
        all = []
        for child in declarator.children:
            if child.type == 'identifier':
                if func_name == self.code[child.start_byte:child.end_byte]:
                    # print(func_name, node.start_point, node.end_point)
                    all.append({
                        'name': func_name,
                        'start_point': node.start_point,
                        'end_point': node.end_point,
                        'start_byte': node.start_byte,
                        'end_byte': node.end_byte, 
                        'node': node,
                    })
        return all         

    def _has_error_in_node(self, node):
        for child in node.children:
            if child.type == 'ERROR':
                return True
        return False

    def _find_all_function_declarator_in_node(self, node):
        all = []
        for child in node.children:
            if child.type == 'function_declarator':
                # ret = match_function_name(child, )
                for sub in child.children:
                    if sub.type == 'identifier':
                        all.append(self.code[sub.start_byte:sub.end_byte])
                        # all.append(sub.text.decode('utf-8'))
                pass
            else:
                all.extend(self._find_all_function_declarator_in_node(child))
        return all

    def _find_function(self, node, func_name):
        c_macro_if = [
            'preproc_if', 'preproc_elif', 'preproc_else',
            'preproc_ifdef', 'preproc_elifdef',
            'ERROR',
        ]
        all = []
        previous_declarator_range = None
        for child in node.children:
            # special check
            if child.type == 'compound_statement' and previous_declarator_range is not None:
                all.append({
                    'name': func_name,
                    'start_point': previous_declarator_range['start_point'],
                    'end_point': child.end_point,
                    'start_byte': previous_declarator_range['start_byte'],
                    'end_byte': child.end_byte, 
                })
                previous_declarator_range = None
            elif child.type in c_macro_if and self._has_error_in_node(child):
                # print(f'error in {child}')
                func_declare_in_error = self._find_all_function_declarator_in_node(child)
                if func_name in func_declare_in_error:
                    previous_declarator_range = {
                        'name': func_name,
                        'start_point': child.start_point,
                        'end_point': child.end_point,
                        'start_byte': child.start_byte,
                        'end_byte': child.end_byte, 
                    }
                continue

            # general check
            if child.type == 'function_definition':
                funcs = self._match_function_name(child, func_name)
                all.extend(funcs)
            elif child.type in c_macro_if:
                funcs = self._find_function(child, func_name)
                all.extend(funcs)
        return all
    
    def _get_node_macro_if_condition(self, node, cond=None):
        if cond is None:
            cond = []
        if node.parent:
            if node.parent.type in ['preproc_if', 'preproc_ifdef']:
                l2 = self._get_node_macro_if_condition(node.parent)
                cond = [node.parent.children[0].text.decode('utf-8') + ' ' + node.parent.children[1].text.decode('utf-8')]
                return (l2 or []) + cond

            cond = self._get_node_macro_if_condition(node.parent, cond)
            if node.parent.type in ['preproc_elif', 'preproc_elifdef']:
                cond.append(node.parent.children[0].text.decode('utf-8') + ' ' + node.parent.children[1].text.decode('utf-8'))
            elif node.parent.type == 'preproc_else':
                cond.append(node.parent.children[0].text.decode('utf-8'))

            return cond
    
    def print_node_macro_if_condition(self, node):
        cond = self._get_node_macro_if_condition(node)
        return '\n'.join(cond) + '\n<following code>'


def request_get(url):
    resp = requests.get(url, headers = {"PRIVATE-TOKEN": os.getenv('GITLAB_TOKEN')})
    if resp.status_code < 200 or resp.status_code >= 300:
        raise ValueError(resp.text)
    return resp.text

def request_file(base_url, repo_id, branch, filename):
    repo_id = urllib.parse.quote(repo_id, safe='')
    branch = urllib.parse.quote(branch, safe='')
    filename = urllib.parse.quote(filename, safe='')
    return request_get(f'{base_url}/projects/{repo_id}/repository/files/{filename}/raw?ref={branch}')

@mcp.tool()
def get_file_content(filepath: str) -> str:
    """Get file content from filepath."""
    return request_file(gitlab_base_url, gitlab_repo, gitlab_branch, filepath)

@mcp.tool()
def get_function_content(filepath: str, function_name: str) -> str:
    """Get function content in specified file."""
    file_content = request_file(gitlab_base_url, gitlab_repo, gitlab_branch, filepath)
    tsc = TscParse(file_content)
    functions = tsc.get_function(function_name)
    content = ''
    if len(functions) == 0:
        content += f'## Not found function `{function_name}` in file `{filepath}`.\n'
    elif len(functions) == 1:
        content += f'## Found function `{function_name}` in file `{filepath}`.\n'
    else:
        content += f'## Found {len(functions)} functions `{function_name}` in file `{filepath}`.\n'
    for i, func in enumerate(functions):
        content += '\n'
        content += f'### definition #{i+1}\n\n'
        if func.get('node'):
            cond = tsc.print_node_macro_if_condition(func.get('node'))
            content += 'defined in macro:\n\n```\n'
            content += cond + '\n'
            content += '```\n\n'
        
        content += 'source code:\n\n'
        content += f'```c {{numberLines: true, startFrom: {func['start_point'].row+1}}}\n'
        content += tsc.code[func['start_byte']:func['end_byte']] + '\n'
        content += '```\n'
    return content

def main():
    mcp.run()

if __name__ == "__main__":
    main
