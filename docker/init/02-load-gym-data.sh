#!/bin/bash
set -euo pipefail

# The analysis SQL uses paths relative to the repository root. The compose file
# mounts the SQL and analysis-ready data under /workspace for this first load.
cd /workspace
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -f sql/analysis_ready_schema.sql
