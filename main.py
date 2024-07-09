import os
import re
import csv
import json
import asyncio
import logging
import traceback
import concurrent.futures
from collections import Counter
from concurrent.futures import as_completed

import tiktoken
import tiktoken_ext
from tiktoken_ext import openai_public
from colorama import just_fix_windows_console

from model.LLM import LLM
from model.NER import NER
from model.Word import Word
from helper.LogHelper import LogHelper
from helper.TextHelper import TextHelper

# 定义全局对象
# 方便共享全局数据
# 丑陋，但是有效，不服你咬我啊
G = type("GClass", (), {})()

# 原始文本切片阈值
# 似乎切的越细，能找到的词越多，失败的概率也会降低
SPLIT_THRESHOLD = 1 * 1024

# 读取TXT文件并返回
def read_txt_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            lines = file.readlines()
        return lines
    except FileNotFoundError:
        LogHelper.error(f"读取文件 {filename} 时出错 : {str(error)}")

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
        LogHelper.error(f"读取文件 {filename} 时出错 : {str(error)}")
    except json.JSONDecodeError:
        LogHelper.error(f"读取文件 {filename} 时出错 : {str(error)}")

# 遍历目录文件夹，读取所有csv文件并返回
def read_csv_files(directory):
    input_data = []

    try:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".csv"):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                        reader = csv.reader(csvfile)

                        for row in reader:
                            input_data.append(row[0])
                        
    except Exception as error:
        LogHelper.error(f"读取文件夹 {directory} 时出错 : {str(error)}")

    return input_data

# 按阈值分割文本
def split_by_token_threshold(lines, threshold):
    tiktoken_encoding = tiktoken.get_encoding("cl100k_base")

    current_size = 0
    current_segment = []
    lines_split_by_token = []

    for line in lines:
        line_token = len(tiktoken_encoding.encode(line))

        # 如果当前段的大小加上当前行的大小超过阈值，则需要将当前段添加到结果列表中，并重置当前段
        if current_size + line_token > threshold:
            lines_split_by_token.append("".join(current_segment))
            current_segment = []
            current_size = 0

        # 添加当前字符串到当前段
        current_segment.append(line)
        current_size += line_token

    # 添加最后一段
    if current_segment:
        lines_split_by_token.append("".join(current_segment))

    return lines_split_by_token

# 合并具有相同表面形式（surface）的 Word 对象，计数并逆序排序。
def merge_and_count(words):
    surface_to_word = {}

    for word in words:
        if word.surface not in surface_to_word:
            surface_to_word[word.surface] = word
        else:
            # 累积 count
            existing_word = surface_to_word[word.surface]
            existing_word.count += word.count

    # 将字典转换为列表，并按count逆序排序
    sorted_words = sorted(surface_to_word.values(), key=lambda x: x.count, reverse=True)

    return sorted_words

# 将 Word 列表写入文件
def write_words_to_file(words, filename, detail):
    with open(filename, "w", encoding="utf-8") as file:
        if not detail:
            data = {}

            for k, word in enumerate(words):
                data[word.surface] = ""

            file.write(json.dumps(data, indent = 4, ensure_ascii = False))
        else:
            for k, word in enumerate(words):
                file.write(f"词语原文 : {word.surface}\n")
                file.write(f"出现次数 : {word.count}\n")

                if G.config.translate_surface_mode == 1:
                    file.write(f"罗马音 : {word.surface_romaji}\n")
                    file.write(f"词语翻译 : {', '.join(word.surface_translation)}, {word.surface_translation_description}\n")
                
                file.write(f"角色性别 : {word.attribute}\n")
                file.write(f"词义分析 : {word.context_summary.get("summary", "")}\n")

                file.write(f"上下文原文 : ※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※\n")
                file.write(f"{'\n'.join(word.context)}\n")

                if G.config.translate_context_mode == 1:
                    file.write(f"上下文翻译 : ※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※\n")
                    file.write(f"{'\n'.join(word.context_translation)}\n")

                file.write(f"\n")

