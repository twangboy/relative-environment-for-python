"""
Common classes and values used around mayflower
"""

import os
import pathlib
import platform
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request

MODULE_DIR = pathlib.Path(__file__).resolve().parent
WORK_IN_CWD = False
PIPE = subprocess.PIPE

if sys.platform == 'win32':
    DEFAULT_DATADIR = pathlib.Path.home() / "AppData" / "Local" / "mayflower"
else:
    DEFAULT_DATADIR = pathlib.Path.home() / ".local" / "mayflower"

DATADIR = os.environ.get("MAYFLOWER_DATA", DEFAULT_DATADIR)


class MayflowerException(Exception):
    """
    Base class for exeptions generated from mayflower
    """


def work_root(root=None):
    """
    Get the root directory that all other mayflower working directories should be based on.

    :param root: An explicitly requested root directory
    :type root: str

    :return: An absolute path to the mayflower root working directory
    :rtype: ``pathlib.Path``
    """
    if root is not None:
        base = pathlib.Path(root).resolve()
    elif WORK_IN_CWD:
        base = pathlib.Path(os.getcwd()).resolve()
    else:
        base = MODULE_DIR
    return base


def work_dir(name, root=None):
    """
    Get the absolute path to the mayflower working directory of the given name.

    :param name: The name of the directory
    :type name: str
    :param root: The root directory that this working directory will be relative to
    :type root: str

    :return: An absolute path to the requested mayflower working directory
    :rtype: ``pathlib.Path``
    """
    root = work_root(root)
    if root == MODULE_DIR:
        base = root / "_{}".format(name)
    else:
        base = root / name
    return base


class WorkDirs:
    """
    Simple class used to hold references to working directories mayflower uses relative to a given root.

    :param root: The root of the working directories tree
    :type root: str
    """

    def __init__(self, root):
        self.root = root
        self.toolchain_config = work_dir("toolchain", self.root)
        self.toolchain = work_dir("toolchain", DATADIR)
        self.build = work_dir("build", DATADIR)
        self.src = work_dir("src", DATADIR)
        self.logs = work_dir("logs", DATADIR)
        self.download = work_dir("download", DATADIR)

    def __getstate__(self):
        """
        Return an object used for pickling.

        :return: The picklable state
        """
        return {
            "root": self.root,
            "toolchain_config": self.toolchain_config,
            "toolchain": self.toolchain,
            "build": self.build,
            "src": self.src,
            "logs": self.logs,
            "download": self.download,
        }

    def __setstate__(self, state):
        """
        Unwrap the object returned from unpickling.

        :param state: The state to unpickle
        :type state: dict
        """
        self.root = state["root"]
        self.toolchain_config = state["toolchain_config"]
        self.toolchain = state["toolchain"]
        self.build = state["build"]
        self.src = state["src"]
        self.logs = state["logs"]
        self.download = state["download"]


def work_dirs(root=None):
    """
    Returns a WorkDirs instance based on the given root.

    :param root: The desired root of mayflower's working directories
    :type root: str

    :return: A WorkDirs instance based on the given root
    :rtype: ``mayflower.common.WorkDirs``
    """
    return WorkDirs(work_root(root))


def get_toolchain(arch=None, root=None):
    """
    Get a the toolchain directory, specific to the arch if supplied.

    :param arch: The architecture to get the toolchain for
    :type arch: str
    :param root: The root of the mayflower working directories to search in
    :type root: str

    :return: The directory holding the toolchain
    :rtype: ``pathlib.Path``
    """
    dirs = work_dirs(root)
    if arch:
        return dirs.toolchain / "{}-linux-gnu".format(arch)
    return dirs.toolchain


def get_triplet(machine=None, plat=None):
    """
    Get the target triplet for the specfied machine and platform.

    If any of the args are None, it will try to deduce what they should be.

    :param machine: The machine for the triplet
    :type machine: str
    :param plat: The platform for the triplet
    :type plat: str

    :raises MayflowerException: If the platform is unknown

    :return: The target triplet
    :rtype: str
    """
    if not plat:
        plat = sys.platform
    if not machine:
        machine = platform.machine()
    machine = machine.lower()
    if plat == "darwin":
        return f"{machine}-macos"
    elif plat == "win32":
        return f"{machine}-win"
    elif plat == "linux":
        return f"{machine}-linux-gnu"
    else:
        raise MayflowerException("Unknown platform {}".format(platform))


def archived_build(triplet=None):
    """
    Finds a the location of an archived build.

    :param triplet: The build triplet to find
    :type triplet: str

    :return: The location of the archived build
    :rtype: ``pathlib.Path``
    """
    if not triplet:
        triplet = get_triplet()
    dirs = work_dirs(DATADIR)
    return (dirs.build / triplet).with_suffix(".tar.xz")


def extract_archive(to_dir, archive):
    """
    Extract an archive to a specific location

    :param to_dir: The directory to extract to
    :type to_dir: str
    :param archive: The archive to extract
    :type archive: str
    """
    if archive.endswith("tgz"):
        read_type = "r:gz"
    elif archive.endswith("xz"):
        read_type = "r:xz"
    elif archive.endswith("bz2"):
        read_type = "r:bz2"
    else:
        read_type = "r"
    with tarfile.open(archive, read_type) as t:
        t.extractall(to_dir)


def download_url(url, dest):
    """
    Download the url to the provided destination. This method assumes the last
    part of the url is a filename. (https://foo.com/bar/myfile.tar.xz)

    :param url: The url to download
    :type url: str
    :param dest: Where to download the url to
    :type dest: str

    :raises urllib.error.HTTPError: If the url was unable to be downloaded

    :return: The path to the downloaded content
    :rtype: str
    """
    local = os.path.join(dest, os.path.basename(url))
    n = 0
    while n < 3:
        n += 1
        try:
            fin = urllib.request.urlopen(url)
        except urllib.error.HTTPError as exc:
            if n == 3:
                raise
            print("Unable to download: %s %r".format(url, exc))
            time.sleep(n + 1 * 10)
    fout = open(local, "wb")
    block = fin.read(10240)
    try:
        while block:
            fout.write(block)
            block = fin.read(10240)
        fin.close()
        fout.close()
    except:
        try:
            os.unlink(local)
        except OSError:
            pass
        raise
    return local


def runcmd(*args, **kwargs):
    """
    Run the provided command, raising an Exception when the command finishes
    with a non zero exit code.  Arguments are passed through to ``subprocess.run``

    :return: The process result
    :rtype: ``subprocess.CompletedProcess``

    :raises MayflowerException: If the command finishes with a non zero exit code
    """
    proc = subprocess.run(*args, **kwargs)
    if proc.returncode != 0:
        raise MayflowerException("Build cmd '{}' failed".format(" ".join(args[0])))
    return proc
