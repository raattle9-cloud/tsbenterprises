#!/bin/bash
set -e 

# Use environment variable for token - DO NOT hardcode secrets!
GIT_REPO_URL="https://github.com/Mannan0313/TSBEnterprises.git"
PROJECT_MAIN_DIR_NAME="TSB"
git clone "$GIT_REPO_URL" "/home/ubuntu/$PROJECT_MAIN_DIR_NAME"
cd "/home/ubuntu/$PROJECT_MAIN_DIR_NAME"
# Install dependencies
chmod +x scripts/*.sh

./scripts/instance_os_dependencies.sh
./scripts/instance_python_dependencies.sh
./scripts/gunicorn.sh
./scripts/instance_nginx.sh
./scripts/start_app.sh
