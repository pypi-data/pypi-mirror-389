#
# Copyright (c) 2021 Dilili Labs, Inc.  All rights reserved. Contains Dilili Labs Proprietary Information. RESTRICTED
# COMPUTER SOFTWARE.  LIMITED RIGHTS DATA.
#

from typing import Dict, List

from brainframe.api.stubs.zone_statuses import ZONE_STATUS_TYPE


class Report:
    def __init__(self, times_hist_len):
        """
        :param samples: The number of samples for the throughput measurement
        """
        self.times_hist_len = times_hist_len

        self.times_hist: Dict[tuple, List[float]] = {}
        """{stream_id: [zs_tstamp, ...]"""

    @property
    def num_samples_collected(self):
        """A helper for returning the number of samples currently collected

        Don't use this for any algorithms in the report. Only use it for getting
        an idea of how many samples have yet been collected."""
        times = list(self.times_hist.values())
        if len(times) == 0:
            return 0

        slowest_stream_n_samples = min(len(ts) for ts in times)
        if slowest_stream_n_samples > 0:
            return slowest_stream_n_samples
