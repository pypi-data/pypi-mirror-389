#!/usr/bin/env python3
import os, sys, json, re, shlex, subprocess, pathlib, argparse, textwrap
from typing import Optional
import requests

DEFAULT_MODEL = os.getenv("AKSCMD_MODEL", "gemini-2.0-flash")
API_KEY = os.getenv("AKSCMD_API_KEY") or os.getenv("AKSCMD_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") or "AIzaSyBUq_wmCJKgoWrmcTEGcKE_c0xQ6MdLOio"
# Endpoint pattern supports both older and newer Gemini routes
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{DEFAULT_MODEL}:generateContent"

RISKY_PATTERNS = [
    r"rm\s+-rf\s+/\b",
    r"rm\s+-rf\s+~\b",
    r":\(\)\s*\{\s*:\|\:\&\s*\};\s*:",
    r"mkfs\.", r"dd\s+if=", r"chmod\s+777\s+-R\s+/", r"chown\s+-R\s+root\b",
    r"shutdown\b", r"reboot\b", r"parted\b", r"fdisk\b",
]

def _fatal(msg: str, code: int = 2):
    print(f"[akscmd] {msg}", file=sys.stderr)
    sys.exit(code)

def _clean_model_output(s: str) -> str:
    if not s: return ""
    # strip code fences and markdown
    s = s.strip()
    s = re.sub(r"^```[a-zA-Z]*\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    # take first non-empty line
    for line in s.splitlines():
        line = line.strip()
        if not line: continue
        # remove leading shell prompt markers
        line = re.sub(r"^\$\s*", "", line)
        return line
    return ""

def _is_risky(cmd: str) -> bool:
    return any(re.search(p, cmd) for p in RISKY_PATTERNS)

SYSTEM_INSTRUCTIONS = """\
You are a converter from natural language to a single shell command.
Rules:
- Output ONE command only (single line). No explanations, no comments, no prompts.
- Prefer safe defaults. Use '&&' if multiple steps are mandatory.
- Quote paths safely. Never output backticks or code fences.
- For creating directories: Use 'mkdir' (without -p flag to avoid compatibility issues)
- For creating files on Windows/PowerShell: Use 'echo $null > filename' or 'New-Item -ItemType File filename'
- For creating files on Unix: Use 'touch filename'
- Detect the environment and use appropriate commands.
"""

def query_gemini(prompt: str, temperature: float = 0.0) -> str:
    if not API_KEY:
        print("[akscmd] API key not found. Set AKSCMD_API_KEY environment variable.")
        sys.exit(1)
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": SYSTEM_INSTRUCTIONS + "\nUser request: " + prompt}]}
        ],
        "generationConfig": {"temperature": temperature},
    }
    try:
        r = requests.post(API_URL, params={"key": API_KEY}, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return _clean_model_output(text)
    except Exception as e:
        _fatal(f"AI request failed: {e}")

def run_command(cmd: str) -> int:
    # Simple approach that works everywhere
    return subprocess.call(cmd, shell=True)

def only_cmd_from_prompt(prompt: str) -> str:
    return query_gemini(prompt)

def write_command_to_terminal(cmd: str):
    """Write command to terminal history/readline buffer so user can just press Enter"""
    try:
        # On Windows (PowerShell/CMD)
        if os.name == 'nt':
            # For Windows, we'll use a different approach
            # Create a temporary batch file that the user can execute
            temp_file = pathlib.Path.cwd() / "akscmd_temp.bat"
            with open(temp_file, 'w') as f:
                f.write(f"@echo off\n{cmd}\n")
            print(f"\n[akscmd] Command saved to {temp_file}")
            print(f"Run: .\\akscmd_temp.bat")
            return
            
        # On Unix-like systems, try to use readline if available
        try:
            import readline
            readline.clear_history()
            readline.add_history(cmd)
            print(f"\n[akscmd] Command added to history. Press ↑ and Enter to execute:")
            print(f"→ {cmd}")
        except ImportError:
            # Fallback: just print the command
            print(f"\n[akscmd] Copy and paste this command:")
            print(f"→ {cmd}")
            
    except Exception as e:
        # Fallback: just print the command
        print(f"\n[akscmd] Copy and paste this command:")
        print(f"→ {cmd}")

def install_hook(shell: Optional[str] = None):
    home = pathlib.Path.home()
    conf_dir = home / ".akscmd"
    conf_dir.mkdir(exist_ok=True)
    
    # Create a simple hook script
    hook_content = '''
# akscmd hook - allows <command> syntax
function akscmd_hook() {
    local input="$1"
    if [[ "$input" =~ ^akscmd[[:space:]] ]]; then
        eval "$input"
    else
        echo "Command not found: $input"
        return 127
    fi
}

# Override command_not_found_handle for bash
if [[ -n "$BASH_VERSION" ]]; then
    function command_not_found_handle() {
        if [[ "$1" =~ ^\<.*\>$ ]]; then
            local prompt="${1:1:-1}"  # Remove < >
            akscmd "$prompt" --interactive
            return $?
        fi
        echo "bash: $1: command not found"
        return 127
    }
fi

# Override command_not_found_handler for zsh
if [[ -n "$ZSH_VERSION" ]]; then
    function command_not_found_handler() {
        if [[ "$1" =~ '^<.*>$' ]]; then
            local prompt="${1:1:-1}"  # Remove < >
            akscmd "$prompt" --interactive
            return $?
        fi
        echo "zsh: command not found: $1"
        return 127
    }
fi
'''

    # Detect shell if not provided
    if not shell:
        shell = os.environ.get("SHELL", "")
        if shell.endswith("zsh"):
            shell = "zsh"
        elif shell.endswith("bash"):
            shell = "bash"
        else:
            shell = "bash"  # default

    # Write hook script
    hook_path = conf_dir / "hooks.sh"
    hook_path.write_text(hook_content)

    if shell == "zsh":
        rc = home / ".zshrc"
        line = '[[ -f ~/.akscmd/hooks.sh ]] && source ~/.akscmd/hooks.sh  # akscmd'
    else:
        rc = home / ".bashrc"
        line = '[[ -f ~/.akscmd/hooks.sh ]] && source ~/.akscmd/hooks.sh  # akscmd'

    rc_text = rc.read_text() if rc.exists() else ""
    if "source ~/.akscmd/hooks.sh" not in rc_text:
        with rc.open("a") as f:
            f.write("\n" + line + "\n")
    print(f"[akscmd] Hook installed for {shell}. Restart your shell.")

def uninstall_hook():
    home = pathlib.Path.home()
    hook_path = home / ".akscmd" / "hooks.sh"
    if hook_path.exists():
        hook_path.unlink()
    for rc_name in (".bashrc", ".zshrc"):
        rc = home / rc_name
        if rc.exists():
            txt = rc.read_text()
            new = re.sub(r"\n?\[\[ -f ~/.akscmd/hooks\.sh \]\] && source ~/.akscmd/hooks\.sh  # akscmd\n?", "", txt)
            if new != txt:
                rc.write_text(new)
    print("[akscmd] Hook uninstalled. Restart your shell.")

def main():
    # Check if the first argument is a known subcommand
    known_subcommands = {"install-hook", "uninstall-hook", "only-cmd"}
    
    # If first arg is not a subcommand, parse normally
    # If it is a subcommand, use subparsers
    if len(sys.argv) > 1 and sys.argv[1] in known_subcommands:
        # Use subcommand parsing
        parser = argparse.ArgumentParser(
            prog="akscmd",
            description="Natural language → shell command via AI",
        )
        
        sub = parser.add_subparsers(dest="sub")
        
        sub.add_parser("install-hook", help="Install Bash/Zsh <...> Enter interception")
        sub.add_parser("uninstall-hook", help="Remove shell hook")
        
        p_only = sub.add_parser("only-cmd", help="Print only the shell command")
        p_only.add_argument("prompt", nargs='+', help="Natural language prompt")
        
        args = parser.parse_args()
        
        # Handle --owner flag
        if args.owner:
            print("Amit Kumar Singh Developed me on 22th August 2025 he is my owner you can contact him over mail as aksmlibts@gmail.com")
            return
        
        if args.sub == "install-hook":
            install_hook()
            return
        if args.sub == "uninstall-hook":
            uninstall_hook()
            return
        if args.sub == "only-cmd":
            prompt = ' '.join(args.prompt)
            print(only_cmd_from_prompt(prompt))
            return
    else:
        # Use main command parsing
        parser = argparse.ArgumentParser(
            prog="akscmd",
            description="Natural language → shell command via AI",
        )
        parser.add_argument(
            "prompt",
            nargs="*",
            help="Natural language prompt (e.g. 'create a folder named apple')",
        )
        parser.add_argument(
            "--yes", action="store_true", help="Execute without confirmation"
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="Show command only"
        )
        parser.add_argument(
            "--interactive", action="store_true", help="Put command in terminal for easy execution"
        )
        parser.add_argument(
            "--owner", action="store_true", help="Show developer information"
        )
        
        args = parser.parse_args()
        
        # Handle --owner flag first
        if args.owner:
            print("Amit Kumar Singh Developed me on 22th August 2025 he is my owner you can contact him over mail as aksmlibts@gmail.com")
            return
            
        # --- default run mode ---
        if args.prompt:
            # Join all prompt words into a single string
            prompt = ' '.join(args.prompt).strip()
            
            # Remove < > if included (for backward compatibility)
            if prompt.startswith("<") and prompt.endswith(">"):
                prompt = prompt[1:-1]

            cmd = only_cmd_from_prompt(prompt)
            print(f"→ {cmd}")
            
            if args.dry_run:
                return
                
            if args.interactive:
                write_command_to_terminal(cmd)
                return
                
            if not args.yes:
                # Instead of just asking for confirmation, put the command in terminal
                print(f"\n[akscmd] Press Enter to execute, or Ctrl+C to cancel")
                try:
                    input()  # Wait for Enter
                    run_command(cmd)
                except KeyboardInterrupt:
                    print("\n[akscmd] Aborted.")
                    return
            else:
                run_command(cmd)
        else:
            parser.print_help()

