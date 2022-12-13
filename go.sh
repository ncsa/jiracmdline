DEBUG=0
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

docker run --rm -it --pull always \
--mount type=bind,src=$HOME,dst=/home \
-e JIRA_SERVER=jira.ncsa.illinois.edu \
-e JIRA_DEFAULT_PROJECT=SVCPLAN \
$REPO:$tag
