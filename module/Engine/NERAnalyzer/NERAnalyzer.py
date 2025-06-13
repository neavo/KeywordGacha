import concurrent.futures
import copy
import os
import re
import shutil
import threading
import time
import webbrowser

import httpx
import opencc
from rich.progress import TaskID

from base.Base import Base
from base.BaseLanguage import BaseLanguage
from model.Item import Item
from module.CacheManager import CacheManager
from module.Config import Config
from module.Engine.Engine import Engine
from module.Engine.NERAnalyzer.NERAnalyzerTask import NERAnalyzerTask
from module.Engine.TaskLimiter import TaskLimiter
from module.Engine.TaskRequester import TaskRequester
from module.FakeNameHelper import FakeNameHelper
from module.File.FileManager import FileManager
from module.Filter.LanguageFilter import LanguageFilter
from module.Filter.RuleFilter import RuleFilter
from module.Localizer.Localizer import Localizer
from module.ProgressBar import ProgressBar
from module.PromptBuilder import PromptBuilder
from module.Text.TextHelper import TextHelper

class NERAnalyzer(Base):

    BLACKLIST_INFO: set[str] = {
        "其它",
        "其他",
        "other",
        "others",
    }

    # 类变量
    OPENCCT2S: opencc.OpenCC = opencc.OpenCC("t2s")
    OPENCCS2T: opencc.OpenCC = opencc.OpenCC("s2tw")

    def __init__(self) -> None:
        super().__init__()

        # 初始化
        self.cache_manager = CacheManager(service = True)

        # 线程锁
        self.lock = threading.Lock()

        # 注册事件
        self.subscribe(Base.Event.PROJECT_CHECK_RUN, self.project_check_run)
        self.subscribe(Base.Event.NER_ANALYZER_RUN, self.ner_analyzer_run)
        self.subscribe(Base.Event.NER_ANALYZER_EXPORT, self.ner_analyzer_export)
        self.subscribe(Base.Event.NER_ANALYZER_REQUIRE_STOP, self.ner_analyzer_require_stop)

    # 项目检查事件
    def project_check_run(self, event: Base.Event, data: dict) -> None:

        def task(event: str, data: dict) -> None:
            if Engine.get().get_status() != Base.TaskStatus.IDLE:
                status = Base.ProjectStatus.NONE
            else:
                cache_manager = CacheManager(service = False)
                cache_manager.load_project_from_file(Config().load().output_folder)
                status = cache_manager.get_project().get_status()

            self.emit(Base.Event.PROJECT_CHECK_DONE, {
                "status" : status,
            })
        threading.Thread(target = task, args = (event, data)).start()

    # 运行事件
    def ner_analyzer_run(self, event: Base.Event, data: dict) -> None:
        if Engine.get().get_status() == Base.TaskStatus.IDLE:
            threading.Thread(
                target = self.start,
                args = (event, data),
            ).start()
        else:
            self.emit(Base.Event.TOAST, {
                "type": Base.ToastType.WARNING,
                "message": Localizer.get().engine_task_running,
            })

    # 停止事件
    def ner_analyzer_export(self, event: Base.Event, data: dict) -> None:
        if Engine.get().get_status() != Base.TaskStatus.NERING:
            return None

        # 复制一份以避免影响原始数据
        def task(event: str, data: dict) -> None:
            self.save_ouput(
                copy.deepcopy(self.cache_manager.get_project().get_extras().get("glossary", [])),
                end = False,
            )
        threading.Thread(target = task, args = (event, data)).start()

    # 请求停止事件
    def ner_analyzer_require_stop(self, event: Base.Event, data: dict) -> None:
        Engine.get().set_status(Base.TaskStatus.STOPPING)

        def task(event: str, data: dict) -> None:
            while True:
                time.sleep(0.5)

                if Engine.get().get_running_task_count() == 0:
                    # 等待回调执行完毕
                    time.sleep(1.0)

                    # 写入缓存
                    self.cache_manager.save_to_file(
                        project = self.cache_manager.get_project(),
                        items = self.cache_manager.get_items(),
                        output_folder = self.config.output_folder,
                    )

                    # 日志
                    self.print("")
                    self.info(Localizer.get().engine_task_stop)
                    self.print("")

                    # 通知
                    self.emit(Base.Event.TOAST, {
                        "type": Base.ToastType.SUCCESS,
                        "message": Localizer.get().engine_task_stop,
                    })

                    # 更新运行状态
                    Engine.get().set_status(Base.TaskStatus.IDLE)
                    self.emit(Base.Event.NER_ANALYZER_DONE, {})
                    break
        threading.Thread(target = task, args = (event, data)).start()

    # 开始
    def start(self, event: Base.Event, data: dict) -> None:
        config: Base.ProjectStatus = data.get("config")
        status: Base.ProjectStatus = data.get("status")

        # 更新运行状态
        Engine.get().set_status(Base.TaskStatus.NERING)

        # 初始化
        self.config = config if isinstance(config, Config) else Config().load()
        self.platform = self.config.get_platform(self.config.activate_platform)
        max_workers, rpm_threshold = self.initialize_max_workers()

        # 重置
        TaskRequester.reset()
        PromptBuilder.reset()
        FakeNameHelper.reset()

        # 生成缓存列表
        if status == Base.ProjectStatus.PROCESSING:
            self.cache_manager.load_from_file(self.config.output_folder)
        else:
            shutil.rmtree(f"{self.config.output_folder}/cache", ignore_errors = True)
            project, items = FileManager(self.config).read_from_path()
            self.cache_manager.set_items(items)
            self.cache_manager.set_project(project)

        # 检查数据是否为空
        if self.cache_manager.get_item_count() == 0:
            # 通知
            self.emit(Base.Event.TOAST, {
                "type": Base.ToastType.WARNING,
                "message": Localizer.get().engine_no_items,
            })

            self.emit(Base.Event.NER_ANALYZER_REQUIRE_STOP, {})
            return None

        # 兼容性处理
        for item in self.cache_manager.get_items():
            if item.get_status() == Base.ProjectStatus.PROCESSED_IN_PAST:
                item.set_status(Base.ProjectStatus.NONE)

        # 从头翻译时加载默认数据
        if status == Base.ProjectStatus.PROCESSING:
            self.extras = self.cache_manager.get_project().get_extras()
            self.extras["start_time"] = time.time() - self.extras.get("time", 0)
        else:
            self.extras = {
                "start_time": time.time(),
                "total_line": 0,
                "line": 0,
                "total_tokens": 0,
                "total_output_tokens": 0,
                "time": 0,
                "glossary": [],
            }

        # 更新翻译进度
        self.emit(Base.Event.NER_ANALYZER_UPDATE, self.extras)

        # 规则过滤
        self.rule_filter(self.cache_manager.get_items())

        # 语言过滤
        self.language_filter(self.cache_manager.get_items())

        # 开始循环
        for current_round in range(self.config.max_round):
            # 检测是否需要停止任务
            # 目的是避免用户正好在两轮之间停止任务
            if Engine.get().get_status() == Base.TaskStatus.STOPPING:
                return None

            # 第一轮且不是继续翻译时，记录任务的总行数
            if current_round == 0 and status == Base.ProjectStatus.NONE:
                self.extras["total_line"] = self.cache_manager.get_item_count_by_status(Base.ProjectStatus.NONE)

            # 第二轮开始切分
            if current_round > 0:
                self.config.token_threshold = max(1, int(self.config.token_threshold / 2))

            # 生成缓存数据条目片段
            chunks = self.cache_manager.generate_item_chunks(self.config.token_threshold)

            # 生成翻译任务
            self.print("")
            tasks: list[NERAnalyzerTask] = []
            with ProgressBar(transient = False) as progress:
                pid = progress.new()
                for items in chunks:
                    progress.update(pid, advance = 1, total = len(chunks))
                    tasks.append(NERAnalyzerTask(self.config, self.platform, items))

            # 打印日志
            self.info(Localizer.get().engine_task_generation.replace("{COUNT}", str(len(chunks))))

            # 输出开始翻译的日志
            self.print("")
            self.print("")
            self.info(f"{Localizer.get().engine_current_round} - {current_round + 1}")
            self.info(f"{Localizer.get().engine_max_round} - {self.config.max_round}")
            self.print("")
            self.info(f"{Localizer.get().engine_api_name} - {self.platform.get("name")}")
            self.info(f"{Localizer.get().engine_api_url} - {self.platform.get("api_url")}")
            self.info(f"{Localizer.get().engine_api_model} - {self.platform.get("model")}")
            self.print("")
            self.info(PromptBuilder(self.config).build_main())
            self.print("")

            # 开始执行翻译任务
            task_limiter = TaskLimiter(rps = max_workers, rpm = rpm_threshold)
            with ProgressBar(transient = True) as progress:
                with concurrent.futures.ThreadPoolExecutor(max_workers = max_workers, thread_name_prefix = Engine.TASK_PREFIX) as executor:
                    pid = progress.new()
                    for task in tasks:
                        # 检测是否需要停止任务
                        # 目的是绕过限流器，快速结束所有剩余任务
                        if Engine.get().get_status() == Base.TaskStatus.STOPPING:
                            return None

                        task_limiter.wait()
                        future = executor.submit(task.start)
                        future.add_done_callback(lambda future: self.task_done_callback(future, pid, progress))

            # 判断是否需要继续翻译
            if self.cache_manager.get_item_count_by_status(Base.ProjectStatus.NONE) == 0:
                self.cache_manager.get_project().set_status(Base.ProjectStatus.PROCESSED)

                # 日志
                self.print("")
                self.info(Localizer.get().engine_task_done)
                self.info(Localizer.get().engine_task_save)

                # 通知
                self.emit(Base.Event.TOAST, {
                    "type": Base.ToastType.SUCCESS,
                    "message": Localizer.get().engine_task_done,
                })
                break

            # 检查是否达到最大轮次
            if current_round >= self.config.max_round - 1:
                # 日志
                self.print("")
                self.warning(Localizer.get().engine_task_fail)
                self.warning(Localizer.get().engine_task_save)

                # 通知
                self.emit(Base.Event.TOAST, {
                    "type": Base.ToastType.SUCCESS,
                    "message": Localizer.get().engine_task_fail,
                })
                break

        # 等待回调执行完毕
        time.sleep(1.0)

        # 写入缓存
        self.cache_manager.save_to_file(
            project = self.cache_manager.get_project(),
            items = self.cache_manager.get_items(),
            output_folder = self.config.output_folder,
        )

        # 检查结果并写入文件
        self.save_ouput(
            self.cache_manager.get_project().get_extras().get("glossary", []),
            end = True,
        )

        # 重置内部状态（正常完成翻译）
        Engine.get().set_status(Base.TaskStatus.IDLE)

        # 触发翻译停止完成的事件
        self.emit(Base.Event.NER_ANALYZER_DONE, {})

    # 初始化速度控制器
    def initialize_max_workers(self) -> tuple[int, int]:
        max_workers: int = self.config.max_workers
        rpm_threshold: int = self.config.rpm_threshold

        # 当 max_workers = 0 时，尝试获取 llama.cpp 槽数
        if max_workers == 0:
            try:
                response_json = None
                response = httpx.get(re.sub(r"/v1$", "", self.platform.get("api_url")) + "/slots")
                response.raise_for_status()
                response_json = response.json()
            except Exception:
                pass
            if isinstance(response_json, list) and len(response_json) > 0:
                max_workers = len(response_json)

        if max_workers == 0 and rpm_threshold == 0:
            max_workers = 8
            rpm_threshold = 0
        elif max_workers > 0 and rpm_threshold == 0:
            pass
        elif max_workers == 0 and rpm_threshold > 0:
            max_workers = 8192
            rpm_threshold = rpm_threshold

        return max_workers, rpm_threshold

    # 规则过滤
    def rule_filter(self, items: list[Item]) -> None:
        if len(items) == 0:
            return None

        # 筛选
        self.print("")
        count: int = 0
        with ProgressBar(transient = False) as progress:
            pid = progress.new()
            for item in items:
                progress.update(pid, advance = 1, total = len(items))
                if RuleFilter.filter(item.get_src()) == True:
                    count = count + 1
                    item.set_status(Base.ProjectStatus.EXCLUDED)

        # 打印日志
        self.info(Localizer.get().engine_task_rule_filter.replace("{COUNT}", str(count)))

    # 语言过滤
    def language_filter(self, items: list[Item]) -> None:
        if len(items) == 0:
            return None

        # 筛选
        self.print("")
        count: int = 0
        with ProgressBar(transient = False) as progress:
            pid = progress.new()
            for item in items:
                progress.update(pid, advance = 1, total = len(items))
                if LanguageFilter.filter(item.get_src(), self.config.source_language) == True:
                    count = count + 1
                    item.set_status(Base.ProjectStatus.EXCLUDED)

        # 打印日志
        self.info(Localizer.get().engine_task_language_filter.replace("{COUNT}", str(count)))

    # 输出结果
    def save_ouput(self, glossary: list[dict[str, str]], end: bool) -> None:
        group: dict[str, list[dict[str, str]]] = {}
        with self.lock:
            v: dict[str, str] = {}
            for v in glossary:
                src: str = v.get("src").strip()
                dst: str = v.get("dst").strip()
                info: str = v.get("info").strip()

                # 简繁转换
                dst = self.convert_chinese_character_form(dst)
                info = self.convert_chinese_character_form(info)

                # 伪名还原
                src, fake_name_injected = FakeNameHelper.restore(src)

                # 将原文和译文都按标点切分
                srcs: list[str] = TextHelper.split_by_punctuation(src, split_by_space = True)
                dsts: list[str] = TextHelper.split_by_punctuation(dst, split_by_space = True)
                if len(srcs) != len(dsts):
                    srcs = [src]
                    dsts = [dst]
                for src, dst in zip(srcs, dsts):
                    src = src.strip()
                    dst = dst.strip()

                    if fake_name_injected == True:
                        dst = ""
                    elif src == "" or dst == "":
                        continue
                    elif src == dst and info == "":
                        continue
                    elif self.check(src, dst, info) == False:
                        continue

                    group.setdefault(src, []).append({
                        "src": src,
                        "dst": dst,
                        "info": info,
                    })

        glossary: list[dict[str, str]] = []
        for src, choices in group.items():
            glossary.append(self.find_best(src, choices))

        # 去重
        glossary = list({v.get("src"): v for v in glossary}.values())

        # 计数
        glossary = self.search_for_context(glossary, self.cache_manager.get_items(), end)

        # 排序
        glossary = sorted(glossary, key = lambda x: x.get("src"))

        # 写入文件
        FileManager(self.config).write_to_path(glossary)
        self.print("")
        self.info(Localizer.get().engine_task_save_done.replace("{PATH}", self.config.output_folder))
        self.print("")

        # 打开输出文件夹
        if self.config.output_folder_open_on_finish == True:
            webbrowser.open(os.path.abspath(self.config.output_folder))

    # 有效性检查
    def check(self, src: str, dst: str, info: str) -> bool:
        result: bool = True

        if TextHelper.get_display_lenght(src) > 32:
            result = False
        elif info.lower() in __class__.BLACKLIST_INFO:
            result = False

        return result

    # 找出最佳结果
    def find_best(self, src: str, choices: list[dict[str, str]]) -> dict[str, str]:
        dst_count: dict[str, int] = {}
        dst_choices: set[str] = set()
        for choice in choices:
            dst: str = choice.get("dst")
            dst_choices.add(dst)
            dst_count[dst] = dst_count.setdefault(dst, 0) + 1
        dst = max(dst_count, key = dst_count.get)

        info_count: dict[str, int] = {}
        info_choices: set[str] = set()
        for choice in choices:
            info: str = choice.get("info")
            info_choices.add(info)
            info_count[info] = info_count.setdefault(info, 0) + 1
        info = max(info_count, key = info_count.get)

        return {
            "src": src,
            "dst": dst,
            "dst_choices": dst_choices,
            "info": info,
            "info_choices": info_choices,
        }

    # 搜索参考文本，并按出现次数排序
    def search_for_context(self, glossary: list[dict[str, str]], items: list[Item], end: bool) -> list[dict[str, str | int | list[str]]]:
        lines: list[str] = [item.get_src().strip() for item in items if item.get_status() == Base.ProjectStatus.PROCESSED]
        lines_cp: list[str] = lines.copy()

        # 按实体词语的长度降序排序
        glossary = sorted(glossary, key = lambda x: len(x.get("src")), reverse = True)

        self.print("")
        with ProgressBar(transient = False) as progress:
            pid = progress.new() if end == True else None
            for entry in glossary:
                progress.update(pid, advance = 1, total = len(glossary)) if end == True else None
                src: str = entry.get("src")

                # 找出匹配的行
                index = {i for i, line in enumerate(lines) if src in line}

                # 获取匹配的参考文本，去重，并按长度降序排序
                entry["context"] = sorted(
                    list({line for i, line in enumerate(lines_cp) if i in index}),
                    key = lambda x: len(x),
                    reverse = True,
                )
                entry["count"] = len(entry.get("context"))

                # 掩盖已命中的实体词语文本，避免其子串错误的与父串匹配
                lines = [
                    line.replace(src, len(src) * "#") if i in index else line
                    for i, line in enumerate(lines)
                ]

        # 打印日志
        self.info(Localizer.get().engine_task_context_search.replace("{COUNT}", str(len(glossary))))

        # 排除零结果
        glossary = [v for v in glossary if v.get("count") > 0]

        # 按出现次数降序排序
        return sorted(glossary, key = lambda x: x.get("count"), reverse = True)

    # 中文字型转换
    def convert_chinese_character_form(self, src: str) -> str:
        if self.config.target_language != BaseLanguage.Enum.ZH:
            return src

        if self.config.traditional_chinese_enable == True:
            return __class__.OPENCCS2T.convert(src)
        else:
            return __class__.OPENCCT2S.convert(src)

    # 翻译任务完成时
    def task_done_callback(self, future: concurrent.futures.Future, pid: TaskID, progress: ProgressBar) -> None:
        try:
            # 获取结果
            result = future.result()

            # 结果为空则跳过后续的更新步骤
            if not isinstance(result, dict) or len(result) == 0:
                return

            # 记录数据
            with self.lock:
                new = {}
                new["glossary"] = self.extras.get("glossary", []) + result.get("glossary", 0)
                new["start_time"] = self.extras.get("start_time", 0)
                new["total_line"] = self.extras.get("total_line", 0)
                new["line"] = self.extras.get("line", 0) + result.get("row_count", 0)
                new["total_tokens"] = self.extras.get("total_tokens", 0) + result.get("input_tokens", 0) + result.get("output_tokens", 0)
                new["total_output_tokens"] = self.extras.get("total_output_tokens", 0) + result.get("output_tokens", 0)
                new["time"] = time.time() - self.extras.get("start_time", 0)
                self.extras = new

            # 更新翻译进度
            self.cache_manager.get_project().set_extras(self.extras)

            # 更新翻译状态
            self.cache_manager.get_project().set_status(Base.ProjectStatus.PROCESSING)

            # 请求保存缓存文件
            self.cache_manager.require_save_to_file(self.config.output_folder)

            # 日志
            progress.update(
                pid,
                total = self.extras.get("total_line", 0),
                completed = self.extras.get("line", 0),
            )

            # 触发翻译进度更新事件
            self.emit(Base.Event.NER_ANALYZER_UPDATE, self.extras)
        except Exception as e:
            self.error(f"{Localizer.get().log_task_fail}", e)