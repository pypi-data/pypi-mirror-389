#
# Copyright (c) 2021 Dilili Labs, Inc.  All rights reserved. Contains Dilili Labs Proprietary Information. RESTRICTED COMPUTER SOFTWARE.  LIMITED RIGHTS DATA.
#

import json
import subprocess
from argparse import ArgumentParser

import requests

try:
    from .command_utils import command, subcommand_parse_args, by_name
except ImportError:
    from command_utils import command, subcommand_parse_args, by_name

header = [
    "Copyright (c) 2021 Dilili Labs, Inc.  All rights reserved.\n\n"
    "bf_info utility checks BrainFrame system information and all inference computing dependencies.\n"
    "=======\n"
]

footer = ["\n\n"]

#
# Check if BrainFrame is still alive?
#
#         curl http://localhost/api/version
#
# Check if BrainFrame has proper license installed?
#
#         curl http://localhost/api/license
#
# Check all VisionCapsules configurations
#
#         curl http://localhost/api/plugins
#
# Check all BrainFrame stream configurations
#
#         curl http://localhost/api/streams
#
# Check if BrainFrame has connected to a stream at some point
#
#         curl http://localhost/api/streams/status
#
# This will continuously pull uoutput from BrainFrame for all streams, including
# the zone status, timestamp.  Let's don't do this in this tool
#
#         curl http://localhost/api/streams/statuses
#

cmdlines = [
    "date",
    "date -u",
    "uptime",
    "uptime -s",
    "cat /etc/os-release",
    "uname -a",
    "ldd --version",
    "cat /proc/cpuinfo",
    "cat /etc/docker/daemon.json",
    "nvidia-smi",
    "whereis nvidia",
    "modinfo nvidia",
    "dpkg -l | grep nvidia",
    "apt list --upgradable",
    "ls /dev/dri -l",
    "df -h",
    "which brainframe",
    "which brainframe-client",
    "brainframe info",
    "cat $(brainframe info install_path)/.env",
    "cat $(brainframe info install_path)/docker-compose.yml",
    "cat $(brainframe info install_path)/docker-compose.override.yml",
    "ls -la $(brainframe info install_path)",
    "ls -la $(brainframe info data_path)/capsules",
    "docker container ls",
    "curl http://localhost/api/version",
    "curl http://localhost/api/license",
    "curl http://localhost/api/plugins | python3 -mjson.tool",
    "curl http://localhost/api/streams | python3 -mjson.tool",
    "curl http://localhost/api/streams/status | python3 -mjson.tool",
    "hostname -I",
    "cat /proc/uptime",
    "nslookup aotu.ai",
    "cat /proc/uptime",
    "ping aotu.ai -c 3",
    "cat /proc/uptime",
    "date",
    "date -u",
]


def _parse_args():
    parser = ArgumentParser(
        "This tool will print out the system and machine information and save to a file"
    )
    parser.add_argument(
        "-f", "--file", default="sys.info", help="The output system info file name"
    )

    return parser


def save_sys_info(log_filename):
    file = open(log_filename, "w")

    for line in header:
        print(line)
        file.writelines(line)

    for line in cmdlines:

        bf_info = "\n======== " + line + " ...\n"

        print(bf_info)
        file.writelines(str(bf_info))

        if line.startswith("no curl"):
            url = line.replace("no curl ", "")
            session = requests.Session()
            session.trust_env = False

            response = session.get(url)
            bf_info = json.dumps(response.json(), indent=2)

        else:
            sys_process = subprocess.Popen(
                line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            )
            bf_info = sys_process.stdout.read().decode("utf-8")

            if len(bf_info) == 0:
                bf_info = "None.\n"

        print(bf_info)
        # file.writelines(str(bf_info.encode('utf-8')))
        file.writelines(str(bf_info))

    for line in footer:
        print(line)
        file.writelines(line)

    file.close()


@command("sys-info")
def sys_info(is_command=True):
    parser = _parse_args()
    args = subcommand_parse_args(parser, is_command)

    save_sys_info(args.file)

    print(f"Saved in {args.file}")


if __name__ == "__main__":
    by_name["sys-info"](False)
