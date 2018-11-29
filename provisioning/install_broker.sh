#! /bin/sh
#
# install_confluent.sh
# Copyright (C) 2018 gaspar_d </var/spool/mail/gaspar_d>
#
# Distributed under terms of the MIT license.
#

if [ "$#" -lt 3 ]; then
  echo "Usage ./install_confluent.sh ZOOKEEPER_URI BROKER_ID BROKER_CONF INFLUX_HOST"
  exit 1
fi

ZOOKEEPER_URI=$1
BROKER_ID=$2
BROKER_CONF=$3
INFLUXDB_HOST=$4

sudo yum install -y curl which wget
sudo rpm --import https://packages.confluent.io/rpm/5.0/archive.key

download_jolokia() {
  cd /home/ec2-user
  wget https://github.com/rhuss/jolokia/releases/download/v1.6.0/jolokia-1.6.0-bin.tar.gz
  tar xf jolokia-1.6.0-bin.tar.gz
  sudo cp jolokia-1.6.0/agents/jolokia-jvm.jar /opt
}

install_confluent() {
  sudo cp /home/ec2-user/configurations/confluent.repo /etc/yum.repos.d/confluent.repo
  sudo yum clean all -y
  sudo yum install -y java
  sudo yum install -y confluent-kafka-2.11

  sudo mkdir -p /etc/systemd/system/confluent-kafka.service.d/
  sudo cp /home/ec2-user/configurations/brokers/override.conf /etc/systemd/system/confluent-kafka.service.d/override.conf
  sudo cp /home/ec2-user/configurations/brokers/$BROKER_CONF /etc/kafka/kafka.properties

  sudo sed -i "s/#ZOOKEEPER_URI#/$ZOOKEEPER_URI/" /etc/kafka/kafka.properties
  sudo sed -i "s/#BROKER_ID#/$BROKER_ID/" /etc/kafka/kafka.properties
}

start_confluent() {
  sudo systemctl enable confluent-kafka
  sudo systemctl start confluent-kafka
}


install_telegraf() {
  sudo cp /home/ec2-user/configurations/influx.repo /etc/yum.repos.d/influx.repo
  sudo yum install -y telegraf
  sudo cp /home/ec2-user/configurations/grafana/telegraf.conf /etc/telegraf/telegraf.conf
  sudo cp /home/ec2-user/configurations/grafana/kafka.conf /etc/telegraf/telegraf.d/kafka.conf
  sudo cp /home/ec2-user/configurations/grafana/host.conf /etc/telegraf/telegraf.d/host.conf

  sudo sed -i "s/#HOSTNAME#/kafka-$BROKER_ID/" /etc/telegraf/telegraf.conf
  sudo sed -i "s~#INFLUXDB_HOST#~$INFLUXDB_HOST~" /etc/telegraf/telegraf.conf
  sudo sed -i "s/#HOSTNAME#/`hostname -f`/" /etc/telegraf/telegraf.d/kafka.conf

  sudo systemctl enable telegraf 
  sudo systemctl start telegraf
}


download_jolokia 
install_confluent 
start_confluent 
install_telegraf
