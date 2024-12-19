import os
import json
import asyncio
from types import SimpleNamespace

from rich import box
from rich.table import Table
from rich.prompt import Prompt
from rich.traceback import install

from model.LLM import LLM
from model.NER import NER
from model.Word import Word
from module.LogHelper import LogHelper
from module.TestHelper import TestHelper
from module.FileManager import FileManager

# 定义常量
SCORE_THRESHOLD = 0.80

# 合并词语，并按出现次数排序
def merge_words(words: list[Word]) -> list[Word]:
    words_unique = {}
    for word in words:
        key = (word.surface, word.type) # 只有文字和类型都一样才视为相同条目，避免跨类词条目合并
        if key not in words_unique:
            words_unique[key] = []
        words_unique[key].append(word)

    words_merged = []
    for v in words_unique.values():
        word = v[0]
        word.context = list(set([word.context[0] for word in v if word.context[0] != ""]))
        word.context.sort(key = lambda x: len(x), reverse = True)
        word.count = len(word.context)
        word.score = min(0.9999, sum(w.score for w in v) / len(v))
        words_merged.append(word)

    return sorted(words_merged, key = lambda x: x.count, reverse = True)

# 按置信度过滤词语
def filter_words_by_score(words: list[Word], threshold: float) -> list[Word]:
    return [word for word in words if word.score >= threshold]

# 按出现次数过滤词语
def filter_words_by_count(words: list[Word], threshold: float) -> list[Word]:
    return [word for word in words if word.count >= max(1, threshold)]

# 获取指定类型的词
def get_words_by_type(words: list[Word], type: str) -> list[Word]:
    return [word for word in words if word.type == type]

# 移除指定类型的词
def remove_words_by_type(words: list[Word], type: str) -> list[Word]:
    return [word for word in words if word.type != type]

# 开始处理文本
async def process_text(llm: LLM, ner: NER, file_manager: FileManager, config: SimpleNamespace, language: int) -> None:
    # 读取输入文件
    input_lines = file_manager.load_lines_from_input_file(language)

    # 查找实体词语
    LogHelper.info("即将开始执行 [查找实体词语] ...")
    words = []
    words = ner.search_for_entity(input_lines, language)

    # 合并相同词条
    words = merge_words(words)

    # 按出现次数阈值进行筛选
    LogHelper.info(f"即将开始执行 [阈值过滤] ... 当前出现次数的阈值设置为 {config.count_threshold} ...")
    words = filter_words_by_score(words, SCORE_THRESHOLD)
    words = filter_words_by_count(words, config.count_threshold)
    LogHelper.info("[阈值过滤] 已完成 ...")

    # 设置 LLM 语言
    llm.set_language(language)

    # 设置请求限制器
    llm.set_request_limiter()

    # 调试功能
    if LogHelper.is_debug():
        with LogHelper.status("正在检查置信度阈值 ..."):
            TestHelper.check_score_threshold(words, "log_score_threshold.log")

    # 等待词义分析任务结果
    LogHelper.info("即将开始执行 [词义分析] ...")
    words = await llm.surface_analysis_batch(words)
    words = remove_words_by_type(words, "")

    # 调试功能
    if LogHelper.is_debug():
        with LogHelper.status("正在保存请求记录 ..."):
            TestHelper.save_surface_analysis_log(words, "log_surface_analysis.log")
        with LogHelper.status("正在检查结果重复度 ..."):
            TestHelper.check_result_duplication(words, "log_result_duplication.log")

    # 等待 上下文翻译 任务结果
    if language in (NER.Language.EN, NER.Language.JP, NER.Language.KO):
        for k, v in NER.TYPES.items():
            if k == "PER" and config.context_translate_per != 1:
                continue

            if k != "PER" and config.context_translate_other != 1:
                continue

            LogHelper.info(f"即将开始执行 [上下文翻译 - {v}] ...")
            word_type = get_words_by_type(words, k)
            word_type = await llm.context_translate_batch(word_type)

    # 调试功能
    if LogHelper.is_debug():
        with LogHelper.status("正在保存请求记录 ..."):
            TestHelper.save_context_translate_log(words, "log_context_translate.log")

    # 将结果写入文件
    LogHelper.info("")
    file_manager.save_result_to_file(words, language)

    # 等待用户退出
    LogHelper.info("")
    LogHelper.info("工作流程已结束 ... 请检查生成的数据文件 ...")
    LogHelper.info("")
    LogHelper.info("")
    os.system("pause")

# 接口测试
async def test_api(llm: LLM) -> None:
    # 设置请求限制器
    llm.set_request_limiter()

    # 等待接口测试结果
    if await llm.api_test():
        LogHelper.print("")
        LogHelper.info("接口测试 [green]执行成功[/] ...")
    else:
        LogHelper.print("")
        LogHelper.warning("接口测试 [red]执行失败[/], 请检查配置文件 ...")

    LogHelper.print("")
    os.system("pause")
    os.system("cls")

