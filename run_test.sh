#!/usr/bin/env bash
BASEDIR=$(dirname "$0")
export PYTHONPATH=$BASEDIR:$PYTHONPATH
python3 -m unittest discover ./tests -v

