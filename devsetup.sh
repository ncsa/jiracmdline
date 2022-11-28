#!/bin/bash

[[ -f /tmp/firstrun ]] || {
  apt update && apt -y install vim less
  touch /tmp/firstrun
}
