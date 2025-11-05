#!/bin/env python
""" Validates zonefiles using the external named-checkzones command """
import os
import re
import subprocess
import sys
from rich.console import Console
from rich import print as rprint


def get_files(paths) -> list:
    """return all files matching *-rev and *-fwd in the directory passed in the "paths" list"""
    files = []
    for path in paths:
        try:
            for file in os.listdir(path):
                if file.endswith("-rev") or file.endswith("-fwd"):
                    files.append(os.path.join(path, file))
        except NotADirectoryError:
            files.append(path)
    return files


def get_zone(zone) -> str:
    """Given the zone file in "zone", find the SOA record to determine what
    zone this file is representing"""
    with open(zone, "r", encoding="UTF-8") as zonefile:
        for line in zonefile:
            if re.search("(.*)SOA(.*)", line):
                return line.split()[0]
    # this should never git hit, but adding this to make a valid case
    # where it would return the same type even if it somehow did
    return ""


def check_zone(zone: str, zonefile: str) -> tuple:
    """execute named_checkzone for the zone(name) and the zonefile given
    returns a tuple of True/False for the validity, and the results
    named_checkzone returned to stdout"""
    console = Console()
    checkzone_bin = "/usr/sbin/named-checkzone"
    # verify the given zonefile using named-checkzone and return a tuple of
    # the succes and the output from stdout
    try:
        with console.status(f"{zonefile}", spinner="point"):
            results = subprocess.run(
                [checkzone_bin, zone, zonefile], capture_output=True, check=True
            )
        if results.returncode == 0:
            return (True, results.stdout)
    except subprocess.CalledProcessError as error:
        return (False, error)
    return (False, "Unhandled excpetion")


def main(files=None):  # pragma: no cover
    """Main logic that runs through the files given and outputs the results"""
    try:
        if not files:
            files = get_files(sys.argv[1:])
    except FileNotFoundError as error:
        print("error:  Could not open file passed")
        print(error)
        sys.exit(1)
    for filename in files:
        myzone = get_zone(filename)
        status = {True: "[green]✓[/]", False: "❌"}
        if myzone:
            result = check_zone(myzone, filename)
            rprint(f"{filename}: {myzone} -> {status[result[0]]}")
            if result[0] is not True:
                print(result[1].decode())

                sys.exit(9)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter # pragma: no cover
