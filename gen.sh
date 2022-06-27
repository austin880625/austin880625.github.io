#!/bin/bash
DATE=$(date)
feasium
cd public
git checkout master
git add .
git commit -m "update site $DATE"
git push origin HEAD
git checkout md
cd ..
mv public/.git ./
git add .
git commit -m "update site $DATE"
git push origin HEAD
mv .git public/
cd public
git reset --hard
git checkout master