# 读取数据文件
def read_data_file():
    input_data = []

    if os.path.exists("ManualTransFile.json"):
        user_input = input(f'已找到数据文件 "ManualTransFile.json"，按回车直接使用或输入其他文件的路径：').strip('"')

        if user_input:
            input_file_name = user_input
        else:
            input_file_name = "ManualTransFile.json"
    elif os.path.exists("all.orig.txt"):
        user_input = input(f'已找到数据文件 "all.orig.txt"，按回车直接使用或输入其他文件的路径：').strip('"')

        if user_input:
            input_file_name = user_input
        else:
            input_file_name = "all.orig.txt"
    elif os.path.exists("data"):
        user_input = input(f'已找到数据文件夹 "data"，按回车直接使用或输入其他文件的路径：').strip('"')

        if user_input:
            input_file_name = user_input
        else:
            input_file_name = "data"
    else:
        input_file_name = input('请输入数据文件的路径: ').strip('"')

    if input_file_name.endswith(".txt"):
        input_data = read_txt_file(input_file_name)
    elif input_file_name.endswith(".json"):
        input_data = read_json_file(input_file_name)
    elif os.path.isdir(input_file_name):
        input_data = read_csv_files(input_file_name)
    else:
        LogHelper.warning(f"不支持的文件格式: {input_file_name}")
        os.system("pause")
        exit(1)

    input_data_filtered = []
    for k, line in enumerate(input_data):
        # 【\N[123]】 这种形式是代指角色名字的变量
        # 直接抹掉就没办法判断角色了
        # 先把 \N 部分抹掉，保留 ID 部分
        line = line.strip().replace(r'\\N', '')
        line = re.sub(r'(\\\{)|(\\\})', '', line) # 放大或者缩小字体的代码
        line = re.sub(r'\\[A-Z]{1,3}\[\d+\]', '', line, flags=re.IGNORECASE) # 干掉其他乱七八糟的部分代码
        line = line.strip().replace("【】", "") # 由于上面的代码移除，可能会产生空人名框的情况，干掉
        line = line.strip().replace('\n', '') # 干掉行内换行

        if len(line) == 0:
            continue

        if not TextHelper.contains_any_japanese(line):
            continue

        input_data_filtered.append(line.strip())

    return input_data_filtered

# 处理第一类（汉字）词语
async def process_first_class_words(llm, ner, input_data_splited, fulltext):
    LogHelper.info("即将开始执行 [查找第一类词语] ...")
    words = ner.search_for_first_class_words(input_data_splited, fulltext)
    words = merge_and_count(words)

    # 按阈值筛选，但是保证至少有20个条目
    words_with_threshold = [word for word in words if word.count >= G.count_threshold]
    words_all_filtered = [word for word in words if word not in words_with_threshold]
    words_with_threshold.extend(words_all_filtered[:max(0, 20 - len(words_with_threshold))])
    words = words_with_threshold

    # 等待词性判断任务结果
    LogHelper.info("即将开始执行 [第一类词语词性判断] ...")
    words = await llm.analyze_attribute_batch(words, llm.TASK_TYPE_FIRST_CLASS_ATTRIBUTE)
    words = merge_and_count(words)

    # 筛选出类型为名词的词语
    words = [word for word in words if word.type == Word.TYPE_NOUN]

    return words

# 处理第二类（片假名）词语
async def process_second_class_words(llm, ner, input_data_splited, fulltext):
    LogHelper.info("即将开始执行 [查找第二类词语] ...")
    words = ner.search_for_second_class_words(input_data_splited, fulltext)
    words = merge_and_count(words)

    # 按阈值筛选，但是保证至少有20个条目
    words_with_threshold = [word for word in words if word.count >= G.count_threshold]
    words_all_filtered = [word for word in words if word not in words_with_threshold]
    words_with_threshold.extend(words_all_filtered[:max(0, 20 - len(words_with_threshold))])
    words = words_with_threshold

    # 等待词性判断任务结果
    LogHelper.info("即将开始执行 [第二类词语词性判断] ...")
    words = await llm.analyze_attribute_batch(words, llm.TASK_TYPE_SECOND_CLASS_ATTRIBUTE)
    words = merge_and_count(words)

    # 筛选出类型为名词的词语
    words = [word for word in words if word.type == Word.TYPE_NOUN]

    return words

