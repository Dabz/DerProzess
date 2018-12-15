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
import tempfile
import pprint
import numpy
import json
import sys
import time
import properties as p
import paramiko

JVM_OPTION = ""
DRIVER_CMD = "java %s -jar driver/target/driver-1.0-SNAPSHOT-jar-with-dependencies.jar" % JVM_OPTION


def print_result(results):
    human_results = {"average": p.humanize_size(results["average"]),
                     "max": p.humanize_size(results["max"]),
                     "min": p.humanize_size(results["min"]),
                     "median": p.humanize_size(results["median"])}
    pprint.pprint(human_results)


class Executor:
    """
    Class representing a single test to run (with potential multiple properties)
    """

    """
    Contains all the set of properties that need to be tested 
    e.g. all combination possible for the ranged properties
    """
    properties_to_test = []

    """
    Contains all the fixed (immutable) properties that need
    to be used in the test
    """
    properties = []

    """
    Contains the set of properties that need are containing multiple values
    """
    ranged_properties = []

    def payload_size(self):
        return 1024

    def is_local(self):
        return self.provisioner is None

    def __init__(self, json_data, provisioner, output_folder):
        self.output_folder = output_folder
        self.provisioner = provisioner
        self.properties_to_test = []
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

        if not self.is_local():
            driver_host = provisioner.driver_host()

            self.ssh = paramiko.SSHClient()
            key = paramiko.RSAKey.from_private_key_file(provisioner.cloud_conf["ssh-key"])
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(hostname=driver_host,
                             username="ec2-user",
                             pkey=key)
            t = paramiko.Transport(driver_host, 22)
            t.connect(username="ec2-user",
                      pkey=key)
            self.sftp = paramiko.SFTPClient.from_transport(t)

        for prop in p.gen_properties_to_test(self.properties, self.ranged_properties):
            if self.is_local():
                (self.properties, _) = p.parse_properties(p.CONF["local"], prop)

            else:
                (self.properties, _) = p.parse_properties(provisioner.configurations(), prop)

            self.properties_to_test.append(self.properties)

    def results_header(self):
        return {"test": self.test_name,
                "type": self.test_type,
                "results": [],
                "ranged_properties": self.ranged_properties,
                "fixed_properties": self.properties}

    def run(self):
        """
        Execute the test
        """

        results = self.results_header()

        if not self.test_type == "producer":
            print("generating some data for %s..." % (self.test_name))
            prop = self.properties_to_test[0]

            args = ' --producer --config %s --payload-size %s --duration 30'
            if self.is_local():
                prop_path = p.properties_to_file(prop)
                p.print_properties(prop)
                subprocess.check_output(DRIVER_CMD + args % (prop_path, self.payload_size()), shell=True)
            else:
                prop_path = p.properties_to_aws(prop, self.sftp)
                p.print_properties(prop)
                stdin, stdout, stderr = self.ssh.exec_command(DRIVER_CMD + args % (prop_path, self.payload_size()))

        print("starting testing %s for %s..." % (self.test_type, self.test_name))
        for properties in self.properties_to_test:
            args = ' --%s --config %s --payload-size %s -m --duration %s'
            if self.is_local():
                prop_path = p.properties_to_file(properties)
                p.print_properties(properties)
                stdout = subprocess.check_output(DRIVER_CMD + args %
                                                 (
                                                     self.test_type,
                                                     prop_path,
                                                     self.payload_size(),
                                                     p.CONF['duration']
                                                 ),
                                                 shell=True).decode('utf-8')
                result = self.process_results(stdout)
            else:
                prop_path = p.properties_to_aws(properties, self.sftp)
                p.print_properties(properties)
                _, stdout_channel, _ = self.ssh.exec_command(DRIVER_CMD + args %
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

            result["configuration"] = properties
            results["results"].append(result)
            print_result(result)

        result_file = open("%s/%s.%s.out" % (self.output_folder, self.test_name, self.test_type), "w+")
        result_file.write(json.dumps(results))

    def process_results(self, results):
        """
        Take the stdout of the driver command and generate simple stats on it
        e.g. median, average, max, etc..
        """
        lines = results.splitlines()
        throughput = []
        for line in lines:
            if line is not None and not line == "":
                throughput.append(int(line))

        average_throughput = numpy.asscalar(numpy.mean(throughput))
        max = numpy.asscalar(numpy.max(throughput))
        min = numpy.asscalar(numpy.min(throughput))
        median = numpy.asscalar(numpy.median(throughput))

        return {"average": average_throughput,
                "max": max,
                "min": min,
                "median": median}
