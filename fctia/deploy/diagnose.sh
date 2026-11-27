#!/usr/bin/env bash
# Read-only diagnostic; no installs, credentials, or network calls.
set -u
echo '=== FCT.IA Office: diagnóstico ==='
for tool in node pnpm npm git python3 docker psql rustc cargo; do
  if command -v "$tool" >/dev/null 2>&1; then
    printf '%s: ' "$tool"
    "$tool" --version 2>/dev/null | head -n 1
  else
    printf '%s: indisponível\n' "$tool"
  fi
done
if command -v docker >/dev/null 2>&1; then
  docker compose version 2>/dev/null || true
  if timeout 5 docker info --format '{{.ServerVersion}}' >/dev/null 2>&1; then
    echo 'Docker daemon: acessível (não implica autorização de implantação)'
  else
    echo 'Docker daemon: inacessível ou não verificado'
  fi
fi
if command -v ss >/dev/null 2>&1; then
  for port in 3100 3101 5432; do
    if ss -H -ltn "sport = :$port" | grep -q .; then
      echo "TCP $port: em uso"
    else
      echo "TCP $port: nenhum listener observado"
    fi
  done
fi
echo '=== Diagnóstico concluído; nenhuma alteração realizada ==='
