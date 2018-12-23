#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2018 gaspar_d </var/spool/mail/gaspar_d>
#
# Distributed under terms of the MIT license.

"""
Start local benchmarking of all the properties
Tests should be located in the properties folder
"""

import os
import subprocess
import pprint
import numpy
import threading
import json
import paramiko
from lib import executor
from lib import properties as p

result_lock = threading.Lock()


class CloudExecutor(executor.Executor):
    """
    Class representing a single test to run (with potential multiple properties)
    """

    def __init__(self, json_data, provisioner, output_folder):
        self.output_folder = output_folder
        self.provisioner = provisioner
        self.properties_to_test = []
        self.hosts = []
        self.properties = {}
        self.ranged_properties = {}
        self.test_name = json_data["test"]
        self.test_type = json_data["type"]
        (self.properties, self.ranged_properties) = p.parse_properties(p.CONF["clients"])
        (self.properties, self.ranged_properties) = p.parse_properties(json_data["properties"],
                                                                       self.properties,
                                                                       self.ranged_properties)

        if not os.path.exists(output_folder):
            os.mkdir(output_folder)

        self.test_name = "%s_%s" % (self.test_name, provisioner.sweet_name())
        driver_hosts = provisioner.driver_host()

        for driver_host in driver_hosts:
            ssh = paramiko.SSHClient()
            key = paramiko.RSAKey.from_private_key_file(provisioner.cloud_conf["ssh-key"])
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=driver_host,
                        username="ec2-user",
                        pkey=key)
            t = paramiko.Transport(driver_host, 22)
            t.connect(username="ec2-user",
                      pkey=key)
            sftp = paramiko.SFTPClient.from_transport(t)
            self.hosts.append({"ssh": ssh, "sftp": sftp, "host": driver_host})

        for prop in p.gen_properties_to_test(self.properties, self.ranged_properties):
            if self.is_local():
                (self.properties, _) = p.parse_properties(p.CONF["local"], prop)

            else:
                (self.properties, _) = p.parse_properties(provisioner.configurations(), prop)

            self.properties_to_test.append(self.properties)

    def run(self):
        """
        Execute the test
        """

        results = self.results_header()
        res = []

        if not self.test_type == "producer":
            print("generating some data for %s..." % (self.test_name))
            prop = self.properties_to_test[0]

            args = ' --producer --config %s --payload-size %s --duration 30'
            prop_path = p.properties_to_aws(prop, self.sftp)
            p.print_properties(prop)
            stdin, stdout, stderr = self.ssh.exec_command(executor.DRIVER_CMD + args % (prop_path, self.payload_size()))

        for properties in self.properties_to_test:
            threads = []
            for host in self.hosts:
                t = threading.Thread(target=self.run_on_one_host, args=(host, properties, res))
                t.start()
                threads.append(t)

            for t in threads:
                t.join()

            result = executor.merge_results(res)
            results["results"].append(result)

            executor.print_result(result)
            result_file = open("%s/%s.%s.out" % (self.output_folder, self.test_name, self.test_type), "w+")
            result_file.write(json.dumps(results))

    def run_on_one_host(self, host, properties, results):
            ssh = host["ssh"]
            sftp = host["sftp"]
            driver_host = host["host"]

            args = ' --%s --config %s --payload-size %s -m --duration %s'
            prop_path = p.properties_to_aws(properties, sftp)
            p.print_properties(properties)
            _, stdout_channel, _ = ssh.exec_command(executor.DRIVER_CMD + args %
                                                    (
                                                        self.test_type,
                                                        prop_path,
                                                        self.payload_size(),
                                                        p.CONF['duration']
                                                    ))
            stdout = ""
            for line in stdout_channel.readlines():
                stdout = stdout + "\n" + line

            result = self.process_results(stdout)

            result_lock.acquire()
            results.append(result)
            result_lock.release()
