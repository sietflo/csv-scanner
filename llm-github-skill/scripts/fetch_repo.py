#!/usr/bin/env python3
"""
Fetches a GitHub repo's file tree + contents via the REST API.
This is the deterministic 90% of the job — no LLM involved.
Prints a JSON object {path: content} to stdout.
"""
import argparse
import json
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}" if GITHUB_TOKEN else "",
    "Accept": "application/vnd.github.v3+json",
}
SKIP_EXT = (".png", ".jpg", ".jpeg", ".ico", ".zip", ".pdf", ".gif", ".woff", ".woff2")


def fetch_github_files(owner: str, repo: str, path: str = "", branch: str = "main") -> dict:
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"GitHub API error: {response.status_code} ({response.json().get('message')})", file=sys.stderr)
        return {}

    repo_data = {}
    for item in response.json():
        if item["name"] == ".git":
            continue
        if item["type"] == "dir":
            repo_data.update(fetch_github_files(owner, repo, item["path"], branch))
        else:
            if item.get("download_url") and not item["name"].lower().endswith(SKIP_EXT):
                file_response = requests.get(item["download_url"])
                repo_data[item["path"]] = (
                    file_response.text if file_response.status_code == 200 else "[failed to download]"
                )
            else:
                repo_data[item["path"]] = "[binary or skipped file]"
    return repo_data


def main():
    parser = argparse.ArgumentParser(description="Fetch a GitHub repo's structure and file contents")
    parser.add_argument("owner")
    parser.add_argument("repo")
    parser.add_argument("--branch", default="main")
    args = parser.parse_args()

    data = fetch_github_files(args.owner, args.repo, branch=args.branch)
    if not data:
        print(json.dumps({"error": "no data fetched, check owner/repo/branch/token"}))
        sys.exit(1)
    print(json.dumps(data, ensure_ascii=False))


if __name__ == "__main__":
    main()