# 打印应用信息
def print_app_info(config: SimpleNamespace, version: str) -> None:
    LogHelper.print()
    LogHelper.print()
    LogHelper.rule(f"KeywordGacha {version}", style = "light_goldenrod2")
    LogHelper.rule("[blue]https://github.com/neavo/KeywordGacha", style = "light_goldenrod2")
    LogHelper.rule("使用 OpenAI 兼容接口自动生成小说、漫画、字幕、游戏脚本等内容文本中实体词语表的翻译辅助工具", style = "light_goldenrod2")
    LogHelper.print()

    table = Table(
        box = box.ASCII2,
        expand = True,
        highlight = True,
        show_lines = True,
        show_header = False,
        border_style = "light_goldenrod2"
    )

    rows = [
        ("模型名称", str(config.model_name)),
        ("接口密钥", str(config.api_key)),
        ("接口地址", str(config.base_url)),
    ]

    for row in rows:
        table.add_row(*row)
    LogHelper.print(table)
    LogHelper.print()

    table = Table(
        box = box.ASCII2,
        expand = True,
        highlight = True,
        show_lines = True,
        border_style = "light_goldenrod2"
    )
    table.add_column("设置", style = "white", ratio = 1, overflow = "fold")
    table.add_column("当前值", style = "white", ratio = 1, overflow = "fold")
    table.add_column("设置", style = "white", ratio = 1, overflow = "fold")
    table.add_column("当前值", style = "white", ratio = 1, overflow = "fold")

    rows = [
        ("是否翻译角色实体上下文", "是" if config.context_translate_per == 1 else "否", "是否翻译其他实体上下文", "是" if config.context_translate_other == 1 else "否"),
        ("网络请求超时时间", f"{config.request_timeout} 秒" , "网络请求频率阈值", f"{config.request_frequency_threshold} 次/秒"),
    ]

    for row in rows:
        table.add_row(*row)
    LogHelper.print(table)

    LogHelper.print()
    LogHelper.print("请编辑 [green]config.json[/] 文件来修改应用设置 ...")
    LogHelper.print()

# 打印菜单
def print_menu_main() -> int:
    LogHelper.print("请选择功能：")
    LogHelper.print("")
    LogHelper.print("\t--> 1. 开始处理 [green]中文文本[/]")
    LogHelper.print("\t--> 2. 开始处理 [green]英文文本[/]")
    LogHelper.print("\t--> 3. 开始处理 [green]日文文本[/]")
    LogHelper.print("\t--> 4. 开始处理 [green]韩文文本[/]")
    LogHelper.print("\t--> 5. 开始执行 [green]接口测试[/]")
    LogHelper.print("")
    choice = int(Prompt.ask("请输入选项前的 [green]数字序号[/] 来使用对应的功能，默认为 [green][3][/] ",
        choices = ["1", "2", "3", "4", "5"],
        default = "3",
        show_choices = False,
        show_default = False
    ))
    LogHelper.print("")

    return choice

# 主函数
async def begin(llm: LLM, ner: NER, file_manager: FileManager, config: SimpleNamespace, version: str) -> None:
    choice = -1
    while choice not in (1, 2, 3, 4):
        print_app_info(config, version)

        choice = print_menu_main()
        if choice == 1:
            await process_text(llm, ner, file_manager, config, NER.Language.ZH)
        elif choice == 2:
            await process_text(llm, ner, file_manager, config, NER.Language.EN)
        elif choice == 3:
            await process_text(llm, ner, file_manager, config, NER.Language.JP)
        elif choice == 4:
            await process_text(llm, ner, file_manager, config, NER.Language.KO)
        elif choice == 5:
            await test_api(llm)

# 一些初始化步骤
def load_config() -> tuple[LLM, NER, FileManager, SimpleNamespace, str]:
    with LogHelper.status("正在初始化 [green]KG[/] 引擎 ..."):
        config = SimpleNamespace()
        version = ""

        try:
            # 优先使用开发环境配置文件
            if not os.path.isfile("config_dev.json"):
                path = "config.json"
            else:
                path = "config_dev.json"

            # 读取配置文件
            with open(path, "r", encoding = "utf-8") as reader:
                for k, v in json.load(reader).items():
                    setattr(config, k, v[0])

            # 读取版本号文件
            with open("version.txt", "r", encoding = "utf-8") as reader:
                version = reader.read().strip()
        except Exception:
            LogHelper.error("配置文件读取失败 ...")

        # 初始化 LLM 对象
        llm = LLM(config)
        llm.load_prompt()

        # 初始化 NER 对象
        ner = NER()
        ner.load_blacklist()

        # 初始化 FileManager 对象
        file_manager = FileManager()

    return llm, ner, file_manager, config, version

# 确保程序出错时可以捕捉到错误日志
async def main() -> None:
    try:
        # 注册全局异常追踪器
        install()

        # 加载配置
        llm, ner, file_manager, config, version = load_config()

        # 开始处理
        await begin(llm, ner, file_manager, config, version)
    except EOFError:
        LogHelper.error("EOFError - 程序即将退出 ...")
    except KeyboardInterrupt:
        LogHelper.error("KeyboardInterrupt - 程序即将退出 ...")
    except Exception as e:
        LogHelper.error(f"{LogHelper.get_trackback(e)}")
        LogHelper.print()
        LogHelper.print()
        LogHelper.error("出现严重错误，程序即将退出，错误信息已保存至日志文件 [green]KeywordGacha.log[/] ...")
        LogHelper.print()
        LogHelper.print()
        os.system("pause")

# 入口函数
if __name__ == "__main__":
    asyncio.run(main())