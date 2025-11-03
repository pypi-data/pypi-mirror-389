#
# Copyright (c) 2021 Dilili Labs, Inc.  All rights reserved. Contains Dilili Labs Proprietary Information. RESTRICTED COMPUTER SOFTWARE.  LIMITED RIGHTS DATA.
#
import os
import subprocess
from argparse import ArgumentParser, RawTextHelpFormatter
from datetime import datetime
from pathlib import Path
from subprocess import Popen
from time import sleep, time
from typing import Callable

from brainframe.api import BrainFrameAPI

try:
    from .bf_info import save_sys_info
    from .command_utils import command, subcommand_parse_args, by_name
except ImportError:
    from bf_info import save_sys_info
    from command_utils import command, subcommand_parse_args, by_name

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


class HeartBeat:
    def __init__(
        self, log_path, interval, threshold, log_save=False, restart_cron=None
    ):

        self.interval = int(interval)
        self.threshold = int(threshold)
        self.log_save = log_save

        if os.path.isdir(log_path) is not True:
            print(f"{log_path} is invalid!")
            exit(1)
        self.log_path = log_path

        self.time_0 = datetime.now()
        self.log_path_prefix = None
        self.heartbeat_log_file = None
        self.brainframe_log_filename = None
        self.heartbeat_log_open(interval, threshold)

        self.d_status = {}
        # add BackgroundScheduler
        self.bgscheduler = None
        self.restart_timeout = None
        # Schedule the job to run daily/weekly/month at midnight (00:00)
        if restart_cron is not None:
            # add BackgroundScheduler for timed task
            self.bgscheduler = BackgroundScheduler()
            # use CronTrigger parse Cron style string
            self.cron_trigger = CronTrigger.from_crontab(restart_cron)
            self.bgscheduler.add_job(self._cron_job, self.cron_trigger)

    def heartbeat_log_open(self, interval, threshold):
        self.time_0 = datetime.now()
        self.log_path_prefix = str(self.log_path) + f"/{self.time_0.isoformat()}_"
        self.brainframe_log_filename = self.log_path_prefix + "brainframe.log"

        log_filename = self.log_path_prefix + "brainframe_heartbeat.log"
        self.heartbeat_log_file = Path(log_filename).resolve().open(mode="a")

        self.heartbeat_log(
            f"BrainFrame HeartBeat starts, interval = {interval}, threshold = {threshold}"
        )

    def heartbeat_log_close(self):
        self.heartbeat_log(
            f"BrainFrame HeartBeat session closed, {datetime.now() - self.time_0}"
        )
        self.heartbeat_log_file.close()

    def heartbeat_log(self, log_str):
        _log_str = f"[{datetime.now()}] " + str(log_str) + "\n"
        print(_log_str)
        self.heartbeat_log_file.writelines(_log_str)
        self.heartbeat_log_file.flush()

    def restart_brainframe(self):
        self.heartbeat_log(f"Stop brainframe")

        if self.log_save:
            self.save_brainframe_logs()
            brainframe_sys_info_filename = self.log_path_prefix + "sys.info"
            save_sys_info(brainframe_sys_info_filename)

        self.stop_brainframe()
        self.heartbeat_log(f"Save brainframe logs at {self.brainframe_log_filename}")
        self.heartbeat_log_close()

        self.heartbeat_log_open(self.interval, self.threshold)
        self.heartbeat_log(f"Start brainframe")
        self.start_brainframe()
        self.heartbeat_log("brainframe has started")

    def process_helper(self, cmd_str):
        execution_start_time = datetime.now()
        self.heartbeat_log(f"{cmd_str}: [{execution_start_time}]")
        p = Popen(
            cmd_str,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            shell=True,
            start_new_session=True,
            close_fds=True,
        )
        # output = p.stdout.read()
        output, err = p.communicate()
        p.wait()
        execution_complete_time = datetime.now()
        self.heartbeat_log(f"{cmd_str} completed: [{execution_complete_time}]")

        brainframe_log_file = (
            Path(self.brainframe_log_filename).resolve().open(mode="a")
        )
        brainframe_log_file.writelines(f"[{execution_start_time}] {cmd_str}: stdout\n")
        brainframe_log_file.writelines(output)
        brainframe_log_file.writelines(f"[{execution_start_time}] {cmd_str}: stderr\n")
        brainframe_log_file.writelines(err)
        brainframe_log_file.writelines(f"[{execution_complete_time}] {cmd_str}\n")
        brainframe_log_file.close()

        self.heartbeat_log(f"Output are saved to {self.brainframe_log_filename}\n")

    def save_brainframe_logs(self):
        # os.system(f"brainframe compose logs &>> {log_filename}", )
        cmd_str = ["brainframe compose logs"]
        self.process_helper(cmd_str)

    def stop_brainframe(self):
        # os.system(f"brainframe compose down &>> {log_filename}")
        cmd_str = ["brainframe compose down"]
        self.process_helper(cmd_str)

    def start_brainframe(self):
        # os.system(f"brainframe compose up -d &>> {log_filename}")
        cmd_str = ["brainframe compose up -d"]
        self.process_helper(cmd_str)

    def wait_for_heartbeat(self, fn: Callable, timeout: float = None):
        """A helpful function to wait for heartbeat."""
        heartbeat_val, heartbeat_response = None, None
        start_time = time()
        while timeout is None or time() - start_time < timeout:
            try:
                heartbeat_response = fn()
                heartbeat_val = time() - start_time
                break
            except:
                heartbeat_val = time() - start_time
                break

        return heartbeat_val, heartbeat_response

    def heartbeat_monitor(self, api):
        # start cron scheduler
        self.start_cron_scheduler()
        has_restarted = False
        while True:
            heartbeat_val, heartbeat_response = self.wait_for_heartbeat(
                lambda: api.version(self.threshold), self.threshold
            )

            if heartbeat_response:
                has_restarted = False
                self.heartbeat_log(
                    f"version {heartbeat_response} heartbeat OK: response time - {heartbeat_val}"
                )

                # zonestatus monitor.
                self.zone_status_monitor(api)
                # check if restart-cron task is timeout, need to deal.
                if self.restart_timeout:
                    self.heartbeat_log(f"cron task timeout, to restart service")
                    self.restart_brainframe()
                    has_restarted = True
                    self.restart_timeout = None
            else:
                self.heartbeat_log(f"heartbeat failed: timeout - {heartbeat_val}")
                if not has_restarted:
                    self.restart_brainframe()
                    has_restarted = True

                if self.restart_timeout:
                    self.restart_timeout = None

            sleep(self.interval)

    def zone_status_monitor(self, api):
        # check api/streams/status,  analyze result is normal or not
        status_val, status_response = self.wait_for_heartbeat(
            lambda: api.get_latest_zone_statuses(self.threshold), self.threshold
        )

        if status_response:
            # streamid,zonestatus = next(iter(status_response.items()))
            # tstamp = zonestatus["Screen"].tstamp
            has_changed = []
            no_change = []
            for streamid, zonestatus in status_response.items():
                last_tstamp = self.d_status.get(streamid, 0.0)
                tstamp = zonestatus["Screen"].tstamp

                if last_tstamp != tstamp:
                    has_changed.append(streamid)
                    self.d_status[streamid] = tstamp
                else:
                    no_change.append((streamid, tstamp))

            self.heartbeat_log(
                f"latest_zone_status OK: changed:{has_changed}, no change:{no_change}, response time - {status_val}"
            )
        else:
            self.heartbeat_log(
                f"latest_zone_status failed: timeout or no zonestatus - {status_val}"
            )

    def _cron_job(self):
        # cron job for restart.
        print(f"_cron_job: {self.cron_trigger}")
        self.restart_timeout = True

    def start_cron_scheduler(self):
        # if set bgscheduler, start scheduler
        if self.bgscheduler is not None:
            self.heartbeat_log(f"start cron scheduler, {self.cron_trigger}")
            self.bgscheduler.start()


