import os
import re
import json
import openai
import concurrent.futures
from collections import Counter
from concurrent.futures import as_completed

try:
    import spacy
    from sudachipy import tokenizer as SudachipyTokenizer
    from sudachipy import dictionary as SudachipyDictionary
    from janome.tokenizer import Tokenizer as JanomeTokenizer
except ModuleNotFoundError:
    print("缺少传统分词模式下的依赖模块 ... 如不是使用传统分词可以忽略本提示 ...")

# 设置文件名
# 支持两种不同的文本输入格式，根据后缀名识别
# 可以直接使用 mtool 导出文本
#
# JSON:
#   {
#       "原文": "译文",
#       "原文": "译文",
#       "原文": "译文"
#   }
# 
# TXT:
#       原文
#       原文
#       原文

# INPUT_FILE_NAME = 'all.orig.txt'
INPUT_FILE_NAME = 'ManualTransFile.json'

# 查找人名
NAME_GACHA = True

# 查找地名（开发中）
REGION_GACHA = False

# 使用传统分词
# 效果较差，仅对比用，不再维护
# 会采集到大量垃圾信息，应同时开启二次校验
USE_TRADITIONAL_TOKENIZER = False

# 开启二次校验
RECHECK_BY_LLM = False

# LLM每次返回的最大Token阈值
MAX_TOKENS = 512

# 分词等计算任务的并发线程数
MAX_WORKERS = 8

# 原始文本切片阈值大小
SPLIT_THRESHOL = 4 * 1024

# 出现次数过滤阈值大小
COUNT_THRESHOLD = 5

# 词汇表黑名单
BLACK_LIST = [
    "様", # sama
    "さま", # sama
    "君", # kun
    "くん", # kun
    "桑", # san
    "さん", # san
    "殿", # dono
    "どの", # dono
    ""
]

# AI客户端初始化
API_KEY = "sk-no-key-required"
BASE_URL = "http://localhost:8080/v1"
MODEL_NAME = "qwen2-7b-instruct"
client = openai.OpenAI(
    base_url= BASE_URL,
    api_key = API_KEY
)

class Word:
    def __init__(self):
        self.name = False
        self.count = 0
        self.context = []
        self.surface = ""
        self.attribute = ""
        self.llmresponse = ""

    def set_name(self, name: bool):
        self.name = name

    def set_count(self, count: int):
        self.count = count

    def set_context(self, context: list):
        self.context = context

    def set_surface(self, surface: str):
        self.surface = surface

    def set_attribute(self, attribute: str):
        self.attribute = attribute

    def set_llmresponse(self, llmresponse: str):
        self.llmresponse = llmresponse

    # 从原始文本中获取上下文
    def set_context_from_lines(self, lines: list):
        for line in lines:
            if self.surface in line:
                # 如果context未满，直接添加
                if len(self.context) < 10:
                    self.context.append(line.strip())
                else:
                    # context已满，替换最短的条目
                    shortest_index = min(range(len(self.context)), key=lambda i: len(self.context[i]))
                    self.context[shortest_index] = line.strip()


        # def set_context_from_lines(self, lines: list):
        #     max_total_chars = 0
        #     best_context = []
            
        #     for index, line in enumerate(lines):
        #         if self.surface in line:
        #             # 确保start_index不小于0，避免负索引
        #             start_index = max(0, index - 4)
        #             # 确保end_index不大于lines的长度，避免索引超出范围
        #             end_index = min(len(lines), index + 5)
                    
        #             # 获取上下文数组
        #             context = lines[start_index:end_index]
        #             # 计算该上下文数组内所有字符串的字符数总和
        #             total_chars = sum(len(line) for line in context)
                    
        #             # 如果当前上下文的字符总数大于之前记录的最大字符总数，则更新best_context
        #             if total_chars > max_total_chars:
        #                 max_total_chars = total_chars
        #                 best_context = context
            
        #     self.set_context(best_context)

# 读取TXT文件并返回
def read_txt_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        return lines
    except FileNotFoundError:
        print(f"文件 {filename} 不存在.")
        exit(1)

# 读取JSON文件并返回
def read_json_file(filename):
    try:
        # 读取并加载JSON文件
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # 遍历JSON数据，提取所有键
        keys_list = []
        for key in data.keys():
            keys_list.append(key)
        
        # 返回包含所有键的列表
        return keys_list
    except FileNotFoundError:
        print(f"文件 {filename} 未找到.")
        exit(1)
    except json.JSONDecodeError:
        print(f"文件 {filename} 不是有效的JSON格式.")
        exit(1)

