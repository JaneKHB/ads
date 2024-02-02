#!/bin/sh

echo "##########################################################"
echo "# WSGI Setup Start."

die () {
	echo "# ERROR: $1. Aborting!"
	exit 1
}

# Configure Data directory
# CUR=$(dirname "${0}") -> .
CUR=$(pwd)
CONF_DIR=${CUR}/app_cras

echo "# copy conf data and etc. "

# copy need files
cp -f "${CONF_DIR}"/cras.service /etc/systemd/system/cras.service

## system service restart
#systemctl daemon-reload
#RET=$?
#if [ ${RET} -ne 0 ]
#then
#	die "Error: cras daemon-reload error ! ret: ${RET}"
#fi
#
#systemctl enable cras
#RET=$?
#if [ ${RET} -ne 0 ]
#then
#	die "Error: cras enable error ! ret: ${RET}"
#fi
#
#systemctl start cras
#RET=$?
#if [ ${RET} -ne 0 ]
#then
#	die "Error: cras start error ! ret: ${RET}"
#fi

echo "# WSGI Setup Success."
echo "##########################################################"

exit 0