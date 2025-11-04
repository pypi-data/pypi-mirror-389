#!/usr/bin/env python3
import sys
import os
import re
import shutil
import subprocess
import importlib
import argparse

# VERSION
__version__ = "0.8.1"

# Exceptions mapping: CLI -> (install_target, install_instructions)
CLI_EXCEPTIONS = {
    "firebase": ("firebase-tools", "npm install -g firebase-tools"),
    "heroku": ("heroku", "npm install -g heroku"),
    "npm": (None, "Install Node.js from https://nodejs.org/"),
    "git": (None, "Install Git from https://git-scm.com/"),
    "aws": ("awscli", "pip install awscli"),
    "terraform": (None, "Download from https://www.terraform.io/downloads"),
    "yarn": ("yarn", "npm install -g yarn"),
    "docker": (None, "Install Docker from https://www.docker.com/get-started")
}

# Known python CLI wrappers to prefer Scripts/*.exe on Windows
PYTHON_CLIS = ["black", "isort", "pylint", "flake8", "mypy", "pytest"]

# small package name translations (module -> pip name)
PACKAGE_NAME_MAP = {
    "bs4": "beautifulsoup4",
    "PIL": "Pillow",
    "cv2": "opencv-python",
    # add more if needed
}

def is_executable(cmd):
    """Check if a CLI exists (handles .exe/.cmd on Windows)."""
    if shutil.which(cmd):
        return True
    if os.name == "nt" and (shutil.which(cmd + ".cmd") or shutil.which(cmd + ".exe")):
        return True
    return False

def get_cli_path(cmd):
    """Return best executable path for a CLI (Windows-safe)."""
    if os.name == "nt" and cmd in PYTHON_CLIS:
        scripts_path = os.path.join(sys.exec_prefix, "Scripts", cmd + ".exe")
        if os.path.exists(scripts_path):
            return scripts_path
    path = shutil.which(cmd) or shutil.which(cmd + ".exe") or shutil.which(cmd + ".cmd")
    return path

