#!/usr/bin/env bash
# Install BS/BSP/BUC skills to ~/.cursor (user-level) and optional project .cursor/
set -euo pipefail

SOURCE_ROOT="$(cd "$(dirname "$0")" && pwd)"
FORCE=0
PROJECT_ROOT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) FORCE=1; shift ;;
    --project) PROJECT_ROOT="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

SKILL_IDS=(bsp-orchestrator buc-orchestrator code-review coder bsp-large-system)
COMMAND_FILES=(bs.md bsp.md buc.md code-review.md coder.md)

install_to() {
  local skills_root="$1"
  local commands_root="$2"
  mkdir -p "$commands_root"

  for id in "${SKILL_IDS[@]}"; do
    mkdir -p "$skills_root/$id"
    local skill_dest="$skills_root/$id/SKILL.md"
    if [[ "$FORCE" -eq 1 || ! -f "$skill_dest" ]]; then
      cp -f "$SOURCE_ROOT/$id/SKILL.md" "$skill_dest"
      echo "[OK] Skill -> $skill_dest"
    else
      echo "[SKIP] Skill exists (use --force): $skill_dest"
    fi
  done

  for cmd in "${COMMAND_FILES[@]}"; do
    local cmd_dest="$commands_root/$cmd"
    if [[ "$FORCE" -eq 1 || ! -f "$cmd_dest" ]]; then
      cp -f "$SOURCE_ROOT/commands/$cmd" "$cmd_dest"
      echo "[OK] Command -> $cmd_dest"
    else
      echo "[SKIP] Command exists (use --force): $cmd_dest"
    fi
  done
}

echo "BS/BSP/BUC Skills install from: $SOURCE_ROOT"
install_to "$HOME/.cursor/skills" "$HOME/.cursor/commands"

if [[ -n "$PROJECT_ROOT" ]]; then
  echo ""
  echo "Project install: $PROJECT_ROOT"
  install_to "$PROJECT_ROOT/.cursor/skills" "$PROJECT_ROOT/.cursor/commands"
fi

echo ""
echo "Done. Restart Cursor (or new Agent session)."
echo "Shortcuts: /bs  /bsp  /buc  /code-review  /coder"