# 将字符串数组按照字节阈值进行分割。
def split_by_byte_threshold(strings, threshold):
    result = []  # 存储处理后的字符串段
    current_segment = []  # 临时存储当前段的字符串
    current_size = 0  # 当前段的字节大小
    
    for string in strings:
        string_size = len(string.encode('utf-8'))  # 计算字符串的字节长度
        
        # 如果加上当前字符串会导致超过阈值，则先处理并清空当前段
        if current_size + string_size > threshold:
            result.append(''.join(current_segment))  # 拼接并添加到结果列表
            current_segment = []  # 重置当前段
            current_size = 0  # 重置当前段字节大小
        
        # 添加当前字符串到当前段
        current_segment.append(string)
        current_size += string_size
    
    # 添加最后一个段，如果非空
    if current_segment:
        result.append(''.join(current_segment))
    
    return result

# 定义日文字符的Unicode范围辅助函数
def is_japanese(ch):
    # 平假名
    if '\u3040' <= ch <= '\u309f':
        return True
    # 片假名
    if '\u30a0' <= ch <= '\u30ff':
        return True
    # 日文汉字
    if '\u4e00' <= ch <= '\u9fff':
        return True
    # 日文全角数字
    if '\u3000' <= ch <= '\u303f':
        return True
    # 日文标点符号
    if '\uff01' <= ch <= '\uff60':
        return True
    # 濁音和半濁音符号
    if '\u309b' <= ch <= '\u309e':
        return True
    # 日文半角片假名
    if '\uff66' <= ch <= '\uff9f':
        return True

# 判断一个字符是否是中文汉字或日文汉字
def is_chinese_or_kanji(ch):
    return '\u4e00' <= ch <= '\u9fff'  # 包括中文汉字和日文汉字

# 检查字符串是否包含至少一个日文字符
def contains_japanese(text):
    return any(is_japanese(char) for char in text)

# 判断输入的字符串是否全部是日文
def is_all_japanese(text):
    # 遍历字符串中的每个字符
    for char in text:
        # 使用已经定义的函数来检查字符是否是中文汉字
        if not is_japanese(char):
            # 如果发现非汉字字符，返回False
            return False
    # 如果所有字符都是汉字，则返回True
    return True

# 判断输入的字符串是否全部是汉字
def is_all_chinese_or_kanji(text):
    # 遍历字符串中的每个字符
    for char in text:
        # 使用已经定义的函数来检查字符是否是中文汉字
        if not is_chinese_or_kanji(char):
            # 如果发现非汉字字符，返回False
            return False
    # 如果所有字符都是汉字，则返回True
    return True

# 判断是否是合法的名词
def is_valid_noun(surface, attribute):
    flag = True

    if surface in BLACK_LIST :
        flag = False

    # if not "角色姓名" in attribute :
    #     flag = False

    if len(surface) <= 1 :
        flag = False

    if not contains_japanese(surface) :
        flag = False

    # っ和ッ结尾的一般是语气词
    if re.compile(r'^[ぁ-んァ-ン]+[っッ]$').match(surface) :
        flag = False

    if not "LLM" in attribute and not "名詞" in attribute or "名詞的" in attribute or "代名詞" in attribute :
        flag = False

    # if not "NOUN" in token.pos_ and not "PRON" in token.pos_ :
    #     continue

    # if is_all_chinese_or_kanji(token.text) :
    #     continue

    # if len(token.text) == 1 and not is_chinese_or_kanji(token.text) :
    #     flag = False

    return flag

# 使用 llm 分词
def extract_nouns_llm(context):
    words = []
    
    completion = client.chat.completions.create(
        model = API_KEY,
        temperature = 0.1,
        top_p = 0.3,
        max_tokens = MAX_TOKENS,
        frequency_penalty = 0.2,
        messages = [
            {
                "role": "system",
                "content": "请分析以下日语句子，这是一段来自日文游戏的文本，从中识别出所有可能的角色名称。在回答中，只需列出这些可能的角色名称，如果有多个，请使用英文逗号(,)进行分隔。"
            },
            {
                "role": "user", "content": f"{context}"
            }
        ]
    )

    llmresponse = completion
    usage = completion.usage
    message = completion.choices[0].message
    finish_reason = completion.choices[0].finish_reason

    # 幻觉，直接抛掉
    if usage.completion_tokens >= MAX_TOKENS:
        return words

    for text in message.content.split(","):
        surface = text.strip()
        attribute = "LLM"

        # 跳过空字符串
        if not surface:
            continue
        
        # 防止模型瞎编出原文中不存在的词
        if not surface in context:
            continue

        if is_valid_noun(surface, attribute):
            word = Word()
            word.set_name(True)
            word.set_count(1)
            word.set_context([context])
            word.set_surface(surface)
            word.set_attribute(attribute)
            word.set_llmresponse(llmresponse)
            words.append(word)

    return words

