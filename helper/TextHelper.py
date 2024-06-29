class TextHelper:
    # 定义日文字符的Unicode范围
    JPN_START = "\u3040"  # 平假名起始
    JPN_END = "\u309f"  # 平假名结束
    KATAKANA_START = "\u30a0"  # 片假名起始
    KATAKANA_END = "\u30ff"  # 片假名结束
    CJK_START = "\u4e00"  # 中日韩统一表意文字起始
    CJK_END = "\u9fff"  # 中日韩统一表意文字结束
    FULLWIDTH_START = "\u3000"  # 全角字符起始
    FULLWIDTH_END = "\u303f"  # 全角字符结束
    SYMBOLS_START = "\uff01"  # 日文标点符号起始
    SYMBOLS_END = "\uff60"  # 日文标点符号结束
    VOICED_SOUND_MARK = "\u309b"  # 濁音和半浊音符号
    HALFWIDTH_KATAKANA_START = "\uff66"  # 半角片假名起始
    HALFWIDTH_KATAKANA_END = "\uff9f"  # 半角片假名结束

    @staticmethod
    def _is_japanese(ch):
        # 判断字符是否为日文字符
        return (
            TextHelper.JPN_START <= ch <= TextHelper.JPN_END
            or TextHelper.KATAKANA_START <= ch <= TextHelper.KATAKANA_END
            or TextHelper.CJK_START <= ch <= TextHelper.CJK_END
            or TextHelper.FULLWIDTH_START <= ch <= TextHelper.FULLWIDTH_END
            or TextHelper.SYMBOLS_START <= ch <= TextHelper.SYMBOLS_END
            or ch == TextHelper.VOICED_SOUND_MARK
            or TextHelper.HALFWIDTH_KATAKANA_START
            <= ch
            <= TextHelper.HALFWIDTH_KATAKANA_END
        )

    # 判断字符是否为中文或日文汉字
    @staticmethod
    def _is_chinese_or_kanji(ch):
        return TextHelper.CJK_START <= ch <= TextHelper.CJK_END

    # 检查字符串是否包含至少一个日文字符
    @staticmethod
    def contains_japanese(text):
        return any(TextHelper._is_japanese(char) for char in text)

    # 判断输入的字符串是否全部由日文字符组成
    @staticmethod
    def is_all_japanese(text):
        return all(TextHelper._is_japanese(char) for char in text)

    # 判断输入的字符串是否全部由中文或日文汉字组成
    @staticmethod
    def is_all_chinese_or_kanji(text):
        return all(TextHelper._is_chinese_or_kanji(char) for char in text)
