#!/usr/bin/env bash
# Cron alternative to the GitHub Actions workflow: refresh the brief on the
# box that runs the scraper. Example crontab (07:10 Tashkent, after the
# 01:00 local scrape):
#   10 7 * * * /opt/brief/run_daily.sh >> /var/log/brief-refresh.log 2>&1
#
# Requires:
#   SUPABASE_DB_URL  Postgres connection string (export it in the cron env
#                    or an .env file next to this script; never hardcode it)
#   UYBOR_TABLE      optional, defaults to uybor_listings_v2
#   PUBLISH_DIR      optional; if set, the refreshed HTML is copied there
#                    (e.g. an nginx webroot)
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PY="$REPO_DIR/.venv/bin/python"
OUT="$REPO_DIR/tashkent_demand_brief.html"

# Optional .env (chmod 600, owned by the cron user) for the DB URL.
if [[ -f "$REPO_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$REPO_DIR/.env"
  set +a
fi

if [[ -z "${SUPABASE_DB_URL:-}" ]]; then
  echo "$(date -u +%FT%TZ) FATAL: SUPABASE_DB_URL is not set" >&2
  exit 1
fi

if [[ ! -x "$VENV_PY" ]]; then
  echo "$(date -u +%FT%TZ) creating venv..."
  python3 -m venv "$REPO_DIR/.venv"
  "$VENV_PY" -m pip install --quiet -r "$REPO_DIR/requirements.txt"
fi

echo "$(date -u +%FT%TZ) refreshing brief..."
"$VENV_PY" "$REPO_DIR/refresh_brief.py" \
  --template "$REPO_DIR/tashkent_demand_brief.template.html" \
  --out "$OUT"

if [[ -n "${PUBLISH_DIR:-}" ]]; then
  install -m 644 "$OUT" "$PUBLISH_DIR/tashkent_demand_brief.html"
  install -m 644 "$OUT" "$PUBLISH_DIR/index.html"
  echo "$(date -u +%FT%TZ) published to $PUBLISH_DIR"
fi

echo "$(date -u +%FT%TZ) done."
