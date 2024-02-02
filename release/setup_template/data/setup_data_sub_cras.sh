#!/bin/sh

die () {
	echo "# ERROR: $1. Aborting!"
	exit 1
}

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 PORTNUMBER" >&2
  exit 1
fi

RSS_INSTALL_PORTNUMBER="$1"

######################################################################
# stop service
echo "# Stop Service."
systemctl stop httpd 2>/dev/null
systemctl stop postgresql-13 2>/dev/null
systemctl stop cras 2>/dev/null

######################################################################
# copy common service data
rm -f setup_postgresql.sh
yes | cp -f setup_postgresql_cras.sh setup_postgresql.sh
sh "setup_postgresql.sh"
RET=$?
if [ ${RET} -ne 0 ]; then die "setup_postgresql.sh fail"; fi

rm -f setup_httpd.sh
yes | cp -f setup_httpd_cras.sh setup_httpd.sh
sh "setup_httpd.sh"
RET=$?
if [ ${RET} -ne 0 ]; then die "setup_httpd.sh fail"; fi

sh "setup_wsgi.sh"
RET=$?
if [ ${RET} -ne 0 ]; then die "setup_wsgi.sh fail"; fi

yes | cp -f logrotate.d/logrotate_rss /etc/logrotate.d/
logrotate /etc/logrotate.d/logrotate_rss
RET=$?
if [ ${RET} -ne 0 ]; then die "logrotate.d fail"; fi

echo "##########################################################"
echo "# CRAS Data Setup Start."

yes | cp -f app_cras/7zz /usr/local/7zz
chmod +x /usr/local/7zz

rm -rf /usr/local/cras.tar
rm -rf /usr/local/crasapp
yes | cp -f app_cras/cras.tar /usr/local/cras.tar
tar xvf /usr/local/cras.tar -C /usr/local

rm -rf /usr/local/cras_script_runner.tar
rm -rf /usr/local/cras_script_runner
yes | cp -f app_cras/check_cras_script_runner.tar /usr/local/check_cras_script_runner.tar
tar xvf /usr/local/check_cras_script_runner.tar -C /usr/local

yes | cp -f app_cras/AcquisitionFileConverter.jar /LOG/CANON/CRAS/acquisition/AcquisitionFileConverter.jar

######################################################################
echo "# Check Httpd Port Change."
if [ ${RSS_INSTALL_PORTNUMBER} -ne 443 ]
then
  echo "# Httpd Port Change. to = ${RSS_INSTALL_PORTNUMBER}"
  sed -i "s/Listen 443/Listen ${RSS_INSTALL_PORTNUMBER}/" /usr/local/apache2/conf/extra/httpd-ssl.conf
  sed -i "s/<VirtualHost _default_:443>/<VirtualHost _default_:${RSS_INSTALL_PORTNUMBER}>/" /usr/local/apache2/conf/extra/httpd-ssl.conf
fi

if [ ${RSS_INSTALL_PORTNUMBER} -eq 80 ]
then
  sed -i "s/Include conf/extra/httpd-vhosts.conf/#Include conf/extra/httpd-vhosts.conf/" /usr/local/apache2/conf/httpd.conf
fi

echo "# CRAS Data Setup End."
echo "##########################################################"

# 24P1 [Timezone] Move to start_services.sh for timezone setting.
## start service
#echo "# Start Service."
#systemctl daemon-reload
#
#systemctl enable postgresql-13
#systemctl enable httpd
#systemctl enable cras
#
#PRET=0
#systemctl start postgresql-13
#RET=$?
#if [ ${RET} -ne 0 ]; then
#  PRET=1
#  echo "# ERROR: systemctl start postgresql-13 fail"
#fi
#
#systemctl start httpd
#RET=$?
#if [ ${RET} -ne 0 ]; then
#  PRET=1
#  echo "# ERROR: systemctl start http fail"
#fi
#
##systemctl start cras
##RET=$?
##if [ ${RET} -ne 0 ]; then
##  PRET=1
##  echo "# ERROR: systemctl start cras fail"
##fi
#
#echo "# Status Service."
#systemctl status postgresql-13
#systemctl status httpd
##systemctl status cras

exit ${PRET}
