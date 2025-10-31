#!/bin/bash
SCRIPTBASEDIR=$(dirname $(readlink -f $0))
export SCRIPTBASEDIR

source $SCRIPTBASEDIR/vault/secrets

rsync -av --exclude=".git" --exclude="*.pyc" --exclude="*.pyo" --exclude="*.pyclass" $SCRIPTBASEDIR/../../warmcat $USERHOST:
