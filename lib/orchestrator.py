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

import properties as p
import provision
from lib import executor
from threading import Thread


class CloudOrchestrator:
    """
    Class representing a single test to run (with potential multiple properties)
    """
    test_name = ""
    test_type = ""

    def __init__(self, json_data, tests):
        self.tests = tests
        self.configuration_to_test = []
        self.properties = {}
        self.ranged_properties = {}
        (self.properties, self.ranged_properties) = p.parse_properties(p.CONF["cloud"])
        (self.properties, self.ranged_properties) = p.parse_properties(json_data,
                                                                       self.properties,
                                                                       self.ranged_properties)

        for properties in p.gen_properties_to_test(self.properties, self.ranged_properties):
            self.configuration_to_test.append(properties)

    def provision(self):
        provisioners = []
        provisioning_threads = []
        for properties in self.configuration_to_test:
            p.print_properties(properties)
            provisioner = provision.Provision(properties)
            provisioning_threads.append(Thread(target=provisioner.apply_if_required()))
            provisioners.append(provisioner)

        for thread in provisioning_threads:
            thread.start()

        for thread in provisioning_threads:
            thread.join()

        return provisioners

    def run(self):
        provisioners = self.provision()
        run_threads = []

        for env in provisioners:
            thread = Thread(target=self.run_for_environment, args=[env])
            thread.start()
            run_threads.append(thread)

        for thread in run_threads:
            thread.join()

    def run_for_environment(self, environment):
        output_folder = "results_%s" % (environment.sweet_name())
        for test in self.tests:
            exe = executor.Executor(test, environment, output_folder)
            exe.run()