# 使用 spacy 分词
def extract_nouns_spacy(tokenizer, text):
    words = []

    for token in tokenizer(text):
        # DEBUG
        # print(token.text, token.lemma_, token.pos_, token.tag_, token.dep_, token.shape_, token.is_alpha, token.is_stop)

        surface = token.text
        attribute = f"{token.pos_}-{token.tag_}"

        if is_valid_noun(surface, attribute):
            word = Word()
            word.set_name(True)
            word.set_count(1)
            word.set_surface(surface)
            word.set_attribute(attribute)
            words.append(word)            

    return words
    
# 使用 janome 分词
def extract_nouns_janome(tokenizer, text):
    words = []

    for token in tokenizer.tokenize(text):
        surface = token.surface
        attribute = token.part_of_speech.replace(",", "-")

        if is_valid_noun(surface, attribute):
            word = Word()
            word.set_name(True)
            word.set_count(1)
            word.set_surface(surface)
            word.set_attribute(attribute)
            words.append(word)  
    
    return words

# 使用 sudachipy 分词
def extract_nouns_sudachipy(tokenizer, text):
    words = []

    for token in tokenizer.tokenize(text, SudachipyTokenizer.Tokenizer.SplitMode.C):
        surface = token.surface()
        attribute = str(token.part_of_speech()).replace(", ", "-").replace("(", "").replace(")", "").replace("\'", "")

        if is_valid_noun(surface, attribute):
            word = Word()
            word.set_name(True)
            word.set_count(1)
            word.set_surface(surface)
            word.set_attribute(attribute)
            words.append(word)  
    
    return words

def process_with_spacy(input_data_splited):
    datas = []
    tokenizer_spacy = spacy.load("ja_core_news_lg")
    for k, v in enumerate(input_data_splited):
        print(f"正在使用 spacy 对 {k + 1} / {len(input_data_splited)} 段进行分词 ...")
        datas = datas + extract_nouns_spacy(tokenizer_spacy, v)
    return datas

def process_with_janome(input_data_splited):
    datas = []
    tokenizer_janome = JanomeTokenizer()
    for k, v in enumerate(input_data_splited):
        print(f"正在使用 janome 对 {k + 1} / {len(input_data_splited)} 段进行分词 ...")
        datas = datas + extract_nouns_janome(tokenizer_janome, v)
    return datas

def process_with_sudachipy(input_data_splited):
    datas = []
    tokenizer_sudachipy = SudachipyDictionary.Dictionary(dict="full").create()
    for k, v in enumerate(input_data_splited):
        print(f"正在使用 sudachipy 对 {k + 1} / {len(input_data_splited)} 段进行分词 ...")
        datas = datas + extract_nouns_sudachipy(tokenizer_sudachipy, v)
    return datas

# 合并具有相同表面形式（surface）的 Word 对象，计数并逆序排序。
def merge_and_count(words_list):
    surface_to_word = {}

    for word in words_list:
        if word.surface not in surface_to_word:

            # 初始化 surface 对应的 Word 对象
            surface_to_word[word.surface] = word
        else:
            existing_word = surface_to_word[word.surface]

            # 累积 count
            existing_word.count += word.count

            # 如果新word的count更大，则更新attribute
            if word.count > existing_word.count:
                existing_word.attribute = word.attribute

    # 将字典转换为列表，并按count逆序排序
    sorted_words = sorted(surface_to_word.values(), key=lambda x: x.count, reverse=True)

    return sorted_words

# 判断是否是角色姓名
def check_name_with_llm(word):
    content = f"请根据以下上下文，判定词汇「{word.surface}」是否为一个角色姓名\n{''.join(word.context)}"
    
    completion = client.chat.completions.create(
        model = API_KEY,
        temperature = 0,
        messages = [
                {
                "role": "system",
                "content": "你擅长日文名词辨识，能依据上下文精确判断词汇属性。回答时仅以「是」或「否」作答，若不确切，回复「是」。"
            },
            {
                "role": "user", "content": content
            }
        ]
    )

    word.set_llmresponse(completion.choices[0].message.content)
    if word.llmresponse == "是":
        word.set_name(True)
    else:
        word.set_name(False)

    return word

