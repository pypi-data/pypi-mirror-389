#
# Copyright (c) 2021 Dilili Labs, Inc.  All rights reserved. Contains Dilili Labs Proprietary Information. RESTRICTED
# COMPUTER SOFTWARE.  LIMITED RIGHTS DATA.
#

import json
from datetime import datetime
from time import sleep

from brainframe.api import BrainFrameAPI, bf_errors
from brainframe.api.stubs.zone_statuses import ZONE_STATUS_STREAM_TYPE
try:
    from .curses_utils import plot
    from .report import Report
except ImportError:
    from curses_utils import plot
    from report import Report

from tabulate import tabulate
from brainframe_apps.list_stream import stream_status
from brainframe_apps.fps_report import (
    collect_tstamps,
    format_fresh_tstamp_fps_report,
    calc_fresh_tstamp_fps,
)
from queue import Queue


class Benchmarker:
    def __init__(
        self,
        version: str,
        fps_history_file: str,
        report: Report,
        fps_hist_buf_len: int,
        server_url: str,
        refresh_interval: int,
        title_padding: int = 0,
        time_axis_padding: int = 6,
    ):
        """
        :param report: A long existing Report object that carries all the state
                                   regarding performance.
        :param server_url: BrainFrame server URL.
        :param refresh_interval: How often to refresh the results screen
        :param title_padding:
        """
        self.version = version
        self.report = report
        self.server_url = server_url
        self.refresh_interval = refresh_interval
        self.fps_hist_buf_len = fps_hist_buf_len
        self.title_padding = title_padding
        self.time_axis_padding = time_axis_padding
        self.api: BrainFrameAPI = BrainFrameAPI(server_url=server_url)

        self.total_streams = 0
        self.total_zs_received = 0
        self.n_zs_buffered = 0

        # This is set on first connection, and holds a zone_status_iterator
        self.zone_status_connection = None

        self.num_of_resets = 0

        self.fps_history_fp = open(fps_history_file, "a")

    def safe_zs_iterator(self, screen):
        """Catch errors from the zone_status_iterator, reinitialize connection
        only when it has been broken."""
        self.zone_status_connection: ZONE_STATUS_STREAM_TYPE = (
            self.zone_status_connection or self.api.get_zone_status_stream()
        )

        def display_error(message):
            screen.clear()
            screen.addstr(0, 0, message)
            screen.refresh()
            sleep(0.5)
            self.zone_status_connection = self.api.get_zone_status_stream()

        while True:
            try:
                for zone_status in self.zone_status_connection:
                    yield zone_status

            except (bf_errors.ServerNotReadyError, json.decoder.JSONDecodeError):
                display_error("Attempting to connect to server...")

            except (
                bf_errors.LicenseExpiredError,
                bf_errors.LicenseRequiredError,
                bf_errors.LicenseInvalidError,
            ):
                display_error("The BrainFrame server needs a new license!")

    def __call__(self, screen, time_0):
        tstamp_0 = None
        zs_time_0 = None
        last_start_time = datetime.now()
        self.num_of_resets += 1
        self.fps_history_fp.write(f"\n{last_start_time}: Screen reset\n")
        self.fps_lock_range = False
        self.fps_min = None
        self.fps_max = None
        time_axis_range_hms, time_axis_range_ms = "", ""

        # Don't wait for user input
        screen.nodelay(True)
        self.plt_width = 60

        stream_info_list = {}
        fps_hist = Queue(maxsize=self.fps_hist_buf_len)

        for zone_statuses in self.safe_zs_iterator(screen):
            # Initialize the screen, clock; collect tstamps
            zs_time = datetime.now()

            pressed_key = screen.getch()
            if pressed_key == ord("q"):
                self.fps_history_fp.close()
                break

            self.report.times_hist, tstamp_hist_0, is_empty = collect_tstamps(
                self.report.times_hist,
                self.report.times_hist_len,
                zone_statuses,
                zs_time.timestamp(),
            )
            if is_empty:
                continue

            if zs_time_0 is None:
                zs_time_0 = zs_time

            if tstamp_0 is None:
                if tstamp_hist_0 is not None:
                    tstamp_0 = tstamp_hist_0
                else:
                    continue

            if (zs_time - last_start_time).total_seconds() < self.refresh_interval:
                continue
            last_start_time = zs_time

            screen.clear()

            # Output the title line: version, # resets, time_elpase
            time_elapse = zs_time - time_0
            try:
                time_elapse_hms, time_elpase_ms = str(time_elapse).split(".")
            except ValueError:
                time_elapse_hms = str(time_elapse)
                time_elpase_ms = ""

            row = 0
            screen.addstr(
                row,
                self.title_padding,
                f" BrainFrame Monitor {self.version}{' ' * 11} Reconnect # {self.num_of_resets:03}] {time_elapse_hms}.{time_elpase_ms[:2]}",
            )
            row += 1

            # Create/output the overall stream throughput report table
            stream_info_list = self.update_stream_info(stream_info_list)

            (
                throughput_fps,
                avg_fps,
                max_fps_t,
                min_fps_t,
                stream_fps_drift_dsync,
            ) = calc_fresh_tstamp_fps(
                self.report.times_hist,
                tstamp_0,
                zs_time_0,
                zone_statuses,
                zs_time.timestamp(),
            )

            (
                stream_fps_summary_header,
                stream_fps_summary,
                throughput_fps_str,
            ) = format_fresh_tstamp_fps_report(
                throughput_fps, avg_fps, max_fps_t, min_fps_t
            )

            self.fps_history_fp.write(
                f"{time_elapse_hms}.{time_elpase_ms[:2]} {throughput_fps_str}\n"
            )
            self.fps_history_fp.flush()

            table_str = tabulate(
                [stream_fps_summary],
                tablefmt="fancy_grid",
                headers=stream_fps_summary_header,
            )

            screen.addstr(row, 0, table_str)
            row += 5

            # Output stream fps list
            stream_fps_list = self.get_stream_fps_list(
                stream_info_list, stream_fps_drift_dsync
            )
            table_str = tabulate(
                stream_fps_list,
                headers=[
                    "   A/K",
                    "sID",
                    "Stream url",
                    "FPS",
                    "[  Buf,  Age,Dsync,Drift]",
                ],
                showindex="never",
            )

            screen.addstr(row, 0, table_str)
            row += len(stream_fps_list) + 2

            # Output the plot title line: number of samples, and total measures
            self.total_zs_received += 1
            if self.total_zs_received < self.fps_hist_buf_len:
                zs_time_elapse = zs_time - zs_time_0
                try:
                    time_axis_range_hms, time_axis_range_ms = str(zs_time_elapse).split(
                        "."
                    )
                except ValueError:
                    time_axis_range_hms = str(zs_time_elapse)
                    time_axis_range_ms = ""

            if self.total_zs_received < self.report.times_hist_len:
                self.n_zs_buffered = self.total_zs_received
            else:
                self.n_zs_buffered = self.report.times_hist_len

            if self.total_zs_received >= self.fps_hist_buf_len + self.n_zs_buffered:
                # Change this to True to enable fps lock
                self.fps_lock_range = False
                fps_range_str = f"    FPS"  # axis locked{' ' * 9}"
            else:
                self.fps_lock_range = False
                fps_range_str = (
                    f"    FPS"  # axis locking.{'.' * (self.n_zs_buffered % 3):6s} "
                )

            scr_rows, scr_cols = screen.getmaxyx()
            plt_height_limit = scr_rows - row - 7
            self.fps_min, self.fps_max, cfg = self.save_fps_throughput(
                self.fps_hist_buf_len,
                plt_height_limit,
                self.plt_width,
                fps_hist,
                throughput_fps,
                self.fps_lock_range,
                self.fps_min,
                self.fps_max,
            )

            row += 1
            screen.addstr(
                row,
                self.title_padding,
                f"FPS/max/min: {throughput_fps_str}/{self.fps_max:.2f}/{self.fps_min:.2f}, total {self.total_zs_received} zone statuses received, {self.n_zs_buffered:>3} in buffer",
            )
            row += 1

            # Plot fps throughput graph
            plot_txt, plot_n_rows, debug_print = plot(
                fps_hist, self.fps_min, self.fps_max, cfg=cfg
            )

            screen.addstr(row, 0, plot_txt)
            row += plot_n_rows + 1

            # Output plot time axis information lines
            t_step = int(10 * self.fps_hist_buf_len / self.plt_width)
            t_max = int(self.fps_hist_buf_len / t_step)
            t_label = "0"
            for t in range(t_max):
                t_label += f"{str((t + 1) * t_step):>10}"
            screen.addstr(row, self.time_axis_padding, t_label)
            row += 1

            screen.addstr(
                row,
                self.title_padding,
                f"{' ' * 9}Refresh interval: {self.refresh_interval} seconds,"
                f" Time axis range: {time_axis_range_hms}.{time_axis_range_ms[:2]}",
            )
            row += 2

            # Output press key prompt and debug information
            screen.addstr(
                row,
                5,
                f"Total {self.total_streams} streams measured. Press q to quit {debug_print}",
            )

            screen.refresh()

    def get_stream_info_list(self):

        stream_info_list = {}
        streams = self.api.get_stream_configurations()
        for stream in streams:
            (
                analyze_status,
                keyframes_only_status,
                stream_url,
            ) = stream_status(self.api, stream, stream.id)
            stream_info_item = {
                "analyze_status": analyze_status,
                "keyframes_only_status": keyframes_only_status,
                "stream_url": stream_url,
            }
            stream_info_list[stream.id] = stream_info_item
            self.fps_history_fp.write(f"{stream_info_item}\n")

        self.fps_history_fp.write(f"TimeElapse FPS\n")
        return stream_info_list

    def update_stream_info(self, stream_info_list):
        times_hist = self.report.times_hist
        for stream_id, stream_times in times_hist.items():

            # let's refresh the whole list
            #     - When a new stream is observed
            #     - When a stream is added or deleted
            if stream_id not in stream_info_list or len(times_hist) != len(
                stream_info_list
            ):
                self.total_streams += 1
                try:
                    stream_info_list = self.get_stream_info_list()
                except:
                    pass

                # In case a stream is deleted
                break
        return stream_info_list

    @staticmethod
    def get_stream_fps_list(stream_info_list, stream_fps_drift_dsync):
        stream_fps_list = []
        stream_info_list_index = 1
        for stream_id in sorted(stream_info_list):
            stream_info_item = stream_info_list[stream_id]
            fps_str = ""
            buf_str = "     "
            age_str = "     "
            dsync_str = "     "
            drift_str = "     "
            if stream_id in stream_fps_drift_dsync:
                fps_drift_dsync = stream_fps_drift_dsync[stream_id]
                if "fps" in fps_drift_dsync:
                    fps = fps_drift_dsync["fps"]
                    if fps != 0:
                        fps_str = f"{fps_drift_dsync['fps']:>5.1f}"

                    if (
                        "drift" in fps_drift_dsync
                        and fps_drift_dsync["drift"] is not None
                    ):
                        drift_str = f"{fps_drift_dsync['drift']: >5.2f}"

                    if (
                        "dsync" in fps_drift_dsync
                        and fps_drift_dsync["dsync"] is not None
                    ):
                        dsync_str = f"{fps_drift_dsync['dsync']: >5.2f}"

                    if "age" in fps_drift_dsync and fps_drift_dsync["age"] is not None:
                        age_str = f"{fps_drift_dsync['age']: >5.2f}"

                    if "buf" in fps_drift_dsync and fps_drift_dsync["buf"] is not None:
                        buf_str = f"{fps_drift_dsync['buf']: >5.2f}"

            stream_fps_list.append(
                [
                    f"{stream_info_list_index}: {stream_info_item['analyze_status']}/{stream_info_item['keyframes_only_status']}",
                    f"{stream_id}",
                    f"{str(stream_info_item['stream_url'])[-25:]:.>25}",
                    fps_str,
                    f"[{buf_str},{age_str},{dsync_str},{drift_str}]",
                ]
            )
            stream_info_list_index = stream_info_list_index + 1

        return stream_fps_list

    def save_fps_throughput(
        self,
        fps_hist_buf_len,
        plt_height_limit,
        plt_width,
        fps_hist,
        throughput,
        fps_lock_range,
        curr_fps_min,
        curr_fps_max,
    ):
        cfg = {
            "fps_hist_buf_len": fps_hist_buf_len,
            "plt_height_limit": plt_height_limit,
            "plt_width": plt_width,
            "col_offset": 2,
        }

        if fps_hist.qsize() >= fps_hist_buf_len:
            fps_hist.get()

        if throughput is not None:
            fps_hist.put(int(throughput))

        if fps_hist.qsize() > 0:
            if fps_lock_range is False or curr_fps_min is None:
                fps_min = float(min(list(fps_hist.queue)))
            else:
                fps_min = min(float(min(list(fps_hist.queue))), curr_fps_min)

            if fps_lock_range is False or curr_fps_max is None:
                fps_max = float(max(list(fps_hist.queue)))
            else:
                fps_max = max(float(max(list(fps_hist.queue))), curr_fps_max)
        else:
            fps_min = 0
            fps_max = 0

        return fps_min, fps_max, cfg


