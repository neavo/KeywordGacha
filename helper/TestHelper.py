from helper.LogHelper import LogHelper

class TestHelper:
 
    @staticmethod
    def check_duplicates(*args):
        a = {}
        b = {}

        keys_a = set(a.keys())
        keys_b = set(b.keys())
        LogHelper.print(len(keys_a & keys_b))