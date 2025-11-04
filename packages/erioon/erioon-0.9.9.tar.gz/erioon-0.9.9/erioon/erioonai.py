# Copyright 2025-present Erioon, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Visit www.erioon.com/dev-docs for more info on the Erioon Python SDK.


"""
Erioon AI Chat Interface

This module provides an interactive terminal chat experience with Erioon AI.
After selecting “Erioon AI” in the CLI, users can communicate directly with
an AI endpoint in real time.

Usage:
    >>> from erioon.erioonai import chat_with_erioon_ai
    >>> chat_with_erioon_ai(user_id="123", project_id="abc")

Dependencies:
    - requests
    - colorama
"""

import requests
import sys
import os
import textwrap
from colorama import Fore, Style, init as color_init

color_init(autoreset=True)

def save_ai_file(file_structure):
    """
    Save or update a file with AI-provided content.

    Parameters:
        file_structure (dict): A dictionary containing:
            - path (str): Relative folder path where file should be saved.
            - filename (str): Name of the file.
            - content (str): The content to write into the file.

    Returns:
        str: Full path of the saved file.
    """
    path = file_structure.get("path", "")
    filename = file_structure.get("filename", "file.txt")
    content = file_structure.get("content", "")

    full_dir = os.path.join(os.getcwd(), path)
    full_path = os.path.join(full_dir, filename)

    os.makedirs(full_dir, exist_ok=True)

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

    return full_path


def get_context(max_file_size=1000*1024):
    """
    Retrieve the current directory structure and small file contents for context.

    Parameters:
        max_file_size (int, optional): Maximum bytes to read per file. Defaults to 1 MB.

    Returns:
        str: Formatted string of current directory, file list, and contents of small text/code files.
    """
    cwd = os.getcwd()
    files = os.listdir(cwd)

    context_lines = [f"Current directory: {cwd}", "Files and folders:"]
    for f in files:
        context_lines.append(f"- {f}")

    context_lines.append("\nFile contents:")
    for f in files:
        file_path = os.path.join(cwd, f)
        if os.path.isfile(file_path):
            try:
                if os.path.getsize(file_path) <= max_file_size and f.endswith(('.txt', '.py', '.md', '.json', '.yaml', '.yml')):
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        context_lines.append(f"\n--- {f} ---\n{content}\n--- end of {f} ---")
            except Exception:
                context_lines.append(f"\n--- {f} ---\n(Could not read file)\n--- end of {f} ---")

    return "\n".join(context_lines)


def print_ai_reply_box(text: str, max_width=80):
    """
    Display AI replies in a nicely formatted colored box with line wrapping.

    Parameters:
        text (str): The text to display in the box.
        max_width (int, optional): Maximum line width for wrapping text. Defaults to 80.
    """
    lines = []
    for paragraph in text.strip().split("\n"):
        wrapped = textwrap.wrap(paragraph, width=max_width)
        lines.extend(wrapped if wrapped else [""])

    width = max(len(line) for line in lines)
    border = f"{Fore.MAGENTA}{'─' * (width + 4)}{Style.RESET_ALL}"

    print(f"{Fore.MAGENTA}┌{border}┐{Style.RESET_ALL}")
    for line in lines:
        print(f"{Fore.MAGENTA}│{Style.RESET_ALL}  {line.ljust(width)}  {Fore.MAGENTA}│{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}└{border}┘{Style.RESET_ALL}\n")


def chat_with_erioon_ai(user_id: str, project_id: str):
    """
    Interactive terminal chat interface with Erioon AI.

    The user can chat in real-time with the AI, optionally providing local
    context (files, folders, and small file contents). AI responses may
    include instructions or code, which can be automatically saved to files.

    Parameters:
        user_id (str): The unique identifier of the user.
        project_id (str): The project identifier for the chat session.

    Notes:
        - Type 'exit' or 'quit' to leave the chat session.
        - If the AI returns a file structure, it will be saved automatically.
    """
    print(f"\n{Fore.CYAN}💬 Starting Erioon AI Chat Mode{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Type 'exit' or 'quit' to leave this session.{Style.RESET_ALL}\n")

    include_context = input(f"{Fore.YELLOW}Do you want me to access your context (files, folders, and content)? [y/N]: {Style.RESET_ALL}").strip().lower()
    use_context = include_context in ("y", "yes")

    api_url = "https://aiservice.erioon.com/cli_ai_chat"
    headers = {"Content-Type": "application/json"}
    history = []

    while True:
        try:
            user_input = input(f"{Fore.GREEN}You:{Style.RESET_ALL} ").strip()
            if user_input.lower() in ("exit", "quit"):
                print(f"\n{Fore.CYAN}👋 Exiting Erioon AI Chat. Goodbye!{Style.RESET_ALL}")
                break
            if not user_input:
                continue

            history.append({"role": "user", "content": user_input})
            context = get_context() if use_context else ""

            payload = {
                "user_id": user_id,
                "project_id": project_id,
                "message": user_input,
                "context": context
            }

            response = requests.post(api_url, json=payload, headers=headers, timeout=60)

            if response.status_code == 200:
                data = response.json()
                ai_reply = data.get("message") or "(No reply received.)"
            
                print(f"{Fore.MAGENTA}\nErioon AI:{Style.RESET_ALL}")
                print_ai_reply_box(ai_reply)
            
                file_structure = data.get("file")  
                if file_structure:
                    saved_path = save_ai_file(file_structure)
                    print(f"{Fore.CYAN}✅ File saved/updated at: {saved_path}{Style.RESET_ALL}")
            
                history.append({"role": "assistant", "content": ai_reply})

            elif response.status_code == 401:
                print(f"{Fore.RED}❌ Unauthorized. Please re-login using `erioon login`.{Style.RESET_ALL}")
                break
            else:
                print(f"{Fore.RED}❌ Error {response.status_code}:{Style.RESET_ALL} {response.text}")

        except KeyboardInterrupt:
            print(f"\n{Fore.CYAN}👋 Chat session terminated by user.{Style.RESET_ALL}")
            sys.exit(0)
        except requests.exceptions.ConnectionError:
            print(f"{Fore.RED}❌ Network error: Unable to connect to Erioon AI.{Style.RESET_ALL}")
            break
        except requests.exceptions.Timeout:
            print(f"{Fore.RED}⚠️  Request timed out. Please try again.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ Unexpected error:{Style.RESET_ALL} {e}")
            break
