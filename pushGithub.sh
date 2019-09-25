#!/usr/bin/env bash

#needs to be run from project root directory

pip freeze | grep -v "pkg-resources" > requirements.txt
git status
git add .
git commit -m 'update controls'
git push origin master
