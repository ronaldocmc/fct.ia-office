#!/usr/bin/env bash
# Run only in an authorized SSH session on the institutional host.
set -euo pipefail
umask 077
cd "$(dirname "$0")/../.."
command -v docker >/dev/null
command -v openssl >/dev/null
command -v curl >/dev/null
docker compose version >/dev/null
docker info >/dev/null
test "$(git branch --show-current)" = "develop/fctia-v0.1"
test -z "$(git status --porcelain)" || { echo "Working tree not clean; aborting." >&2; exit 1; }
config_dir="$HOME/.config/fctia-office"
mkdir -p "$config_dir"
chmod 700 "$config_dir"
envfile="$config_dir/office.env"
if [ ! -e "$envfile" ]; then
  (set -C; printf 'FCTIA_DB_PASSWORD=%s\nFCTIA_AUTH_SECRET=%s\nFCTIA_SIGNING_SECRET=%s\nFCTIA_PORT=3100\n' "$(openssl rand -hex 32)" "$(openssl rand -hex 32)" "$(openssl rand -hex 32)" > "$envfile")
fi
test -f "$envfile" && test ! -L "$envfile"
chmod 600 "$envfile"
# Do not source the secrets file as executable shell code.
port="$(sed -n 's/^FCTIA_PORT=//p' "$envfile")"
port="$(printf '%s' "$port" | tr -d '\r')"
[[ "$port" =~ ^[0-9]{4,5}$ ]] && (( port >= 1024 && port <= 65535 )) || { echo "Invalid configured port." >&2; exit 1; }
compose=(docker compose --project-name fctia-office --env-file "$envfile" -f fctia/deploy/compose.yml)
"${compose[@]}" config --quiet
# Docker will refuse a conflicting host port; never stop another project.
echo "Building isolated FCT.IA Office stack (PostgreSQL 17 + Paperclip)..."
"${compose[@]}" up -d --build
"${compose[@]}" ps
for attempt in $(seq 1 90); do
  if curl --fail --silent --max-time 5 "http://127.0.0.1:$port/api/ready" >/dev/null; then
    code="$(curl --silent --max-time 10 -o /dev/null -w '%{http_code}' "http://127.0.0.1:$port/api/companies")"
    case "$code" in
      401|403) echo "Paperclip ready; unauthenticated companies access blocked."; exit 0 ;;
      *) echo "Unexpected authentication status: $code. Keep private." >&2; exit 1 ;;
    esac
  fi
  sleep 5
done
echo "Readiness not confirmed. Stack remains private on loopback; inspect container status." >&2
exit 1
