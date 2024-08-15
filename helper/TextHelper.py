import re

class TextHelper:

    # 平假名
    HIRAGANA = ("\u3040", "\u309F")

    # 片假名
    KATAKANA = ("\u30A0", "\u30FF")

    # 片假名语音扩展
    KATAKANA_PHONETIC_EXTENSIONS = ("\u31F0", "\u31FF")

    # 濁音和半浊音符号
    VOICED_SOUND_MARKS = ("\u309B", "\u309C")

    # 中日韩统一表意文字
    CJK = ("\u4E00", "\u9FFF")

    # 中日韩通用标点符号
    GENERAL_PUNCTUATION = ("\u2000", "\u206F")
    CJK_SYMBOLS_AND_PUNCTUATION = ("\u3000", "\u303F")
    HALFWIDTH_AND_FULLWIDTH_FORMS = ("\uFF00", "\uFFEF")
    OTHER_CJK_PUNCTUATION = (
        "\u30FB"    # ・ 在片假名 ["\u30A0", "\u30FF"] 范围内
    )

    # 拉丁字符
    LATIN_1 = ("\u0041", "\u005A") # 大写字母 A-Z
    LATIN_2 = ("\u0061", "\u007A") # 小写字母 a-z
    LATIN_EXTENDED_A = ("\u0100", "\u017F")
    LATIN_EXTENDED_B = ("\u0180", "\u024F")
    LATIN_SUPPLEMENTAL = ("\u00A0", "\u00FF")
    
    # 拉丁标点符号
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
            TextHelper.CJK[0] <= ch <= TextHelper.CJK[1] 
            or TextHelper.KATAKANA[0] <= ch <= TextHelper.KATAKANA[1]
            or TextHelper.HIRAGANA[0] <= ch <= TextHelper.HIRAGANA[1]
            or TextHelper.KATAKANA_PHONETIC_EXTENSIONS[0] <= ch <= TextHelper.KATAKANA_PHONETIC_EXTENSIONS[1]
            or ch in TextHelper.VOICED_SOUND_MARKS
        )

    # 判断字符是否为中日韩汉字
    @staticmethod
    def is_cjk(ch):
        return TextHelper.CJK[0] <= ch <= TextHelper.CJK[1]

    # 判断输入的字符串是否全部由中日韩汉字组成
    @staticmethod
    def is_all_cjk(text):
        return all(TextHelper.is_cjk(char) for char in text)

    # 检查字符串是否包含至少一个中日韩汉字组成
    @staticmethod
    def has_any_cjk(text):
        return any(TextHelper.is_cjk(char) for char in text)

    # 判断字符是否为片假名
    @staticmethod
    def is_katakana(ch):
        return TextHelper.KATAKANA[0] <= ch <= TextHelper.KATAKANA[1]

    # 判断字符串是否全部为片假名
    @staticmethod
    def is_all_katakana(ch):
        return all(TextHelper.is_katakana(ch) for ch in text)

    # 检查字符串是否包含至少一个片假名
    @staticmethod
    def has_any_katakanae(text):
        return any(TextHelper.is_katakana(char) for char in text)

    # 判断字符是否为平假名
    @staticmethod
    def is_hiragana(ch):
        return TextHelper.HIRAGANA[0] <= ch <= TextHelper.HIRAGANA[1]

    # 判断字符串是否全部为平假名
    @staticmethod
    def is_all_hiragana(text):
        return all(TextHelper.is_hiragana(ch) for ch in text)

    # 检查字符串是否包含至少一个平假名
    @staticmethod
    def has_any_hiragana(text):
        return any(TextHelper.is_hiragana(char) for char in text)

    # 判断输入的字符串是否全部由日文字符（含汉字）组成
    @staticmethod
    def is_all_japanese(text):
        return all(TextHelper.is_japanese(char) for char in text)

    # 检查字符串是否包含至少一个日文字符（含汉字）
    @staticmethod
    def has_any_japanese(text):
        return any(TextHelper.is_japanese(char) for char in text)

    # 移除开头结尾的标点符号
    @staticmethod
    def strip_punctuation(text):
        text = text.strip()

        while text and TextHelper.is_punctuation(text[0]):
            text = text[1:]

        while text and TextHelper.is_punctuation(text[-1]):
            text = text[:-1]

        return text.strip()

    # 移除开头结尾的阿拉伯数字
    @staticmethod
    def strip_arabic_numerals(text):
        return re.sub(r'^\d+|\d+$', '', text)

    # 移除开头结尾的非日文字符
    @staticmethod
    def strip_not_japanese(text):
        text = text.strip()

        while text and not TextHelper.is_japanese(text[0]):
            text = text[1:]

        while text and not TextHelper.is_japanese(text[-1]):
            text = text[:-1]

        return text.strip()

    # 移除结尾的汉字字符
    @staticmethod
    def remove_suffix_cjk(text):
        while text and TextHelper.is_cjk(text[-1]):
            text = text[:-1]

        return text

    # 修复不合规的JSON字符串
    @staticmethod
    def fix_broken_json_string(jsonstring):
        # 在 Qwen2 7B 回复中发现
        jsonstring = re.sub(
            r'(?<=: ").+(?=")', # 匹配Json字符中的值不包括双引号的部分
            lambda matches: matches.group(0).replace('\\"', '"').replace('"', '\\"'), 
            jsonstring,
        ).strip()

        # 在 GLM4-9B 回复中发现
        jsonstring = jsonstring.replace("```json", "").replace("```", "").strip()
        jsonstring = jsonstring.replace('“', '\\"').replace('”', '\\"').strip()
        jsonstring = jsonstring + "}" if not jsonstring.endswith("}") else jsonstring
        jsonstring = jsonstring.replace(",\n}", "\n}") if not jsonstring.endswith(",\n}") else jsonstring

        return jsonstring

    # 按汉字、平假名、片假名拆开日文短语
    @staticmethod
    def extract_japanese(text):
        return re.findall(
            (
                rf"(?:[{TextHelper.CJK[0]}-{TextHelper.CJK[1]}]+)|" +               # 汉字
                rf"(?:[{TextHelper.HIRAGANA[0]}-{TextHelper.HIRAGANA[1]}]+)|" +     # 平假名
                rf"(?:[{TextHelper.KATAKANA[0]}-{TextHelper.KATAKANA[1]}]+)"        # 片假名
            ), 
            text
        )

    # 移除开头结尾的非汉字字符
    @staticmethod
    def strip_not_cjk(text):
        text = text.strip()

        while text and not TextHelper.is_cjk(text[0]):
            text = text[1:]

        while text and not TextHelper.is_cjk(text[-1]):
            text = text[:-1]

        return text.strip()

    # 判断字符是否为拉丁字符
    @staticmethod
    def is_latin(ch):
        return (
            TextHelper.LATIN_1[0] <= ch <= TextHelper.LATIN_1[1] or
            TextHelper.LATIN_2[0] <= ch <= TextHelper.LATIN_2[1] or
            TextHelper.LATIN_EXTENDED_A[0] <= ch <= TextHelper.LATIN_EXTENDED_A[1] or
            TextHelper.LATIN_EXTENDED_B[0] <= ch <= TextHelper.LATIN_EXTENDED_B[1] or
            TextHelper.LATIN_PUNCTUATION_SUPPLEMENTAL[0] <= ch <= TextHelper.LATIN_PUNCTUATION_SUPPLEMENTAL[1]
        )

    # 判断输入的字符串是否全部由拉丁字符组成
    @staticmethod
    def is_all_latin(text):
        return all(TextHelper.is_latin(ch) for ch in text)

    # 检查字符串是否包含至少一个拉丁字符组成
    @staticmethod
    def has_any_latin(text):
        return any(TextHelper.is_latin(ch) for ch in text)

    # 移除开头结尾的非拉丁字符
    @staticmethod
    def strip_not_latin(text):
        text = text.strip()

        while text and not TextHelper.is_latin(text[0]):
            text = text[1:]

        while text and not TextHelper.is_latin(text[-1]):
            text = text[:-1]

        return text.strip()