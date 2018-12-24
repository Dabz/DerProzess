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

from lib import properties as p
from lib import provision
from lib import executor_cloud
from threading import Thread
from fabulous.color import *
import json


class CloudOrchestrator:
    """
    Class representing a single test to run (with potential multiple properties)
    """
    test_name = ""
    test_type = ""

    def __init__(self, json_data, tests, destroy=True):
        self.destroy = destroy
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

    def run(self):
        for properties in self.configuration_to_test:
            provisioner = provision.Provision(properties, self.ranged_properties)
            section(provisioner.sweet_name())
            print(bold("Configuration"))
            print(json.dumps(properties, indent=2))
            print(plain(bold("Provisioning "), underline(bold(provisioner.sweet_name()))))
            provisioner.apply_if_required()
            print(plain(bold("Benchmarking")))
            self.run_for_environment(provisioner)
            if self.destroy:
                print(plain(bold("Destroying")))
                provisioner.destroy()

        if not self.destroy:
            print(plain(blink(underline("Don't forget to destroy the provisioned resources! (python delete.py)"))))

    def run_for_environment(self, environment):
        output_folder = "results_%s" % (environment.sweet_name())
        for test in self.tests:
            exe = executor_cloud.CloudExecutor(test, environment, output_folder)
            exe.run()
