#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2018 gaspar_d </var/spool/mail/gaspar_d>
#
# Distributed under terms of the MIT license.

"""
Parse properties
"""

import tempfile
import pprint
import json
import uuid

CONFIGURATION_PATH = "./configuration.json"
CONF = json.load(open(CONFIGURATION_PATH))


def parse_properties(properties, default_fixed_properties={}, default_ranged_properties={}):
    """
     Parse the the test file configuration and return the ranged and fixed properties
    """
    fixed_properties = default_fixed_properties.copy()
    ranged_properties = default_ranged_properties.copy()

    for property_name, property_value in properties.items():
        if isinstance(property_value, list):
            ranged_properties[property_name] = property_value
        else:
            fixed_properties[property_name] = property_value

    return fixed_properties, ranged_properties


def get_combination(ranged_properties):
    """
    Returns a set of all combination for all ranged and fixed properties
    """
    for combination in get_combination_internal(ranged_properties, []):
        yield combination


def get_combination_internal(ranged_properties, visited_properties):
    for property_name, values in ranged_properties.items():
        if property_name in visited_properties:
            continue
        for value in values:
            if len(ranged_properties) - len(visited_properties) <= 1:
                yield {property_name: value}
            else:
                for combination in get_combination_internal(ranged_properties, visited_properties + [property_name]):
                    copy = combination.copy()
                    copy[property_name] = value
                    yield copy
        break


def properties_to_file(properties):
    file = tempfile.NamedTemporaryFile(delete=False)
    for prop, value in CONF["clients"].items():
        file.write(("%s=%s\n" % (prop, value)).encode("utf-8"))
    for prop, value in properties.items():
        file.write(("%s=%s\n" % (prop, value)).encode("utf-8"))
    name = file.name
    file.close()
    return name


def properties_to_aws(properties, sftp):
    file_name = properties_to_file(properties)
    to_name = "/tmp/%s.properties" % (uuid.uuid4())
    sftp.put(file_name, to_name)
    return to_name


def print_properties(properties):
    pprint.pprint(properties)


def humanize_size(size):
    for count in ['Bytes', 'KB', 'MB', 'GB']:
        if -1024.0 < size < 1024.0:
            return "%3.1f%s" % (size, count)
        size /= 1024.0
    return "%3.1f%s" % (size, 'TB')


def gen_properties_to_test(properties, ranged_properties):
    if len(ranged_properties) <= 0:
        yield properties

    for combination in get_combination(ranged_properties):
        copy = combination.copy()
        copy.update(properties)
        yield copy
