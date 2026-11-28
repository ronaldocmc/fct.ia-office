#!/usr/bin/env bash
# Install this wrapper outside the checkout, owned by the host administrator.
# The dedicated deployment user's authorized_keys must force this command.
set -euo pipefail
umask 077
export PATH=/usr/local/bin:/usr/bin:/bin
unset BASH_ENV ENV CDPATH GIT_DIR GIT_WORK_TREE GIT_CONFIG_COUNT
command_text="${SSH_ORIGINAL_COMMAND:-}"
[[ "$command_text" =~ ^deploy-office\ ([a-f0-9]{40})$ ]] || { echo "Command denied" >&2; exit 1; }
revision="${BASH_REMATCH[1]}"
repo="$HOME/fctia-office"
exec 9>"$HOME/.fctia-office-deploy.lock"
flock -n 9 || { echo "Deployment in progress" >&2; exit 1; }
cd "$repo"
test "$(git remote get-url origin)" = "https://github.com/ronaldocmc/fct.ia-office.git"
test "$(git branch --show-current)" = "develop/fctia-v0.1"
test -z "$(git status --porcelain)" || { echo "Dirty checkout; aborting." >&2; exit 1; }
git fetch --no-tags origin refs/heads/develop/fctia-v0.1:refs/remotes/origin/develop/fctia-v0.1
# Only deploy the current protected branch head; reject old or unrelated revisions.
test "$(git rev-parse refs/remotes/origin/develop/fctia-v0.1)" = "$revision"
git merge --ff-only "$revision"
test "$(git rev-parse HEAD)" = "$revision"
bash fctia/deploy/install-private.sh
