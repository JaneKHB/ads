#!/bin/sh

echo "##########################################################"
echo "# Install Start."
echo "##########################################################"

die () {
	echo "# ERROR: $1. Aborting!"
	exit 1
}

# =========================================================
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 PORTNUMBER" >&2
  exit 1
fi

# =========================================================
RSS_INSTALL_PORTNUMBER="$1"
echo "# Install PORT = ${RSS_INSTALL_PORTNUMBER}"

# =========================================================
# is root
user=$(whoami)
if [ "${user}" != "root" ]
then
	die "Error: Execution user must be root!"
fi

export PATH=.:$PATH

# =========================================================
# CUR=$(dirname "${0}")
CUR=$(pwd)

# =========================================================
# Copy httpd server cert file
echo "# Copy httpd cert to setup dst."
yes | cp ${CUR}/server/server.key ${CUR}/data/httpd/server.key
yes | cp ${CUR}/server/server.crt ${CUR}/data/httpd/server.crt

rm -f ${CUR}/data/foldermake/make_canon_sub.sh
yes | cp ${CUR}/data/foldermake/make_canon_sub_cras.sh ${CUR}/data/foldermake/make_canon_sub.sh
#yes | cp ${CUR}/data/foldermake/make_canon_sub_esp.sh ${CUR}/data/foldermake/make_canon_sub.sh
#yes | cp ${CUR}/data/foldermake/make_canon_sub_lm.sh ${CUR}/data/foldermake/make_canon_sub.sh
#yes | cp ${CUR}/data/foldermake/make_canon_sub_ots.sh ${CUR}/data/foldermake/make_canon_sub.sh

rm -f ${CUR}/oss/install_oss_sub.sh
yes | cp ${CUR}/oss/install_oss_sub_cras.sh ${CUR}/oss/install_oss_sub.sh
#yes | cp ${CUR}/oss/install_oss_sub_esp.sh ${CUR}/oss/install_oss_sub.sh
#yes | cp ${CUR}/oss/install_oss_sub_lm.sh ${CUR}/oss/install_oss_sub.sh
#yes | cp ${CUR}/oss/install_oss_sub_ots.sh ${CUR}/oss/install_oss_sub.sh

rm -f ${CUR}/data/setup_data_sub.sh
yes | cp ${CUR}/data/setup_data_sub_cras.sh ${CUR}/data/setup_data_sub.sh
#yes | cp ${CUR}/data/setup_data_sub_esp.sh ${CUR}/data/setup_data_sub.sh
#yes | cp ${CUR}/data/setup_data_sub_lm.sh ${CUR}/data/setup_data_sub.sh
#yes | cp ${CUR}/data/setup_data_sub_ots.sh ${CUR}/data/setup_data_sub.sh

# =========================================================
chmod +x ${CUR}/*.sh
chmod +x ${CUR}/oss/*.sh
chmod +x ${CUR}/data/*.sh
chmod +x ${CUR}/data/foldermake/*.sh

sh "install_common_oss.sh"
RET=$?
if [ ${RET} -ne 0 ]; then die "install_common_oss.sh fail"; fi

cd ${CUR}
pwd
install_common_data.sh ${RSS_INSTALL_PORTNUMBER}
RET=$?
if [ ${RET} -ne 0 ]; then die "install_common_data.sh fail"; fi
cd ${CUR}

echo "##########################################################"
echo "# Install Success."
echo "##########################################################"
