variable "name" {}
variable "region" {}
variable "key-name" {}
variable "owner" {}
variable "ownershort" {}
variable "key-file" {}
variable "influx-host" {}

variable "broker-count" {
  default = 3
}

variable "broker-instance-type" {
  default = "t2.large"
}

variable "broker-configuration" {
  default = "default.properties"
}

variable "driver-count" {
  default = 1
}

variable "driver-test" {
  default = ""
}

variable "driver-instance-type" {
  default = "t2.xlarge"
}

provider "aws" {
  region = "${var.region}"
}

data "aws_ami" "rhel7" {
  most_recent = true

  filter {
    name   = "name"
    values = ["RHEL-7.5_HVM_GA-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = ["309956199498"]
}

resource "aws_security_group" "drivers" {
  description = "drivers - Managed by DerProzess"
  name        = "${terraform.workspace}-${var.ownershort}-drivers"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = -1
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "brokers" {
  description = "brokers - Managed by DerProzess"
  name        = "${terraform.workspace}-${var.ownershort}-brokers"

  # client connections from hosts, my ip, clients
  ingress {
    from_port       = 9092
    to_port         = 9092
    protocol        = "tcp"
    self            = true
    security_groups = ["${aws_security_group.drivers.id}"]
  }

  # Jolokia 
  ingress {
    from_port   = 8778
    to_port     = 8778
    protocol    = "TCP"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "TCP"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = -1
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "zookeepers" {
  description = "zookeeper - Managed by DerProzess"
  name        = "${terraform.workspace}-${var.ownershort}-zookeeper"

  # zookeeper connections hosts, my ip, clients
  ingress {
    from_port       = 2181
    to_port         = 2181
    protocol        = "tcp"
    self            = true
    security_groups = ["${aws_security_group.drivers.id}", "${aws_security_group.brokers.id}"]
  }

  ingress {
    from_port = 2888
    to_port   = 2888
    protocol  = "TCP"
    self      = true
  }

  ingress {
    from_port = 3888
    to_port   = 3888
    protocol  = "TCP"
    self      = true
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "TCP"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = -1
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "zookeepers" {
  count         = "1"
  ami           = "${data.aws_ami.rhel7.id}"
  instance_type = "t2.small"

  security_groups = ["${aws_security_group.zookeepers.name}"]
  key_name        = "${var.key-name}"

  root_block_device {
    volume_size = 10
  }

  tags {
    Name          = "${terraform.workspace}-${var.ownershort}-zookeeper-${count.index}"
    description   = "zookeeper node - Managed by DerProzess (${terraform.workspace})"
    nice-name     = "${terraform.workspace}-zookeeper-${count.index}"
    big-nice-name = "${terraform.workspace}-zookeeper-${count.index}"
    role          = "zookeeper"
    owner         = "${var.owner}"
    sshUser       = "ec2-user"
    createdBy     = "terraform"
  }

  provisioner "file" {
    source      = "./configurations"
    destination = "/home/ec2-user/"

    connection {
      user        = "ec2-user"
      private_key = "${file("${var.key-file}")}"
    }
  }

  provisioner "file" {
    source      = "install_zookeeper.sh"
    destination = "/home/ec2-user/install_zookeeper.sh"

    connection {
      user        = "ec2-user"
      private_key = "${file("${var.key-file}")}"
    }
  }

  provisioner "remote-exec" {
    inline = [
      "chmod +x /home/ec2-user/install_zookeeper.sh",
      "/home/ec2-user/install_zookeeper.sh",
    ]

    connection {
      user        = "ec2-user"
      private_key = "${file("${var.key-file}")}"
    }
  }

  timeouts {
    create = "10m"
  }
}

resource "aws_instance" "brokers" {
  count         = "${var.broker-count}"
  ami           = "${data.aws_ami.rhel7.id}"
  instance_type = "${var.broker-instance-type}"

  security_groups = ["${aws_security_group.brokers.name}"]
  key_name        = "${var.key-name}"

  root_block_device {
    volume_size = 100
  }

  tags {
    Name          = "${terraform.workspace}-${var.ownershort}-broker-${count.index}"
    description   = "broker node - Managed by DerProzess"
    nice-name     = "${terraform.workspace}-broker-${count.index}"
    big-nice-name = "${terraform.workspace}-broker-${count.index}"
    role          = "broker"
    owner         = "${var.owner}"
    sshUser       = "ec2-user"
    createdBy     = "terraform"
  }

  provisioner "file" {
    source      = "./configurations"
    destination = "/home/ec2-user/"

    connection {
      user        = "ec2-user"
      private_key = "${file("${var.key-file}")}"
    }
  }

  provisioner "file" {
    source      = "install_broker.sh"
    destination = "/home/ec2-user/install_broker.sh"

    connection {
      user        = "ec2-user"
      private_key = "${file("${var.key-file}")}"
    }
  }

  provisioner "remote-exec" {
    inline = [
      "chmod +x /home/ec2-user/install_broker.sh",
      "/home/ec2-user/install_broker.sh ${aws_instance.zookeepers.0.private_dns} ${count.index} ${var.broker-configuration} ${var.influx-host}",
    ]

    connection {
      user        = "ec2-user"
      private_key = "${file("${var.key-file}")}"
    }
  }

  timeouts {
    create = "10m"
  }
}

resource "aws_instance" "drivers" {
  count           = "${var.driver-count}"
  ami             = "${data.aws_ami.rhel7.id}"
  instance_type   = "${var.driver-instance-type}"
  security_groups = ["${aws_security_group.drivers.name}"]
  key_name        = "${var.key-name}"

  tags {
    Name          = "${terraform.workspace}-${var.ownershort}-driver-${count.index}"
    description   = "driver node - Managed by DerProzess"
    nice-name     = "${terraform.workspace}-driver-${count.index}"
    big-nice-name = "${terraform.workspace}-driver-${count.index}"
    role          = "driver"
    owner         = "${var.owner}"
    sshUser       = "ec2-user"
    createdBy     = "terraform"
  }

  provisioner "file" {
    source      = "../driver"
    destination = "/home/ec2-user/"

    connection {
      user        = "ec2-user"
      private_key = "${file("${var.key-file}")}"
    }
  }

  provisioner "file" {
    source      = "../tests"
    destination = "/home/ec2-user/"

    connection {
      user        = "ec2-user"
      private_key = "${file("${var.key-file}")}"
    }
  }

  provisioner "file" {
    source      = "../configuration.json"
    destination = "/home/ec2-user/"

    connection {
      user        = "ec2-user"
      private_key = "${file("${var.key-file}")}"
    }
  }

  provisioner "file" {
    source      = "./configurations"
    destination = "/home/ec2-user/"

    connection {
      user        = "ec2-user"
      private_key = "${file("${var.key-file}")}"
    }
  }

  provisioner "file" {
    source      = "install_driver.sh"
    destination = "/home/ec2-user/install_driver.sh"

    connection {
      user        = "ec2-user"
      private_key = "${file("${var.key-file}")}"
    }
  }

  provisioner "remote-exec" {
    inline = [
      "chmod +x /home/ec2-user/install_driver.sh",
      "/home/ec2-user/install_driver.sh ${aws_instance.brokers.0.private_dns} ${count.index}",
    ]

    connection {
      user        = "ec2-user"
      private_key = "${file("${var.key-file}")}"
    }
  }
}

// Output
output "broker_private_dns" {
  value = ["${aws_instance.brokers.*.private_dns}"]
}

output "broker_public_ips" {
  value = ["${aws_instance.brokers.*.public_ip}"]
}

output "broker_public_dns" {
  value = ["${aws_instance.brokers.*.public_dns}"]
}

output "driver_drivers_ip" {
  value = ["${aws_instance.drivers.*.public_ip}"]
}

output "driver_drivers_dns" {
  value = ["${aws_instance.drivers.*.public_dns}"]
}
