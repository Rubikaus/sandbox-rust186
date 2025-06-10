import os
import uuid
import shutil
from collections import namedtuple
from app import config

import re

def _wrap_rust_code(code: str) -> str:
    if re.search(r'\bfn\s+main\s*\(', code):
        return code

    lines = code.splitlines()
    global_lines = []
    inner_lines = []

    global_prefixes = (
        'use ', 'extern crate', 'struct ', 'enum ', 'trait ', 'impl ',
        'mod ', 'type ', 'const ', 'static ', '#[', 'fn '
    )

    collecting_global_block = False
    block_level = 0

    for line in lines:
        stripped = line.lstrip()
        opening = stripped.count('{')
        closing = stripped.count('}')
        if (collecting_global_block or
            any(stripped.startswith(p) for p in global_prefixes)):
            global_lines.append(line)
            block_level += opening - closing
            collecting_global_block = block_level > 0
        else:
            inner_lines.append(line)

    while inner_lines and inner_lines[0].strip() == '':
        inner_lines.pop(0)
    while inner_lines and inner_lines[-1].strip() == '':
        inner_lines.pop()

    if inner_lines:
        indented_body = '\n    '.join(inner_lines)
        main_block = f"fn main() {{\n    {indented_body}\n}}"
    else:
        main_block = "fn main() {}"  # fallback

    result_parts = []
    if global_lines:
        result_parts.append('\n'.join(global_lines))
    result_parts.append(main_block)
    return '\n'.join(result_parts)

ExecuteResult = namedtuple('ExecuteResult', ('result', 'error'))

class RustFile:

    def __init__(self, code: str):
        file_id = str(uuid.uuid4()).replace('-', '_')
        self.package_name = f"sandbox_proj_{file_id}"
        self.project_dir = os.path.join(config.SANDBOX_DIR, self.package_name)
        self.src_dir = os.path.join(self.project_dir, 'src')
        os.makedirs(self.src_dir, exist_ok=True)

        import re
        main_regex = re.compile(r'\bfn\s+main\s*\(')
        if not main_regex.search(code):
            code = _wrap_rust_code(code)

        self.filepath_rs = os.path.join(self.src_dir, 'main.rs')
        with open(self.filepath_rs, 'w') as file:
            file.write(code)

        self.manifest_path = os.path.join(self.project_dir, 'Cargo.toml')
        with open(self.manifest_path, 'w') as manifest:
            manifest.write(f"""[package]
                                name = "{self.package_name}"
                                version = "0.1.0"
                                edition = "2021"

                                [dependencies] 
                                """)
        self.filepath_out = os.path.join(
            self.project_dir,
            'target',
            'release',
            self.package_name.replace('-', '_')
        )

    def remove(self):
        try:
            shutil.rmtree(self.project_dir, ignore_errors=True)
        except FileNotFoundError:
            pass