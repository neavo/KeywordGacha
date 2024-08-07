import re
import json
import random
import asyncio

from openai import AsyncOpenAI
from aiolimiter import AsyncLimiter

from model.NER import NER
from model.Word import Word
from helper.LogHelper import LogHelper
from helper.TextHelper import TextHelper

class LLM:

    MAX_RETRY = 2 # 最大重试次数

    TASK_TYPE_SUMMAIRZE_CONTEXT = 10    # 语义分析
    TASK_TYPE_TRANSLATE_SURFACE = 20    # 翻译词语
    TASK_TYPE_TRANSLATE_CONTEXT = 30    # 翻译上下文
    TASK_TYPE_VALIDATE_NER = 40         # 实体校验
    TASK_TYPE_CLASSIFY_NER = 50         # 实体分类

    # 初始化请求配置参数
    LLMCONFIG = {}

    # 请求参数配置 - 语义分析
    LLMCONFIG[TASK_TYPE_SUMMAIRZE_CONTEXT] = type("GClass", (), {})()
    LLMCONFIG[TASK_TYPE_SUMMAIRZE_CONTEXT].TEMPERATURE = 0.01
    LLMCONFIG[TASK_TYPE_SUMMAIRZE_CONTEXT].TOP_P = 1
    LLMCONFIG[TASK_TYPE_SUMMAIRZE_CONTEXT].MAX_TOKENS = 512
    LLMCONFIG[TASK_TYPE_SUMMAIRZE_CONTEXT].FREQUENCY_PENALTY = 0

    # 请求参数配置 - 翻译词语
    LLMCONFIG[TASK_TYPE_TRANSLATE_SURFACE] = type("GClass", (), {})()
    LLMCONFIG[TASK_TYPE_TRANSLATE_SURFACE].TEMPERATURE = 0.01
    LLMCONFIG[TASK_TYPE_TRANSLATE_SURFACE].TOP_P = 1
    LLMCONFIG[TASK_TYPE_TRANSLATE_SURFACE].MAX_TOKENS = 512
    LLMCONFIG[TASK_TYPE_TRANSLATE_SURFACE].FREQUENCY_PENALTY = 0

    # 请求参数配置 - 翻译上下文
    LLMCONFIG[TASK_TYPE_TRANSLATE_CONTEXT] = type("GClass", (), {})()
    LLMCONFIG[TASK_TYPE_TRANSLATE_CONTEXT].TEMPERATURE = 0.99
    LLMCONFIG[TASK_TYPE_TRANSLATE_CONTEXT].TOP_P = 1
    LLMCONFIG[TASK_TYPE_TRANSLATE_CONTEXT].MAX_TOKENS = 768
    LLMCONFIG[TASK_TYPE_TRANSLATE_CONTEXT].FREQUENCY_PENALTY = 0

    # 请求参数配置 - 实体校验
    LLMCONFIG[TASK_TYPE_VALIDATE_NER] = type("GClass", (), {})()
    LLMCONFIG[TASK_TYPE_VALIDATE_NER].TEMPERATURE = 0.01
    LLMCONFIG[TASK_TYPE_VALIDATE_NER].TOP_P = 1
    LLMCONFIG[TASK_TYPE_VALIDATE_NER].MAX_TOKENS = 512
    LLMCONFIG[TASK_TYPE_VALIDATE_NER].FREQUENCY_PENALTY = 0
    
    # 请求参数配置 - 实体分类
    LLMCONFIG[TASK_TYPE_CLASSIFY_NER] = type("GClass", (), {})()
    LLMCONFIG[TASK_TYPE_CLASSIFY_NER].TEMPERATURE = 0.01
    LLMCONFIG[TASK_TYPE_CLASSIFY_NER].TOP_P = 1
    LLMCONFIG[TASK_TYPE_CLASSIFY_NER].MAX_TOKENS = 512
    LLMCONFIG[TASK_TYPE_CLASSIFY_NER].FREQUENCY_PENALTY = 0

    def __init__(self, config):
        # 初始化OpenAI API密钥、基础URL和模型名称
        self.api_key = config.api_key
        self.base_url = config.base_url
        self.model_name = config.model_name
        
        # 初始化各类prompt和黑名单
        self.black_list = ""
        self.prompt_analyze_attribute = ""
        self.prompt_summarize_context = ""
        self.prompt_translate_surface = ""
        self.prompt_translate_context = ""

        # 请求限制器
        if config.request_frequency_threshold > 1:
            self.semaphore = asyncio.Semaphore(config.request_frequency_threshold)
            self.async_limiter = AsyncLimiter(max_rate = config.request_frequency_threshold, time_period = 1)
        elif config.request_frequency_threshold > 0:
            self.semaphore = asyncio.Semaphore(1)
            self.async_limiter = AsyncLimiter(max_rate = 1, time_period = 1 / config.request_frequency_threshold)
        else:
            self.semaphore = asyncio.Semaphore(1)
            self.async_limiter = AsyncLimiter(max_rate = 1, time_period = 1)

        # 初始化OpenAI客户端
        self.openai_handler = AsyncOpenAI(
            api_key = self.api_key,
            base_url = self.base_url if self.base_url.endswith("/v1") else self.base_url + "/v1",
            timeout = config.request_timeout,
            max_retries = 0
        )

    # 从指定路径加载黑名单文件内容
    def load_blacklist(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                data = json.load(file)

                self.blacklist = ""
                for k, v in enumerate(data):
                    self.blacklist = self.blacklist + v + "\n"
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

    # 根据类型加载不同的prompt模板文件
    def load_prompt_classify_ner(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                self.prompt_classify_ner = file.read()
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

    # 根据类型加载不同的prompt模板文件
    def load_prompt_validate_ner_evt(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                self.prompt_validate_ner_evt = file.read()
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

    # 根据类型加载不同的prompt模板文件
    def load_prompt_validate_ner_ins(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                self.prompt_validate_ner_ins = file.read()
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

    # 根据类型加载不同的prompt模板文件
    def load_prompt_validate_ner_loc(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                self.prompt_validate_ner_loc = file.read()
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

    # 根据类型加载不同的prompt模板文件
    def load_prompt_validate_ner_org(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                self.prompt_validate_ner_org = file.read()
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

    # 根据类型加载不同的prompt模板文件
    def load_prompt_validate_ner_prd(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                self.prompt_validate_ner_prd = file.read()
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

    # 根据类型加载不同的prompt模板文件
    def load_prompt_summarize_context(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                self.prompt_summarize_context = file.read()
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

    # 根据类型加载不同的prompt模板文件
    def load_prompt_translate_context(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                self.prompt_translate_context = file.read()
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

    # 根据类型加载不同的prompt模板文件
    def load_prompt_translate_surface_common(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                self.prompt_translate_surface_common = file.read()
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

    # 根据类型加载不同的prompt模板文件
    def load_prompt_translate_surface_person(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                self.prompt_translate_surface_person = file.read()
        except Exception as e:
            LogHelper.error(f"加载配置文件时发生错误 - {LogHelper.get_trackback(e)}")

    # 异步发送请求到OpenAI获取模型回复
    async def request(self, content, task_type, retry = False):
        completion = await self.openai_handler.chat.completions.create(
            model = self.model_name,
            temperature = self.LLMCONFIG[task_type].TEMPERATURE,
            top_p = self.LLMCONFIG[task_type].TOP_P,
            max_tokens = self.LLMCONFIG[task_type].MAX_TOKENS,
            frequency_penalty = self.LLMCONFIG[task_type].FREQUENCY_PENALTY + 0.2 if retry else self.LLMCONFIG[task_type].FREQUENCY_PENALTY,
            messages = [
                {
                    "role": "user", 
                    "content": content
                },
            ],
        )

        llmresponse = completion
        usage = completion.usage
        message = completion.choices[0].message

        return usage, message, llmresponse

    # 词语翻译任务
    async def translate_surface(self, word, retry):
        async with self.semaphore, self.async_limiter:
            if word.ner_type != NER.NER_TYPES.get("PER"):
                prompt = self.prompt_translate_surface_common.replace("{surface}", word.surface)
            else:
                prompt = self.prompt_translate_surface_person.replace("{attribute}", word.attribute).replace("{surface}", word.surface)

            usage, message, word.llmresponse_translate_surface = await self.request(
                prompt,
                self.TASK_TYPE_TRANSLATE_SURFACE,
                retry
            )

            if usage.completion_tokens >= self.LLMCONFIG[self.TASK_TYPE_TRANSLATE_SURFACE].MAX_TOKENS:
                raise Exception("usage.completion_tokens >= MAX_TOKENS")

            try:
                data = json.loads(
                    TextHelper.fix_broken_json_string(message.content.strip())
                )
            except Exception as error:
                LogHelper.debug(error)
                LogHelper.debug(word.surface)
                LogHelper.debug(message.content.strip())
                LogHelper.debug(TextHelper.fix_broken_json_string(message.content.strip()))
                raise error

            word.surface_romaji = data["romaji"]
            word.surface_translation = [data["translation_1"], data["translation_2"]]
            word.surface_translation_description = data["description"]

            return word

    # 词语翻译任务完成时的回调
    def on_translate_surface_task_done(self, future, words, words_failed, words_successed):
        try:
            word = future.result()
            words_successed.append(word)
            LogHelper.info(f"[词语翻译] 已完成 {len(words_successed)} / {len(words)} ...")       
        except Exception as e:
            LogHelper.warning(f"[词语翻译] 子任务执行失败，稍后将重试 ... {LogHelper.get_trackback(e)}")

        # 此处需要直接修改原有的数组，而不能创建新的数组来赋值
        words_failed.clear()
        for k, word in enumerate(words):
            if word not in words_successed:
                words_failed.append(word)

    # 批量执行词语翻译任务的具体实现
    async def do_translate_surface_batch(self, words, words_failed, words_successed):
        if len(words_failed) == 0:
            retry = False
            words_this_round = words
        else:
            retry = True
            words_this_round = words_failed       

        tasks = []
        for k, word in enumerate(words_this_round):
            task = asyncio.create_task(self.translate_surface(word, retry))
            task.add_done_callback(lambda future: self.on_translate_surface_task_done(future, words, words_failed, words_successed))
            tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=True)

        return words_failed, words_successed

    # 批量执行词语翻译任务 
    async def translate_surface_batch(self, words):
        words_failed = []
        words_successed = []

        words_failed, words_successed = await self.do_translate_surface_batch(words, words_failed, words_successed)

        if len(words_failed) > 0:
            for i in range(self.MAX_RETRY):
                LogHelper.warning( f"[词语翻译] 即将开始第 {i + 1} / {self.MAX_RETRY} 轮重试...")

                words_failed, words_successed = await self.do_translate_surface_batch(words, words_failed, words_successed)
                if len(words_failed) == 0:
                    break
        return words

    # 上下文翻译任务
    async def translate_context(self, word, retry):
        async with self.semaphore, self.async_limiter:
            usage, message, word.llmresponse_translate_context = await self.request(
                self.prompt_translate_context.replace("{context}", "\n".join(word.context)),
                self.TASK_TYPE_TRANSLATE_CONTEXT,
                retry
            )

            if usage.completion_tokens >= self.LLMCONFIG[self.TASK_TYPE_TRANSLATE_CONTEXT].MAX_TOKENS:
                raise Exception("usage.completion_tokens >= MAX_TOKENS")
            
            context_translation = []
            for k, line in enumerate(message.content.split("\n")):
                if len(line) > 0:
                    context_translation.append(line)

            word.context_translation = context_translation

            return word

    # 上下文翻译任务完成时的回调
    def on_translate_context_task_done(self, future, words, words_failed, words_successed):
        try:
            word = future.result()
            words_successed.append(word)
            LogHelper.info(f"[上下文翻译] 已完成 {len(words_successed)} / {len(words)} ...")       
        except Exception as e:
            LogHelper.warning(f"[上下文翻译] 子任务执行失败，稍后将重试 ... {LogHelper.get_trackback(e)}")

        # 此处需要直接修改原有的数组，而不能创建新的数组来赋值
        words_failed.clear()
        for k, word in enumerate(words):
            if word not in words_successed:
                words_failed.append(word)

    # 批量执行上下文翻译任务的具体实现
    async def do_translate_context_batch(self, words, words_failed, words_successed):
        if len(words_failed) == 0:
            retry = False
            words_this_round = words
        else:
            retry = True
            words_this_round = words_failed       

        tasks = []
        for k, word in enumerate(words_this_round):
            task = asyncio.create_task(self.translate_context(word, retry))
            task.add_done_callback(lambda future: self.on_translate_context_task_done(future, words, words_failed, words_successed))
            tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=True)

        return words_failed, words_successed

    # 批量执行上下文翻译任务 
    async def translate_context_batch(self, words):
        words_failed = []
        words_successed = []

        words_failed, words_successed = await self.do_translate_context_batch(words, words_failed, words_successed)

        for i in range(self.MAX_RETRY):
            if len(words_failed) > 0:
                LogHelper.warning( f"[上下文翻译] 即将开始第 {i + 1} / {self.MAX_RETRY} 轮重试...")
                words_failed, words_successed = await self.do_translate_context_batch(words, words_failed, words_successed)

        return words

    # 语义分析任务 
    async def summarize_context(self, word, retry):
        async with self.semaphore, self.async_limiter:
            usage, message, word.llmresponse_summarize_context = await self.request(
                self.prompt_summarize_context.replace("{surface}", word.surface).replace("{context}", "\n".join(word.context)),
                self.TASK_TYPE_SUMMAIRZE_CONTEXT,
                retry
            )

            if usage.completion_tokens >= self.LLMCONFIG[self.TASK_TYPE_SUMMAIRZE_CONTEXT].MAX_TOKENS:
                raise Exception("usage.completion_tokens >= MAX_TOKENS")
    
            try:
                result = json.loads(
                    TextHelper.fix_broken_json_string(message.content.strip())
                )
            except Exception as e:
                LogHelper.debug(f"{LogHelper.get_trackback(e)}")
                LogHelper.debug(message.content.strip())
                LogHelper.debug(TextHelper.fix_broken_json_string(message.content.strip()))
                raise e

            if "否" in result["is_name"]:
                word.ner_type = ""
                LogHelper.info(f"[语义分析] 已剔除 - {word.surface} - {result}")
            else:
                LogHelper.debug(f"[语义分析] 已完成 - {word.surface} - {result}")

            word.attribute = result["sex"]
            word.context_summary = result

            return word

    # 语义分析任务完成时的回调
    def on_summarize_context_task_done(self, future, words, words_failed, words_successed):
        try:
            word = future.result()
            words_successed.append(word)
            LogHelper.info(f"[语义分析] 已完成 {len(words_successed)} / {len(words)} ...")       
        except Exception as e:
            LogHelper.warning(f"[语义分析] 子任务执行失败，稍后将重试 ... {LogHelper.get_trackback(e)}")

    # 批量执行语义分析任务的具体实现
    async def do_summarize_context_batch(self, words, words_failed, words_successed):
        if len(words_failed) == 0:
            retry = False
            words_this_round = words
        else:
            retry = True
            words_this_round = words_failed       

        tasks = []
        for k, word in enumerate(words_this_round):
            task = asyncio.create_task(self.summarize_context(word, retry))
            task.add_done_callback(lambda future: self.on_summarize_context_task_done(future, words, words_failed, words_successed))
            tasks.append(task)

        # 等待异步任务完成 
        await asyncio.gather(*tasks, return_exceptions=True)

        # 获得失败任务的列表
        words_failed = [word_a for word_a in words if not any(word_a.surface == word_b.surface for word_b in words_successed)]

        return words_failed, words_successed

    # 批量执行语义分析任务
    async def summarize_context_batch(self, words):
        words_failed = []
        words_successed = []

        # 第一次请求
        words_failed, words_successed = await self.do_summarize_context_batch(words, words_failed, words_successed)

        # 开始重试流程
        for i in range(self.MAX_RETRY):
            if len(words_failed) > 0:
                LogHelper.warning( f"[语义分析] 即将开始第 {i + 1} / {self.MAX_RETRY} 轮重试...")
                words_failed, words_successed = await self.do_summarize_context_batch(words, words_failed, words_successed)

        return words

    # 实体校验任务 
    async def validate_ner(self, prompt, chunk, retry):
        async with self.semaphore, self.async_limiter:
            surfaces = [word.surface for word in chunk]

            usage, message, _ = await self.request(
                prompt.replace("{surfaces}", "\n".join(surfaces)),
                self.TASK_TYPE_VALIDATE_NER,
                retry
            )

            if usage.completion_tokens >= self.LLMCONFIG[self.TASK_TYPE_VALIDATE_NER].MAX_TOKENS:
                raise Exception("usage.completion_tokens >= MAX_TOKENS")

            results = message.content.strip().split(",")
            for v in results:
                for word in chunk:
                    if word.surface == v:
                        LogHelper.info(f"[实体校验] 已剔除 - {word.ner_type} - {word.surface}")
                        word.ner_type = ""

            return chunk

    # 实体校验任务完成时的回调
    def on_validate_ner_task_done(self, future, chunks, chunks_failed, chunks_successed):
        try:
            chunk = future.result()
            chunks_successed.append(chunk)
            LogHelper.info(f"[实体校验] 已完成 {len(chunks_successed)} / {len(chunks)} ...")       
        except Exception as e:
            LogHelper.warning(f"[实体校验] 子任务执行失败，稍后将重试 ... {LogHelper.get_trackback(e)}")

    # 批量执行实体校验任务的具体实现
    async def do_validate_ner_batch(self, prompt, chunks, chunks_failed, chunks_successed):
        if len(chunks_failed) == 0:
            retry = False
            chunks_this_round = chunks
        else:
            retry = True
            chunks_this_round = chunks_failed       

        tasks = []
        for chunk in chunks_this_round:
            task = asyncio.create_task(self.validate_ner(prompt, chunk, retry))
            task.add_done_callback(lambda future: self.on_validate_ner_task_done(future, chunks, chunks_failed, chunks_successed))
            tasks.append(task)

        # 等待异步任务完成 
        await asyncio.gather(*tasks, return_exceptions = True)

        # 获得失败任务的列表
        chunks_failed = [chunk for chunk in chunks if chunk not in chunks_successed]

        return chunks_failed, chunks_successed
 
    # 批量执行实体校验任务
    async def validate_ner_batch(self, words):
        ner_type = [
            ("EVT", self.prompt_validate_ner_evt),
            ("INS", self.prompt_validate_ner_ins),
            ("LOC", self.prompt_validate_ner_loc),
            ("ORG", self.prompt_validate_ner_org),
            ("PRD", self.prompt_validate_ner_prd),
        ]

        for v in ner_type:
            chunks_failed = []
            chunks_successed = []
            chunks = [word for word in words if word.ner_type == v[0]]
            chunks = [chunks[i:(i + 20)] for i in range(0, len(chunks), 20)]

            # 第一次请求
            chunks_failed, chunks_successed = await self.do_validate_ner_batch(v[1], chunks, chunks_failed, chunks_successed)

            # 开始重试流程
            for i in range(self.MAX_RETRY):
                if len(chunks_failed) > 0:
                    LogHelper.warning( f"[实体校验] 即将开始第 {i + 1} / {self.MAX_RETRY} 轮重试...")
                    chunks_failed, chunks_successed = await self.do_validate_ner_batch(v[1], chunks, chunks_failed, chunks_successed)

        return words

    # 实体分类任务 
    async def classify_ner(self, chunk, retry):
        async with self.semaphore, self.async_limiter:
            surface = [word.surface for word in chunk]
            context = [word.context[0] for word in chunk]

            usage, message, _ = await self.request(
                self.prompt_classify_ner.replace("{surface}", "\n".join(surface)).replace("{context}", "\n".join(context)),
                self.TASK_TYPE_CLASSIFY_NER,
                retry
            )

            if usage.completion_tokens >= self.LLMCONFIG[self.TASK_TYPE_CLASSIFY_NER].MAX_TOKENS:
                raise Exception("usage.completion_tokens >= MAX_TOKENS")

            try:
                result = json.loads(
                    message.content.strip().replace("```json", "").replace("```", "")
                )
            except Exception as e:
                LogHelper.debug(f"{LogHelper.get_trackback(e)}")
                LogHelper.debug(message.content.strip())
                raise e

            result_dict = {v["name"]: v["ner_type"] for v in result}
            for word in chunk:
                if (
                    word.surface not in result_dict
                    or
                    (word.surface in result_dict and result_dict[word.surface] != word.ner_type)
                ):
                    LogHelper.info(f"[实体分类] 已剔除 - {word.ner_type} - {word.surface}")
                    word.ner_type = ""

            # for word in chunk:
            #     for v in result:
            #         if word.surface == v["name"]:
            #             word.ner_type = v["ner_type"]
            #             LogHelper.info(f"[实体分类] 已识别 - {word.ner_type} - {word.surface}")
            #             break  # 找到匹配后立即退出内层循环

            return chunk

    # 实体分类任务 完成时的回调
    def on_classify_ner_task_done(self, future, chunks, chunks_failed, chunks_successed):
        try:
            chunk = future.result()
            chunks_successed.append(chunk)
            LogHelper.info(f"[实体分类] 已完成 {len(chunks_successed)} / {len(chunks)} ...")       
        except Exception as e:
            LogHelper.warning(f"[实体分类] 子任务执行失败，稍后将重试 ... {LogHelper.get_trackback(e)}")

    # 批量执行 实体分类任务 的具体实现
    async def do_classify_ner_bacth(self, chunks, chunks_failed, chunks_successed):
        if len(chunks_failed) == 0:
            retry = False
            chunks_this_round = chunks
        else:
            retry = True
            chunks_this_round = chunks_failed       

        tasks = []
        for chunk in chunks_this_round:
            task = asyncio.create_task(self.classify_ner(chunk, retry))
            task.add_done_callback(lambda future: self.on_classify_ner_task_done(future, chunks, chunks_failed, chunks_successed))
            tasks.append(task)

        # 等待异步任务完成 
        await asyncio.gather(*tasks, return_exceptions = True)

        # 获得失败任务的列表
        chunks_failed = [chunk for chunk in chunks if chunk not in chunks_successed]

        return chunks_failed, chunks_successed

    # 批量执行 实体分类任务 
    async def classify_ner_bacth(self, words):
        chunks_failed = []
        chunks_successed = []
        chunks = [words[i:(i + 5)] for i in range(0, len(words), 5)]

        # 第一次请求
        chunks_failed, chunks_successed = await self.do_classify_ner_bacth(chunks, chunks_failed, chunks_successed)

        # 开始重试流程
        for i in range(self.MAX_RETRY):
            if len(chunks_failed) > 0:
                LogHelper.warning( f"[实体分类] 即将开始第 {i + 1} / {self.MAX_RETRY} 轮重试...")
                chunks_failed, chunks_successed = await self.do_classify_ner_bacth(chunks, chunks_failed, chunks_successed)

        return words        