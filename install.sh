#!/usr/bin/env bash
#
# Installer pdf-print-ready dans Claude Code et/ou Cursor.
#
# Usage : ./install.sh [claude|cursor|both]
# Défaut : both (les deux s'ils sont détectés)
#
set -euo pipefail

REPO_URL="https://raw.githubusercontent.com/uccellolabs/pdf-print-ready/main"
TARGET="${1:-both}"

install_for() {
  local kind="$1"
  local dir
  case "$kind" in
    claude) dir="$HOME/.claude/skills/pdf-print-ready" ;;
    cursor) dir="$HOME/.cursor/skills/pdf-print-ready" ;;
    *) echo "❌ Cible inconnue : $kind"; exit 1 ;;
  esac

  mkdir -p "$dir/references" "$dir/scripts"
  curl -fsSL "$REPO_URL/SKILL.md" -o "$dir/SKILL.md"
  curl -fsSL "$REPO_URL/references/template.html" -o "$dir/references/template.html" 2>/dev/null || true
  curl -fsSL "$REPO_URL/scripts/rendre_pdf.py" -o "$dir/scripts/rendre_pdf.py" 2>/dev/null && chmod +x "$dir/scripts/rendre_pdf.py" || true

  echo "✅ $kind : skill installé dans $dir"
}

case "$TARGET" in
  claude) install_for claude ;;
  cursor) install_for cursor ;;
  both)
    [ -d "$HOME/.claude" ] && install_for claude || echo "⚠️  Claude Code non détecté (~/.claude absent), skip."
    [ -d "$HOME/.cursor" ] && install_for cursor || echo "⚠️  Cursor non détecté (~/.cursor absent), skip."
    ;;
  *) echo "Usage : $0 [claude|cursor|both]"; exit 1 ;;
esac

echo ""
echo "🎉 Installation terminée. Lance Claude Code ou Cursor et tape /pdf-print-ready pour démarrer."
