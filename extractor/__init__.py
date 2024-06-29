import os
import re
import json
import asyncio
from openai import AsyncOpenAI
from model.word import Word
from tqdm.asyncio import tqdm
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)


class CharacterNameExtractor:
    def __init__(self):
        # 初始化配置
        self.max_tokens_word_extract = 512
        self.max_tokens_context_translation = 1024
        self.split_threshold = 4 * 1024
        self.count_threshold = 3
        self.black_list = ["様", "さま", "君", "くん", "桑", "さん", "殿", "どの", ""]
        self.max_workers = 5
        self.concurrency = asyncio.Semaphore(self.max_workers)
        self.input_data = []

        # 加载配置文件
        self.load_config()

        # 初始化AsyncOpenAI客户端
        self.openai_handler = AsyncOpenAI(
            api_key=self.api_key, base_url=self.base_url, timeout=120, max_retries=0
        )

        # 如果不是本地API，调整并发数
        # if "127.0.0.1" not in self.api_key and "localhost" not in self.base_url:
        # self.max_workers = 8

        # 创建异步事件循环
        self.loop = asyncio.get_event_loop()

    def load_config(self):
        try:
            config_file = (
                "config_dev.json"
                if os.path.exists("config_dev.json")
                else "config.json"
            )
            with open(config_file, "r", encoding="utf-8") as file:
                config = json.load(file)
                for key, value in config.items():
                    setattr(self, key, value)

            with open(
                "prompt/prompt_context_translation.txt", "r", encoding="utf-8"
            ) as file:
                self.prompt_context_translation = file.read()

        except FileNotFoundError:
            print(f"文件 {config_file} 未找到.")
        except json.JSONDecodeError:
            print(f"文件 {config_file} 不是有效的JSON格式.")

    @classmethod
    async def create(cls):
        self = CharacterNameExtractor()
        return self

    async def gather_with_concurrency(self, *tasks, desc):
        async def sem_task(task):
            async with self.concurrency:
                return await task

        sem_tasks = [sem_task(task) for task in tasks]
        results = []
        for f in tqdm.as_completed(sem_tasks, total=len(tasks), desc=desc):
            try:
                result = await f
                results.extend(result)
            except Exception as e:
                print(f"Task failed with error: {e}")
                # 可以选择是否将失败的任务结果添加到结果列表中
                # results.append(None)

        return results

    def is_japanese(self, ch):
        # 平假名
        if "\u3040" <= ch <= "\u309f":
            return True
        # 片假名
        if "\u30a0" <= ch <= "\u30ff":
            return True
        # 日文汉字
        if "\u4e00" <= ch <= "\u9fff":
            return True
        # 日文全角数字
        if "\u3000" <= ch <= "\u303f":
            return True
        # 日文标点符号
        if "\uff01" <= ch <= "\uff60":
            return True
        # 濁音和半濁音符号
        if "\u309b" <= ch <= "\u309e":
            return True
        # 日文半角片假名
        if "\uff66" <= ch <= "\uff9f":
            return True
        return False

    def is_chinese_or_kanji(self, ch):
        return "\u4e00" <= ch <= "\u9fff"

    def contains_japanese(self, text):
        return any(self.is_japanese(char) for char in text)

    def is_all_japanese(self, text):
        return all(self.is_japanese(char) for char in text)

    def is_all_chinese_or_kanji(self, text):
        return all(self.is_chinese_or_kanji(char) for char in text)

    def is_valid_noun(self, surface):
        if surface in self.black_list:
            return False
        if not self.contains_japanese(surface):
            return False
        if re.compile(r"^[ぁ-んァ-ン]+[っッ]$").match(surface):
            return False
        if len(surface) == 1 and not self.is_chinese_or_kanji(surface):
            return False
        return True

    def split_by_byte_threshold(self, strings, threshold):
        result = []
        current_segment = []
        current_size = 0

        for string in strings:
            string = string.strip()
            string_size = len(string.encode("utf-8"))

            if current_size + string_size > threshold:
                result.append("".join(current_segment))
                current_segment = []
                current_size = 0

            current_segment.append(string)
            current_size += string_size

        if current_segment:
            result.append("".join(current_segment))

        return result

    async def read_input_data(self):
        if os.path.exists("ManualTransFile.json"):
            user_input = input(
                f'已找到数据文件 "ManualTransFile.json"，按回车直接使用或输入其他文件的路径：'
            ).strip('"')
            input_file_name = user_input if user_input else "ManualTransFile.json"
        elif os.path.exists("all.orig.txt"):
            user_input = input(
                f'已找到数据文件 "all.orig.txt"，按回车直接使用或输入其他文件的路径：'
            ).strip('"')
            input_file_name = user_input if user_input else "all.orig.txt"
        else:
            input_file_name = input(
                '未找到 "all.orig.txt" 或 "ManualTransFile.json"，请输入数据文件的路径: '
            ).strip('"')

        if input_file_name.endswith(".txt"):
            with open(input_file_name, "r", encoding="utf-8") as file:
                self.input_data = file.readlines()
        elif input_file_name.endswith(".json"):
            with open(input_file_name, "r", encoding="utf-8") as file:
                data = json.load(file)
                self.input_data = list(data.keys())
        else:
            print(f"不支持的文件格式: {input_file_name}")
            self.input_data = []

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception),
    )
    async def extract_nouns_llm(self, context):
        words = []

        try:
            completion = await self.openai_handler.chat.completions.create(
                model=self.model_name,
                temperature=0.1,
                top_p=0.3,
                max_tokens=self.max_tokens_word_extract,
                frequency_penalty=0.2,
                messages=[
                    {
                        "role": "system",
                        "content": "请分析以下日语句子，这是一段来自日文游戏的文本，从中识别出所有可能的角色名称。在回答中，只需列出这些可能的角色名称，如果有多个，请使用英文逗号(,)进行分隔。",
                    },
                    {"role": "user", "content": f"{context}"},
                ],
            )

            usage = completion.usage
            message = completion.choices[0].message

            if usage.completion_tokens >= self.max_tokens_word_extract:
                return words

            for text in message.content.split(","):
                surface = text.strip()

                if not surface or surface not in context:
                    continue

                if self.is_valid_noun(surface):
                    word = Word()
                    word.count = 1
                    word.surface = surface
                    word.llmresponse = completion
                    word.set_context(surface, self.input_data)

                    words.append(word)

        except Exception as error:
            print(f"Error in extract_nouns_llm: {error}")
            raise

        return words

    def merge_and_count(self, words_list):
        surface_to_word = {}

        for word in words_list:
            if word.surface not in surface_to_word:
                surface_to_word[word.surface] = word
            else:
                existing_word = surface_to_word[word.surface]
                existing_word.count += word.count

        sorted_words = sorted(
            surface_to_word.values(), key=lambda x: x.count, reverse=True
        )

        return sorted_words

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception)
    )
    async def translate_surface_by_llm(self, original):
        translation = ""

        try:
            completion = await self.openai_handler.chat.completions.create(
                model=self.model_name,
                temperature=0.1,
                top_p=0.3,
                max_tokens=self.max_tokens_word_extract,
                frequency_penalty=0.2,
                messages=[
                    {
                        "role": "system",
                        "content": "这是一段来自幻想系日文游戏的角色名称，请标注罗马音并给出2种中文翻译。结果只需列出罗马音和翻译，无需额外解释，每项之间用顿号分隔。请严格遵循格式：罗马音、翻译1、翻译2",
                    },
                    {"role": "user", "content": f"{original}"},
                ],
            )

            usage = completion.usage
            translation = (
                completion.choices[0]
                .message.content.strip()
                .replace("\n", "、")
                .replace("罗马音：", "")
                .replace("翻译1：", "")
                .replace("翻译2：", "")
            )

            if usage.completion_tokens >= self.max_tokens_word_extract:
                return ""

        except Exception as error:
            print(f"Error in translate_surface_by_llm: {error}")
            raise

        return translation

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception),
    )
    async def translate_context_by_llm(self, original):
        content = []

        try:
            completion = await self.openai_handler.chat.completions.create(
                model=self.model_name,
                temperature=0.1,
                top_p=0.3,
                max_tokens=self.max_tokens_context_translation,
                frequency_penalty=0,
                messages=[
                    {
                        "role": "system",
                        "content": self.prompt_context_translation,
                    },
                    {"role": "user", "content": "\n".join(original)},
                ],
            )

            usage = completion.usage
            content = completion.choices[0].message.content.strip()

            if (
                usage.completion_tokens >= self.max_tokens_context_translation
                or len(content) == 0
            ):
                return ""

            return content.split("\n")

        except Exception as error:
            print(f"Error in translate_context_by_llm: {error}")
            raise

        return content

    async def words_post_process(self, words):
        async def process_word(word):
            word.surface_translation = await self.translate_surface_by_llm(word.surface)
            word.context_translation = await self.translate_context_by_llm(word.context)

        tasks = [process_word(word) for word in words]
        await self.gather_with_concurrency(*tasks)

    def write_words_to_file(self, words, filename, detailmode):
        with open(filename, "w", encoding="utf-8") as file:
            if not detailmode:
                file.write("{\n")

            for k, word in enumerate(words):
                if detailmode:
                    file.write(f"词语原文 : {word.surface}\n")
                    file.write(f"词语翻译 : {word.surface_translation}\n")
                    file.write(f"出现次数 : {word.count}\n")
                    file.write(
                        f"上下文原文 : -----------------------------------------------------\n"
                    )
                    # file.write(f"{'    \n'.join(word.context)}\n")
                    file.write("    \n".join(word.context) + "\n")
                    file.write(
                        f"上下文翻译 : -----------------------------------------------------\n"
                    )
                    # file.write(f"{'    \n'.join(word.context_translation)}\n")
                    file.write("    \n".join(word.context_translation) + "\n")
                    file.write("\n")
                elif k == 0:
                    file.write(f'    "{word.surface}" : "",\n')
                elif k != len(words) - 1:
                    file.write(f'    "{word.surface}" : "",\n')
                else:
                    file.write(f'    "{word.surface}" : ""\n')

            if not detailmode:
                file.write("}")

    async def process(self):
        await self.read_input_data()
        print("正在读取文件中的文本 ...")
        input_data_splited = self.split_by_byte_threshold(
            self.input_data, self.split_threshold
        )

        tasks = [self.extract_nouns_llm(text) for text in input_data_splited]
        words_llm = await self.gather_with_concurrency(*tasks, desc="LLM 分词任务")

        words_llm_counted = self.merge_and_count(words_llm)
        words_all = self.merge_and_count(words_llm_counted)
        words_with_threshold = [
            word for word in words_all if word.count >= self.count_threshold
        ]

        post_process_tasks = [self.process_word(word) for word in words_with_threshold]
        words_with_threshold = await self.gather_with_concurrency(*post_process_tasks, desc="LLM 翻译任务")

        names_true_output_file = "角色姓名_日志.txt"
        dictionary_names_true_file = "角色姓名_列表.json"

        self.write_words_to_file(words_with_threshold, names_true_output_file, True)
        self.write_words_to_file(
            words_with_threshold, dictionary_names_true_file, False
        )

        print(f"\n结果已写入到:")
        print(f"　　{names_true_output_file}")
        print(f"　　{dictionary_names_true_file}")

    async def process_word(self, word):
        word.surface_translation = await self.translate_surface_by_llm(word.surface)
        word.context_translation = await self.translate_context_by_llm(word.context)
        return [word]