# 将 Word 列表写入文件
def write_words_to_file(words, filename, detailmode = False):
    with open(filename, 'w', encoding='utf-8') as file:
        if not detailmode: file.write("{")

        for k, word in enumerate(words):
            if detailmode:
                file.write(f"""
                    "surface": {word.surface},
                    "name": {word.name},
                    "count": {word.count},
                    "context": {word.context},
                    "attribute": {word.attribute},
                    "llmresponse": {word.llmresponse}
                """)
                file.write("\n")
            elif k == 0:
                file.write("\n")
                file.write(f"    \"{word.surface}\" : \"\",\n")
            elif k != len(words) - 1:
                file.write(f"    \"{word.surface}\" : \"\",\n")
            else:
                file.write(f"    \"{word.surface}\" : \"\"\n")

        if not detailmode: file.write("}")

# 主函数
def main():
    # 读取文件
    print(f"正在读取 {INPUT_FILE_NAME} 文件 ...")

    if INPUT_FILE_NAME.endswith('.json'):
        input_data = read_json_file(INPUT_FILE_NAME)
    elif INPUT_FILE_NAME.endswith('.txt'):
        input_data = read_txt_file(INPUT_FILE_NAME)
    else:
        print(f"不支持的文件格式: {INPUT_FILE_NAME}")

    print("正在分割输入文本 ...")
    input_data_splited = split_by_byte_threshold(input_data, SPLIT_THRESHOL)

    # 执行分词，并行处理
    with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 传统分词
        if USE_TRADITIONAL_TOKENIZER:
            spacy_result = executor.submit(process_with_spacy, input_data_splited)
            janome_result = executor.submit(process_with_janome, input_data_splited)
            sudachipy_result = executor.submit(process_with_sudachipy, input_data_splited)

            words_spacy = spacy_result.result()
            words_janome = janome_result.result()
            words_sudachipy = sudachipy_result.result()
        else:
            words_spacy = []
            words_janome = []
            words_sudachipy = []

        # LLM分词
        futures = []
        words_llm = []
        finished_task = 0

        for k, text in enumerate(input_data_splited):
            futures.append(executor.submit(extract_nouns_llm, text))   

        for future in as_completed(futures):
            try:
                words_llm.extend(future.result())
                finished_task = finished_task + 1
                print(f"正在使用 LLM 对 {finished_task} / {len(input_data_splited)} 段进行分词 ...")
            except Exception as exc:
                print(f'Task generated an exception: {exc}')

    # 分别处理并统计每个tokenizer的结果
    words_llm_counted = merge_and_count(words_llm)
    words_spacy_counted = merge_and_count(words_spacy)
    words_janome_counted = merge_and_count(words_janome)
    words_sudachipy_counted = merge_and_count(words_sudachipy)

    # 合并所有数组
    words_all = merge_and_count(words_llm_counted + words_spacy_counted + words_janome_counted + words_sudachipy_counted)

    # 筛选并移除 count 小于 COUNT_THRESHOLD 的条目
    words_filtered = [word for word in words_all if word.count >= COUNT_THRESHOLD]

    # 更新 words_all 为过滤后的列表
    words_all = words_filtered

    # 二次确认
    if RECHECK_BY_LLM:
        # 查找上下文
        for k, word in enumerate(words_all):
            print(f"正在查找第 {k + 1} / {len(words_all)} 个条目的上下文 ...")
            word.set_context_from_lines(input_data)

        # 判断是否是角色姓名，并行处理
        finished_task = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = []
            for k, word in enumerate(words_all):
                futures.append(executor.submit(check_name_with_llm, word))   

            for future in as_completed(futures):
                try:
                    future.result()
                    finished_task = finished_task + 1
                    print(f"正在判断第 {finished_task} / {len(words_all)} 个条目是否是角色姓名 ...")
                except Exception as exc:
                    print(f'Task generated an exception: {exc}')

    # 分离出角色姓名和非角色姓名的单词列表
    names_true = [word for word in words_all if word.name]
    names_false = [word for word in words_all if not word.name]

    # 定义输出文件名
    dictionary_names_true_file = "角色姓名_列表.json"
    dictionary_names_false_file = "角色姓名_列表_未通过检查.json"
    names_true_output_file = "角色姓名_日志.txt"
    names_false_output_file = "角色姓名_日志_未通过检查.txt"

    # 写入词典
    write_words_to_file(names_true, dictionary_names_true_file, False)
    write_words_to_file(names_false, dictionary_names_false_file, False)

    # 写入日志
    write_words_to_file(names_true, names_true_output_file, True)
    write_words_to_file(names_false, names_false_output_file, True)

    # 输出日志
    print(f"结果已写入到:")
    print(f"{dictionary_names_true_file}, {names_true_output_file}")
    print(f"{dictionary_names_false_file}, {names_false_output_file}")

# 开始运行程序
if __name__ == '__main__':
    main()