def _parse_args():
    parser = ArgumentParser(
        description="This is the brainframe service monitor. Run the command with no arguments will launch"
        " brainframe service and monitor the brainframe heartbeats. It will restart the service"
        " when the heartbeats are not observed in the given timeout threshold. For example, run"
        " the command below will monitor the heartbeats at an interval of 5 seconds. The command"
        " will not launch brainframe automatically as '--start-now' is specified.\n\n"
        "    python brainframe_service_monitor.py --log-path ~/workspace --interval 2 --threshold 6 --start-now False\n\n"
        "If the communication with brainframe fails, or a heartbeat deplay exceeds 6 seconds, the"
        " service monitor will save the following log files in ~/workspace directory, then restart"
        " the brainframe service,\n\n"
        "    <timestamp>_hearbeat.log\n"
        "    <timestamp>_brainframe.log\n"
        "    <timestamp>_sys.info\n\n"
        "The default heartbeat interval and timeout threshold can be found in the arguments'"
        " description.",
        formatter_class=RawTextHelpFormatter,
    )
    parser.add_argument(
        "--server-url",
        default="http://localhost",
        help="The URL for the BrainFrame server.",
    )
    parser.add_argument(
        "--interval",
        default=120,
        help="The heartbeat checking interval. Default: %(default)i",
    )
    parser.add_argument(
        "--threshold",
        default=360,
        help="The heartbeat timeout threshold. The service monitor will restart when the communication fails or timeout."
        " Default: %(default)i",
    )
    parser.add_argument(
        "--log-path",
        type=Path,
        default="./",
        help="The logs will be saved in this path. Default: %(default)s",
    )
    parser.add_argument(
        "--start-now",
        action="store_true",
        help="Start the brainframe service. Default: %(default)s",
    )

    parser.add_argument(
        "--log-save",
        action="store_true",
        help="Brainframe log and sys.info will be saved when the service is unavailable. Default: %(default)s",
    )

    parser.add_argument(
        "--restart-cron",
        default=None,
        type=str,
        help="""Brainframe service will restart on midnight, using Cron-style schedule string (e.g., '* * * * *'), Default: %(default)s.
        For example, '0 0 * * 3' is on midnight every Thursday,
        The first  0: Minute (0 - 59)
        The second 0: Hour (0 - 23)
        The third  *: Day of the month (1 - 31)
        The fourth *: Month (1 - 12)
        The fifth  3: Day of the week (0 - 6 for Monday to Sunday, accroding to apscheduler)
        When you use an asterisk (*) in any of these fields, it represents 'every'.""",
    )

    return parser


@command("service-monitor")
def service_monitor(is_command=True):
    parser = _parse_args()
    args = subcommand_parse_args(parser, is_command)

    # if restart_cron is set, check if cron string is fine.
    if args.restart_cron:
        try:
            # use from_crontab() create CronTrigger instance
            trigger = CronTrigger.from_crontab(args.restart_cron)
            print(f"restart-cron: {trigger}")
        except (ValueError, KeyError) as e:
            # cron string invalid
            print(f"Invalid argument restart-cron format: {e}")
            exit(1)

    # Connect to the BrainFrame Server
    server_url = args.server_url

    hb = HeartBeat(
        args.log_path,
        args.interval,
        args.threshold,
        log_save=args.log_save,
        restart_cron=args.restart_cron,
    )

    if args.start_now:
        hb.start_brainframe()

    hb.heartbeat_log(
        f"heartbeat Connecting: BrainFrameAPI({server_url}), wait_for_server_initialization() ..."
    )
    api = BrainFrameAPI(server_url)
    api.wait_for_server_initialization()

    hb.heartbeat_log("heartbeat Connected")

    hb.heartbeat_monitor(api)

    hb.heartbeat_log("heartbeat exit")


if __name__ == "__main__":
    by_name["service-monitor"](False)
