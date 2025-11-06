#!/usr/bin/env python3
import os
import sys
import subprocess
import requests
from datetime import datetime
import argparse

API_URL = "https://your-laravel-domain.com/api/report-pull"


def get_git_info():
    try:
        repo_name = os.path.basename(
            subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).strip().decode()
        )
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip().decode()
        user_email = subprocess.check_output(["git", "config", "user.email"]).strip().decode()
        return {"repo_name": repo_name, "branch": branch, "user_email": user_email}
    except subprocess.CalledProcessError:
        return None


def report_pull():
    info = get_git_info()
    if not info:
        print("❌ Not a git repository.")
        return

    payload = {**info, "timestamp": datetime.utcnow().isoformat()}
    try:
        res = requests.post(API_URL, json=payload, timeout=5)
        if res.status_code == 200:
            print("✅ Git pull event reported successfully!")
        else:
            print(f"⚠️ Server error {res.status_code}: {res.text}")
    except Exception as e:
        print(f"❌ Network error: {e}")


def setup_hook(force=False):
    """Install or update the post-merge hook automatically."""
    try:
        repo_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"]
        ).strip().decode()
    except subprocess.CalledProcessError:
        print("❌ Not a git repository. Run this inside a project with Git initialized.")
        return

    hooks_dir = os.path.join(repo_root, ".git", "hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    hook_path = os.path.join(hooks_dir, "post-merge")

    hook_line = "gitpulse\n"

    # ✅ Handle --force reinstall
    if force and os.path.exists(hook_path):
        os.remove(hook_path)
        print("♻️  Old post-merge hook removed (forced reinstall).")

    installed = False
    if os.path.exists(hook_path):
        with open(hook_path, "r") as f:
            content = f.read()
        if "gitpulse" in content:
            print("✅ GitPulse hook already installed — nothing to do.")
            installed = True
        else:
            with open(hook_path, "a") as f:
                f.write(f"\n# Added by GitPulse\n{hook_line}")
            print("🔁 GitPulse hook appended to existing post-merge file.")
    else:
        with open(hook_path, "w") as f:
            f.write("#!/bin/sh\n")
            f.write("# Git post-merge hook — automatically reports pulls\n")
            f.write(hook_line)
        print("✅ New GitPulse hook installed!")

    try:
        os.chmod(hook_path, 0o755)
    except Exception:
        pass

    if not installed:
        print(f"📍 Hook location: {hook_path}")
    print("🚀 Every `git pull` will now trigger a GitPulse report automatically.")


def main():
    parser = argparse.ArgumentParser(
        prog="gitpulse",
        description="GitPulse CLI — automatically report git pulls to your Laravel backend."
    )
    subparsers = parser.add_subparsers(dest="command")

    # `setup` command
    setup_parser = subparsers.add_parser("setup", help="Install the Git post-merge hook.")
    setup_parser.add_argument("--force", action="store_true", help="Force reinstall the GitPulse hook.")

    # Default command (report pull)
    subparsers.add_parser("run", help="Send a pull event (automatically called by Git hook).")

    args = parser.parse_args()

    if args.command == "setup":
        setup_hook(force=args.force)
    elif args.command == "run" or args.command is None:
        report_pull()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
