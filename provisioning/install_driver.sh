#! /bin/sh
#
# install_confluent.sh
# Copyright (C) 2018 gaspar_d </var/spool/mail/gaspar_d>
#
# Distributed under terms of the MIT license.
#

if [ "$#" -lt 1 ]; then
  echo "Usage ./install_driver.sh BROKER_URI TEST TESTS..."
  exit 1
fi

BROKER_URI=$1
INFLUXDB_HOST=$2
TEST=$3

sudo yum install -y curl which wget
sudo rpm --import https://packages.confluent.io/rpm/5.0/archive.key

install_telegraf() {
  sudo cp /home/ec2-user/configurations/influx.repo /etc/yum.repos.d/influx.repo
  sudo yum install -y telegraf
  sudo cp /home/ec2-user/configurations/telegraf/telegraf.conf /etc/telegraf/telegraf.conf
  sudo cp /home/ec2-user/configurations/telegraf/host.conf /etc/telegraf/telegraf.d/host.conf

  sudo sed -i "s/#HOSTNAME#/kafka-$BROKER_ID/" /etc/telegraf/telegraf.conf
  sudo sed -i "s~#INFLUXDB_HOST#~$INFLUXDB_HOST~" /etc/telegraf/telegraf.conf
  sudo sed -i "s~#TEST#~$TEST~" /etc/telegraf/telegraf.conf
  sudo sed -i "s~#TYPE#~driver~" /etc/telegraf/telegraf.conf

  sudo systemctl enable telegraf 
  sudo systemctl start telegraf
}

build_package() {
	sudo wget http://repos.fedorapeople.org/repos/dchen/apache-maven/epel-apache-maven.repo -O /etc/yum.repos.d/epel-apache-maven.repo
	sudo yum-config-manager --enable rhui-REGION-rhel-server-extras rhui-REGION-rhel-server-optional
	sudo yum install -y java-1.8.0-openjdk-devel
	sudo yum install -y apache-maven
	cd /home/ec2-user/driver/
	mvn package -DskipTests
}


install_telegraf
build_package
