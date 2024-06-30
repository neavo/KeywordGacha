import os
import re
import json
import asyncio
import concurrent.futures
from collections import Counter
from concurrent.futures import as_completed

from openai import OpenAI
from openai import AsyncOpenAI

from model.LLM import LLM
from model.Word import Word
from helper.TextHelper import TextHelper
from helper.LogHelper import LogHelper

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

# 使用 LLM 翻译词语
def translate_surface_by_llm(orignal, max_retry):
    translation = ""

    for i in range(max_retry):
        try:
            completion = G.openai_handler.chat.completions.create(
                model=G.model_name,
                temperature=0.1,
                top_p=0.3,
                max_tokens=512,
                frequency_penalty=0.2,
                messages=[
                    {"role": "system", "content": G.prompt_translate_surface},
                    {"role": "user", "content": f"{orignal}"},
                ],
            )

            break
        except Exception as error:
            if i + 1 >= max_retry:
                print(
                    f"[错误] 执行 [后处理任务 - 翻译词语] 任务时 : 重试次数耗尽，放弃该请求."
                )
            else:
                print(
                    f"[错误] 执行 [后处理任务 - 翻译词语] 任务时 : 请求失败，原因：{error}, 正在进行第 {i + 1} / {max_retry} 次重试 ..."
                )

    usage = completion.usage
    translation = completion.choices[0].message.content.strip().replace("\n", "  ")

    # 幻觉，直接抛掉
    if usage.completion_tokens >= 512:
        return ""

    return translation

# 使用 LLM 翻译上下文
def translate_context_by_llm(orignal, max_retry):
    content = []

    for i in range(max_retry):
        try:
            completion = G.openai_handler.chat.completions.create(
                model=G.model_name,
                temperature=0.1,
                top_p=0.3,
                max_tokens=G.max_tokens_context_translation,
                frequency_penalty=0,
                messages=[
                    {
                        "role": "system",
                        "content": G.prompt_translate_context,
                    },
                    {"role": "user", "content": f"{'\n'.join(orignal)}"},
                ],
            )

            break
        except Exception as error:
            if i + 1 >= max_retry:
                print(
                    f"[错误] 执行 [后处理任务 - 翻译上下文] 任务时 : 重试次数耗尽，放弃该请求."
                )
            else:
                print(
                    f"[错误] 执行 [后处理任务 - 翻译上下文] 任务时 : 请求失败，原因：{error}, 正在进行第 {i + 1} / {max_retry} 次重试 ..."
                )

    usage = completion.usage
    content = completion.choices[0].message.content.strip()

    # 幻觉，直接抛掉
    if usage.completion_tokens >= G.max_tokens_context_translation:
        return ""

    # 空字符串，直接抛掉
    if len(content) == 0:
        return ""

    return content.split("\n")

# 词表后处理
def words_post_process(words):
    with concurrent.futures.ThreadPoolExecutor(max_workers=G.max_workers) as executor:
        mapping = {}
        futures = []
        finished_task = 0

        for k, word in enumerate(words):
            future = executor.submit(translate_surface_by_llm, word.surface, 3)
            mapping[future] = word
            futures.append(future)

        for future in as_completed(futures):
            try:
                result = future.result()

                mapping_word = mapping[future]
                mapping_word.surface_translation = result

                finished_task = finished_task + 1
                print(
                    f"已完成 [后处理任务 - 翻译词语] {finished_task} / {len(futures)} ..."
                )
            except Exception as error:
                print(f"[错误] 执行 [后处理任务 - 翻译词语] 任务时 : {error}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=G.max_workers) as executor:
        mapping = {}
        futures = []
        finished_task = 0

        for k, word in enumerate(words):
            future = executor.submit(translate_context_by_llm, word.context, 3)
            mapping[future] = word
            futures.append(future)

        for future in as_completed(futures):
            try:
                result = future.result()

                mapping_word = mapping[future]
                mapping_word.context_translation = result

                finished_task = finished_task + 1
                print(
                    f"已完成 [后处理任务 - 翻译上下文] {finished_task} / {len(futures)} ..."
                )
            except Exception as error:
                print(f"[错误] 执行 [后处理任务 - 翻译上下文] 任务时 : {error}")

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
                file.write(
                    f"上下文原文 : -----------------------------------------------------\n"
                )
                file.write(f"{'    \n'.join(word.context)}\n")
                file.write(
                    f"上下文翻译 : -----------------------------------------------------\n"
                )
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
    input_data_splited = split_by_byte_threshold(fulltext, G.split_threshold)

    LogHelper.info("即将开始执行 [LLM 分词] ...")
    llm = LLM(G.api_key, G.base_url, G.model_name)
    llm.load_black_list("blacklist.txt")
    llm.load_prompt_extract_words("prompt\\prompt_extract_words.txt")
    llm.load_prompt_translate_surface("prompt\\prompt_translate_surface.txt")
    llm.load_prompt_translate_context("prompt\\prompt_translate_context.txt")
    
    words = await llm.extract_words_batch(input_data_splited, fulltext)

    # 合并所有数组
    words_all = merge_and_count(words)

    # 按阈值筛选
    words_with_threshold = [word for word in words_all if word.count >= G.count_threshold]

    # 对筛选出的词表进行后处理
    words_post_process(words_with_threshold)

    # 定义输出文件名
    names_true_output_file = "角色姓名_日志.txt"
    dictionary_names_true_file = "角色姓名_列表.json"

    # 写入文件
    write_words_to_file(words_with_threshold, names_true_output_file, True)
    write_words_to_file(words_with_threshold, dictionary_names_true_file, False)

    # 输出日志
    print()
    print(f"结果已写入到:")
    print(f"　　{names_true_output_file}")
    print(f"　　{dictionary_names_true_file}")

# 开始运行程序
if __name__ == "__main__":
    print()
    print()
    print(f"※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※")
    print(f"※※※※")
    print(f"※※※※  ※※※※                  注意              ")
    print(f"※※※※  ※※※※        处理流程将消耗巨量 Token     ")
    print(f"※※※※  ※※※※    使用在线接口的同学请关注自己的账单 ")
    print(f"※※※※")
    print(f"※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※※")
    print()
    print()

    # 每次返回的最大Token阈值 - 翻译上下文时
    G.max_tokens_context_translation = 1024

    # 原始文本切片阈值大小
    G.split_threshold = 4 * 1024

    # 出现次数过滤阈值大小
    G.count_threshold = 3

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

        with open("prompt\\prompt_translate_surface.txt", "r", encoding="utf-8") as file:
            G.prompt_translate_surface = file.read()

        with open("prompt\\prompt_translate_context.txt", "r", encoding="utf-8") as file:
            G.prompt_translate_context = file.read()

    except FileNotFoundError:
        print(f"文件 {config_file} 未找到.")
    except json.JSONDecodeError:
        print(f"文件 {config_file} 不是有效的JSON格式.")

    # OpenAI SDK
    G.openai_handler = OpenAI(
        api_key=G.api_key, base_url=G.base_url, timeout=120, max_retries=0
    )

    # 异步线程数
    if not "127.0.0.1" in G.api_key and not "localhost" in G.base_url:
        G.max_workers = 4
    else:
        G.max_workers = 4

    # 开始业务逻辑
    asyncio.run(main())
