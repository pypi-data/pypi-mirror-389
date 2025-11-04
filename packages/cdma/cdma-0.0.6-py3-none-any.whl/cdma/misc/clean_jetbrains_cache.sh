#!/bin/bash

# Directories to clean
dirs=("$HOME/.local/share/JetBrains/" "$HOME/.cache/JetBrains/" "$HOME/.config/JetBrains/")

for dir in "${dirs[@]}"; do
    rm -rf "$dir/$pattern"
done

echo "JetBrains cache, config, and data folders cleaned. You will be prompted download a new IDE backend the next time you log into remote development."
