import yaml
from dataclasses import dataclass, field
import importlib
import re
from typing import Any
import inspect
import ast
import subprocess
import time
import sys, os
import argparse
import shutil
from importlib import resources

@dataclass
class PitoMeta:
    title: str
    author: str
    version: str
    header: str
    entry: str
    documentclass: str
    include: list[str]
    package: list[str]
    extra_args: dict[str, Any] = field(default_factory=dict)

    def __init__(self, **kwargs):
        self.title = kwargs.pop("title", "")
        self.author = kwargs.pop("author", "")
        self.version = kwargs.pop("version", "")
        self.header = kwargs.pop("header", "")
        self.entry = kwargs.pop("entry", "")
        self.documentclass = kwargs.pop("documentclass", "article")
        self.include = kwargs.pop("include", []) # assert the same file (repeat)
        self.package = kwargs.pop("package", []) # assert the same package (repeat)
        self.extra_args = kwargs



@dataclass
class FnTree:
    literal: str    # {{fn_name()}}
    name: str   # fn_name
    func: str   # fn()
    start_idx: int
    end_idx: int
    result: Any = None


class Pito:
    def __init__(self, data):
        self.meta = PitoMeta(**data)
        self.transform_content = ""
        self.get_entry()
        self.add_builtin()
        self.transform_content = self.process(self.entry_content)

    def add_builtin(self):
        self.meta.include.append("builtin.base")


    def process(self, content):
        self.parse_fn(content)
        self.get_mod() #
        self.get_fn() #
        self.get_fn_result() #
        content = self.apply_pito(content)
        if self.is_remain_fn(content):
            content = self.process(content)
        return content

    def get_entry(self):
        entry_file_name = self.meta.entry
        with open(entry_file_name, "r") as file:
            self.entry_content = file.read()

    def get_mod(self):
        self.meta.include = [mod.split(".py")[0] for mod in self.meta.include]
        #self.modules = [importlib.import_module(name) for name in self.meta.include]
        self.modules = []
        for name in self.meta.include:
            try:
                # 1. พยายาม import แบบปกติก่อน (สำหรับ user modules เช่น 'fn')
                module = importlib.import_module(name)
                self.modules.append(module)
            except ModuleNotFoundError as e:
                # 2. ถ้าหาไม่เจอ (เช่น 'builtin') ให้ลองหาข้างใน 'pito'
                try:
                    relative_name = f"pito.{name}"
                    module = importlib.import_module(relative_name)
                    self.modules.append(module)
                except ModuleNotFoundError:
                    # 3. ถ้ายังหาไม่เจออีก = พังจริง
                    print(f"FATAL: Module '{name}' not found as a user module or as a pito module (pito.{name})", file=sys.stderr)
                    raise e

    def get_fn(self):
        self.functions_map = {}
        def apply_fn_map(module, fn):
            if fn in self.functions_map and module != self.functions_map[fn]:
                raise Exception(f"Found the same `{fn}` more than one module.")
            self.functions_map[fn] = module
            return fn
        self.funcs = [{mod.__name__: [apply_fn_map(mod, name) for name, obj in inspect.getmembers(mod, inspect.isfunction)]} for mod in self.modules]

    def is_remain_fn(self, content):
        pat = r"\{\{[A-Za-z]+\(.*\)\}\}"
        remain = re.findall(pat, content)
        remain = [c for c in remain if c.strip() != ""]
        return True if len(remain) > 0 else False

    def parse_fn(self, content):
        pat = r"\{\{[A-Za-z]+\(.*\)\}\}"
        fn_tree_list = []
        for m in re.finditer(pat, content):
            literal = m.group()
            fn = FnTree(
                literal=literal,
                name=literal[2:-2].split('(')[0].strip(),
                func=literal[2:-2].strip(),
                start_idx=m.start(),
                end_idx=m.end(),
            )
            fn_tree_list.append(fn)
        self.fn_list = fn_tree_list


    def get_fn_result(self):
        for parse_fn in self.fn_list:
            if parse_fn.name not in self.functions_map:
                raise Exception(f"Not found `{parse_fn.name}` in any modules.")
            module = self.functions_map[parse_fn.name]
            node = ast.parse(parse_fn.func, mode='eval').body
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                func_name = node.func.id
                args = [ast.literal_eval(a) for a in node.args]
                func = getattr(module, func_name, None)
                if func:
                    result = func(*args)
                    parse_fn.result = result

    def apply_pito(self, content):
        for parse_fn in self.fn_list:
            start_idx = content.find(parse_fn.literal)
            content = content[:start_idx] + str(parse_fn.result) + content[start_idx+len(parse_fn.literal):]
        return content
    
