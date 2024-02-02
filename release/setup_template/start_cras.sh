#!/bin/sh

echo "##########################################################"
echo "# Cras Service Start."

PRET=0
systemctl start cras
RET=$?
if [ ${RET} -ne 0 ]; then
  PRET=1
  echo "# ERROR: systemctl start cras fail"
fi

echo "# Status Service."

systemctl status cras

echo "##########################################################"
exit ${PRET}
