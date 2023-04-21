#!/usr/bin/bash

# Useful script for testing local cmdline builds
# SYNOPSIS:
# alias p3='docker run --rm -it --mount type=bind,src=$HOME,dst=/home python:3 bash'
# p3
# ./test.sh

if [[ -z "$JIRA_SERVER" ]] ; then
  export JIRA_SERVER=jira.ncsa.illinois.edu
  export JIRA_PROJECT=SVCPLAN
  cp /home/.netrc /root/.netrc
fi

cd /home/working/jiracmdline/jiracmdline
python lost_children.py -d

