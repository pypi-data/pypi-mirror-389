#
# Copyright (c) 2021 Dilili Labs, Inc.  All rights reserved. Contains Dilili Labs Proprietary Information. RESTRICTED COMPUTER SOFTWARE.  LIMITED RIGHTS DATA.
#

import subprocess
from argparse import ArgumentParser

try:
    from .command_utils import command, subcommand_parse_args, by_name
except ImportError:
    from command_utils import command, subcommand_parse_args, by_name


def _parse_args():
    parser = ArgumentParser("brainframe-sys-tools ssh_tunnel")
    parser.add_argument(
        "-s",
        "--server-url",
        default="dililitechnology.com",
        help="The SSH server url or ip, Default is %(default)s.",
    )
    parser.add_argument(
        "-u",
        "--user",
        default="ubuntu",
        help="Username to access the SSH server, Default is %(default)s.",
    )
    parser.add_argument(
        "-p",
        "--port",
        default="22",
        help="The SSH server port, Default is %(default)s.",
    )
    parser.add_argument(
        "-r",
        "--remoteforward",
        action="append",
        required=True,
        help="The SSH remote forward port(s) and local port(s), \
                format is 'remoteport:localhost:localport'. Use multiple -r to specify additional rules. \
                For example '-r 8088:localhost:80', on remote ssh server, you can use 'localhost:8088' to access local port 80",
    )
    parser.add_argument(
        "-i",
        "--identity_file",
        default=None,
        help="The SSH identity file, Default is %(default)s.",
    )
    parser.add_argument(
        "-o",
        "--option",
        default=["ExitOnForwardFailure=yes"],
        action="append",
        help="SSH client options, Default is %(default)s. \
                Use muliple -o to specify more options, for example '-o ServerAliveInterval=120 -o ServerAliveCountMax=3'.",
    )

    return parser


def run_command_list(commandlst):
    print(" ".join(commandlst))
    print("Press Ctrl-C, to quit")

    try:
        result = subprocess.run(
            commandlst, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"Error: {result.stderr}")
    except KeyboardInterrupt:
        print(" Process was interrupted by user")


@command("ssh-tunnel")
def ssh_tunnel(is_command=True):
    parser = _parse_args()
    args = subcommand_parse_args(parser, is_command)

    # Build the SSH command
    ssh_command = ["ssh", "-N", "-p", args.port]
    if args.identity_file:
        ssh_command.extend(["-i", args.identity_file])

    # Add each remote forward rule to the SSH command
    for rf in args.remoteforward:
        ssh_command.extend(["-R", rf])

    # Add each option to command list
    for option in args.option:
        ssh_command.extend(["-o", option])

    ssh_command.append(f"{args.user}@{args.server_url}")
    # start ssh tunnel
    print(
        "Note: After establishing an SSH reverse tunnel, the remote host can access the locally mapped ports and services.\n"
        "      Please ensure the privacy and security of the local host."
    )
    run_command_list(ssh_command)


if __name__ == "__main__":
    by_name["ssh-tunnel"](False)
