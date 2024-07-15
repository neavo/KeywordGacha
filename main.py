import os
import re
import csv
import json
import asyncio

import rich
from rich.prompt import Prompt

from model.LLM import LLM
from model.NER import NER
from model.Word import Word
from helper.LogHelper import LogHelper
from helper.TestHelper import TestHelper
from helper.TextHelper import TextHelper
from helper.ProgressHelper import ProgressHelper

# 定义全局对象
# 方便共享全局数据
# 丑陋，但是有效，不服你咬我啊
G = type("GClass", (), {})()

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

# 合并重复项并计数
def merge_and_count(words, full_text_string):
    # 去除重复项
    words_merged = []
    words_merged_set = set()
    for word in words:
        if word.surface not in words_merged_set:
            words_merged.append(word)
            words_merged_set.add(word.surface)

    # 在原文中查找出现次数
    for word in words_merged:
        word.count = len(re.findall(re.escape(word.surface), full_text_string))

    # 将字典转换为列表，并按count逆序排序
    words_sorted = sorted(words_merged, key=lambda x: x.count, reverse=True)

    return words_sorted

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

# 查找 NER 实体
async def search_for_entity(ner, full_text_lines, task_mode):
    LogHelper.info("即将开始执行 [查找 NER 实体] ...")
    words = ner.search_for_entity(full_text_lines, task_mode)
    words = merge_and_count(words, "\n".join(full_text_lines))

    if os.path.exists("debug.txt"):
        words_dict = {}
        for k, word in enumerate(words):
            if word.ner_type not in words_dict:
                words_dict[word.ner_type] = []

            t = {}
            t["count"] = word.count
            t["surface"] = word.surface
            t["ner_type"] = word.ner_type
            words_dict[word.ner_type].append(t)

        with open("words_dict.json", "w", encoding="utf-8") as file:
            file.write(json.dumps(words_dict, indent = 4, ensure_ascii = False))

    # 按阈值筛选，但是保证至少有20个条目
    words_with_threshold = [word for word in words if word.count >= G.config.count_threshold]
    words_all_filtered = [word for word in words if word not in words_with_threshold]
    words_with_threshold.extend(words_all_filtered[:max(0, 20 - len(words_with_threshold))])
    words = words_with_threshold

    # 查找上下文
    LogHelper.info("即将开始执行 [查找上下文] ...")
    LogHelper.print()

    with ProgressHelper.get_progress() as progress:
        pid = progress.add_task("查找上下文", total = None)
        for k, word in enumerate(words):
            word.set_context(word.surface, full_text_lines)
            progress.update(pid, advance = 1, total = len(words))

    LogHelper.print()
    LogHelper.info("[查找上下文] 已完成 ...")

    return words

# 主函数
async def begin():
    # 工作模式选择
    LogHelper.print()
    LogHelper.print()
    LogHelper.print(f"※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※")
    LogHelper.print(f"※※※※")
    LogHelper.print(f"※※※※  ※※  [green]KeywordGacha[/]")
    LogHelper.print(f"※※※※  ※※  [green]https://github.com/neavo/KeywordGacha[/]")
    LogHelper.print(f"※※※※")
    LogHelper.print(f"※※※※")
    LogHelper.print(f"※※※※  ※※  [green]支持 CSV、JSON、纯文本 三种输入格式[/]")
    LogHelper.print(f"※※※※  ※※  [green]处理 JSON、纯文本文件时，请输入目标文件的路径[/]")
    LogHelper.print(f"※※※※  ※※  [green]处理 CSV 文件时，请输入目标文件夹的路径，会读取其中所有的 CSV 文件[/]")
    LogHelper.print(f"※※※※  ※※  [green]目录下如有 [white]data[/] 文件夹、[white]all.orig.txt[/] 文件 或者 [white]ManualTransFile.json[/] 文件，会自动选择[/]")
    LogHelper.print(f"※※※※")
    LogHelper.print(f"※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※")
    LogHelper.print()
    LogHelper.print()

    LogHelper.print(f"选择工作模式：")
    LogHelper.print(f"　　--> 1. 快速模式 - [green]默认[/]")
    LogHelper.print(f"　　--> 2. 全面模式 - 速度较慢，但是可以更加全面的识别目标词语（同时杂质也较多）")
    LogHelper.print(f"")
    G.work_mode = int(Prompt.ask(
        "请输入选项前的 [green]数字序号[/] 选择运行模式", 
        choices = ["1", "2"],
        default = "1",
        show_choices = False,
        show_default = False
    ))
    
    if G.work_mode == 1:
        LogHelper.info(f"您选择了 1. 快速模式 ...")
        LogHelper.print()
    elif G.work_mode == 2:
        LogHelper.info(f"您选择了 2. 全面模式 ...")
        LogHelper.print()

    # 初始化 LLM 对象
    llm = LLM(G.config)
    llm.load_blacklist("blacklist.txt")
    llm.load_prompt_analyze_attribute("prompt\\prompt_analyze_attribute.txt")
    llm.load_prompt_summarize_context("prompt\\prompt_summarize_context.txt")
    llm.load_prompt_translate_surface("prompt\\prompt_translate_surface.txt")
    llm.load_prompt_translate_context("prompt\\prompt_translate_context.txt")

    # 初始化 NER 对象
    ner = NER()
    ner.load_blacklist("blacklist.txt")

    # 读取数据文件
    full_text_lines = read_data_file()

    # 查找 NER 实体
    words = []
    words = await search_for_entity(ner, full_text_lines, G.work_mode * 10)

    # 等待词性判断任务结果
    LogHelper.info("即将开始执行 [词性判断] ...")
    words = await llm.analyze_attribute_batch(words)

    # 筛选出类型为人名的词语
    words = [word for word in words if word.type == Word.TYPE_PERSON]

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

# 一些初始化步骤
def init():
   # 测试
    if LogHelper.is_debug():
        TestHelper.check_duplicates()

    # 注册全局异常追踪器
    rich.traceback.install()

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

# 确保程序出错时可以捕捉到错误日志
async def main():
    try:
        init()
        await begin()
    except EOFError:
        LogHelper.error(f"EOFError - 程序即将退出 ...")
    except KeyboardInterrupt:
        LogHelper.error(f"KeyboardInterrupt - 程序即将退出 ...")
    except Exception as e:
        LogHelper.error(f"{LogHelper.get_trackback(e)}")
        LogHelper.print()
        LogHelper.print()
        LogHelper.error(f"出现严重错误，程序即将退出，错误信息已保存至日志文件 [green]KeywordGacha.log[/] ...")
        LogHelper.print()
        LogHelper.print()
        os.system("pause")

if __name__ == "__main__":
    asyncio.run(main())