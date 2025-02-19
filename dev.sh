DEBUG=1

[[ "$DEBUG" -eq 1 ]] && set -x

DOCKER=/usr/bin/docker
PATH=jiracmdline
IMGNAME=jiracmdline
TAG=dev

${DOCKER} buildx build \
  -f ${PATH}/Dockerfile.dev \
  -t "${IMGNAME}:${TAG}" \
  ${PATH}

${DOCKER} run -it \
--mount type=bind,src=$HOME,dst=/home \
-e JIRA_SERVER=jira.ncsa.illinois.edu \
-e JIRA_PROJECT=SVCPLAN \
-p 5000:5000 \
--entrypoint "/bin/bash" \
${IMGNAME}:${TAG}
