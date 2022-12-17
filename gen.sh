#!/bin/bash
DATE=$(date)
cd public
git checkout master
cd ..
feasium
cd public
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
