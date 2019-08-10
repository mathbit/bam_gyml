#!/usr/bin/env bash

#needs to be run from project root directory
#is run by UPDATEALL.py
pip freeze | grep -v "pkg-resources" > requirements.txt
git status
git add .
git commit -m 'update controls'
git push heroku master
