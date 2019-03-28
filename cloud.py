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
import os
import argparse
from lib import orchestrator
from fabulous import color


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


def launch_test(args):
    tests = []
    if len(args.tests) <= 0:
        list_of_files = os.listdir('./tests')
        for file in list_of_files:
            handler = open("./tests/" + file)
            json_data = json.load(handler)
            tests.append(json_data)
    else:
        for test in args.tests:
            handler = open(test)
            json_data = json.load(handler)
            tests.append(json_data)

    orch = orchestrator.CloudOrchestrator(tests, destroy=args.destroy)
    orch.run()


parser = argparse.ArgumentParser(description='Kafka load test on AWS')
parser.add_argument('--keep',
                    dest='destroy',
                    help='destroy the environment after testing',
                    action='store_false')

parser.add_argument('tests', nargs='*', help='test files')

args = parser.parse_args()

color.section("Der Prozess - Cloud Orchestrator!")
launch_test(args)
