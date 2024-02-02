#!/bin/sh

die () {
	echo "# ERROR: $1. Aborting!"
	exit 1
}

echo "##########################################################"

# start service
echo "# Start Service."
systemctl daemon-reload

systemctl enable postgresql-13
systemctl enable httpd
systemctl enable cras

PRET=0
systemctl start postgresql-13
RET=$?
if [ ${RET} -ne 0 ]; then
  PRET=1
  echo "# ERROR: systemctl start postgresql-13 fail"
fi

systemctl start httpd
RET=$?
if [ ${RET} -ne 0 ]; then
  PRET=1
  echo "# ERROR: systemctl start http fail"
fi

#systemctl start cras
#RET=$?
#if [ ${RET} -ne 0 ]; then
#  PRET=1
#  echo "# ERROR: systemctl start cras fail"
#fi

echo "# Status Service."
systemctl status postgresql-13
systemctl status httpd
#systemctl status cras
echo "##########################################################"

exit ${PRET}
