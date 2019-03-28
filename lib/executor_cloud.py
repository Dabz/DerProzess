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

    def __init__(self, properties, ranged_properties, provisioner, output_folder, test_name):
        self.output_folder = output_folder
        self.test_name = test_name
        self.provisioner = provisioner
        self.hosts = []
        self.properties = properties
        self.test_type = properties["type"]
        self.ranged_properties = ranged_properties
        self.properties["provision"] = provisioner.configurations()

        if not os.path.exists(output_folder):
            os.mkdir(output_folder)

        driver_hosts = provisioner.driver_host()
        broker_hosts = provisioner.broker_host()

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
            self.hosts.append({"ssh": ssh, "sftp": sftp, "host": driver_host, "type": "driver"})

        for broker_host in broker_hosts:
            ssh = paramiko.SSHClient()
            key = paramiko.RSAKey.from_private_key_file(provisioner.cloud_conf["ssh-key"])
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=broker_host,
                        username="ec2-user",
                        pkey=key)
            t = paramiko.Transport(broker_host, 22)
            t.connect(username="ec2-user",
                      pkey=key)
            sftp = paramiko.SFTPClient.from_transport(t)
            self.hosts.append({"ssh": ssh, "sftp": sftp, "host": broker_host, "type": "broker"})

    def run(self):
        """
        Execute the test
        """

        results = self.results_header()
        res = []

        if not self.test_type == "producer":
            print("generating some data for %s..." % (self.test_name))
            prop = self.properties_to_test[0]

            args = ' --producer --config %s --payload-size 10240 --duration 30 --partition %s'
            prop_path = p.properties_to_aws(prop, self.sftp)
            p.print_properties(prop)
            stdin, stdout, stderr = self.ssh.exec_command(executor.DRIVER_CMD + args %
                                                          (prop_path, executor.partition_count(self.provisioner.cloud_conf)))

        threads = []
        for host in self.hosts:
            if not host["type"] == "driver":
                continue
            t = threading.Thread(target=self.run_on_one_host, args=(host, self.properties, res))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

            result = executor.merge_results(res)
            results["results"].append(result)
            executor.print_result(result)

            # Aggregating and writing results locally
            results_dir = "%s/%s" % (self.output_folder, self.test_name)
            if not os.path.exists(results_dir):
                os.makedirs(results_dir)
            result_file = open("%s/%s.out" % (results_dir, self.test_type), "w+")
            result_file.write(json.dumps(results))

            # Fetching InfluxDB information
            for host in self.hosts:
                sftp = host["sftp"]
                name = host["host"]
                type = host["type"]
                metric_file_path = "%s/influx.%s.%s.out" % (results_dir, type, name)
                sftp.get("/tmp/metrics.out", metric_file_path)
                if host["type"] == "driver":
                    annotation_file_path = "%s/annotation.%s.%s.out" % (results_dir, type, name)
                    sftp.get("/tmp/annotation.out", annotation_file_path)

    def run_on_one_host(self, host, properties, results):
            ssh = host["ssh"]
            sftp = host["sftp"]

            args = ' -m --%s --partition %s --config %s --influx /tmp/annotation.out --test %s ' \
                   + p.properties_to_client_options()
            prop_path = p.properties_to_aws(properties, sftp)
            p.print_properties(properties)
            cmd = executor.DRIVER_CMD + args % (
                self.test_type,
                executor.partition_count(self.provisioner.cloud_conf),
                prop_path,
                self.test_name
            )
            _, stdout_channel, _ = ssh.exec_command(cmd)
            stdout = ""
            for line in stdout_channel.readlines():
                stdout = stdout + "\n" + line

            result = self.process_results(stdout)

            result_lock.acquire()
            results.append(result)
            result_lock.release()
