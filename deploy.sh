#!/bin/bash -e

source deploy_config.sh

src="app.py web.py browser config.py riven.sqlite"
rsync --archive --recursive --exclude="CD" --exclude="*.gif" \
  --exclude="*.mov" --exclude="*~" --exclude="*.pyc" --exclude="*.swp" \
  --exclude="*.sav" --exclude="*.orig" \
  --progress $src ${dest_user}@${dest_host}:${dest_root}/browser
