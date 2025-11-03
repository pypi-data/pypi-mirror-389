#!/bin/bash
set -e

BASEDIR=$(dirname $0)
pushd $BASEDIR
rm -fr dist/*
python test/test_module.py
python -m build
popd