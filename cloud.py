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

import sys
import json
from lib import orchestrator
import os


def gen_broker_config(tests):
    """
    :param tests: all the test to execute in the environment
    :return: the combination of all the broker to create with the ranged/fixed properties format:
    { "instance-type": ["t2.xlarge", "t2.large"], "count": 3 }
    """
    brokers = {}
    for test in tests:
        if "brokers" in test.keys():
            for key, value in test["brokers"].items():
                if key in brokers.keys():
                    if isinstance(brokers[key], list) and value not in brokers[key]:
                        brokers[key].append(value)
                    elif not brokers[key] == value:
                        cv = brokers[key]
                        brokers[key] = [cv, value]
                else:
                    brokers[key] = value

    return brokers


def launch_test():
    tests = []
    if len(sys.argv) <= 1:
        list_of_files = os.listdir('./tests')
        for file in list_of_files:
            handler = open("./tests/" + file)
            json_data = json.load(handler)
            tests.append(json_data)
    else:
        for arg in sys.argv[1:]:
            handler = open(arg)
            json_data = json.load(handler)
            tests.append(json_data)

    brokers = gen_broker_config(tests)
    orch = orchestrator.CloudOrchestrator(brokers, tests)
    orch.run()


launch_test()
