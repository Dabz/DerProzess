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


"""
Render a 3d surface plot with the required axis
"""
def render_3d_graph(json_data, xAxis, yAxix, zAxis):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    xSet = set()
    ySet = set()

    for result in json_data:
        xSet.add(int(result["configuration"][xAxis]))
        ySet.add(int(result["configuration"][yAxix]))

    X = list(xSet)
    Y = list(ySet)
    X.sort()
    Y.sort()
    Z = np.zeros(shape=(len(Y), len(X)))

    for result in json_data:
        xa = int(result["configuration"][xAxis])
        ya = int(result["configuration"][yAxix])
        za = result[zAxis] / (1024 * 1024)
        Z[Y.index(ya)][X.index(xa)] = int(za)

    xv, yv = np.meshgrid(X, Y)

    surf = ax.plot_surface(xv, yv, Z, cmap='summer', rstride=1, cstride=1, alpha=0.8, antialiased=True)
    ax.zaxis.set_major_locator(LinearLocator(10))
    ax.zaxis.set_major_formatter(FormatStrFormatter('%d'))
    ax.set_xlabel(xAxis)
    ax.set_ylabel(yAxix)
    ax.set_title("kafka throughput (MB/s)")


    plt.show()

"""
Render a 2d bar graph
"""
def render_2d_graph_string(json_data, xAxis, zAxis):
    fig = plt.figure()
    ax = plt.subplot(111)

    X = []
    Y = []

    for result in json_data:
        X.append(result["configuration"][xAxis])
        Y.append(int(result[zAxis]) / (1024 * 1024))

    ax.bar(X, Y)
    ax.yaxis.set_major_formatter(FormatStrFormatter('%d'))
    ax.set_title('kafka throughput (MB/s)')
    ax.set_ylim(0, max(Y))
    plt.show()


"""
Render a 2d line graph
"""
def render_2d_graph(json_data, xAxis, zAxis):
    fig = plt.figure()
    ax = plt.subplot(111)

    X = []
    Y = []

    for result in json_data:
        Y.append(int(result[zAxis]) / (1024 * 1024))
        X.append(result["configuration"][xAxis])

    ax.plot(X, Y, label=xAxis, color='c', marker='o')
    ax.yaxis.set_major_formatter(FormatStrFormatter('%d'))
    ax.set_title('kafka throughput (MB/s)')
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels)
    ax.set_ylim(0, max(Y))
    ax.grid('on')
    plt.show()



"""
Analyze the result and render the required graph.
"""
def render_graph(json_data):
    ranged_properties = json_data["ranged_properties"]

    keys = list(ranged_properties.keys())
    # If there is 2 ranged properties, render a 3D surface graph
    if len(ranged_properties) == 2:
        if isinstance(ranged_properties[keys[0]][0], int):
            render_3d_graph(json_data["results"], keys[0], keys[1], "average")
        else:
            raise Exception('can not render required graph')

    # Only 1 ranged properties, if it's a number, plot a line, otherwise
    # plot a bar graph
    if len(ranged_properties) == 1:
        if isinstance(ranged_properties[keys[0]][0], int):
            render_2d_graph(json_data["results"], keys[0], "average")
        else:
            render_2d_graph_string(json_data["results"], keys[0], "average")


def usage():
    print("Usage: python graph.py FILE1 FILE ...")


def main():
    if len(sys.argv) <= 1:
        usage()
    else:
        for arg in sys.argv[1:]:
            handler = open(arg)
            json_data = json.load(handler)
            render_graph(json_data)


main()
