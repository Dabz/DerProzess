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

terraform_lock = threading.Lock()
terraform = python_terraform.Terraform(working_dir=provision.WORKING_DIR)


def delete_workspace(workspace):
    terraform_lock.acquire()
    terraform.workspace("select", workspace)
    terraform.destroy(force=True, capture_output=False)
    terraform.workspace("select", "default")
    terraform.workspace("delete", workspace)
    terraform_lock.release()


def delete_all():
    workspaces_raw = str(terraform.workspace("list")[1])
    workspaces = workspaces_raw.splitlines()
    threads = []
    for workspace in workspaces:
        workspace = workspace.replace("*", "")
        workspace = workspace.strip()
        if workspace == "default":
            continue
        if workspace == "":
            continue
        th = threading.Thread(target=delete_workspace, args=[workspace])
        th.start()
        threads.append(th)

    for th in threads:
        th.join()


delete_all()
