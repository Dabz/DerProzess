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

    def __init__(self, tests, destroy=True):
        self.destroy = destroy
        self.tests = tests
        self.configuration_to_test = []
        (self.properties, self.ranged_properties) = p.parse_properties(p.CONF)
        for test in tests:
            (self.properties, self.ranged_properties) = p.parse_properties(test,
                                                                           self.properties,
                                                                           self.ranged_properties)

        for properties in p.gen_properties_to_test(self.properties, self.ranged_properties):
            self.configuration_to_test.append(properties)

    def run(self):
        threads = []
        for properties in self.configuration_to_test:
            test = CloudOrchestrator.CloudTest(properties, self.ranged_properties, self.destroy)
            test.start()
            threads.append(test)

            if len(threads) >= 4:
                for test in threads:
                    test.join()
                threads = []

        for test in threads:
            test.join()

    class CloudTest(Thread):
        def __init__(self, prop, ranged_prop, destroy):
            self.status = "NOT_STARTED"
            self.properties = prop
            self.ranged_properties = ranged_prop
            self.test_name = p.generate_uid(prop, ranged_prop)
            self.destroy = destroy
            Thread.__init__(self)

        def run(self):
            self.status = "PROVISIONING"
            provisioner = provision.Provision(self.properties, self.test_name)
            section(provisioner.sweet_name())
            provisioner.apply_if_required()
            self.status = "TESTING"
            output_folder = "results_%s" % (provisioner.sweet_name())
            exe = executor_cloud.CloudExecutor(self.properties, self.ranged_properties, provisioner, output_folder, self.test_name)
            exe.run()
            if self.destroy:
                self.status = "DESTROYING"
                provisioner.destroy()
                self.status = "DESTROYED"




