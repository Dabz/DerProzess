variable "region" {
  default = "eu-west-3"
}

variable "owner" {
  default = "dgasparina"
}

variable "keyname" {
  default = "damien-paris"
}

variable "ownershort" {
  default = "dga"
}

variable "broker-instance-type" {
  default = "t2.large"
}

variable "driver-instance-type" {
  default = "t2.large"
}

variable "broker-count" {
  default = 3
}

variable "driver-count" {
  default = 2
}

variable "key-file" {
  default = "/home/gaspar_d/.ssh/damien-paris.pem"
}

variable "fingerprint" {
  default = ""
}

variable "test-name" {
  default = "results"
}

variable "grafana-enabled" {
  default = true
}

module "grafana" {
  source        = "./grafana"
  region        = "${var.region}"
  owner         = "${var.owner}"
  ownershort    = "${var.ownershort}"
  key-file      = "${var.key-file}"
  key-name      = "${var.keyname}"
  test-name     = "${var.test-name}"
  grafana-count = "${var.grafana-enabled ? 1 : 0}"
}

module "kafka-cluster" {
  source               = "./confluent"
  broker-count         = "${var.broker-count}"
  driver-count         = "${var.driver-count}"
  name                 = "cluster"
  test-name            = "${var.test-name}"
  region               = "${var.region}"
  owner                = "${var.owner}"
  ownershort           = "${var.ownershort}"
  key-file             = "${var.key-file}"
  key-name             = "${var.keyname}"
  influx-host          = "${module.grafana.influxdb_public_dns}"
  broker-instance-type = "${var.broker-instance-type}"
  driver-instance-type = "${var.driver-instance-type}"
}

output "fingerprint" {
  value = "${var.fingerprint}"
}

output "kafka-brokers-private-dns" {
  value = ["${module.kafka-cluster.broker_private_dns}"]
}

output "kafka-brokers-public-dns" {
  value = ["${module.kafka-cluster.broker_public_dns}"]
}

output "kafka-driver-public-dns" {
  value = ["${module.kafka-cluster.driver_drivers_dns}"]
}

output "grafana-public-dns" {
  value = "${module.grafana.influxdb_public_dns}"
}

output "grafana-url" {
  value = "http://${module.grafana.influxdb_public_dns}:3000"
}
