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

JVM_OPTION = ""
DRIVER_CMD = "java %s -jar java/driver/target/driver-1.0-SNAPSHOT-jar-with-dependencies.jar" % JVM_OPTION
CONFIGURATION_PATH="./configuration.json"
CONF=json.load(open(CONFIGURATION_PATH))


"""
Class representing a single test to run (with potential multiple properties)
"""
class BenchTest:
    test_name = ""
    test_type = ""

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

    """
    Parse the the test file configuration and return the ranged and fixed properties
    """
    def parse_properties(self, properties):
        fixed_properties = {}
        ranged_properties = {}
        for property_name, property_value in properties.items():
            if isinstance(property_value, list):
                ranged_properties[property_name] = property_value
            else:
                fixed_properties[property_name] = property_value
        return fixed_properties, ranged_properties


    """
    Returns a set of all combinatoin for all ranged and fixed properties
    """
    def get_combination(self, ranged_properties):
        for combination in self.get_combination_internal(ranged_properties, []):
            yield combination

    def get_combination_internal(self, ranged_properties, visited_properties):
        for property_name, values in ranged_properties.items():
            if property_name in visited_properties:
                continue
            for value in values:
                if len(ranged_properties) - len(visited_properties) <= 1:
                    yield {property_name: value}
                else:
                    for combination in self.get_combination_internal(ranged_properties, visited_properties + [property_name]):
                        copy = combination.copy()
                        copy[property_name] = value
                        yield copy
            break

    def gen_properties_to_test(self):
        if len(self.ranged_properties) <= 0:
            yield self.properties

        for combination in self.get_combination(self.ranged_properties):
            copy = combination.copy()
            copy.update(self.properties)
            yield copy

    def __init__(self, json_data):
        self.properties_to_test = []
        self.properties = []
        self.ranged_properties = []
        self.test_name = json_data["test"]
        self.test_type = json_data["type"]
        (self.properties, self.ranged_properties) = self.parse_properties(json_data["properties"])

        for properties in self.gen_properties_to_test():
            self.properties_to_test.append(properties)

    def propertie_to_file(self, properties):
        file = tempfile.NamedTemporaryFile(delete=False)
        for prop, value in CONF.items():
            if not prop in ["zookeeper"]:
                file.write(("%s=%s\n" % (prop, value)).encode("utf-8"))
        for prop, value in properties.items():
            file.write(("%s=%s\n" % (prop, value)).encode("utf-8"))
        name = file.name
        file.close()
        return name

    def print_properties(self, properties):
        pprint.pprint(properties)

    def humanize_size(self, size):
        for count in ['Bytes', 'KB', 'MB', 'GB']:
            if size > -1024.0 and size < 1024.0:
                return "%3.1f%s" % (size, count)
            size /= 1024.0
        return "%3.1f%s" % (size, 'TB')

    def print_result(self, results):
        human_results = {"average": self.humanize_size(results["average"]),
                         "max": self.humanize_size(results["max"]),
                         "min": self.humanize_size(results["min"]),
                         "median": self.humanize_size(results["median"])}
        pprint.pprint(human_results)

    def results_header(self):
        return {"test": self.test_name,
                "type": self.test_type,
                "results": [],
                "ranged_properties": self.ranged_properties,
                "fixed_properties": self.properties}

    """
    Take the stdout of the driver command and generate simple stats on it
    e.g. median, average, max, etc..
    """
    def process_results(self, results):
        lines = results.splitlines()
        throughput = []
        for line in lines:
            throughput.append(int(line))

        average_throughput = numpy.asscalar(numpy.mean(throughput))
        max = numpy.asscalar(numpy.max(throughput))
        min = numpy.asscalar(numpy.min(throughput))
        median = numpy.asscalar(numpy.median(throughput))

        return {"average": average_throughput,
                "max": max,
                "min": min,
                "median": median}

    """
    Execute the test 
    """
    def run(self):
        results = self.results_header()

        print("deleting topic __driver...")
        try:
            subprocess.check_output("kafka-topics --zookeeper %s --topic __driver --delete " % CONF["zookeeper"], shell=True)
        except subprocess.CalledProcessError as e:
            print(e.output)

        print("creating topic __driver...")
        try:
            subprocess.check_output("kafka-topics --zookeeper %s --topic __driver --create --replication-factor 1 --partitions 32 --config retention.bytes=21474836480" % CONF["zookeeper"], shell=True)
        except subprocess.CalledProcessError as e:
            print(e.output)

        if not self.test_type == "producer":
            print("generating some data for %s..." % (self.test_name))
            first_prop = self.properties_to_test[0]
            prop = {'bootstrap.servers': CONF['bootstrap.servers']}
            self.print_properties(prop)
            prop_path = self.propertie_to_file(prop)
            subprocess.check_output(DRIVER_CMD + ' --producer --config %s --payload-size %s --duration 30' %
                           (
                               prop_path,
                               self.payload_size()
                           ),
                           shell=True)

        print("starting testing %s for %s..." % (self.test_type, self.test_name))
        for properties in self.properties_to_test:
            self.print_properties(properties)
            prop_path = self.propertie_to_file(properties)
            stdout = subprocess.check_output(DRIVER_CMD + ' --%s --config %s --payload-size %s -m' %
                                             (
                                                 self.test_type,
                                                 prop_path,
                                                 self.payload_size()
                                             ),
                                             shell=True).decode('utf-8')
            result = self.process_results(stdout)
            result["configuration"] = properties
            results["results"].append(result)
            self.print_result(result)

        result_file = open("results/%s.%s.out" % (self.test_name, self.test_type), "w+")
        result_file.write(json.dumps(results))


def launch_test():
    if len(sys.argv) <= 1:
        list_of_files = os.listdir('./properties')
        for file in list_of_files:
            handler = open("./properties/" + file)
            json_data = json.load(handler)
            test = BenchTest(json_data)
            test.run()
    else:
        for arg in sys.argv[1:]:
            handler = open(arg)
            json_data = json.load(handler)
            test = BenchTest(json_data)
            test.run()


launch_test()
