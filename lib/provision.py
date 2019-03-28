#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2018 gaspar_d </var/spool/mail/gaspar_d>
#
# Distributed under terms of the MIT license.

"""
Terraform Binding
"""

import python_terraform
import hashlib
import os
from distutils.dir_util import copy_tree

TERRAFORM_SOURCE_DIR = "./provisioning"


def fingerprint_from_configuration(cloud_conf):
    """
    Return a fingerprint identifying a unique
    cloud configuration
    """
    json_str = str(cloud_conf)
    ha = hashlib.md5()
    ha.update(json_str.encode())

    return str(ha.hexdigest())


def workspace_with_fingerprint(cloud_conf):
    target_fingerprint = fingerprint_from_configuration(cloud_conf)
    for directory in os.listdir("./"):
        if os.path.exists("%s/main.tf" % directory):
            terraform = python_terraform.Terraform(working_dir=directory)
            workspace_fingerprint = terraform.output("fingerprint")
            if workspace_fingerprint == target_fingerprint:
                return directory

    return None


class Provision:

    def __init__(self, properties, uid):
        self.cloud_conf = properties["brokers"]
        self.uid = uid
        workspace = workspace_with_fingerprint(self.cloud_conf)

        if workspace is None:
            if not os.path.exists(self.uid):
                copy_tree(src=TERRAFORM_SOURCE_DIR,
                          dst=self.uid)

            self.terraform = python_terraform.Terraform(working_dir=self.uid)
            self.terraform.init()
            self.provisioned = False
        else:
            self.terraform = python_terraform.Terraform(working_dir=workspace)
            self.uid = workspace
            self.provisioned = True

    def apply_if_required(self):
        if not self.provisioned:
            self.apply()

    def apply(self):
        """
        Provision the environment in a dedicated workspace
        """
        self.provisioned = True
        self.terraform.apply(skip_plan=True, var={
            "broker-count": self.cloud_conf["broker-count"],
            "test-name": self.uid,
            "driver-count": self.cloud_conf["driver-count"],
            "key-file": self.cloud_conf["ssh-key"],
            "keyname": self.cloud_conf["ssh-keyname"],
            "owner": self.cloud_conf["owner"],
            "ownershort": self.cloud_conf["ownershort"],
            "region": self.cloud_conf["region"],
            "broker-instance-type": self.cloud_conf['broker-instance-type'],
            "driver-instance-type": self.cloud_conf['driver-instance-type'],
            "fingerprint": fingerprint_from_configuration(self.cloud_conf),
            "grafana-enabled": False
        })

    def destroy(self):
        self.terraform.destroy(force=True)

    def sweet_name(self):
        return self.uid

    def configurations(self):
        return {
            "bootstrap.servers": self.bootstrap_servers()
        }

    def bootstrap_servers(self):
        config = {}

        brokers = self.terraform.output("kafka-brokers-private-dns")
        bootstrapped = ""
        for broker in brokers:
            bootstrapped = bootstrapped + "," + broker + ":9092"
        bootstrapped = bootstrapped[1:]

        return bootstrapped

    def driver_host(self):
        drivers = self.terraform.output("kafka-driver-public-dns")
        return drivers

    def broker_host(self):
        brokers = self.terraform.output("kafka-brokers-public-dns")
        return brokers