def safe_run(cmd_list, env=None, check=True):
    """Run subprocess safely and handle KeyboardInterrupt gracefully."""
    try:
        subprocess.run(cmd_list, env=env, check=check)
    except KeyboardInterrupt:
        print("Installation/command cancelled by user.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        return False
    return True

def install_via_pip(pkg_name):
    """Install a Python package with pip."""
    pip_target = PACKAGE_NAME_MAP.get(pkg_name, pkg_name)
    print(f"'{pkg_name}' not found, installing via pip ({pip_target})...")
    return safe_run([sys.executable, "-m", "pip", "install", pip_target])

def install_via_npm(install_target):
    """Install a package via npm -g (Windows-safe)."""
    npm_path = shutil.which("npm")
    if not npm_path:
        print("'npm' not found in PATH. Install Node.js from https://nodejs.org/")
        return False
    print(f"Installing {install_target} via npm...")
    if os.name == "nt":
        return safe_run(["cmd", "/c", npm_path, "install", "-g", install_target])
    else:
        return safe_run([npm_path, "install", "-g", install_target])

def try_import(name):
    """Try importing a module name; return True if success."""
    try:
        importlib.import_module(name)
        return True
    except Exception:
        return False

def parse_imports_from_file(path):
    """Parse top-level module names from a .py file, robust."""
    modules = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("import "):
                    parts = line[7:].split(",")
                    for p in parts:
                        mod = p.split("as")[0].strip().split(".")[0]
                        if mod:
                            modules.append(mod)
                elif line.startswith("from "):
                    mod = line[5:].split("import")[0].strip().split(".")[0]
                    if mod:
                        modules.append(mod)
    except Exception:
        pass
    # dedupe keeping order
    seen = set()
    out = []
    for m in modules:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out

def auto_install_imports_for_file(path, prompt=True):
    """Scan file for imports and auto-install missing packages."""
    mods = parse_imports_from_file(path)
    if not mods:
        return True

    print("Detected imports:", ", ".join(mods))
    success = True

    for mod in mods:
        if try_import(mod):
            continue  # builtin or already installed
        pkg = PACKAGE_NAME_MAP.get(mod, mod)
        if prompt:
            response = input(f"Module '{mod}' not installed. Install '{pkg}'? [Y/n]: ").strip().lower()
            if response not in ("", "y", "yes"):
                print(f"Skipping '{pkg}'")
                success = False
                continue
        ok = install_via_pip(pkg)
        if not ok:
            print(f"Failed to install '{pkg}'")
            success = False

    return success

def run_cli(target, args):
    """Run a CLI command. Will auto-install known exceptions when missing."""
    if target in CLI_EXCEPTIONS:
        install_target, instructions = CLI_EXCEPTIONS[target]
        if install_target:
            if install_target.endswith("-tools") or install_target in ("heroku", "yarn"):
                if not is_executable("npm"):
                    print(f"'npm' is required to install '{install_target}'. {instructions}")
                    return
                if not install_via_npm(install_target):
                    return
            else:
                if not safe_run([sys.executable, "-m", "pip", "install", install_target]):
                    return
        else:
            print(f"'{target}' CLI not found. {instructions}")
            return
    elif not is_executable(target):
        print(f"'{target}' CLI not found in PATH. Try installing it manually or let caki handle known exceptions.")
        return

    exe_path = get_cli_path(target)
    if not exe_path:
        print(f"Could not find executable for {target}")
        return

    env = os.environ.copy()
    if os.name == "nt":
        current_dir = os.getcwd()
        paths = env.get("PATH", "").split(";")
        filtered = [p for p in paths if os.path.normcase(p) != os.path.normcase(current_dir)]
        env["PATH"] = ";".join(filtered)

    if os.name == "nt" and exe_path.lower().endswith(".cmd"):
        safe_run(["cmd", "/c", exe_path] + args, env=env)
    else:
        safe_run([exe_path] + args, env=env)

def run_library(package, code=None):
    """Ensure library installed then run code (exec)."""
    try:
        importlib.import_module(package)
    except ModuleNotFoundError:
        if not install_via_pip(PACKAGE_NAME_MAP.get(package, package)):
            return
    if code:
        exec_globals = {}
        try:
            exec(code, exec_globals)
        except Exception as e:
            print("Error while executing code:", e)
    else:
        print(f"Library '{package}' installed. No code to run.")

def run_python_file(script_path, script_args):
    """Auto-install imports found in script, then run the script."""
    if not os.path.exists(script_path):
        print(f"Script not found: {script_path}")
        return
    if not auto_install_imports_for_file(script_path):
        print("Some imports failed to install; aborting run.")
        return
    cmd = [sys.executable, script_path] + script_args
    safe_run(cmd)

def main():
    parser = argparse.ArgumentParser(
        description="Caki 0.8.1 — auto-install CLI and Python deps\n"
                    "Use '--caki-version' or 'caki version' to check Caki's version."
    )
    parser.add_argument("target", help="Command, module or script to run (e.g. black, rich, python, main.py)")
    parser.add_argument("--code", help="Python code to execute for a library (do not pass CLI flags here)", default=None)
    parser.add_argument("--caki-version", action="version", version=f"caki {__version__}",
                        help="Show caki version (for scripts or automation)")

    args, rest = parser.parse_known_args()
    target = args.target
    code = args.code
    rest_args = [r for r in rest if r.strip() != ""]

    # Version subcommand for humans
    if target.lower() == "version":
        print(f"caki {__version__}")
        return

    if code is not None:
        run_library(target, code)
        return

    if target in ("python", "py"):
        if not rest_args:
            print("No script specified for python. Usage: caki python script.py [args]")
            return
        script = rest_args[0]
        script_args = rest_args[1:]
        run_python_file(script, script_args)
        return

    if target.endswith(".py") and os.path.exists(target):
        script_args = rest_args
        run_python_file(target, script_args)
        return

    if is_executable(target) or target in CLI_EXCEPTIONS:
        run_cli(target, rest_args)
        return
    else:
        code_to_run = None
        if rest_args:
            code_to_run = " ".join(rest_args)
        run_library(target, code_to_run)

if __name__ == "__main__":
    main()