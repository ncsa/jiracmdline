#!/bin/bash
set -eu

assert_var_is_set() {
  echo "assert_var_is_set: got '$1'"
  if [[ -z "${!1}" ]] ; then
    echo "FATAL: Env var '${1}' cannot be empty"
    exit 1
  else
    echo "Env Var '${1}' = '${!1}'"
  fi
}

# # Check for required environment variables
assert_var_is_set JIRA_SERVER
assert_var_is_set JIRA_PROJECT

# # IF static_web_files directory exists, run as a web backend service
static_dir='/mnt/static_web_files/'
if [[ -d "$static_dir" ]] ; then
  # static web files will be served by the web server (reverse proxy)
  cp -udR static/* "$static_dir"

  # start gunicorn service
  exec gunicorn 'app:app'
else
  echo "ERROR: static_files_dir '$static_dir' not found"
  mount
fi
