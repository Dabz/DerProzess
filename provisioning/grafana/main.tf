variable "region" {}
variable "key-name" {}
variable "owner" {}
variable "ownershort" {}
variable "key-file" {}

variable "grafana-instance-type" {
  default = "t2.small"
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

resource "aws_security_group" "grafana" {
  description = "Grafana - Managed by DerProzess"
  name        = "${terraform.workspace}-${var.ownershort}-grafana"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8086
    to_port     = 8086
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

resource "aws_instance" "grafana" {
  count         = "1"
  ami           = "${data.aws_ami.rhel7.id}"
  instance_type = "${var.grafana-instance-type}"

  security_groups = ["${aws_security_group.grafana.name}"]
  key_name        = "${var.key-name}"

  root_block_device {
    volume_size = 10
  }

  tags {
    Name          = "${terraform.workspace}-${var.ownershort}-grafana"
    description   = "grafana node - Managed by DerProzess"
    nice-name     = "${terraform.workspace}-grafana"
    big-nice-name = "${terraform.workspace}-grafana"
    role          = "grafana"
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
    source      = "install_grafana.sh"
    destination = "/home/ec2-user/install_grafana.sh"

    connection {
      user        = "ec2-user"
      private_key = "${file("${var.key-file}")}"
    }
  }

  provisioner "remote-exec" {
    inline = [
      "chmod +x /home/ec2-user/install_grafana.sh",
      "/home/ec2-user/install_grafana.sh",
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

output "grafana_public_dns" {
  value = "${aws_instance.grafana.0.public_dns}"
}

output "influxdb_public_dns" {
  value = "${aws_instance.grafana.0.public_dns}"
}
