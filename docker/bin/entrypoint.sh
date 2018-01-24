#!/bin/bash
set -e

eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
source /root/.pyenv/completions/pyenv.bash

pip install tox

exec $@

