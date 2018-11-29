#! /bin/sh
#
# install_confluent.sh
# Copyright (C) 2018 gaspar_d </var/spool/mail/gaspar_d>
#
# Distributed under terms of the MIT license.
#

install_zookeeper() {

  sudo yum install -y curl which
  sudo rpm --import https://packages.confluent.io/rpm/5.0/archive.key

  sudo cp /home/ec2-user/configurations/confluent.repo /etc/yum.repos.d/confluent.repo

  sudo yum clean all -y
  sudo yum install -y java
  sudo yum install -y confluent-kafka-2.11

  sudo systemctl enable confluent-zookeeper
  sudo systemctl start confluent-zookeeper
}

install_zookeeper
