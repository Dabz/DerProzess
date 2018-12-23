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

import json
import numpy
from lib import properties as p
from fabulous.color import  *

JVM_OPTION = ""
DRIVER_CMD = "java %s -jar driver/target/driver-1.0-SNAPSHOT-jar-with-dependencies.jar" % JVM_OPTION


def print_result(results):
    print(plain(underline("Results")))
    print(json.dumps({"throughput": humanize_section(results["throughput"]),
                      "latency": humanize_section(results["latency"])},
                     indent=2))


def humanize_section(results):
    human_results = {"average": p.humanize_size(results["average"]),
                     "max": p.humanize_size(results["max"]),
                     "min": p.humanize_size(results["min"]),
                     "median": p.humanize_size(results["median"])}
    return human_results


def compute_section(metrics, lines):
    average = numpy.asscalar(numpy.mean(metrics))
    max = numpy.asscalar(numpy.max(metrics))
    min = numpy.asscalar(numpy.min(metrics))
    median = numpy.asscalar(numpy.median(metrics))

    return {"average": average,
            "max": max,
            "min": min,
            "count": len(lines),
            "median": median}


def merge_section(metrics):
    average_throughtput = numpy.asscalar(numpy.mean([res["average"] for res in metrics]))
    max = numpy.asscalar(numpy.max([res["max"] for res in metrics]))
    min = numpy.asscalar(numpy.max([res["min"] for res in metrics]))
    median = numpy.asscalar(numpy.median([res["median"] for res in metrics]))
    count = numpy.asscalar(numpy.sum([res["count"] for res in metrics]))
    number_of_driver = len(metrics)

    return {"average": average_throughtput * number_of_driver,
            "max": max,
            "min": min,
            "median": median * number_of_driver,
            "count": count}


def merge_results(results):
    return {"throughput": merge_section([res["throughput"] for res in results]),
            "latency": merge_section([res["latency"] for res in results])}


class Executor:
    """
    Class representing a single test to run (with potential multiple properties)
    """

    def __init__(self):
        pass

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

    def results_header(self):
        result = {"test": self.test_name,
                  "type": self.test_type,
                  "results": [],
                  "ranged_properties": self.ranged_properties,
                  "fixed_properties": self.properties}

        if not self.is_local():
            result["cloud"] = self.provisioner.cloud_conf

        return result

    def run(self):
        """
        Execute the test
        """
        pass

    def process_results(self, results):
        """
        Take the stdout of the driver command and generate simple stats on it
        e.g. median, average, max, etc..
        """
        lines = results.splitlines()
        throughput = []
        latency = []
        for line in lines:
            if line is None or line == "":
                continue
            csv = line.split(",")
            throughput.append(int(csv[0]))
            latency.append(int(csv[1]))

        return {"throughput": compute_section(throughput, lines),
                "latency": compute_section(latency, lines)
                }