def test_plot():
    from random import random

    benchmarker = Benchmarker(
        version="v0.0",
        fps_history_file="test_plot.txt",
        report=None,
        fps_hist_buf_len=100,
        server_url="",
        refresh_interval=0,
    )

    fps_data = []
    n_tests = 55
    fps_sample_data_max = 30
    for i in range(n_tests):
        # test fixed pattern or random pattern?
        value = i % fps_sample_data_max
        # value = float(random() * 29)
        fps_data.append(value)

    fps_data = [3, 3, 3, 7, 6, 6, 9, 11, 8, 1, 1, 2, 902]
    # fps_data = [122]
    """
    fps_data = [
        224,
        104,
        1,
        2,
        3,
        70,
        60,
        56,
        40,
        25,
        14,
        14,
        13,
        12,
        11,
        10,
        10,
        10,
        9,
        9,
        9,
        9,
        8,
        8,
        8,
        8,
        8,
        8,
        8,
        8,
        7,
        7,
        7,
        431,
        136,
        98,
        61,
        11,
        9,
        8,
        8,
        6,
        6,
        6,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        3,
        1357,
        147,
        80,
        57,
        40,
        39,
    ]
    """
    plt_height_limit = 20
    plt_width = 60

    fps_hist_buf_len = 100
    fps_hist = Queue(maxsize=fps_hist_buf_len)
    for i, value in enumerate(fps_data):
        throughput = value
        curr_fps_min, curr_fps_max, cfg = benchmarker.save_fps_throughput(
            fps_hist_buf_len, plt_height_limit, plt_width, fps_hist, throughput, False
        )
        plot_txt, plot_n_rows, debug_print = plot(
            fps_hist, curr_fps_min, curr_fps_max, cfg
        )
        print(f"{plot_txt}\nIndex: {i}, fps: {value}\n{debug_print}")


if __name__ == "__main__":
    test_plot()
