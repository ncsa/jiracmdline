#!/bin/bash

export NETRC=/home/.ssh/netrc

[[ -f /tmp/firstrun ]] || {
  pip install --upgrade pip
  pip install -r requirements.txt
  ln -s "$NETRC" ~/.netrc
  apt update && apt -y install vim less
  touch /tmp/firstrun
}
