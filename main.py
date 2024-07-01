import os
import re
import json
import asyncio
import concurrent.futures
from collections import Counter
from concurrent.futures import as_completed

from model.LLM import LLM
from model.Word import Word
from helper.LogHelper import LogHelper
from helper.TextHelper import TextHelper

# 定义全局对象
# 方便共享全局数据
# 丑陋，但是有效，不服你咬我啊
G = type("GClass", (), {})()

# 原始文本切片阈值
SPLIT_THRESHOLD = 4 * 1024

# 词频阈值
COUNT_THRESHOLD = 3

# 读取TXT文件并返回
def read_txt_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            lines = file.readlines()
        return lines
    except FileNotFoundError:
        print(f"文件 {filename} 不存在.")
        exit(1)

# 读取JSON文件并返回
def read_json_file(filename):
    try:
        # 读取并加载JSON文件
        with open(filename, "r", encoding="utf-8") as file:
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
def split_by_byte_threshold(lines, threshold):
    result = []  # 存储处理后的字符串段
    current_segment = []  # 临时存储当前段的字符串
    current_size = 0  # 当前段的字节大小

    for line in lines:
        line_len = len(line.encode("utf-8"))  # 计算字符串的字节长度

        # 如果加上当前字符串会导致超过阈值，则先处理并清空当前段
        if current_size + line_len > threshold:
            result.append("".join(current_segment))  # 拼接并添加到结果列表
            current_segment = []  # 重置当前段
            current_size = 0  # 重置当前段字节大小

        # 添加当前字符串到当前段
        current_segment.append(line)
        current_size += line_len

    # 添加最后一个段，如果非空
    if current_segment:
        result.append("".join(current_segment))

    return result

# 合并具有相同表面形式（surface）的 Word 对象，计数并逆序排序。
def merge_and_count(words_list):
    surface_to_word = {}

    for word in words_list:
        if word.surface not in surface_to_word:
            # 初始化 surface 对应的 Word 对象
            surface_to_word[word.surface] = word
        else:
            # 累积 count
            existing_word = surface_to_word[word.surface]
            existing_word.count += word.count

    # 将字典转换为列表，并按count逆序排序
    sorted_words = sorted(surface_to_word.values(), key=lambda x: x.count, reverse=True)

    return sorted_words

# 将 Word 列表写入文件
def write_words_to_file(words, filename, detailmode):
    with open(filename, "w", encoding="utf-8") as file:
        if not detailmode:
            file.write("{")

        for k, word in enumerate(words):
            if detailmode:
                file.write(f"词语原文 : {word.surface}\n")
                file.write(f"词语翻译 : {word.surface_translation}\n")
                file.write(f"出现次数 : {word.count}\n")
                file.write(f"上下文原文 : -----------------------------------------------------\n")
                file.write(f"{'    \n'.join(word.context)}\n")
                file.write(f"上下文翻译 : -----------------------------------------------------\n")
                file.write(f"{'    \n'.join(word.context_translation)}\n")
                file.write("\n")
            elif k == 0:
                file.write("\n")
                file.write(f'    "{word.surface}" : "",\n')
            elif k != len(words) - 1:
                file.write(f'    "{word.surface}" : "",\n')
            else:
                file.write(f'    "{word.surface}" : ""\n')

        if not detailmode:
            file.write("}")

# 读取数据文件
def read_data_file():
    input_data = []

    if os.path.exists("ManualTransFile.json"):
        user_input = input(
            f'已找到数据文件 "ManualTransFile.json"，按回车直接使用或输入其他文件的路径：'
        ).strip('"')

        if user_input:
            input_file_name = user_input
        else:
            input_file_name = "ManualTransFile.json"
    elif os.path.exists("all.orig.txt"):
        user_input = input(
            f'已找到数据文件 "all.orig.txt"，按回车直接使用或输入其他文件的路径：'
        ).strip('"')

        if user_input:
            input_file_name = user_input
        else:
            input_file_name = "all.orig.txt"
    else:
        input_file_name = input(
            '未找到 "all.orig.txt" 或 "ManualTransFile.json"，请输入数据文件的路径: '
        ).strip('"')

    if input_file_name.endswith(".txt"):
        input_data = read_txt_file(input_file_name)
    elif input_file_name.endswith(".json"):
        input_data = read_json_file(input_file_name)
    else:
        print(f"不支持的文件格式: {input_file_name}")

    for k, line in enumerate(input_data):
        line.strip()

        if len(line) == 0:
            input_data.pop(k)

        if not TextHelper.contains_any_japanese(line):
            input_data.pop(k)

    return input_data

# 主函数
async def main():
    fulltext = read_data_file()
    LogHelper.info("正在对文件中的文本进行预处理 ...")
    input_data_splited = split_by_byte_threshold(fulltext, SPLIT_THRESHOLD)

    llm = LLM(G.api_key, G.base_url, G.model_name)
    llm.load_black_list("blacklist.txt")
    llm.load_prompt_extract_words("prompt\\prompt_extract_words.txt")
    llm.load_prompt_translate_surface("prompt\\prompt_translate_surface.txt")
    llm.load_prompt_translate_context("prompt\\prompt_translate_context.txt")
    
    # 等待分词任务结果
    LogHelper.info("即将开始执行 [LLM 分词] ...")
    words = await llm.extract_words_batch(input_data_splited, fulltext)

    # 合并与排序
    words_all = merge_and_count(words)

    # 按阈值筛选
    words_with_threshold = [word for word in words_all if word.count >= COUNT_THRESHOLD]

    # 等待翻译词表任务结果
    if G.translate_surface_mode == 1:
        LogHelper.info("即将开始执行 [后处理 - 词表翻译] ...")
        words_with_threshold = await llm.translate_surface_batch(words_with_threshold)

    # 等待上下文词表任务结果
    if G.translate_context_mode == 1:
        LogHelper.info("即将开始执行 [后处理 - 上下文翻译] ...")
        words_with_threshold = await llm.translate_context_batch(words_with_threshold)

    # 定义输出文件名
    names_true_output_file = "角色姓名_日志.txt"
    dictionary_names_true_file = "角色姓名_列表.json"

    # 写入文件
    write_words_to_file(words_with_threshold, names_true_output_file, True)
    write_words_to_file(words_with_threshold, dictionary_names_true_file, False)

    # 输出日志
    LogHelper.info("")
    LogHelper.info(f"结果已写入到:")
    LogHelper.info(f"　　{names_true_output_file}")
    LogHelper.info(f"　　{dictionary_names_true_file}")
    LogHelper.info("\n\n")

# 开始运行程序
if __name__ == "__main__":
    print()
    print()
    print(f"※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※")
    print(f"※※※※")
    print(f"※※※※  ※※※※                 注意               ")
    print(f"※※※※  ※※※※        处理流程将消耗巨量 Token     ")
    print(f"※※※※  ※※※※    使用在线接口的同学请关注自己的账单 ")
    print(f"※※※※")
    print(f"※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※")
    print()
    print()

    # 加载配置文件
    try:
        if os.path.exists("config_dev.json"):
            config_file = "config_dev.json"
        else:
            config_file = "config.json"

        with open(config_file, "r", encoding="utf-8") as file:
            config = json.load(file)
            for key in config:
                setattr(G, key, config[key])
    except FileNotFoundError:
        LogHelper.error(f"文件 {config_file} 未找到.")
    except json.JSONDecodeError:
        LogHelper.error(f"文件 {config_file} 不是有效的JSON格式.")

    # 开始业务逻辑
    asyncio.run(main())
