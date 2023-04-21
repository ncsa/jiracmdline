#!/usr/bin/bash

# Start the web container via podman on RHEL8

DEBUG=1
REGISTRY=ghcr.io
REPO=ncsa/jiracmdline

tag=production

podman run --rm -it --pull always \
--publish 8000:8000 \
--mount type=bind,source=/var/www/html,destination=/mnt/static_web_files \
-e JIRA_SERVER=jira.ncsa.illinois.edu \
-e JIRA_PROJECT=SVCPLAN \
$REGISTRY/$REPO:$tag
