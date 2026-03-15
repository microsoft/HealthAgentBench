#!/usr/bin/env bash
# Install the Codex CLI inside the running Harbor task container using the same
# steps Harbor's installed-agent template uses.
set -euo pipefail
source "$(dirname "$0")/common.sh"

hb::setup_task_env
hb::require_running_main

: "${HB_CODEX_NVM_VERSION:=v0.40.2}"
: "${HB_CODEX_NODE_VERSION:=22}"
: "${HB_CODEX_PACKAGE:=@openai/codex@latest}"

if hb::compose exec "${HB_MAIN_SERVICE}" bash -lc '. "$HOME/.nvm/nvm.sh" >/dev/null 2>&1 || true; command -v codex >/dev/null 2>&1'; then
  echo "Codex already installed in the running container."
  hb::compose exec "${HB_MAIN_SERVICE}" bash -lc '. "$HOME/.nvm/nvm.sh" >/dev/null 2>&1 || true; codex --version'
  exit 0
fi

hb::compose exec "${HB_MAIN_SERVICE}" bash -lc "
set -euo pipefail
apt-get update
apt-get install -y curl
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/${HB_CODEX_NVM_VERSION}/install.sh | bash
export NVM_DIR=\"\$HOME/.nvm\"
. \"\$NVM_DIR/nvm.sh\" || true
command -v nvm >/dev/null 2>&1 || { echo 'Error: NVM failed to load' >&2; exit 1; }
nvm install ${HB_CODEX_NODE_VERSION}
npm -v
npm install -g ${HB_CODEX_PACKAGE}
codex --version
"
