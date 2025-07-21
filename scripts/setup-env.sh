#!/bin/bash
set -eu -o pipefail
# Set up the dev server environment. Uses the convention template's ensure_env.sh
# script so that we're all on the same page.

PROJECT_DIR=$(cd $(dirname "$0")/.. && pwd)
cd "$PROJECT_DIR"

${PROJECT_DIR}/convention-template/scripts/ensure_env.sh
