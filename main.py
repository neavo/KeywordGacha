import os
import re
import csv
import copy
import json
import asyncio

import rich
from rich import box
from rich.table import Table
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

# 合并与计数
def merge_and_count(words, full_text_string):
    words_categorized = {}
    for v in words:
        if v.surface not in words_categorized:
            words_categorized[(v.surface, v.ner_type)] = [] # 只有文字和类型都一样才视为相同条目，避免跨类词条目合并
        words_categorized[(v.surface, v.ner_type)].append(v)

    words_merged = []
    for k, v in words_categorized.items():
        score = 0
        for w in v:
            score = score + w.score
    
        word = v[0]
        word.score = score / len(v)

        if word.score > 0.90:
            words_merged.append(word)

    for word in words_merged:
        word.count = full_text_string.count(word.surface)

    return sorted(words_merged, key=lambda x: x.count, reverse=True)

# 将 Word 列表写入文件
def write_words_to_file(words, filename, detail):
    with open(filename, "w", encoding = "utf-8") as file:
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
                
                if word.ner_type == NER.NER_TYPES.get("PERSON"):
                    file.write(f"角色性别 : {word.attribute}\n")

                file.write(f"词义分析 : {word.context_summary.get("summary", "")}\n")
                file.write(f"上下文原文 : ※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※\n")
                file.write(f"{'\n'.join(word.context)}\n")

                if G.config.translate_context_mode == 1 and len(word.context_translation) > 0:
                    file.write(f"上下文翻译 : ※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※\n")
                    file.write(f"{'\n'.join(word.context_translation)}\n")

                if LogHelper.is_debug():
                    file.write(f"置信度 : {word.score}\n")
                    file.write(f"{word.llmresponse_analyze_attribute}\n")
                    file.write(f"{word.llmresponse_summarize_context}\n")
                    file.write(f"{word.llmresponse_translate_context}\n")
                    file.write(f"{word.llmresponse_translate_surface}\n")
                    
                file.write("\n")

    LogHelper.info(f"结果已写入 - [green]{filename}[/]")

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

        if not TextHelper.has_any_japanese(line):
            continue

        input_data_filtered.append(line.strip())

    return input_data_filtered

# 获取指定类型的词
def get_words_by_ner_type(words, ner_type):
    # 显式的复制对象，避免后续修改对原始列表的影响，浅拷贝不复制可变对象（列表、字典、自定义对象等），慎重修改它们
    return [copy.copy(word) for word in words if word.ner_type == ner_type]

# 移除指定类型的词
def remove_words_by_ner_type(words, ner_type):
    return [word for word in words if word.ner_type != ner_type]

# 指定类型的词
def replace_words_by_ner_type(words, in_words, ner_type):
    words = remove_words_by_ner_type(words, ner_type)
    words.extend(in_words)
    return words

# 查找 NER 实体
def search_for_entity(ner, full_text_lines, task_mode):
    LogHelper.info("即将开始执行 [查找 NER 实体] ...")

    if task_mode == NER.TASK_MODES.QUICK:
        words = ner.search_for_entity_qucik(full_text_lines)
    elif task_mode == NER.TASK_MODES.ACCURACY:
        words = ner.search_for_entity_accuracy(full_text_lines)
    words = merge_and_count(words, "\n".join(full_text_lines))

    if os.path.exists("debug.txt"):
        words_dict = {}
        for k, word in enumerate(words):
            if word.ner_type not in words_dict:
                words_dict[word.ner_type] = []

            t = {}
            t["score"] = float(word.score)
            t["count"] = word.count
            t["surface"] = word.surface
            t["ner_type"] = word.ner_type
            words_dict[word.ner_type].append(t)

        with open("words_dict.json", "w", encoding="utf-8") as file:
            file.write(json.dumps(words_dict, indent = 4, ensure_ascii = False))

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

    # 有了上下文译后才能执行后续的处理
    # 执行还原词根
    LogHelper.info("即将开始执行 [词根还原] ...")
    words_person = get_words_by_ner_type(words, NER.NER_TYPES.get("PERSON"))
    words_person = ner.lemmatize_words_by_rule(words_person)
    words_person = merge_and_count(words_person, "\n".join(full_text_lines))
    words_person = ner.lemmatize_words_by_count(words_person)
    words_person = merge_and_count(words_person, "\n".join(full_text_lines))
    words = replace_words_by_ner_type(words, words_person, NER.NER_TYPES.get("PERSON"))
    LogHelper.info(f"[词根还原] 已完成 ...")

    # 执行语法校验
    LogHelper.info("即将开始执行 [语法校验] ...")
    words = ner.validate_words_by_morphology(words)
    words = remove_words_by_ner_type(words, "")
    LogHelper.info(f"[语法校验] 已完成 ...")

    # 按阈值筛选角色实体，但是保证至少有20个条目
    LogHelper.info(f"即将开始执行 [阈值筛选] ... 当前出现次数的筛选阈值设置为 {G.config.count_threshold} ...")
    words_person = get_words_by_ner_type(words, NER.NER_TYPES.get("PERSON"))
    words_with_threshold = [word for word in words_person if word.count >= G.config.count_threshold]
    words_all_filtered = [word for word in words_person if word not in words_with_threshold]
    words_with_threshold.extend(words_all_filtered[:max(0, 20 - len(words_with_threshold))])
    words = replace_words_by_ner_type(words, words_with_threshold, NER.NER_TYPES.get("PERSON"))
    LogHelper.info(f"[阈值筛选] 已完成 ... 出现次数 <= {G.config.count_threshold} 的条目已剔除 ...")

    return words

