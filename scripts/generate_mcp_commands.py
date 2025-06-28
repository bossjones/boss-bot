#!/usr/bin/env python3
"""
Script to generate Claude MCP add commands from a repos.txt file.

Reads GitHub repository URLs from repos.txt and outputs corresponding
claude mcp add commands for each repository.
"""

import sys
from pathlib import Path


def extract_repo_info(github_url: str) -> tuple[str, str] | None:
    """Extract owner and repo name from GitHub URL."""
    if not github_url.startswith("https://github.com/"):
        return None

    # Remove the base URL and split the path
    path = github_url.replace("https://github.com/", "").strip()
    parts = path.split("/")

    if len(parts) != 2:
        return None

    owner, repo = parts
    return owner, repo


def generate_mcp_command(owner: str, repo: str) -> str:
    """Generate the claude mcp add command for a repository."""
    server_name = f"mcp-server-{repo}"
    gitmcp_url = f"https://gitmcp.io/{owner}/{repo}"

    return f"claude mcp add {server_name} -- npx -y mcp-remote@v0.1.9 {gitmcp_url}"


def main():
    """Main function to process repos.txt and generate MCP commands."""
    # Look for repos.txt in the same directory as this script
    script_dir = Path(__file__).parent
    repos_file = script_dir / "repos.txt"

    if not repos_file.exists():
        print(f"Error: {repos_file} not found", file=sys.stderr)
        sys.exit(1)

    try:
        with open(repos_file) as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            repo_info = extract_repo_info(line)
            if repo_info is None:
                print(f"Warning: Skipping invalid URL: {line}", file=sys.stderr)
                continue

            owner, repo = repo_info
            command = generate_mcp_command(owner, repo)
            print(command)

    except Exception as e:
        print(f"Error reading {repos_file}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
