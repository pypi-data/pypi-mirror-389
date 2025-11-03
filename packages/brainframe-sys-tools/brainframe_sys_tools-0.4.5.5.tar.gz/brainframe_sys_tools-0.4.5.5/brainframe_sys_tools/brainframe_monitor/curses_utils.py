#
# Copyright (c) 2021 Dilili Labs, Inc.  All rights reserved. Contains Dilili Labs Proprietary Information. RESTRICTED
# COMPUTER SOFTWARE.  LIMITED RIGHTS DATA.
#

from math import ceil, floor


def plot(fps_data, fps_min=None, fps_max=None, cfg={}):
    fps_data_len = fps_data.qsize()
    if fps_data_len == 0:
        return (
            "[INVALID PLOT, NO DATA]",
            1,
            "",
        )

    padding = cfg["padding"] if "padding" in cfg else "           "
    placeholder = cfg["format"] if "format" in cfg else "{:4.0f} "
    fps_hist_buf_len = cfg["fps_hist_buf_len"] if "fps_hist_buf_len" in cfg else 60
    plt_height_limit = cfg["plt_height_limit"] if "plt_height_limit" in cfg else 60
    plt_width = cfg["plt_width"] if "plt_width" in cfg else 60
    # 1st col for label, 2nd col for Y-axis symbol
    canvas_plt_offset = cfg["canvas_plt_offset"] if "canvas_plt_offset" in cfg else 2

    fps_range = fps_max - fps_min + 1
    if fps_range == 0:
        fps_min = fps_max - 1
        fps_range = 1
    fps_row_range = fps_range
    row2fps_ratio = fps_row_range / fps_range

    fps_row_min = int(floor(float(fps_min) * row2fps_ratio) - 1)
    fps_row_ceil = int(ceil(float(fps_max) * row2fps_ratio) + 1)
    plt_height = int(min(plt_height_limit, fps_row_ceil - fps_row_min))
    fps_row_floor = fps_row_ceil - plt_height

    fps_measures_per_col = int(fps_hist_buf_len / plt_width)
    canvas_col_width = int(plt_width + canvas_plt_offset + 1)
    canvas_row_height = plt_height + 1

    canvas_buf = [[" "] * canvas_col_width for i in range(canvas_row_height)]

    # axis and labels
    canvas_buf[plt_height] = ["─"] * (plt_width + canvas_plt_offset)
    for fps_row_n in range(fps_row_floor, fps_row_ceil + 1):
        canvas_row_n = plt_height - (fps_row_n - fps_row_floor)
        label = placeholder.format(fps_row_ceil - canvas_row_n)
        canvas_buf[canvas_row_n][max(canvas_plt_offset - len(label), 0)] = label
        if canvas_row_n == fps_row_ceil:
            canvas_buf[canvas_row_n][canvas_plt_offset - 1] = "┴"
        elif canvas_row_n == plt_height:
            canvas_buf[canvas_row_n][canvas_plt_offset - 1] = "┼"
        else:
            canvas_buf[canvas_row_n][canvas_plt_offset - 1] = "┤"

    fps_0, i_fps_data = 0, 0
    for n in range(i_fps_data, i_fps_data + fps_measures_per_col):
        # Average measures per col
        fps_0 += fps_data.queue[n] / fps_measures_per_col

    canvas_row_0 = int(plt_height - (round(fps_0 * row2fps_ratio) - fps_row_floor))
    if canvas_row_0 > plt_height:
        canvas_row_0 = plt_height

    canvas_buf[canvas_row_0][canvas_plt_offset - 1] = (
        "┴" if canvas_row_0 == 0 else "┼"
    )  # first value

    fps_data_available_cols = int(len(fps_data.queue) / fps_measures_per_col)

    if fps_data_available_cols >= 2:
        for plt_col_n in range(
            0, min(plt_width - 1, fps_data_available_cols - 1)
        ):  # plot the line
            i_fps_data = plt_col_n * fps_measures_per_col
            fps_1, fps_2 = 0, 0
            for n in range(i_fps_data, i_fps_data + fps_measures_per_col):
                # Average measures per col
                fps_1 += fps_data.queue[n] / fps_measures_per_col
                fps_2 += fps_data.queue[n + fps_measures_per_col] / fps_measures_per_col

            canvas_row_1 = int(
                plt_height - (round(fps_1 * row2fps_ratio) - fps_row_floor)
            )
            canvas_row_2 = int(
                plt_height - (round(fps_2 * row2fps_ratio) - fps_row_floor)
            )
            if canvas_row_2 > plt_height:
                canvas_row_2 = plt_height
            if canvas_row_1 > plt_height:
                canvas_row_1 = plt_height

            canvas_col = plt_col_n + canvas_plt_offset
            if canvas_row_1 == canvas_row_2:
                canvas_buf[canvas_row_1][canvas_col] = "─"
            else:
                canvas_buf[canvas_row_1][canvas_col] = (
                    "╮" if canvas_row_1 < canvas_row_2 else "╯"
                )
                canvas_row_1to2_start, canvas_row_1to2_end = (
                    min(canvas_row_1, canvas_row_2) + 1,
                    max(canvas_row_1, canvas_row_2),
                )
                if canvas_row_1to2_start > plt_height:
                    canvas_row_1to2_start = plt_height
                for canvas_row_n in range(canvas_row_1to2_start, canvas_row_1to2_end):
                    canvas_buf[canvas_row_n][canvas_col] = "│"
                canvas_buf[canvas_row_2][canvas_col] = (
                    "╰" if canvas_row_1 < canvas_row_2 else "╭"
                )

    plot_n_rows = len(canvas_buf) - 1
    debug_print = ""
    return (
        "\n".join(["".join(row) for row in canvas_buf]),
        plot_n_rows,
        debug_print,
    )
