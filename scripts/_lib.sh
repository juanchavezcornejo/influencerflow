#!/usr/bin/env bash
# Shared helpers sourced by every scripts/*.sh.
# Sets strict mode, resolves repo root, provides logging helpers.

set -euo pipefail

# Repo root (parent of scripts/). Works regardless of CWD.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export REPO_ROOT

# Colors (disabled if not a TTY or NO_COLOR is set).
if [[ -t 1 ]] && [[ -z "${NO_COLOR:-}" ]]; then
  C_RESET=$'\033[0m'
  C_BOLD=$'\033[1m'
  C_DIM=$'\033[2m'
  C_RED=$'\033[31m'
  C_GREEN=$'\033[32m'
  C_YELLOW=$'\033[33m'
  C_BLUE=$'\033[34m'
else
  C_RESET=""; C_BOLD=""; C_DIM=""; C_RED=""; C_GREEN=""; C_YELLOW=""; C_BLUE=""
fi

log()  { printf "%s▸ %s%s\n" "$C_BLUE" "$*" "$C_RESET"; }
ok()   { printf "%s✓ %s%s\n" "$C_GREEN" "$*" "$C_RESET"; }
warn() { printf "%s! %s%s\n" "$C_YELLOW" "$*" "$C_RESET" >&2; }
die()  { printf "%s✗ %s%s\n" "$C_RED" "$*" "$C_RESET" >&2; exit 1; }

have() { command -v "$1" >/dev/null 2>&1; }

require() {
  for cmd in "$@"; do
    have "$cmd" || die "Missing required command: $cmd"
  done
}

# Run a labeled step; on failure, abort with the step name.
step() {
  local label="$1"; shift
  log "$label"
  "$@" || die "Failed: $label"
}

cd "$REPO_ROOT"

prompt_for_input() {
  local var_name=$1
  local prompt_text=$2
  local default=$3
  local is_secret=${4:-false}

  local value
  if [[ "$is_secret" == "true" ]]; then
    read -sp "$prompt_text [hidden]: " value
    echo
  else
    if [[ -n "$default" ]]; then
      read -p "$prompt_text [$default]: " value
      value="${value:-$default}"
    else
      read -p "$prompt_text: " value
    fi
  fi

  if [[ -z "$value" ]]; then
    die "Input required: $var_name"
  fi

  echo "$value"
}

write_env_file() {
  local env_file=$1
  local -A vars=()

  # Shift args and process key=value pairs
  shift
  while [[ $# -gt 0 ]]; do
    local key="${1%=*}"
    local value="${1#*=}"
    vars["$key"]="$value"
    shift
  done

  # Read existing .env, update vars, write back
  if [[ -f "$env_file" ]]; then
    local temp_file="${env_file}.tmp"
    > "$temp_file"

    while IFS= read -r line; do
      if [[ -z "$line" || "$line" =~ ^# ]]; then
        echo "$line" >> "$temp_file"
      else
        local key="${line%=*}"
        if [[ -n "${vars[$key]:-}" ]]; then
          echo "${key}=${vars[$key]}" >> "$temp_file"
          unset "vars[$key]"
        else
          echo "$line" >> "$temp_file"
        fi
      fi
    done < "$env_file"

    # Append any remaining new vars
    for key in "${!vars[@]}"; do
      echo "${key}=${vars[$key]}" >> "$temp_file"
    done

    mv "$temp_file" "$env_file"
  fi
}

validate_api_key_format() {
  local key=$1
  local pattern=$2
  if [[ ! "$key" =~ $pattern ]]; then
    return 1
  fi
  return 0
}

generate_nextauth_secret() {
  openssl rand -base64 32
}
