DEBUG=1
REGISTRY=ghcr.io
REPO=ncsa/jiracmdline

[[ "$DEBUG" -eq 1 ]] && set -x

tag=production
tag=latest

# -p 5000:5000 \
docker run -it --pull always \
--mount type=bind,src=$HOME,dst=/home \
-e JIRA_SERVER=jira.ncsa.illinois.edu \
-e JIRA_PROJECT=SVCPLAN \
--entrypoint "/bin/bash" \
$REGISTRY/$REPO:$tag
