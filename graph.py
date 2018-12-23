#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2018 gaspar_d </var/spool/mail/gaspar_d>
#
# Distributed under terms of the MIT license.

"""
Generating graphs for a specific test
"""

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import sys
import json
import os
import numpy as np


def render_3d_graph(results, xAxis, yAxix, zAxis):
    """
    Render a 3d surface plot with the required axis
    """
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    surfaces = []
    legends = []
    for json_data in results:
        xSet = set()
        ySet = set()

        for result in json_data["results"]:
            xSet.add(int(result["configuration"][xAxis]))
            ySet.add(int(result["configuration"][yAxix]))

        X = list(xSet)
        Y = list(ySet)
        X.sort()
        Y.sort()
        Z = np.zeros(shape=(len(Y), len(X)))

        for result in json_data["results"]:
            xa = int(result["configuration"][xAxis])
            ya = int(result["configuration"][yAxix])
            za = result["throughput"][zAxis] / (1024 * 1024)
            Z[Y.index(ya)][X.index(xa)] = int(za)

        xv, yv = np.meshgrid(X, Y)

        surf = ax.plot_surface(xv, yv, Z, rstride=1, cstride=1, alpha=0.8, antialiased=True)
        surf._facecolors2d = surf._facecolors3d
        surf._edgecolors2d = surf._edgecolors3d
        ax.zaxis.set_major_locator(LinearLocator(10))
        ax.zaxis.set_major_formatter(FormatStrFormatter('%d'))
        surfaces.append(surf)
        legends.append(json_data["test"])

    ax.set_xlabel(xAxis)
    ax.set_ylabel(yAxix)
    ax.set_ylim(0, max(Y) * 1.2)
    ax.set_title("kafka throughput (MB/s)")
    ax.legend(surfaces, legends)

    plt.show()


def render_2d_graph_string(results, xAxis, zAxis):
    """
    Render a 2d bar graph
    """
    fig = plt.figure()
    ax = plt.subplot(111)

    for json_data in results:
        X = []
        Y = []

        for result in json_data["results"]:
            X.append(result["configuration"][xAxis])
            Y.append(int(result["throughput"][zAxis]) / (1024 * 1024))

        ax.bar(X, Y)
        ax.yaxis.set_major_formatter(FormatStrFormatter('%d'))

    ax.set_title('kafka throughput (MB/s)')
    ax.set_ylim(0, max(Y) * 1.2)
    plt.show()


def render_2d_graph_string_from_file(results, zAxis):
    """
    Render a 2d bar graph
    """
    fig = plt.figure()
    ax = plt.subplot(111)

    for json_data in results:
        X = []
        Y = []

        for result in json_data["results"]:
            X.append(json_data["test"])
            Y.append(int(result["throughput"][zAxis]) / (1024 * 1024))

        ax.bar(X, Y)
        ax.yaxis.set_major_formatter(FormatStrFormatter('%d'))

    ax.set_title('kafka throughput (MB/s)')
    ax.set_ylim(0, max(Y) * 1.2)
    plt.show()


def render_2d_graph(results, xAxis, zAxis):
    """
    Render a 2d line graph
    """
    fig = plt.figure()
    ax = plt.subplot(111)

    for json_data in results:
        X = []
        Y = []

        for result in json_data:
            Y.append(int(result["throughput"][zAxis]) / (1024 * 1024))
            X.append(result["configuration"][xAxis])

        ax.plot(X, Y, label=xAxis, color='c', marker='o')
        ax.yaxis.set_major_formatter(FormatStrFormatter('%d'))
        ax.set_title('kafka throughput (MB/s)')

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels)
    ax.set_ylim(0, max(Y))
    ax.grid('on')
    plt.show()


def render_graph(results):
    """
    Analyze the result and render the required graph.
    """
    ranged_properties = results[0]["ranged_properties"]
    number_of_ranged_properties = len(ranged_properties)
    keys = list(ranged_properties.keys())
    if len(results) > 1:
        number_of_ranged_properties += 1

    # If there is 2 ranged properties, render a 3D surface graph
    if number_of_ranged_properties == 2:
        if isinstance(ranged_properties[keys[0]][0], int):
            render_3d_graph(results, keys[0], keys[1], "average")
        else:
            raise Exception('can not render required graph')

    # Only 1 ranged properties, if it's a number, plot a line, otherwise
    # plot a bar graph
    if number_of_ranged_properties == 1:
        if len(results) > 1:
            render_2d_graph_string_from_file(results, "average")
        elif not isinstance(ranged_properties[keys[0]][0], int):
            render_2d_graph_string(results, keys[0], "average")
        else:
            render_2d_graph(results, keys[0], "average")


def usage():
    print("Usage: python graph.py FILE1 FILE ...")


def main():
    if len(sys.argv) <= 1:
        usage()
    else:
        results = []
        for arg in sys.argv[1:]:
            handler = open(arg)
            json_data = json.load(handler)
            results.append(json_data)
        render_graph(results)


main()
