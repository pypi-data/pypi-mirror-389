# template loading & generate_main/source/header_template

import os
from pathlib import Path
from datetime import date

TEMPLATE_DIR = Path(__file__).parent / "templates/c"

def load_template(name: str) -> str:
    path = TEMPLATE_DIR / name
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def generate_main_template() -> str:
    template = load_template("main_template.c.tpl")
    return template.replace("{{date}}", str(date.today()))

def generate_source_template(filename: str, include_header: bool = True) -> str:
    module_name = filename.replace(".c", "")
    header_name = f"{module_name}.h"
    if include_header:
        template = load_template("source_template.c.tpl")
        return (template.replace("{{filename}}", filename)
                        .replace("{{header_name}}", header_name)
                        .replace("{{module_name}}", module_name)
                        .replace("{{date}}", str(date.today())))
    else:
        return f"""/**
 * @file {filename}
 * @brief Source file for {module_name}
 * @version 0.1
 * @date {date.today()}
 */

// TODO: Implement functions
"""

def generate_header_template(filename: str) -> str:
    module_name = filename.replace(".h", "")
    include_guard = f"_{module_name.upper()}_H_"
    template = load_template("header_template.h.tpl")
    return (template.replace("{{filename}}", filename)
                    .replace("{{module_name}}", module_name)
                    .replace("{{include_guard}}", include_guard)
                    .replace("{{date}}", str(date.today())))
