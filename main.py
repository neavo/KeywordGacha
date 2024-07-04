import os
import re
import csv
import json
import asyncio
import traceback
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
        file.write("{") if not detailmode else None
        for k, word in enumerate(words):
            if detailmode:
                file.write(f"词语原文 : {word.surface}\n")
                file.write(f"词语翻译 : {word.surface_translation}\n")
                file.write(f"出现次数 : {word.count}\n")
                file.write(f"上下文原文 : ※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※\n")
                file.write(f"{'    \n'.join(word.context)}\n")
                file.write(f"上下文翻译 : ※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※\n")
                file.write(f"{'    \n'.join(word.context_translation)}\n")
                file.write("\n")
            elif k == 0:
                file.write("\n")
                file.write(f'    "{word.surface}" : "",\n')
            elif k != len(words) - 1:
                file.write(f'    "{word.surface}" : "",\n')
            else:
                file.write(f'    "{word.surface}" : ""\n')
        file.write("}") if not detailmode else None

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
        print(f"不支持的文件格式: {input_file_name}")

    input_data_filtered = []
    for k, line in enumerate(input_data):
        # 【\N[123]】 这种形式是代指角色名字的变量
        # 直接抹掉就没办法判断角色了
        # 先把 \N 部分抹掉，保留 ID 部分
        line = line.strip().replace(r'\\N', '') 
        line = re.sub(r'(\\\{)|(\\\})', '', line) # 放大或者缩小字体的代码
        line = re.sub(r'\\[A-Z]{1,3}\[\d+\]', '', line, flags=re.IGNORECASE) # 干掉其他乱七八糟的部分代码
        line = line.strip().replace('\n', '') # 干掉行内换行

        if len(line) == 0:
            continue

        if not TextHelper.contains_any_japanese(line):
            continue

        input_data_filtered.append(line.strip())

    return input_data_filtered

# 主函数
async def main():
    fulltext = read_data_file()
    LogHelper.info("正在对文件中的文本进行预处理 ...")
    input_data_splited = split_by_byte_threshold(fulltext, SPLIT_THRESHOLD)

    llm = LLM(G.config)
    llm.load_black_list("blacklist.txt")
    llm.load_prompt_extract_words("prompt\\prompt_extract_words.txt")
    llm.load_prompt_translate_surface("prompt\\prompt_translate_surface.txt")
    llm.load_prompt_translate_context("prompt\\prompt_translate_context.txt")
    
    # 等待分词任务结果
    LogHelper.info("即将开始执行 [LLM 分词] ...")
    words = await llm.extract_words_batch(input_data_splited, fulltext)

    # 合并与排序
    words_all = merge_and_count(words)

    # 按阈值筛选，但是保证至少10个
    words_with_threshold = [word for word in words_all if word.count >= COUNT_THRESHOLD]
    words_all_filtered = [word for word in words_all if word not in words_with_threshold]
    words_with_threshold.extend(words_all_filtered[:max(0, 10 - len(words_with_threshold))])

    # 等待翻译词表任务结果
    if G.config.translate_surface_mode == 1:
        LogHelper.info("即将开始执行 [后处理 - 词表翻译] ...")
        words_with_threshold = await llm.translate_surface_batch(words_with_threshold)

    # 等待上下文词表任务结果
    if G.config.translate_context_mode == 1:
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

    # 等待用户推出
    os.system("pause")

# 确保程序出错时可以捕捉到错误日志
async def run_main():
    try:
        await main()
    except Exception as error:
        LogHelper.error(traceback.format_exc())
        print(f"※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※")
        print(f"※※※※")
        print(f"※※※※  ※※  \033[38;5;214m出现严重错误，程序即将退出，错误信息已保存至日志文件 KeywordGacha.log ...\033[0m")
        print(f"※※※※")
        print(f"※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※")
        os.system("pause")

# 开始运行程序
if __name__ == "__main__":
    print()
    print()
    print(f"※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※")
    print(f"※※※※")
    print(f"※※※※  ※※  \033[38;5;214mKeywordGacha\033[0m")
    print(f"※※※※  ※※  \033[38;5;214mhttps://github.com/neavo/KeywordGacha\033[0m")
    print(f"※※※※")
    print(f"※※※※")
    print(f"※※※※  ※※  \033[38;5;214m!!! 注意 !!!\033[0m")
    print(f"※※※※  ※※  \033[38;5;214m处理流程将消耗巨量 Token\033[0m")
    print(f"※※※※  ※※  \033[38;5;214m使用在线接口的同学请关注自己的账单\033[0m")
    print(f"※※※※")
    print(f"※※※※")
    print(f"※※※※  ※※  \033[38;5;214m支持 CSV、JSON、纯文本 三种输入格式\033[0m")
    print(f"※※※※  ※※  \033[38;5;214m处理 JSON、纯文本文件时，请输入目标文件的路径\033[0m")
    print(f"※※※※  ※※  \033[38;5;214m处理 CSV 文件时，请输入目标文件夹的路径，会读取其中所有的 CSV 文件\033[0m")
    print(f"※※※※  ※※  \033[38;5;214m目录下如有 data 文件夹、all.orig.txt 文件 或者 ManualTransFile.json 文件，会自动选择\033[0m")
    print(f"※※※※")
    print(f"※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※")
    print()
    print()

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

    # 开始业务逻辑
    asyncio.run(run_main())