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
import copy

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
        elif isinstance(property_value, dict):
            fixed_properties[property_name], ranged_properties[property_name] = \
                parse_properties(property_value,
                                 default_fixed_properties.get(property_name, {}),
                                 default_ranged_properties.get(property_name, {}))
            if fixed_properties[property_name] == {}:
                del fixed_properties[property_name]
            if ranged_properties[property_name] == {}:
                del ranged_properties[property_name]
        elif property_name in fixed_properties and property_value != fixed_properties[property_name]:
            ranged_properties[property_name] = [fixed_properties[property_name], property_value]
            del fixed_properties[property_name]
        else:
            fixed_properties[property_name] = property_value

    return fixed_properties, ranged_properties


def get_combination(ranged_properties):
    """
    Returns a set of all combination for all ranged and fixed properties
    """
    for combination in get_combination_internal(ranged_properties):
        yield combination


def get_combination_internal(ranged_properties):
    if len(list(ranged_properties.keys())) == 1 and isinstance(list(ranged_properties.values())[0], list):
        for property_name, values in ranged_properties.items():
            for value in values:
                yield {property_name: value}
        return

    for property_name, values in ranged_properties.items():
        if isinstance(values, dict):
            for combination in get_combination_internal(ranged_properties[property_name]):
                copy = {property_name: combination.copy()}
                if len(ranged_properties.keys()) == 1:
                    yield copy
                    continue
                dict_witout_key = ranged_properties.copy()
                del dict_witout_key[property_name]
                for combination in get_combination_internal(dict_witout_key):
                    copy.update(combination.copy())
                    yield copy
            break
        elif isinstance(values, list):
            dict_witout_key = ranged_properties.copy()
            del dict_witout_key[property_name]
            for value in values:
                for combination in get_combination_internal(dict_witout_key):
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
    merged_prop = {}
    for top_prop, top_value in properties.items():
        if top_prop in ["local", "duration", "brokers"]:
            continue
        if isinstance(top_value, dict):
            for bot_prop, bot_value in top_value.items():
                merged_prop[bot_prop] = bot_value
    file_name = properties_to_file(merged_prop)
    to_name = "/tmp/%s.properties" % (uuid.uuid4())
    sftp.put(file_name, to_name)
    return to_name


def print_properties(properties):
    print(json.dumps(properties, indent=2))


def humanize_size(size):
    for count in ['Bytes', 'KB', 'MB', 'GB']:
        if -1024.0 < size < 1024.0:
            return "%3.1f%s" % (size, count)
        size /= 1024.0
    return "%3.1f%s" % (size, 'TB')


def gen_properties_to_test(properties, ranged_properties):
    """
    :param properties: fixed properties
    :param ranged_properties: dictionary of properties with multiple values
    (e.g. {"broker-count": [3,4,5], "driver-count": [3,4,5]}
    :return: yield all the possible combination of the ranged properties
    combined with the fixed properties
    """
    if len(ranged_properties) <= 0:
        yield properties

    for res in get_combination(ranged_properties):
        to_yield = copy.deepcopy(properties)
        for key, values in res.items():
            if key in to_yield:
                to_yield[key].update(values.copy())
            else:
                to_yield[key] = values.copy()
        yield to_yield


def properties_to_client_options():
    """
    :return: stringify version of the properties (e.g. {"duration": "10"} become "--duration 10"
    properties are fetched from global configuration (p.CONF)
    """
    result = ""
    for key in CONF["drivers"]:
        result += "--%s %s " % (key, str(CONF["drivers"][key]))

    return result


def generate_uid(properties, ranged_properties):
    """
    :param properties:
    :param ranged_properties:
    :return:
    """
    ranged_values = []
    res = ""
    for key in ranged_properties.keys():
        if isinstance(properties[key], dict):
            res = generate_uid(properties[key], ranged_properties[key])
        else:
            ranged_values.append("%s-%s" % (key, properties[key]))

    if len(ranged_values) != 0:
        res = res + '_'.join(ranged_values)
    elif res == "":
        res = "prozess"
    return res
