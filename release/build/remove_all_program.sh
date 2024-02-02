#!/bin/sh

echo "##########################################################"
echo "# OSS Remove Start."
echo "##########################################################"

die () {
	echo "ERROR: $1. Aborting!"
	exit 1
}

# is root
user=$(whoami)
if [ "${user}" != "root" ]
then
	die "Error: Execution user must be root!"
fi

yum remove -y postgresql13*
# yum remove -y java
yum remove -y python39*
rm -rf /usr/local/lib/python3.9

systemctl stop httpd
rm -rf /usr/local/apache2
rm -rf /etc/systemd/system/httpd.service
rm -rf /etc/profile.d/httpd.sh

systemctl stop tomcat_sm
systemctl stop tomcat_rc
systemctl stop tomcat_fsc
systemctl stop tomcat_lm
systemctl stop tomcat_lr_1
systemctl stop tomcat_lr_2
systemctl stop tomcat_lr_3
systemctl stop tomcat_lr_4
rm -rf /usr/local/tomcat*
rm -rf /etc/systemd/system/tomcat*

systemctl stop redis*
rm -rf /etc/redis
rm -rf /etc/systemd/system/redis.service
rm -rf /usr/local/bin/redis-*

rm -rf /CANON/*
rm -rf /CANON