# 主函数
async def main():
    # 初始化 LLM 对象
    llm = LLM(G.config)
    llm.load_blacklist("blacklist.txt")
    llm.load_prompt_first_class_attribute("prompt\\prompt_first_class_attribute.txt")
    llm.load_prompt_second_class_attribute("prompt\\prompt_second_class_attribute.txt")
    llm.load_prompt_summarize_context("prompt\\prompt_summarize_context.txt")
    llm.load_prompt_translate_surface("prompt\\prompt_translate_surface.txt")
    llm.load_prompt_translate_context("prompt\\prompt_translate_context.txt")

    # 初始化 NER 对象
    ner = NER()
    ner.load_blacklist("blacklist.txt")

    # 切分文本
    fulltext = read_data_file()
    LogHelper.info("正在对文件中的文本进行预处理 ...")
    input_data_splited = split_by_token_threshold(fulltext, SPLIT_THRESHOLD)

    # 设置阈值
    G.count_threshold = 1

    # 获取第一类词语
    first_class_words = []
    if G.work_mode == 2:
        first_class_words = await process_first_class_words(llm, ner, input_data_splited, fulltext)

    # 获取第二类词语
    second_class_words = []
    second_class_words = await process_second_class_words(llm, ner, input_data_splited, fulltext)

    # 合并各类词语表
    words = merge_and_count(first_class_words + second_class_words)

    # 查找上下文
    LogHelper.info("即将开始执行 [查找上下文]")
    for k, word in enumerate(words):
        word.set_context(word.surface, fulltext)
        LogHelper.info(f"[查找上下文] 已完成 {k + 1} / {len(words)}")

    # 等待词义分析任务结果
    LogHelper.info("即将开始执行 [词义分析] ...")
    words = await llm.summarize_context_batch(words)

    # 筛选出类型为人名的词语
    words = [word for word in words if word.type == Word.TYPE_PERSON]

    # 等待翻译词汇任务结果
    if G.config.translate_surface_mode == 1:
        LogHelper.info("即将开始执行 [词汇翻译] ...")
        words = await llm.translate_surface_batch(words)

    # 等待上下文词表任务结果
    if G.config.translate_context_mode == 1:
        LogHelper.info("即将开始执行 [上下文翻译] ...")
        words = await llm.translate_context_batch(words)

    # 定义输出文件名
    names_true_output_file = "角色姓名_日志.txt"
    dictionary_names_true_file = "角色姓名_列表.json"

    # 写入文件
    write_words_to_file(words, names_true_output_file, True)
    write_words_to_file(words, dictionary_names_true_file, False)

    # 输出日志
    LogHelper.info("")
    LogHelper.info(f"结果已写入到:")
    LogHelper.info(f"　　{names_true_output_file}")
    LogHelper.info(f"　　{dictionary_names_true_file}")
    LogHelper.info("\n\n")

    # 等待用户推出
    os.system("pause")

# 确保程序出错时可以捕捉到错误日志
async def run_main():
    try:
        await main()
    except Exception as error:
        LogHelper.error(traceback.format_exc())
        print()
        print()
        print(f"※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※")
        print(f"※※※※")
        print(f"※※※※  ※※  \033[91m出现严重错误，程序即将退出，错误信息已保存至日志文件 KeywordGacha.log ...\033[0m")
        print(f"※※※※")
        print(f"※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※")
        print()
        print()
        os.system("pause")

# 开始运行程序
if __name__ == "__main__":
    # 通过 Colorama 实现在较旧的 Windows 控制台下输出彩色字符
    just_fix_windows_console()

    print()
    print()
    print(f"※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※")
    print(f"※※※※")
    print(f"※※※※  ※※  \033[92mKeywordGacha\033[0m")
    print(f"※※※※  ※※  \033[92mhttps://github.com/neavo/KeywordGacha\033[0m")
    print(f"※※※※")
    print(f"※※※※")
    print(f"※※※※  ※※  \033[92m支持 CSV、JSON、纯文本 三种输入格式\033[0m")
    print(f"※※※※  ※※  \033[92m处理 JSON、纯文本文件时，请输入目标文件的路径\033[0m")
    print(f"※※※※  ※※  \033[92m处理 CSV 文件时，请输入目标文件夹的路径，会读取其中所有的 CSV 文件\033[0m")
    print(f"※※※※  ※※  \033[92m目录下如有 data 文件夹、all.orig.txt 文件 或者 ManualTransFile.json 文件，会自动选择\033[0m")
    print(f"※※※※")
    print(f"※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※")
    print()
    print()


    print(f"选择工作模式：")
    print(f"　　--> 1.快速模式 - 只识别假名词语（\033[92m默认\033[0m）")
    print(f"　　--> 2.全面模式 - 同时识别假名和汉字词语（速度较慢，汉字词语目前本地模型的过滤能力较差，杂质词条较多）")
    print(f"")
    work_mode = input(f"请输入选项前的数字序号选择运行模式：")

    try:
        work_mode = int(work_mode)
    except ValueError:
        print()
        LogHelper.error(f"输入数字无效, 将使用默认模式运行 ... ")
        work_mode = 1

    if work_mode == 1:
        print()
        LogHelper.info(f"以 \033[92m快速模式\033[0m 运行 ...")
        print()
    elif work_mode == 2:
        print()
        LogHelper.info(f"以 全面模式 运行 ...")
        print()

    G.work_mode = work_mode

    # 加载配置文件
    try:
        config_file = "config.json"

        with open(config_file, "r", encoding="utf-8") as file:
            config = json.load(file)
            G.config = type("GClass", (), {})()

            for key in config:
                setattr(G.config, key, config[key])
    except FileNotFoundError:
        LogHelper.error(f"文件 {config_file} 未找到.")
    except json.JSONDecodeError:
        LogHelper.error(f"文件 {config_file} 不是有效的JSON格式.")

    # 检查 DEBUG 模式
    if os.path.exists("debug.txt"):
        LogHelper.setLevel(logging.DEBUG)

    # 开始业务逻辑
    asyncio.run(run_main())