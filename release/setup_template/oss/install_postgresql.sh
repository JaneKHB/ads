#!/bin/sh

echo "##########################################################"
echo "# postgresql Install Start."

die () {
	echo "# ERROR: $1. Aborting!"
	exit 1
}

# if postgresql.x86_64 is exist, remove
if [ -n "$(yum list installed | grep postgresql.x86_64)" ]; then
	echo "# uninstall other postgresql.x86_64###"
	yum remove -y postgresql.x86_64
fi
if [ -n "$(yum list installed | grep postgresql-libs.x86_64)" ]; then
	echo "# uninstall other postgresql-libs.x86_64###"
	yum remove -y postgresql-libs.x86_64
fi

# Configure Data directory
# CUR=$(dirname "${0}") -> .
CUR=$(pwd)

# package download directory
DOWNLOAD_DIR=${CUR}/postgresql

# extract
if [ -n "$(yum list installed | grep postgresql13)" ]; then
	echo "# already installed postgresql13"
else
	cd ${DOWNLOAD_DIR} || die "Error: postgresql13 directory change"
	yum localinstall -y *.rpm
	RET=$?
	if [ ${RET} -ne 0 ]; then
		die "Error: yum localinstall fail"
	fi
fi

echo "# postgresql Install Success."
echo "##########################################################"

exit 0