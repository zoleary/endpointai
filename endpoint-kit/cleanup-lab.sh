#!/usr/bin/env bash
set -euo pipefail
LAB="${LAB_DIR:-$HOME/zsai-demo}"
case "$LAB" in "$HOME"/zsai-demo*) ;; *) echo "Refusing to delete $LAB"; exit 1;; esac
rm -rf "$LAB" && echo "Removed $LAB"
