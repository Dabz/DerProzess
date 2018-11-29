#! /bin/sh
#
# install_grafana.sh
# Copyright (C) 2018 gaspar_d </var/spool/mail/gaspar_d>
#
# Distributed under terms of the MIT license.
#

GRAFANA_URL="http://admin:admin@localhost:3000"

install_influx() {
  sudo cp /home/ec2-user/configurations/influx.repo /etc/yum.repos.d/influx.repo
  sudo yum install -y influxdb
  sudo systemctl enable influxdb
  sudo systemctl start influxdb
}

install_grafana() {

  sudo yum install -y curl which
  sudo rpm --import https://packages.confluent.io/rpm/5.0/archive.key

  sudo cp /home/ec2-user/configurations/confluent.repo /etc/yum.repos.d/confluent.repo
  sudo cp /home/ec2-user/configurations/grafana.repo /etc/yum.repos.d/grafana.repo

  sudo yum clean all -y
  sudo yum install -y java
  sudo yum install -y confluent-kafka-2.11
  sudo yum install -y grafana

	sudo grafana-cli plugins install grafana-piechart-panel
  sudo systemctl enable grafana-server
  sudo systemctl restart grafana-server
}

wait_for_grafana() {
  while : ;
  do
    curl ${GRAFANA_URL} --output /dev/null
    if [ $? -eq 0 ] ; then
      break;
    fi
    sleep 1
  done
}

configure_grafana() {
  for datasource in /home/ec2-user/configurations/grafana/datasources/*json ; do
    curl -XPOST ${GRAFANA_URL}/api/datasources/ -H 'Content-Type: application/json;charset=UTF-8' --output /dev/null -d @${datasource}
  done

  for dashboard in /home/ec2-user/configurations/grafana/dashboards/*.json ; do
    curl -XPOST ${GRAFANA_URL}/api/dashboards/db/ -H 'Content-Type: application/json;charset=UTF-8' --output /dev/null -d @${dashboard}
  done
}

install_influx
install_grafana
wait_for_grafana
configure_grafana 
