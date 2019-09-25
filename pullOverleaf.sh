#!/usr/bin/env bash

#needs to be run in overleafgit.
#Is called from python-script UPDATEALL.py
git pull origin master

yes | cp -f main.tex ../static/latex/
yes | cp -f preamble.tex ../static/latex/
yes | cp -rf pics/* ../static/latex/pics/
