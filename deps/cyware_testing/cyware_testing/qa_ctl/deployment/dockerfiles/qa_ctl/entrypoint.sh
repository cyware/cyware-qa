#!/bin/bash

BRANCH="$1"
CONFIG_FILE_PATH="$2"
EXTRA_ARGS="${@:3}"

# Download the custom branch of cyware-qa repository
curl -Ls https://github.com/cyware/cyware-qa/archive/${BRANCH}.tar.gz | tar zx &> /dev/null && mv cyware-* cyware-qa

# Install python dependencies not installed from
python3 -m pip install -r cyware-qa/requirements.txt &> /dev/null

# Install Cyware QA framework
cd cyware-qa/deps/cyware_testing &> /dev/null
python3 setup.py install &> /dev/null

# Run qa-ctl tool
/usr/local/bin/qa-ctl -c /cyware_qa_ctl/${CONFIG_FILE_PATH} ${EXTRA_ARGS}
