#!/bin/sh

# =========================================================
# Make CANON Folder
echo "# Make CANON Folder ..."
mkdir -p /LOG/CANON
readlink -s /CANON
if [ $? -ne 0 ]; then
  echo "# create symbolic link /CANON"
  ln -s /LOG/CANON /CANON
fi

mkdir -p /LOG/CANON/CRAS/job
mkdir -p /LOG/CANON/CRAS/CRASDB
mkdir -p /LOG/CANON/CRAS/job/legacy
mkdir -p /LOG/CANON/CRAS/client
mkdir -p /LOG/CANON/CRAS/DEVLOG
mkdir -p /LOG/CANON/DB
mkdir -p /LOG/CANON/CRAS/acquisition
chmod -R 777 /LOG/CANON/CRAS

exit 0
