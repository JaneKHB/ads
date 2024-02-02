#!/bin/sh

echo "##########################################################"
echo "# Setup Data Start."
echo "##########################################################"

die () {
	echo "# ERROR: $1. Aborting!"
	exit 1
}

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 PORTNUMBER" >&2
  exit 1
fi

RSS_INSTALL_PORTNUMBER="$1"

# =========================================================
# CUR=$(dirname "${0}")
CUR=$(pwd)
cd ${CUR}/data || die "Error: working directory change. setup_data.sh"
setup_data_sub.sh ${RSS_INSTALL_PORTNUMBER}
RET=$?
if [ ${RET} -ne 0 ]; then die "setup_data_sub.sh fail"; fi

echo "##########################################################"
echo "# Setup Data End."
echo "##########################################################"

exit 0