# 打印应用信息
def print_app_info():
    LogHelper.print()
    LogHelper.print()
    LogHelper.rule(f"KeywordGacha", style = "light_goldenrod2")
    LogHelper.rule(f"[blue]https://github.com/neavo/KeywordGacha", style = "light_goldenrod2")
    LogHelper.rule(f"使用 OpenAI 兼容接口自动生成小说、漫画、字幕、游戏脚本等任意文本中的词汇表的翻译辅助工具", style = "light_goldenrod2")
    LogHelper.print()

    table = Table(box = box.ASCII2, expand = True, highlight = True, show_lines = True, border_style = "light_goldenrod2")
    table.add_column("设置", justify = "left", style = "white", width = 24,overflow = "fold")
    table.add_column("当前值", justify = "left", style = "white", width = 24, overflow = "fold")
    table.add_column("说明信息 - 修改设置请打开 [blue]Config.json[/] 文件", justify = "left", style = "white", overflow = "fold")

    table.add_row("api_key", str(G.config.api_key), "授权密钥，从接口平台方获取，使用在线接口时一定要设置正确")
    table.add_row("base_url", str(G.config.base_url), "请求地址，从接口平台方获取，使用在线接口时一定要设置正确")
    table.add_row("model_name", str(G.config.model_name), "模型名称，从接口平台方获取，使用在线接口时一定要设置正确")
    table.add_row("count_threshold", str(G.config.count_threshold), "出现次数低于此值的词语会被过滤掉，调低它可以抓取更多低频词语")
    table.add_row("translate_surface_mode", str(G.config.translate_surface_mode), "是否启用词语翻译功能，0 - 禁用，1 - 启用")
    table.add_row("translate_context_mode", str(G.config.translate_context_mode), "是否启用上下文翻译功能，只对角色实体生效，0 - 禁用，1 - 启用")
    table.add_row("request_timeout", str(G.config.request_timeout), "网络请求超时时间（秒）如果频繁出现网络错误，可以调大这个值")
    table.add_row("request_frequency_threshold", str(G.config.request_frequency_threshold), "网络请求频率阈值（次/秒，可以小于 1）\n如果频繁出现网络错误，特别是使用中转平台时，可以调小这个值")

    LogHelper.print(table)
    LogHelper.print()

