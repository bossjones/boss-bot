#!/usr/bin/env python3

"""
This script generates a YAML file containing contributor information for a given GitHub repository.
It uses the GitHub CLI to fetch contributor data and formats it into a structured YAML file.

Usage:

uv run python scripts/docs/people.py --repo bossjones/boss-bot --output docs/people.yml
"""

import argparse
import json
import os
import subprocess
from typing import Any, Dict, List

import yaml


def get_contributors_gh_cli(repo_name: str) -> list[dict[str, Any]]:
    """
    Get contributors using GitHub CLI
    """
    try:
        result = subprocess.run(
            ['gh', 'api', f'repos/{repo_name}/contributors', '--paginate'],
            capture_output=True,
            text=True,
            check=True
        )

        # Combine paginated results
        contributors: list[dict[str, Any]] = []
        for line in result.stdout.split('\n'):
            if line.strip():
                contributors.extend(json.loads(line))

        return contributors
    except subprocess.CalledProcessError as e:
        print(f"GitHub CLI error: {e.stderr}")
        exit(1)
    except json.JSONDecodeError:
        print("Error decoding GitHub CLI response")
        exit(1)

def format_contributors(contributors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    formatted: list[dict[str, Any]] = []
    for c in contributors:
        formatted.append({
            'login': c['login'],
            'count': c['contributions'],
            'avatarUrl': c['avatar_url'],
            'url': c['html_url']
        })
    return sorted(formatted, key=lambda x: x['count'], reverse=True)

def generate_yaml(contributors: list[dict[str, Any]], output_file: str) -> None:
    with open(output_file, 'w') as f:
        for c in contributors:
            yaml.dump([c], f, default_flow_style=False, sort_keys=False)

def main() -> None:
    parser = argparse.ArgumentParser(description='Generate contributors YAML using GitHub CLI')
    parser.add_argument('--repo', required=True, help='owner/repo format')
    parser.add_argument('--output', default='people.yml', help='Output YAML file')
    args = parser.parse_args()

    contributors = get_contributors_gh_cli(args.repo)
    formatted = format_contributors(contributors)
    generate_yaml(formatted, args.output)
    print(f"Generated {len(formatted)} contributors in {args.output}")

if __name__ == '__main__':
    main()
