#
# Copyright (c) 2021 Dilili Labs, Inc.  All rights reserved. Contains Dilili Labs Proprietary Information. RESTRICTED
# COMPUTER SOFTWARE.  LIMITED RIGHTS DATA.
#


class FakeScreen:
    @staticmethod
    def clear():
        pass

    @staticmethod
    def addstr(row, col, message):
        print(message)
        pass

    @staticmethod
    def refresh():
        pass

    def nodelay(self):
        pass

    @staticmethod
    def getch():
        pass

    @staticmethod
    def getmaxyx():
        return 80, 80
