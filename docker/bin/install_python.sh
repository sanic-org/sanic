#!/bin/bash
set -e

export CFLAGS='-O2'
export EXTRA_CFLAGS="-DTHREAD_STACK_SIZE=0x100000"

curl -L https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer | bash
eval "$(pyenv init -)"

for ver in $@
do
    pyenv install $ver
done

pyenv global $@
pip install --upgrade pip
pyenv rehash
