#!/bin/bash
# Run one test scene against a throwaway copy of the project.
# usage: GODOT=/path/to/godot tests/run.sh tests/testerNN.gd [seconds]
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
G="${GODOT:-godot}"
TMP="$(mktemp -d)"
cp -r "$ROOT"/. "$TMP"/
rm -rf "$TMP/tools"
cp "$1" "$TMP/tester.gd"
sed -i.bak 's|^Audio="\*res://scripts/audio.gd"|Audio="*res://scripts/audio.gd"\nTester="*res://tester.gd"|' "$TMP/project.godot"
mkdir -p /tmp/sh /tmp/shx
"$G" --headless --path "$TMP" --import >/dev/null 2>&1 || true
timeout "${2:-300}" "$G" --path "$TMP" --audio-driver Dummy --fixed-fps 60
