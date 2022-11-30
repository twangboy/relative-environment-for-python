# Copyright 2022 VMware, Inc.
# SPDX-License-Identifier: Apache-2
"""
The ``relenv fetch`` command.
"""

import os
import sys

from .build import platform_module
from .common import (
    DATA_DIR,
    build_arch,
    download_url,
    get_triplet,
    work_dir,
)


def setup_parser(subparsers):
    """
    Setup the subparser for the ``fetch`` command.

    :param subparsers: The subparsers object returned from ``add_subparsers``
    :type subparsers: argparse._SubParsersAction
    """
    mod = platform_module()
    subparser = subparsers.add_parser("fetch", description="Fetch relenv builds")
    subparser.set_defaults(func=main)
    subparser.add_argument(
        "--arch",
        default=build_arch(),
        choices=mod.ARCHES,
        type=str,
        help="Architecture to download. [default: %(default)s]",
    )


def main(args):
    """
    The entrypoint into the ``relenv fetch`` command.

    :param args: The args passed to the command
    :type args: argparse.Namespace
    """
    version = os.environ.get("RELENV_FETCH_VERSION", "latest")
    triplet = get_triplet(machine=args.arch)
    url = f"https://woz.io/relenv/{version}/build/{triplet}.tar.xz"
    builddir = work_dir("build", DATA_DIR)
    os.makedirs(builddir, exist_ok=True)
    archive = download_url(url, builddir)
