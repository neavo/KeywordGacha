from helper.LogHelper import LogHelper
from helper.TextHelper import TextHelper


class TestHelper:
    @staticmethod
    def check_duplicates(*args):
        a = {}
        b = {}

        if len(a) == 0 and len(b) == 0:
            return

        keys_a = set(a.keys())
        keys_b = set(b.keys())

        LogHelper.print(f"两个字典共有的键 - {len(keys_a & keys_b)}")
        LogHelper.print(keys_a & keys_b)

        LogHelper.print(f"第一个词典独有的键 - {len(keys_a - keys_b)}")
        LogHelper.print(keys_a - keys_b)

        LogHelper.print(f"第二个词典独有的键 - {len(keys_b - keys_a)}")
        LogHelper.print(keys_b - keys_a)
