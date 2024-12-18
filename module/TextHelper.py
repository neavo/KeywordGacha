import re
import json

class TextHelper:

    # 平假名
    HIRAGANA = ("\u3040", "\u309F")

    # 片假名
    KATAKANA = ("\u30A0", "\u30FF")

    # 半角片假名（包括半角浊音、半角拗音等）
    KATAKANA_HALF_WIDTH = ("\uFF65", "\uFF9F")

    # 片假名语音扩展
    KATAKANA_PHONETIC_EXTENSIONS = ("\u31F0", "\u31FF")

    # 濁音和半浊音符号
    VOICED_SOUND_MARKS = ("\u309B", "\u309C")

    # 韩文字母 (Hangul Jamo)
    HANGUL_JAMO = ("\u1100", "\u11FF")

    # 韩文字母扩展-A (Hangul Jamo Extended-A)
    HANGUL_JAMO_EXTENDED_A = ("\uA960", "\uA97F")

    # 韩文字母扩展-B (Hangul Jamo Extended-B)
    HANGUL_JAMO_EXTENDED_B = ("\uD7B0", "\uD7FF")

    # 韩文音节块 (Hangul Syllables)
    HANGUL_SYLLABLES = ("\uAC00", "\uD7AF")

    # 韩文兼容字母 (Hangul Compatibility Jamo)
    HANGUL_COMPATIBILITY_JAMO = ("\u3130", "\u318F")

    # 中日韩统一表意文字
    CJK = ("\u4E00", "\u9FFF")

    # 中日韩通用标点符号
    GENERAL_PUNCTUATION = ("\u2000", "\u206F")
    CJK_SYMBOLS_AND_PUNCTUATION = ("\u3001", "\u303F") # \u3000 是半角空格
    HALFWIDTH_AND_FULLWIDTH_FORMS = ("\uFF00", "\uFFEF")

    # 拉丁字符
    LATIN_1 = ("\u0041", "\u005A") # 大写字母 A-Z
    LATIN_2 = ("\u0061", "\u007A") # 小写字母 a-z
    LATIN_EXTENDED_A = ("\u0100", "\u017F")
    LATIN_EXTENDED_B = ("\u0180", "\u024F")
    LATIN_SUPPLEMENTAL = ("\u00A0", "\u00FF")

    # 拉丁标点符号
    LATIN_PUNCTUATION_BASIC_1 = ("\u0021", "\u002F") # \u0020 是半角空格
    LATIN_PUNCTUATION_BASIC_2 = ("\u003A", "\u0040")
    LATIN_PUNCTUATION_BASIC_3 = ("\u005B", "\u0060")
    LATIN_PUNCTUATION_BASIC_4 = ("\u007B", "\u007E")
    LATIN_PUNCTUATION_GENERAL = ("\u2000", "\u206F")
    LATIN_PUNCTUATION_SUPPLEMENTAL = ("\u2E00", "\u2E7F")

    # 特殊符号
    SPECIAL_PUNCTUATION = (
        "\u00b7",    # ·
        "\u30FB",    # ・
        "\u2665",    # ♥
    )

    # 分割符号
    SPLIT_BY_PUNCTUATION_PATTERN = re.compile(""
        + rf"["
        + rf"{GENERAL_PUNCTUATION[0]}-{GENERAL_PUNCTUATION[1]}"
        + rf"{CJK_SYMBOLS_AND_PUNCTUATION[0]}-{CJK_SYMBOLS_AND_PUNCTUATION[1]}"
        + rf"{HALFWIDTH_AND_FULLWIDTH_FORMS[0]}-{HALFWIDTH_AND_FULLWIDTH_FORMS[1]}"
        + rf"{LATIN_PUNCTUATION_BASIC_1[0]}-{LATIN_PUNCTUATION_BASIC_1[1]}"
        + rf"{LATIN_PUNCTUATION_BASIC_2[0]}-{LATIN_PUNCTUATION_BASIC_2[1]}"
        + rf"{LATIN_PUNCTUATION_BASIC_3[0]}-{LATIN_PUNCTUATION_BASIC_3[1]}"
        + rf"{LATIN_PUNCTUATION_BASIC_4[0]}-{LATIN_PUNCTUATION_BASIC_4[1]}"
        + rf"{LATIN_PUNCTUATION_GENERAL[0]}-{LATIN_PUNCTUATION_GENERAL[1]}"
        + rf"{LATIN_PUNCTUATION_SUPPLEMENTAL[0]}-{LATIN_PUNCTUATION_SUPPLEMENTAL[1]}"
        + rf"{"".join(SPECIAL_PUNCTUATION)}"
        + rf"]+",
    )

    # 判断字符是否为汉字字符
    def is_cjk(char: str) -> bool:
        return TextHelper.CJK[0] <= char <= TextHelper.CJK[1]

    # 判断字符是否为拉丁字符
    def is_latin(char: str) -> bool:
        return (
            TextHelper.LATIN_1[0] <= char <= TextHelper.LATIN_1[1]
            or TextHelper.LATIN_2[0] <= char <= TextHelper.LATIN_2[1]
            or TextHelper.LATIN_EXTENDED_A[0] <= char <= TextHelper.LATIN_EXTENDED_A[1]
            or TextHelper.LATIN_EXTENDED_B[0] <= char <= TextHelper.LATIN_EXTENDED_B[1]
            or TextHelper.LATIN_PUNCTUATION_SUPPLEMENTAL[0] <= char <= TextHelper.LATIN_PUNCTUATION_SUPPLEMENTAL[1]
        )

    # 判断字符是否为韩文字符
    def is_korean(char: str) -> bool:
        return (
            TextHelper.CJK[0] <= char <= TextHelper.CJK[1]
            or TextHelper.HANGUL_JAMO[0] <= char <= TextHelper.HANGUL_JAMO[1]
            or TextHelper.HANGUL_JAMO_EXTENDED_A[0] <= char <= TextHelper.HANGUL_JAMO_EXTENDED_A[1]
            or TextHelper.HANGUL_JAMO_EXTENDED_B[0] <= char <= TextHelper.HANGUL_JAMO_EXTENDED_B[1]
            or TextHelper.HANGUL_SYLLABLES[0] <= char <= TextHelper.HANGUL_SYLLABLES[1]
            or TextHelper.HANGUL_COMPATIBILITY_JAMO[0] <= char <= TextHelper.HANGUL_COMPATIBILITY_JAMO[1]
        )

    # 判断字符是否为平假名
    def is_hiragana(char: str) -> bool:
        return TextHelper.HIRAGANA[0] <= char <= TextHelper.HIRAGANA[1]

    # 判断字符是否为片假名
    def is_katakana(char: str) -> bool:
        return TextHelper.KATAKANA[0] <= char <= TextHelper.KATAKANA[1]

    # 判断字符是否为日文字符
    def is_japanese(char: str) -> bool:
        return (
            TextHelper.CJK[0] <= char <= TextHelper.CJK[1]
            or TextHelper.KATAKANA[0] <= char <= TextHelper.KATAKANA[1]
            or TextHelper.HIRAGANA[0] <= char <= TextHelper.HIRAGANA[1]
            or TextHelper.KATAKANA_HALF_WIDTH[0] <= char <= TextHelper.KATAKANA_HALF_WIDTH[1]
            or TextHelper.KATAKANA_PHONETIC_EXTENSIONS[0] <= char <= TextHelper.KATAKANA_PHONETIC_EXTENSIONS[1]
            or TextHelper.VOICED_SOUND_MARKS[0] <= char <= TextHelper.VOICED_SOUND_MARKS[1]
        )

    # 判断一个字符是否是标点符号
    def is_punctuation(char: str) -> bool:
        return TextHelper.is_cjk_punctuation(char) or TextHelper.is_latin_punctuation(char) or TextHelper.is_special_punctuation(char)

    # 判断一个字符是否是汉字字符标点符号
    def is_cjk_punctuation(char: str) -> bool:
        return (
            TextHelper.GENERAL_PUNCTUATION[0] <= char <= TextHelper.GENERAL_PUNCTUATION[1]
            or TextHelper.CJK_SYMBOLS_AND_PUNCTUATION[0] <= char <= TextHelper.CJK_SYMBOLS_AND_PUNCTUATION[1]
            or TextHelper.HALFWIDTH_AND_FULLWIDTH_FORMS[0] <= char <= TextHelper.HALFWIDTH_AND_FULLWIDTH_FORMS[1]
        )

    # 判断一个字符是否是拉丁标点符号
    def is_latin_punctuation(char: str) -> bool:
        return (
            TextHelper.LATIN_PUNCTUATION_BASIC_1[0] <= char <= TextHelper.LATIN_PUNCTUATION_BASIC_1[1]
            or TextHelper.LATIN_PUNCTUATION_BASIC_2[0] <= char <= TextHelper.LATIN_PUNCTUATION_BASIC_2[1]
            or TextHelper.LATIN_PUNCTUATION_BASIC_3[0] <= char <= TextHelper.LATIN_PUNCTUATION_BASIC_3[1]
            or TextHelper.LATIN_PUNCTUATION_BASIC_4[0] <= char <= TextHelper.LATIN_PUNCTUATION_BASIC_4[1]
            or TextHelper.LATIN_PUNCTUATION_GENERAL[0] <= char <= TextHelper.LATIN_PUNCTUATION_GENERAL[1]
            or TextHelper.LATIN_PUNCTUATION_SUPPLEMENTAL[0] <= char <= TextHelper.LATIN_PUNCTUATION_SUPPLEMENTAL[1]
        )

    # 判断一个字符是否是拉丁标点符号
    def is_special_punctuation(char: str) -> bool:
        return char in TextHelper.SPECIAL_PUNCTUATION

    # 检查字符串是否包含至少一个汉字字符组成
    def has_any_cjk(text: str) -> bool:
        return any(TextHelper.is_cjk(char) for char in text)

    # 检查字符串是否包含至少一个拉丁字符组成
    def has_any_latin(text: str) -> bool:
        return any(TextHelper.is_latin(char) for char in text)

    # 检查字符串是否包含至少一个韩文字符组成
    def has_any_korean(text: str) -> bool:
        return any(TextHelper.is_korean(char) for char in text)

    # 检查字符串是否包含至少一个平假名
    def has_any_hiragana(text: str) -> bool:
        return any(TextHelper.is_hiragana(char) for char in text)

    # 检查字符串是否包含至少一个片假名
    def has_any_katakanae(text: str) -> bool:
        return any(TextHelper.is_katakana(char) for char in text)

    # 检查字符串是否包含至少一个日文字符（含汉字字符）
    def has_any_japanese(text: str) -> bool:
        return any(TextHelper.is_japanese(char) for char in text)

    # 检查字符串是否包含至少一个标点符号
    def has_any_punctuation(text: str) -> bool:
        return any(TextHelper.is_punctuation(char) for char in text)

    # 判断输入的字符串是否全部由汉字字符组成
    def is_all_cjk(text: str) -> bool:
        return all(TextHelper.is_cjk(char) for char in text)

    # 判断输入的字符串是否全部由拉丁字符组成
    def is_all_latin(text: str) -> bool:
        return all(TextHelper.is_latin(char) for char in text)

    # 判断输入的字符串是否全部由韩文字符组成
    def is_all_korean(text: str) -> bool:
        return all(TextHelper.is_korean(char) for char in text)

    # 判断字符串是否全部为平假名
    def is_all_hiragana(text: str) -> bool:
        return all(TextHelper.is_hiragana(char) for char in text)

    # 判断字符串是否全部为片假名
    def is_all_katakana(text: str) -> bool:
        return all(TextHelper.is_katakana(char) for char in text)

    # 判断输入的字符串是否全部由日文字符（含汉字字符）组成
    def is_all_japanese(text: str) -> bool:
        return all(TextHelper.is_japanese(char) for char in text)

    # 移除开头结尾的非汉字字符
    def strip_not_cjk(text: str) -> str:
        text = text.strip()

        while text and not TextHelper.is_cjk(text[0]):
            text = text[1:]

        while text and not TextHelper.is_cjk(text[-1]):
            text = text[:-1]

        return text.strip()

    # 移除开头结尾的非拉丁字符
    def strip_not_latin(text: str) -> str:
        text = text.strip()

        while text and not TextHelper.is_latin(text[0]):
            text = text[1:]

        while text and not TextHelper.is_latin(text[-1]):
            text = text[:-1]

        return text.strip()

    # 移除开头结尾的非韩文字符
    def strip_not_korean(text: str) -> str:
        text = text.strip()

        while text and not TextHelper.is_korean(text[0]):
            text = text[1:]

        while text and not TextHelper.is_korean(text[-1]):
            text = text[:-1]

        return text.strip()

    # 移除开头结尾的非日文字符
    def strip_not_japanese(text: str) -> str:
        text = text.strip()

        while text and not TextHelper.is_japanese(text[0]):
            text = text[1:]

        while text and not TextHelper.is_japanese(text[-1]):
            text = text[:-1]

        return text.strip()

    # 移除开头结尾的标点符号
    def strip_punctuation(text: str) -> str:
        text = text.strip()

        while text and TextHelper.is_punctuation(text[0]):
            text = text[1:]

        while text and TextHelper.is_punctuation(text[-1]):
            text = text[:-1]

        return text.strip()

    # 移除开头结尾的阿拉伯数字
    def strip_arabic_numerals(text: str) -> str:
        return re.sub(r"^\d+|\d+$", "", text)

    # 按标点符号分割字符串
    def split_by_punctuation(text: str) -> list[str]:
        return re.split(TextHelper.SPLIT_BY_PUNCTUATION_PATTERN, text)

    # 安全加载 JSON 字典
    def safe_load_json_dict(json_str: str) -> dict:
        result = {}

        # 移除首尾空白符（含空格、制表符、换行符）
        json_str = json_str.strip()

        # 移除代码标识
        json_str = json_str.removeprefix("```json").removeprefix("```").strip()

        # 先尝试使用 json.loads 解析
        try:
            result = json.loads(json_str)
        except Exception as e:
            pass

        # 否则使用正则表达式匹配
        if len(result) == 0:
            for item in re.findall(r"['\"].+?['\"]\s*\:\s*['\"].+?['\"]\s*(?=[,}])", json_str, flags = re.IGNORECASE):
                p = item.split(":")
                result[p[0].strip().strip("'\"").strip()] = p[1].strip().strip("'\"").strip()

        return result