DEBUG=1
REGISTRY=ghcr.io
REPO=ncsa/jiracmdline

function latest_tag {
  [[ "$DEBUG" -eq 1 ]] && set -x
  echo "production"
}

[[ "$DEBUG" -eq 1 ]] && set -x

tag=$(latest_tag)

docker run -it --pull always \
--mount type=bind,src=$HOME,dst=/home \
-e JIRA_SERVER=jira.ncsa.illinois.edu \
-e JIRA_PROJECT=SVCPLAN \
--entrypoint "/bin/bash" \
$REGISTRY/$REPO:$tag
