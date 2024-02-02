#!/bin/sh

echo "##########################################################"
echo "# java install Start."

die () {
	echo "# ERROR: $1. Aborting!"
	exit 1
}

# Configure Data directory
# CUR=$(dirname "${0}")
CUR=$(pwd)

# package download directory
DOWNLOAD_DIR=${CUR}/java

# install
yum remove -y java-1.7.0-openjdk.x86_64
yum remove -y java-1.7.0-openjdk-headless.x86_64
yum remove -y java-1.8.0-openjdk.x86_64
yum remove -y java-1.8.0-openjdk-headless.x86_64

if [ -n "$(yum list installed | grep java-11)" ]; then
	echo "# already installed java-11"
else
	cd ${DOWNLOAD_DIR} || die "Error: java directory change"
	yum localinstall -y *.rpm
	RET=$?
	if [ ${RET} -ne 0 ]; then
		die "Error: yum localinstall fail"
	fi
fi

echo "# java install Success."
echo "##########################################################"

exit 0