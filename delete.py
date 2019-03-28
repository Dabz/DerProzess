#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2018 gaspar_d </var/spool/mail/gaspar_d>
#
# Distributed under terms of the MIT license.

"""
Terraform Clean up
Will delete every workspace and all the content inside
"""

from lib import provision
import python_terraform
import threading
import os
import shutil


def delete_workspace(directory):
    terraform = python_terraform.Terraform(working_dir=directory)
    terraform.destroy(force=True, capture_output=False)
    if directory != "provisioning":
        shutil.rmtree(directory)


def delete_all():
    threads = []
    for directory in os.listdir("./"):
        if os.path.exists("%s/main.tf" % directory):
            th = threading.Thread(target=delete_workspace, args=[directory])
            th.start()
            threads.append(th)

    for th in threads:
        th.join()


delete_all()
