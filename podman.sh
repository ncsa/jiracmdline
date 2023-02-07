#!/usr/bin/bash

# Start the web container via podman on RHEL8

DEBUG=1
REGISTRY=docker.io
REPO=andylytical/jiracmdline

function latest_tag {
  [[ "$DEBUG" -eq 1 ]] && set -x
  local _page=1
  local _pagesize=100
  local _baseurl=https://registry.hub.docker.com/v2/repositories

  curl -L -s "${_baseurl}/${REPO}/tags?page=${_page}&page_size=${_pagesize}" \
  | jq '."results"[]["name"]' \
  | sed -e 's/"//g' \
  | sort -r \
  | head -1
}

[[ "$DEBUG" -eq 1 ]] && set -x

tag=$(latest_tag)

podman run --rm -it --pull always \
--publish 8000:8000 \
--mount type=bind,source=/var/www/html,destination=/mnt/static_web_files \
-e JIRA_SERVER=jira.ncsa.illinois.edu \
-e JIRA_PROJECT=SVCPLAN \
$REGISTRY/$REPO:$tag
