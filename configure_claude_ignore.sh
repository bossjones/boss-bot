#!/bin/bash

# Dry-run flag
DRY_RUN=true

# Read .gitignore and add each non-comment pattern to Claude Code's ignorePatterns
while IFS= read -r line || [[ -n "$line" ]]; do
    # Skip comments and empty lines
    if [[ "$line" =~ ^\s*# || -z "$line" ]]; then
        continue
    fi

    # Trim leading/trailing whitespace and remove escaping backslashes
    pattern=$(echo "$line" | sed 's/^[ \t]*//;s/[ \t]*$//' | tr -d '\\')

    # Skip negated patterns (Claude Code doesn't support them)
    if [[ "$pattern" =~ ^! ]]; then
        continue
    fi

    # Dry-run: echo the pattern
    if $DRY_RUN; then
        echo "Dry-run: Would add pattern '$pattern' to Claude configuration"
        echo "[cmd] claude config add ignorePatterns \"$pattern\""
    else
        # Add pattern to Claude configuration
        claude config add ignorePatterns "$pattern"
    fi
done < .gitignore

# Instructions for toggling dry-run mode:
echo "To disable dry-run mode, set DRY_RUN=false at the top of the script."
