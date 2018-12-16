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
import threading
import hashlib
import string

WORKING_DIR = "./provisioning"

terraform_lock = threading.Lock()


def fingerprint_from_configuration(cloud_conf):
    """
    Return a fingerprint identifying a unique
    cloud configuration
    """
    json_str = str(cloud_conf)
    ha = hashlib.md5()
    ha.update(json_str.encode())

    return str(ha.hexdigest())


class Provision:

    def __init__(self, cloud_conf, ranged_properties):
        self.cloud_conf = cloud_conf
        self.terraform = python_terraform.Terraform(working_dir=WORKING_DIR)
        workspace = self.workspace_with_fingerprint(cloud_conf)
        if workspace is None:
            self.uid = self.generate_uid(cloud_conf, ranged_properties)
            self.provisioned = False
        else:
            self.uid = workspace
            self.provisioned = True
        self.terraform.workspace("new", self.uid)

    def generate_uid(self, cloud_conf, ranged_properties):
        ranged_values = []
        for ranged_propertie in ranged_properties:
            ranged_values.append("%s-%s" % (ranged_propertie, cloud_conf[ranged_propertie]))
        return '_'.join(ranged_values)

    def workspace_with_fingerprint(self, cloud_conf):
        workspaces_raw = str(self.terraform.workspace("list")[1])
        workspaces = workspaces_raw.splitlines()
        target_fingerprint = fingerprint_from_configuration(cloud_conf)

        for workspace in workspaces:
            workspace = workspace.replace("*", "")
            workspace = workspace.strip()
            if workspace == "default":
                continue
            if workspace == "":
                continue

            terraform_lock.acquire()
            self.terraform.workspace("select", workspace)
            workspace_fingerprint = self.terraform.output("fingerprint")
            if workspace_fingerprint == target_fingerprint:
                terraform_lock.release()
                return workspace
            terraform_lock.release()

        return None

    def apply_if_required(self):
        if not self.provisioned:
            self.apply()

    def apply(self):
        """
        Provision the environment in a dedicated workspace
        """
        terraform_lock.acquire()
        self.provisioned = True
        self.terraform.workspace("select", self.uid)
        self.terraform.apply(skip_plan=True, var={
            "broker-count": self.cloud_conf["count"],
            "key-file": self.cloud_conf["ssh-key"],
            "keyname": self.cloud_conf["ssh-keyname"],
            "owner": self.cloud_conf["owner"],
            "ownershort": self.cloud_conf["ownershort"],
            "region": self.cloud_conf["region"],
            "broker-instance-type": self.cloud_conf['broker-instance-type'],
            "driver-instance-type": self.cloud_conf['driver-instance-type'],
            "fingerprint": fingerprint_from_configuration(self.cloud_conf)
        })
        terraform_lock.release()

    def destroy(self):
        terraform_lock.acquire()
        self.terraform.workspace("select", self.uid)
        self.terraform.destroy(force=True)
        terraform_lock.release()

    def sweet_name(self):
        return self.uid

    def configurations(self):
        return {
            "bootstrap.servers": self.bootstrap_servers()
        }

    def bootstrap_servers(self):
        config = {}

        terraform_lock.acquire()

        self.terraform.workspace("select", self.uid)
        brokers = self.terraform.output("kafka-brokers-private-dns")
        bootstrapped = ""
        for broker in brokers:
            bootstrapped = bootstrapped + "," + broker + ":9092"
        bootstrapped = bootstrapped[1:]

        terraform_lock.release()

        return bootstrapped

    def driver_host(self):
        config = {}

        terraform_lock.acquire()

        self.terraform.workspace("select", self.uid)
        drivers = self.terraform.output("kafka-driver-public-dns")
        terraform_lock.release()

        return drivers[0]
