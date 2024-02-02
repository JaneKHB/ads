#!/bin/sh

echo "##########################################################"
echo "# httpd Setup Start."

die () {
	echo "# ERROR: $1. Aborting!"
	exit 1
}

# Configure Data directory
# CUR=$(dirname "${0}") -> .
CUR=$(pwd)
CONF_DIR=${CUR}/httpd

echo "# copy conf data and etc. "

# copy need files
yes | cp -f "${CONF_DIR}"/httpd.conf /usr/local/apache2/conf/httpd.conf
yes | cp -f "${CONF_DIR}"/server.crt /usr/local/apache2/conf/server.crt
yes | cp -f "${CONF_DIR}"/server.key /usr/local/apache2/conf/server.key
yes | cp -f "${CONF_DIR}"/pass.sh /usr/local/apache2/conf/pass.sh
chmod +x /usr/local/apache2/conf/pass.sh

yes | cp -f "${CONF_DIR}"/extra/httpd-ssl_cras.conf /usr/local/apache2/conf/extra/httpd-ssl.conf
yes | cp -f "${CONF_DIR}"/extra/httpd-vhosts_cras.conf /usr/local/apache2/conf/extra/httpd-vhosts.conf
yes | cp -f "${CONF_DIR}"/httpd.service /etc/systemd/system/httpd.service
rm -f /usr/local/apache2/logs/httpd.pid

# system service restart
#systemctl daemon-reload
#RET=$?
#if [ ${RET} -ne 0 ]
#then
#	die "Error: httpd daemon-reload error ! ret: ${RET}"
#fi
#
#systemctl enable httpd
#RET=$?
#if [ ${RET} -ne 0 ]
#then
#	die "Error: httpd enable error ! ret: ${RET}"
#fi
#
#systemctl start httpd
#RET=$?
#if [ ${RET} -ne 0 ]
#then
#	die "Error: httpd start error ! ret: ${RET}"
#fi

echo "# httpd Setup Success."
echo "##########################################################"

exit 0