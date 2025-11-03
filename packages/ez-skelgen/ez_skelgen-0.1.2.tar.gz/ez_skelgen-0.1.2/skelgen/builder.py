# build_structure & create files

import os
from .generator import generate_main_template, generate_source_template, generate_header_template

def collect_headers(tree, base_path=""):
    """트리에서 모든 .h 파일의 상대 경로를 수집"""
    headers = {}
    for node in tree:
        path = os.path.join(base_path, node["name"])
        if node["name"].endswith('/'):
            headers.update(collect_headers(node["children"], path))
        else:
            if node["name"].endswith('.h'):
                module_name = node["name"].replace(".h", "")
                headers[module_name] = path  # module_name -> 실제 경로
    return headers


def build_structure(tree, base_path, author="Unknown"):
    # 1️⃣ 헤더 먼저 생성
    headers = {}

    def create_headers(nodes, current_path):
        for node in nodes:
            path = os.path.join(current_path, node["name"])
            if node["name"].endswith('/'):
                os.makedirs(path, exist_ok=True)
                create_headers(node["children"], path)
            elif node["name"].endswith('.h'):
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(generate_header_template(node["name"]))
                module_name = node["name"].replace(".h", "")
                headers[module_name] = os.path.abspath(path)
                print(f"[HEADER] Created: {path}")

    create_headers(tree, base_path)

    # 2️⃣ .c 파일 생성
    def create_sources(nodes, current_path):
        for node in nodes:
            path = os.path.join(current_path, node["name"])
            if node["name"].endswith('/'):
                create_sources(node["children"], path)
            elif node["name"].endswith('.c'):
                os.makedirs(os.path.dirname(path), exist_ok=True)
                content = ""
                if node["name"] == "main.c":
                    content = generate_main_template()
                else:
                    module_name = node["name"].replace(".c", "")
                    include_header = headers.get(module_name)
                    if include_header:
                        rel_path = os.path.relpath(include_header, start=os.path.dirname(os.path.abspath(path)))
                        content = generate_source_template(node["name"], include_header=rel_path)
                    else:
                        content = generate_source_template(node["name"], include_header=None)

                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"[SOURCE] Created: {path}")

    create_sources(tree, base_path)

    return headers
