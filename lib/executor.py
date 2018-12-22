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
import paramiko
from lib import properties as p

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
                "count": len(lines),
                "median": median}

    def merge_results(self, results):
        average_throughtput = numpy.asscalar(numpy.mean([res["average"] for res in results]))
        max = numpy.asscalar(numpy.max([res["max"] for res in results]))
        min = numpy.asscalar(numpy.max([res["min"] for res in results]))
        median = numpy.asscalar(numpy.median([res["median"] for res in results]))
        count = numpy.asscalar(numpy.sum([res["count"] for res in results]))

        return {"average": average_throughtput,
                "max": max,
                "min": min,
                "median": median,
                "count": count}
