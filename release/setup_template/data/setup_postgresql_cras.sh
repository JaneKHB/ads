#!/bin/sh

echo "##########################################################"
echo "# Postgresql Setup Start."

die () {
	echo "# ERROR: $1. Aborting!"
	exit 1
}

PGDATA_PATH=/CANON/DB
PGPORT=5443

# Configure Data directory
# CUR=$(dirname "${0}") -> .
CUR=$(pwd)
CONF_DIR=${CUR}/postgresql

echo "# postgres initdb."

systemctl stop postgresql-13

yes | cp -f "${CONF_DIR}"/postgresql-13_cras.service /usr/lib/systemd/system/postgresql-13.service

if [ ! -e "${PGDATA_PATH}/postgresql.conf" ]
then
	# if not exist postgresql.conf
	mkdir -p ${PGDATA_PATH}
	chown -R postgres:postgres ${PGDATA_PATH}
	su - postgres -c "/usr/pgsql-13/bin/initdb --pgdata=${PGDATA_PATH}"

	# for 24P1 [Timezone]
	echo "# copy postgresql.conf"
	yes | cp -f "${CONF_DIR}"/postgresql_cras.conf ${PGDATA_PATH}/postgresql.conf
else
  echo "# ${PGDATA_PATH}/postgresql.conf is already exists. do not initdb"
fi

# copy need files
echo "# copy pg_hba.conf"
yes | cp -f "${CONF_DIR}"/pg_hba.conf ${PGDATA_PATH}/pg_hba.conf

echo "# First Service start. "

# system service restart
systemctl daemon-reload
RET=$?
if [ ${RET} -ne 0 ]
then
	die "Error: postgresql daemon-reload error ! ret: ${RET}"
fi

systemctl enable postgresql-13
RET=$?
if [ ${RET} -ne 0 ]
then
	die "Error: postgresql enable error ! ret: ${RET}"
fi

systemctl start postgresql-13
RET=$?
if [ ${RET} -ne 0 ]
then
	die "Error: postgresql start error ! ret: ${RET}"
fi

echo "# postgres make db and user. "

if [[ -z $(su - postgres -c "psql -p ${PGPORT} -Atqc '\list rssdb'") ]]
then
	# if not exist rssdb
	su - postgres -c "psql -p ${PGPORT} -c \"CREATE ROLE rssadmin WITH LOGIN PASSWORD 'canon' \""
	su - postgres -c "psql -p ${PGPORT} -c \"alter user rssadmin with superuser \""
	su - postgres -c "psql -p ${PGPORT} -c \"alter user rssadmin with createdb \""
	su - postgres -c "psql -p ${PGPORT} -c \"alter user rssadmin with createrole \""
	su - postgres -c "psql -p ${PGPORT} -c \"alter user rssadmin with replication \""
	su - postgres -c "psql -p ${PGPORT} -c \"CREATE DATABASE rssdb OWNER rssadmin \""
	RET=$?
	if [ ${RET} -ne 0 ]
	then
		die "Error: postgresql make db and user error ! ret: ${RET}"
	fi
else
    echo "# rssdb is already exists."
fi

echo "# Service stop. "

systemctl stop postgresql-13

echo "# Postgresql Setup Success."
echo "##########################################################"

exit 0