def copy_template_files(pwd, destination_dir):
    try:
        destination_dir = os.path.join(pwd, destination_dir)
        template_path = resources.files("pito").joinpath("template")

        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)
            
        if os.listdir(destination_dir):
            print(f"Error: Directory '{destination_dir}' is not empty.", file=sys.stderr)
            print("Please run 'pito init' in an empty directory.")
            return False

        shutil.copytree(str(template_path), destination_dir, dirs_exist_ok=True)
        
        print(f"✅ Pito project initialized in: {destination_dir}")
        print("You can now edit 'config.yaml' and '.pto' files.")
        return True

    except Exception as e:
        print(f"Error copying template files: {e}", file=sys.stderr)
        return False

def get_meta(filename: str):
    with open(filename, 'r') as file:
        data = yaml.safe_load(file)
    return data

def to_pdf(pito, argparse):
    filename = pito.meta.entry.split(".")[0]
    if argparse.pdf is not None:
        filename = argparse.pdf
    tex_file = filename + ".tex"
    content = pito.transform_content
    
    header_file_content = ""
    if pito.meta.header:
        with open(pito.meta.header, "r") as header_file:
            header_file_content = header_file.read()
    
    packages = []
    for pkg in pito.meta.package:
        options = None
        if len(pkg.split("[")) > 1:
            options = pkg.split("[")[-1][:-1]
            pkg = pkg.split("[")[0]
        if options is not None:
            packages.append(r"\usepackage[OPS]{pkg}".replace("pkg", pkg).replace("OPS", options))
        else:
            packages.append(r"\usepackage{pkg}".replace("pkg", pkg))
    packages = "\n".join(packages)
    args = "\n".join([r"\NAME{PARAM}"\
                      .replace("NAME", arg.replace(".", "\\")).replace("PARAM", str(pito.meta.extra_args[arg])) for arg in pito.meta.extra_args])
    latex_source = r"""\documentclass{DOCCLASS}
PACKAGES
ARGS
HEADER
\begin{document}
CONTENT
\end{document}
"""
    latex_source = latex_source\
        .replace("CONTENT", content).replace("PACKAGES", packages)\
            .replace("ARGS", args).replace("DOCCLASS", pito.meta.documentclass)\
            .replace("HEADER", header_file_content)

    with open(tex_file, "w") as file:
        file.write(latex_source)

    proc = subprocess.run(
        ["xelatex", "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", tex_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(proc.stdout.decode("utf-8"))
    if not argparse.keep_tex:
        subprocess.run(
            ["rm", f"{filename}.tex", f"{filename}.log", f"{filename}.aux"]
        )

def run_build_process(args):
    pwd = os.getcwd()
    if pwd not in sys.path:
        sys.path.insert(0, pwd)
    meta_file = "config.yaml"
    start = time.time()
    data = get_meta(meta_file)
    pito = Pito(data)
    to_pdf(pito, args)
    print(f"time usage {time.time()-start:.3f}s")


def main():
    parser = argparse.ArgumentParser(
        description="""Pito: A lightweight dynamic programatically static pdf document generator."""
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)
    init_parser = subparsers.add_parser("init", help="Initialize a new Pito project in the current directory.")

    init_parser.add_argument("directory", type=str, nargs="?", default=".", 
                                       help="Directory to initialize (default: current directory)")

    build_parser = subparsers.add_parser("build", help="Build PDF from .pto files in the current directory.")
    build_parser.add_argument("--pdf", type=str, help="output pdf file name (optional)")
    build_parser.add_argument("--keep-tex", action="store_true", help="keep tex file.")

    args = parser.parse_args()

    if args.command == "init":
        copy_template_files(os.getcwd(), args.directory)
    
    elif args.command == "build":
        run_build_process(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()