# 主函数
async def begin():
    # 打印应用信息
    print_app_info()

    LogHelper.print(f"选择工作模式：")
    LogHelper.print(f"　　--> 1. 快速模式 - 速度快，只能识别角色，无法识别其他类型的实体")
    LogHelper.print(f"　　--> 2. 增强模式 - [green]默认模式[/]，速度较慢，识别能力强，可以识别角色、组织、道具等各种类型的实体")
    LogHelper.print(f"")
    G.work_mode = int(Prompt.ask("请输入选项前的 [green]数字序号[/] 选择运行模式，默认为 [green]增强模式[/]", 
        choices = ["1", "2"],
        default = "2",
        show_choices = False,
        show_default = False
    ))
    
    if G.work_mode == 1:
        LogHelper.info(f"您选择了 [green]快速模式[/] ...")
        LogHelper.print()
    elif G.work_mode == 2:
        LogHelper.info(f"您选择了 [green]增强模式[/] ...")
        LogHelper.print()

    # 初始化 LLM 对象
    llm = LLM(G.config)
    llm.load_blacklist("blacklist.txt")
    llm.load_prompt_analyze_attribute("prompt\\prompt_analyze_attribute.txt")
    llm.load_prompt_summarize_context("prompt\\prompt_summarize_context.txt")
    llm.load_prompt_translate_context("prompt\\prompt_translate_context.txt")
    llm.load_prompt_translate_surface_common("prompt\\prompt_translate_surface_common.txt")
    llm.load_prompt_translate_surface_person("prompt\\prompt_translate_surface_person.txt")

    # 初始化 NER 对象
    with LogHelper.status(f"正在初始化 NER 引擎 ..."):
        ner = NER()
        ner.load_blacklist("blacklist.txt")

    # 读取数据文件
    full_text_lines = read_data_file()

    # 查找 NER 实体
    words = []
    words = search_for_entity(ner, full_text_lines, G.work_mode * 10)

    # 等待词性判断任务结果
    LogHelper.info("即将开始执行 [词性判断] ...")
    words_person = get_words_by_ner_type(words, NER.NER_TYPES.get("PERSON"))
    words_person = await llm.analyze_attribute_batch(words_person)
    words_person = remove_words_by_ner_type(words_person, "")
    words = replace_words_by_ner_type(words, words_person, NER.NER_TYPES.get("PERSON"))

    # 等待词义分析任务结果
    LogHelper.info("即将开始执行 [词义分析] ...")
    words_person = get_words_by_ner_type(words, NER.NER_TYPES.get("PERSON"))
    words_person = await llm.summarize_context_batch(words_person)
    words_person = remove_words_by_ner_type(words_person, "")
    words = replace_words_by_ner_type(words, words_person, NER.NER_TYPES.get("PERSON"))

    # 此时对角色实体的校验已全部完成，将其他类型实体中与角色名重复的剔除
    LogHelper.info("即将开始执行 [重复性检验] ...")
    words = ner.validate_words_by_duplication(words)
    words = remove_words_by_ner_type(words, "")
    LogHelper.info("[重复性检验] 已完成 ...")

    # 等待翻译词语任务结果
    if G.config.translate_surface_mode == 1:
        LogHelper.info("即将开始执行 [词语翻译] ...")
        words = await llm.translate_surface_batch(words)

    # 等待上下文词表任务结果
    if G.config.translate_context_mode == 1:
        LogHelper.info("即将开始执行 [上下文翻译] ...")
        words_person = get_words_by_ner_type(words, NER.NER_TYPES.get("PERSON"))
        words_person = await llm.translate_context_batch(words_person)
        words = replace_words_by_ner_type(words, words_person, NER.NER_TYPES.get("PERSON"))

    ner_type = [
        ("PERSON", "角色实体"),
        ("ORG", "组织实体"),
        ("LOC", "地点实体"),
        ("INS", "设施实体"),
        ("PRODUCT", "物品实体"),
        ("EVENT", "事件实体"),
    ]

    LogHelper.info("")
    for v in ner_type:
        words_ner_type = get_words_by_ner_type(words, NER.NER_TYPES.get(v[0]))
        if len(words_ner_type) > 0:
            write_words_to_file(words_ner_type, f"{v[1]}_日志.txt", True)
            write_words_to_file(words_ner_type, f"{v[1]}_列表.json", False)
        else:
            os.remove(f"{v[1]}_日志.txt") if os.path.isfile(f"{v[1]}_日志.txt") else None
            os.remove(f"{v[1]}_列表.json") if os.path.isfile(f"{v[1]}_列表.json") else None

    # 等待用户退出
    LogHelper.info("")
    LogHelper.info(f"工作流程已结束 ... 请检查生成的数据文件 ...")
    LogHelper.info("")
    LogHelper.info("")
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
        config_file = "config_dev.json" if LogHelper.is_debug else "config.json"

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