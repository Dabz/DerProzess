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
import json
from lib import properties as p
from lib import executor
from fabulous.color import *

class LocalExecutor(executor.Executor):
    """
    Class representing a single test to run (with potential multiple properties)
    """

    def __init__(self, json_data, output_folder):
        self.output_folder = output_folder
        self.provisioner = None
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

        for prop in p.gen_properties_to_test(self.properties, self.ranged_properties):
            (self.properties, _) = p.parse_properties(p.CONF["local"], prop)
            self.properties_to_test.append(self.properties)

    def run(self):
        """
        Execute the test
        """

        results = self.results_header()

        if not self.test_type == "producer":
            print(bold("generating some data for %s..." % (self.test_name)))
            prop = self.properties_to_test[0]
            args = ' --producer --config %s --payload-size %s --duration 30'
            prop_path = p.properties_to_file(prop)
            p.print_properties(prop)
            subprocess.check_output(executor.DRIVER_CMD + args % (prop_path, self.payload_size()), shell=True)

        count = 0
        for properties in self.properties_to_test:
            count += 1
            args = ' -m --%s --config %s ' + p.properties_to_client_options()
            prop_path = p.properties_to_file(properties)
            section("Test #%d" % count)
            print(bold(underline("Configuration")))
            p.print_properties(properties)
            stdout = subprocess.check_output(executor.DRIVER_CMD + args %
                                             (
                                                 self.test_type,
                                                 prop_path
                                             ),
                                             shell=True).decode('utf-8')
            result = self.process_results(stdout)

            result["configuration"] = properties
            results["results"].append(result)
            print(bold(underline("Results")))
            executor.print_result(result)

        result_file = open("%s/%s.%s.out" % (self.output_folder, self.test_name, self.test_type), "w+")
        result_file.write(json.dumps(results))
