#!/bin/sh

die () {
	echo "# ERROR: $1. Aborting!"
	exit 1
}

sh "install_java.sh"
RET=$?
if [ ${RET} -ne 0 ]; then die "install_java.sh fail"; fi

sh "install_postgresql.sh"
RET=$?
if [ ${RET} -ne 0 ]; then die "install_postgresql.sh fail"; fi

sh "install_python.sh"
RET=$?
if [ ${RET} -ne 0 ]; then die "install_python.sh fail"; fi

sh "install_httpd.sh"
RET=$?
if [ ${RET} -ne 0 ]; then die "install_httpd.sh fail"; fi

exit 0
