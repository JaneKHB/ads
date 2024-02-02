#!/bin/sh

echo "##########################################################"
echo "# Python Install Start."

die () {
	echo "# ERROR: $1. Aborting!"
	exit 1
}

# Configure Data directory
# CUR=$(dirname "${0}")
CUR=$(pwd)

# package download directory
DOWNLOAD_DIR=${CUR}/python

if [ -n "$(yum list installed | grep python39)" ]; then
	echo "# already installed python39"
else
	# we need psql
	test -d /usr/pgsql-13/bin
	RET=$?
	if [ ${RET} -ne 0 ]; then
		die "Error: /usr/pgsql-13/bin is not exist."
	fi

	export PATH=$PATH:/usr/pgsql-13/bin

	# install rpm
	cd ${DOWNLOAD_DIR}/rpm || die "Error: rpm directory change"
	yum localinstall -y *.rpm
	RET=$?
	if [ ${RET} -ne 0 ]; then
		die "Error: yum localinstall fail rpm"
	fi
	
	# install ext_rpm
	cd ${DOWNLOAD_DIR}/ext_rpm || die "Error: ext_rpm directory change"
	yum localinstall -y *.rpm
	RET=$?
	if [ ${RET} -ne 0 ]; then
		die "Error: yum localinstall fail ext_rpm"
	fi
	
	rm -f /usr/bin/pip
	rm -f /usr/bin/python
	ln -sf /usr/bin/pip3.9 /usr/bin/pip
	ln -sf /usr/bin/python3.9 /usr/bin/python

	# install pkg
	cd ${DOWNLOAD_DIR}/pkg || die "Error: pkg directory change 2"
	pip install --no-index --find-links=${DOWNLOAD_DIR}/pkg -r requirements.txt
	RET=$?
	if [ ${RET} -ne 0 ]; then
		die "Error: pip install fail"
	fi
fi

echo "# Python Install Success."
echo "##########################################################"

exit 0