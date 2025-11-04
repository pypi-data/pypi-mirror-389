#!/usr/bin/env python3
import sys
import os
import re
import shutil
import subprocess
import importlib
import argparse

# VERSION
__version__ = "0.8.0"

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

# Regex to find imports (simple, pragmatic)
_IMPORT_RE = re.compile(r'^\s*(?:from\s+([A-Za-z0-9_.]+)\s+import|import\s+([A-Za-z0-9_.]+))')

def is_executable(cmd):
    """Check if a CLI exists (handles .exe/.cmd on Windows)."""
    if shutil.which(cmd):
        return True
    if os.name == "nt" and (shutil.which(cmd + ".cmd") or shutil.which(cmd + ".exe")):
        return True
    return False

def get_cli_path(cmd):
    """Return best executable path for a CLI (Windows-safe)."""
    # Prefer Scripts/<cmd>.exe for Python CLIs on Windows
    if os.name == "nt" and cmd in PYTHON_CLIS:
        scripts_path = os.path.join(sys.exec_prefix, "Scripts", cmd + ".exe")
        if os.path.exists(scripts_path):
            return scripts_path
    # fallback to PATH resolution
    path = shutil.which(cmd) or shutil.which(cmd + ".exe") or shutil.which(cmd + ".cmd")
    return path

def safe_run(cmd_list, env=None, check=True):
    """Run subprocess safely and handle KeyboardInterrupt gracefully."""
    try:
        subprocess.run(cmd_list, env=env, check=check)
    except KeyboardInterrupt:
        print("Installation/command cancelled by user.")
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
    """Parse top-level import/module names from a .py file."""
    modules = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                m = _IMPORT_RE.match(line)
                if m:
                    mod = m.group(1) or m.group(2)
                    if mod:
                        # take top-level module name (before dot)
                        top = mod.split(".")[0]
                        modules.append(top)
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

def auto_install_imports_for_file(path):
    """Scan file for imports and auto-install missing packages (Option A: auto-install everything)."""
    mods = parse_imports_from_file(path)
    if not mods:
        return True
    print("Detected imports:", ", ".join(mods))
    success = True
    for mod in mods:
        # Skip builtins quickly by trying import first
        if try_import(mod):
            continue
        # Map e.g. bs4 -> beautifulsoup4
        pkg = PACKAGE_NAME_MAP.get(mod, mod)
        # Install via pip
        ok = install_via_pip(pkg)
        if not ok:
            success = False
    return success

def install_package_if_missing_for_library(pkg):
    """Ensure a Python package is installed (used by --code when executing module code)."""
    if try_import(pkg):
        return True
    return install_via_pip(pkg)

def run_cli(target, args):
    """Run a CLI command. Will auto-install known exceptions when missing."""
    # If target is in exceptions and needs install
    if target in CLI_EXCEPTIONS:
        install_target, instructions = CLI_EXCEPTIONS[target]
        if install_target:
            # decide npm vs pip heuristic
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

    # Prepare env — remove current folder precedence to avoid collision with caki
    env = os.environ.copy()
    if os.name == "nt":
        current_dir = os.getcwd()
        paths = env.get("PATH", "").split(";")
        filtered = [p for p in paths if os.path.normcase(p) != os.path.normcase(current_dir)]
        env["PATH"] = ";".join(filtered)

    # Windows: when exe_path endswith .cmd we need cmd /c, else run directly
    if os.name == "nt" and exe_path.lower().endswith(".cmd"):
        safe_run(["cmd", "/c", exe_path] + args, env=env)
    else:
        safe_run([exe_path] + args, env=env)

def run_library(package, code=None):
    """Ensure library installed then run code (exec)."""
    # If code is a simple "import x; ..." we could try to detect packages to install.
    # But primarily, try to import the named package/module first.
    try:
        importlib.import_module(package)
    except ModuleNotFoundError:
        # try auto-install package name = module name
        if not install_via_pip(PACKAGE_NAME_MAP.get(package, package)):
            return
    # execute code if present
    if code:
        # code string is trusted from user; run in a fresh globals context
        exec_globals = {}
        try:
            exec(code, exec_globals)
        except Exception as e:
            print("Error while executing code:", e)
    else:
        print(f"Library '{package}' installed. No code to run.")

def run_python_file(script_path, script_args):
    """Auto-install imports found in script, then run the script with current Python interpreter."""
    if not os.path.exists(script_path):
        print(f"Script not found: {script_path}")
        return
    if not auto_install_imports_for_file(script_path):
        print("Some imports failed to install; aborting run.")
        return
    # Run script with current interpreter
    cmd = [sys.executable, script_path] + script_args
    safe_run(cmd)

def main():
    parser = argparse.ArgumentParser(description="Caki 0.8.0 — auto-install CLI and Python deps")
    parser.add_argument("target", help="Command, module or script to run (e.g. black, rich, python, main.py)")
    # use parse_known_args to ensure --code is consumed by Caki, not forwarded
    parser.add_argument("--code", help="Python code to execute for a library (do not pass CLI flags here)", default=None)
    parser.add_argument("-v", "--version", action="version", version=f"caki {__version__}")
    # parse_known_args will leave other tokens (CLI flags for target) in 'rest'
    args, rest = parser.parse_known_args()
    target = args.target
    code = args.code
    # Determine script args:
    rest_args = [r for r in rest if r.strip() != ""]  # keep as-is; these are passed to the underlying command
    # CASES:
    # 1) explicit --code given: treat as library mode, run 'target' as module name and exec code
    if code is not None:
        # library execution: ensure package installed then exec
        run_library(target, code)
        return
    # 2) if target is 'python' and there's a script following: caki python main.py ...
    if target in ("python", "py"):
        if not rest_args:
            print("No script specified for python. Usage: caki python script.py [args]")
            return
        script = rest_args[0]
        script_args = rest_args[1:]
        # Auto-install imports in the script, then run
        run_python_file(script, script_args)
        return
    # 3) if target looks like a .py file itself: caki main.py ...
    if target.endswith(".py") and os.path.exists(target):
        script_args = rest_args
        run_python_file(target, script_args)
        return
    # 4) Otherwise, attempt to run as CLI first (auto-install exceptions), fallback to library mode if no CLI
    if is_executable(target) or target in CLI_EXCEPTIONS:
        # run CLI, pass rest_args as CLI flags/args
        run_cli(target, rest_args)
        return
    else:
        # treat as Python library/module; if rest_args exist, join them and exec as code if present
        code_to_run = None
        if rest_args:
            # user might have passed inline python code as remainder (not recommended in cmd)
            code_to_run = " ".join(rest_args)
        run_library(target, code_to_run)

if __name__ == "__main__":
    main()