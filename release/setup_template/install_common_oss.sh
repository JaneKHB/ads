#!/bin/sh

echo "##########################################################"
echo "# OSS install Start."
echo "##########################################################"

die () {
	echo "# ERROR: $1. Aborting!"
	exit 1
}

# =========================================================
# CUR=$(dirname "${0}")
CUR=$(pwd)

# リポジトリ設定ファイルパス
REPO_DIR="/etc/yum.repos.d"

# =========================================================
# SELinux disable
echo "# SELinux disable ..."
yes | cp -rfp ${CUR}/oss/selinux/config /etc/selinux/config
RET=$?
if [ ${RET} -ne 0 ]
then
	exit 1
fi
chown root:root /etc/selinux/config
chmod 644 /etc/selinux/config
setenforce 0

# =========================================================
# FirewallD enable
echo "# FirewallD enable ..."
systemctl start firewalld
systemctl enable firewalld
firewall-cmd --zone=public --add-port=1-65535/tcp --permanent
firewall-cmd --zone=public --add-port=1-65535/udp --permanent
firewall-cmd --zone=public --remove-port=8081/tcp --permanent
firewall-cmd --zone=public --remove-port=8081/udp --permanent
firewall-cmd --reload

# =========================================================
# Make CANON Folder
sh "${CUR}/data/foldermake/make_canon_sub.sh"

# =========================================================
# DVD mount
echo "##########################################################"
echo "# Please put the AlmaLinux iso file to root like /root/AlmaLinux-8.7-x86_64-dvd.iso."
echo "# During initial installation, you must input 'y'."
echo "# Are you ready? (y:Yes/s:Skip): >>"
YES=0
read -p "" cdromyn
# case "$cdromyn" in [yY]*) ;; *) echo "abort." ; exit 1 ;; esac

if [ $cdromyn = "y" ]; then
  YES=1
fi
if [ $cdromyn = "Y" ]; then
  YES=1
fi

# =========================================================
# Install Start
# =========================================================
if [ $YES -eq 1 ]; then
  if [ ! -d "/root/bak_repo" ]
  then
  	echo "# mkdir /root/bak_repo"
  	mkdir /root/bak_repo
  fi
  
  if ls /etc/yum.repos.d/* > /dev/null 2>&1
  then
  	echo "# mv /etc/yum.repos.d/* /root/bak_repo/."
  	mv /etc/yum.repos.d/* /root/bak_repo/.
  fi
  
  # =========================================================
  # change repo file
  echo "# change repo file"
  yes | cp -Rfp ${CUR}/oss/yum.repos.d/base.repo /etc/yum.repos.d/.
  RET=$?
  if [ ${RET} -ne 0 ]
  then
  	exit 1
  fi
  chown root:root /etc/yum.repos.d/base.repo
  chmod 644 /etc/yum.repos.d/base.repo
  
  echo "# mount /root/AlmaLinux-8.7-x86_64-dvd.iso /media"
  mount /root/AlmaLinux-8.7-x86_64-dvd.iso /media
  
  if [ ! -e "/media/media.repo" ]
  then
  	echo "# Error: AlmaLinux media is not mount !!"
  	exit 1
  fi
  
  # =========================================================
  # yum groupinstall "Development Tools"
  echo "##########################################################"
  echo "# yum install base oss "
  yum install -y autoconf automake binutils bison flex gcc gcc-c++ gdb glibc-devel libtool make pkgconf pkgconf-m4 pkgconf-pkg-config redhat-rpm-config \
  	rpm-build rpm-sign strace elfutils-libelf-devel expat-devel pcre pcre-devel openssl-devel libtool libpq google-noto-sans-cjk-ttc-fonts dejavu-sans-fonts
  
  systemctl stop httpd 2>/dev/null
  systemctl stop tomcat_sm 2>/dev/null
  systemctl stop tomcat_rc 2>/dev/null
  systemctl stop tomcat_fsc 2>/dev/null
  systemctl stop tomcat_lm 2>/dev/null
  systemctl stop tomcat_lr_1 2>/dev/null
  systemctl stop tomcat_lr_2 2>/dev/null
  systemctl stop tomcat_lr_3 2>/dev/null
  systemctl stop tomcat_lr_4 2>/dev/null
  systemctl stop redis 2>/dev/null
  systemctl stop cras 2>/dev/null
  systemctl stop postgresql-13 2>/dev/null
  
  cd ${CUR}/oss
  sh "install_oss_sub.sh"
  RET=$?
  if [ ${RET} -ne 0 ]; then die "install_oss_sub.sh fail"; fi
  
  # =========================================================
  # DVD umount
  # echo "# umount /media"
  # umount /media
  # echo "# eject cdrom"
  # eject cdrom
  
  # =========================================================
  # Recovery repo file
  echo "##########################################################"
  echo "# recovery repo file"
  if [ -d "/root/bak_repo" ]
  then
  	rm -rf /etc/yum.repos.d/base.repo
  	mv /root/bak_repo/* /etc/yum.repos.d/.
  fi
  
  echo "##########################################################"
  echo "# OSS install End."
  echo "##########################################################"
  
  exit 0
fi

echo "##########################################################"
echo "# OSS install Skip."
echo "##########################################################"
yum list installed | grep libpq
RET=$?
if [ ${RET} -ne 0 ]; then die "OSS must be install on this PC. Please insert CD-ROM and select Yes."; fi

exit 0
