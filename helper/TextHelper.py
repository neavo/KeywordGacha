import re

class TextHelper:

    # 平假名
    JPN_START = "\u3040"
    JPN_END = "\u309F"

    # 片假名
    KATAKANA_START = "\u30A0"
    KATAKANA_END = "\u30FF"

    # 中日韩统一表意文字
    CJK_START = "\u4E00"
    CJK_END = "\u9FFF"

    # 全角字符（CJK符号和标点符号）
    FULLWIDTH_START = "\u3000"
    FULLWIDTH_END = "\u303F"

    # 日文标点符号
    SYMBOLS_START = "\uFF01"
    SYMBOLS_END = "\uFF65"

    # 濁音和半浊音符号
    VOICED_SOUND_MARKS = ["\u309B", "\u309C"]

    # 半角片假名
    HALFWIDTH_KATAKANA_START = "\uFF66"
    HALFWIDTH_KATAKANA_END = "\uFF9F"

    # 片假名语音扩展
    KATAKANA_PHONETIC_EXTENSIONS_START = "\u31F0"
    KATAKANA_PHONETIC_EXTENSIONS_END = "\u31FF"

    # 中日韩通用标点符号
    GENERAL_PUNCTUATION = ["\u2000", "\u206F"]
    CJK_SYMBOLS_AND_PUNCTUATION = ["\u3000", "\u303F"]
    HALFWIDTH_AND_FULLWIDTH_FORMS = ["\uFF00", "\uFFEF"]
    OTHER_CJK_PUNCTUATION = [
        "\u30FB"    # ・
    ]

    # 英文标点符号
    LATIN_PUNCTUATION_BASIC_1 = ("\u0020", "\u002F")
    LATIN_PUNCTUATION_BASIC_2 = ("\u003A", "\u0040")
    LATIN_PUNCTUATION_BASIC_3 = ("\u005B", "\u0060")
    LATIN_PUNCTUATION_BASIC_4 = ("\u007B", "\u007E")
    LATIN_PUNCTUATION_GENERAL = ("\u2000", "\u206F")
    LATIN_PUNCTUATION_SUPPLEMENTAL = ("\u2E00", "\u2E7F")

    # 判断一个字符是否是中日韩标点符号
    @staticmethod
    def is_cjk_punctuation(char):
        return (
            TextHelper.GENERAL_PUNCTUATION[0] <= char <= TextHelper.GENERAL_PUNCTUATION[1]
            or TextHelper.CJK_SYMBOLS_AND_PUNCTUATION[0] <= char <= TextHelper.CJK_SYMBOLS_AND_PUNCTUATION[1]
            or TextHelper.HALFWIDTH_AND_FULLWIDTH_FORMS[0] <= char <= TextHelper.HALFWIDTH_AND_FULLWIDTH_FORMS[1]
            or char in TextHelper.OTHER_CJK_PUNCTUATION
        )

    # 判断一个字符是否是拉丁标点符号
    @staticmethod
    def is_latin_punctuation(char):
        return (
            TextHelper.LATIN_PUNCTUATION_BASIC_1[0] <= char <= TextHelper.LATIN_PUNCTUATION_BASIC_1[1]
            or TextHelper.LATIN_PUNCTUATION_BASIC_2[0] <= char <= TextHelper.LATIN_PUNCTUATION_BASIC_2[1]
            or TextHelper.LATIN_PUNCTUATION_BASIC_3[0] <= char <= TextHelper.LATIN_PUNCTUATION_BASIC_3[1]
            or TextHelper.LATIN_PUNCTUATION_BASIC_4[0] <= char <= TextHelper.LATIN_PUNCTUATION_BASIC_4[1]
            or TextHelper.LATIN_PUNCTUATION_GENERAL[0] <= char <= TextHelper.LATIN_PUNCTUATION_GENERAL[1]
            or TextHelper.LATIN_PUNCTUATION_SUPPLEMENTAL[0] <= char <= TextHelper.LATIN_PUNCTUATION_SUPPLEMENTAL[1]
        )

    # 判断一个字符是否是标点符号
    @staticmethod
    def is_punctuation(char):
        return TextHelper.is_cjk_punctuation(char) or TextHelper.is_latin_punctuation(char)

    # 判断字符是否为日文字符
    @staticmethod
    def is_japanese(ch):
        return (
            TextHelper.JPN_START <= ch <= TextHelper.JPN_END
            or TextHelper.KATAKANA_START <= ch <= TextHelper.KATAKANA_END
            or TextHelper.CJK_START <= ch <= TextHelper.CJK_END
            or TextHelper.HALFWIDTH_KATAKANA_START <= ch <= TextHelper.HALFWIDTH_KATAKANA_END
            or TextHelper.KATAKANA_PHONETIC_EXTENSIONS_START <= ch <= TextHelper.KATAKANA_PHONETIC_EXTENSIONS_END
            or ch in TextHelper.VOICED_SOUND_MARKS
        )

    # 判断字符是否为日文字符（包含日文标点符号）
    @staticmethod
    def is_japanese_with_punctuation(ch):
        return (
            TextHelper.JPN_START <= ch <= TextHelper.JPN_END
            or TextHelper.KATAKANA_START <= ch <= TextHelper.KATAKANA_END
            or TextHelper.CJK_START <= ch <= TextHelper.CJK_END
            or TextHelper.HALFWIDTH_KATAKANA_START <= ch <= TextHelper.HALFWIDTH_KATAKANA_END
            or TextHelper.KATAKANA_PHONETIC_EXTENSIONS_START <= ch <= TextHelper.KATAKANA_PHONETIC_EXTENSIONS_END
            or TextHelper.FULLWIDTH_START <= ch <= TextHelper.FULLWIDTH_END
            or TextHelper.SYMBOLS_START <= ch <= TextHelper.SYMBOLS_END
            or ch in TextHelper.VOICED_SOUND_MARKS
        )

    # 判断字符是否为中日韩汉字
    @staticmethod
    def is_cjk(ch):
        return TextHelper.CJK_START <= ch <= TextHelper.CJK_END

    # 判断输入的字符串是否全部由中文或日文汉字组成
    @staticmethod
    def is_all_cjk(text):
        return all(TextHelper.is_cjk(char) for char in text)

    # 检查字符串是否包含至少一个日文字符
    @staticmethod
    def contains_any_japanese(text):
        return any(TextHelper.is_japanese(char) for char in text)

    # 判断输入的字符串是否全部由日文字符组成
    @staticmethod
    def is_all_japanese(text):
        return all(TextHelper.is_japanese(char) for char in text)

    # 移除开头结尾的标点符号
    @staticmethod
    def strip_punctuation(text):
        text = text.strip()

        while text and TextHelper.is_punctuation(text[0]):
            text = text[1:]

        while text and TextHelper.is_punctuation(text[-1]):
            text = text[:-1]

        return text.strip()

    # 判断是否是一个有意义的日文词语
    @staticmethod
    def is_valid_japanese_word(surface, blacklist):
        flag = True

        if surface in blacklist:
            flag = False

        if len(surface) == 1:
            flag = False

        if not TextHelper.contains_any_japanese(surface):
            flag = False

        return flag

    # 找出文本中所有的片假名词
    @staticmethod
    def find_all_katakana_word(fulltext):
        # 使用时再导入，避免相互导入死循环
        from model.Word import Word

        words = []
        for k, v in enumerate(re.findall(r"[\u30A0-\u30FF]+", "\n".join(fulltext))):
            # 移除首尾标点符号
            v = TextHelper.strip_punctuation(v)

            # 有效性检查
            if not TextHelper.is_valid_japanese_word(v, []):
                continue

            word = Word()
            word.count = 1
            word.surface = v
            word.set_context(v, fulltext)

            words.append(word)

        return words

    # 修复不合规的JSON字符串
    @staticmethod
    def fix_broken_json_string(jsonstring):
        # 在 Qwen2 7B 回复中发现
        jsonstring = re.sub(
            r'(?<=: ").+(?=")', # 匹配Json字符中的值不包括双引号的部分
            lambda matches: matches.group(0).replace('\\"', '"').replace('"', '\\"'), 
            jsonstring,
        )

        # 在 GLM4-9B 回复中发现
        jsonstring = jsonstring.replace("```json", "").replace("```", "")

        return jsonstring