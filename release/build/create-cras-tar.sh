#!/bin/bash

if [ -d crasapp ]
then
  echo "Delete old crasapp folder"
  rm -rf crasapp
fi
rm -rf cras.tar

mkdir crasapp

echo "Copy all files to run as a cras-server"

cp ../../main.py ./crasapp

folders=(common config controller dao flaskapp resource service dockerlib)
for folder in ${folders[@]}
do
  cp -r ../../$folder ./crasapp/$folder
done

mkdir crasapp/pyrunner
mkdir crasapp/pyrunner/src
cp ../../pyrunner/src/steprunnerhost.py ./crasapp/pyrunner/src
cp ../../pyrunner/src/servicemgr.py ./crasapp/pyrunner/src

echo "Create a achieve file"
tar cvf cras.tar crasapp

echo "Clean up all temporaries"
rm -rf crasapp

echo "Success"
