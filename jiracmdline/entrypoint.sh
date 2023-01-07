#!/bin/sh
set -eu

# copy static files to container shared mount point
#rsync -rlpt --delete static/ /mnt/static_web_files/
cp -udR static/* /mnt/static_web_files/

# start gunicorn service
exec gunicorn 'app:app'
