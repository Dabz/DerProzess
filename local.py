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
import os
from lib import executor


def launch_test():
    if len(sys.argv) <= 1:
        list_of_files = os.listdir('./tests')
        for file in list_of_files:
            handler = open("./tests/" + file)
            json_data = json.load(handler)
            test = executor.Executor(json_data, None, "results")
            test.run()
    else:
        for arg in sys.argv[1:]:
            handler = open(arg)
            json_data = json.load(handler)
            test = executor.Executor(json_data, None, "results")
            test.run()


launch_test()
