import threading

import tiktoken

class Word:

    TYPE_FILTER = (int, str, bool, float, list, dict, tuple)

    def __init__(self) -> None:
        super().__init__()

        # 默认值
        self.score: float = 0.0
        self.count: int = 0
        self.context: list[str] = []
        self.context_summary: str = ""
        self.context_translation: list[str] = []
        self.surface: str = ""
        self.surface_romaji: str = ""
        self.surface_translation: str = ""
        self.surface_translation_description: str = ""
        self.type: str = ""
        self.gender: str = ""
        self.input_lines: list[str] = []
        self.llmresponse_summarize_context: str = ""
        self.llmresponse_translate_context: str = ""
        self.llmresponse_translate_surface: str = ""

        # 类变量
        Word.cache = {} if not hasattr(Word, "cache") else Word.cache

        # 类线程锁
        Word.lock = threading.Lock() if not hasattr(Word, "lock") else Word.lock

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.get_vars()})"


    def get_vars(self) -> dict:
        return {
            k:v
            for k, v in vars(self).items()
            if isinstance(v, __class__.TYPE_FILTER)
        }

    # 获取token数量，优先从缓存中获取
    def get_token_count(self, line: str) -> int:
        count = 0

        # 优先从缓存中取数据
        with Word.lock:
            if line in Word.cache:
                count = Word.cache[line]
            else:
                count = len(tiktoken.get_encoding("cl100k_base").encode(line))
                Word.cache[line] = count

        return count

    # 按阈值截取文本，如果句子长度全部超过阈值，则取最接近阈值的一条
    def clip_lines(self, lines: list[str], line_threshold: int, token_threshold: int) -> tuple[list[str], int]:
        context = []
        context_token_count = 0

        for line in lines:
            # 行数阈值有效，且超过行数阈值，则跳出循环
            if line_threshold > 0 and len(context) > line_threshold:
                break

            line_token_count = self.get_token_count(line)

            # 跳过超出阈值的句子
            if line_token_count > token_threshold:
                continue

            # 更新上下文与计数
            context.append(line)
            context_token_count = context_token_count + line_token_count

            # 如果计数超过 Token 阈值，则跳出循环
            if context_token_count > token_threshold:
                break

        # 如果句子长度全部超过 Token 阈值，则取最接近阈值的一条
        if len(lines) > 0 and len(context) == 0:
            line = min(lines, key = lambda line: abs(self.get_token_count(line) - token_threshold))

            context.append(line)
            context_token_count = self.get_token_count(line)

        return context, context_token_count


    # 按长度截取上下文并返回，
    def clip_context(self, line_threshold: int, token_threshold: int) -> list[str]:
        # 先从上下文中截取
        context, context_token_count = self.clip_lines(self.context, line_threshold, token_threshold)

        # 如果句子长度不足 75%，则尝试全文匹配中补充
        if context_token_count < token_threshold * 0.75:
            context_ex, context_token_count_ex = self.clip_lines(
                sorted([line for line in self.input_lines if self.surface in line], key = lambda line: self.get_token_count(line), reverse = True),
                line_threshold - len(context),
                token_threshold - context_token_count,
            )

            context.extend(context_ex)
            context_token_count = context_token_count + context_token_count_ex

        return context

    # 获取用于上下文分析任务的上下文文本
    def get_context_str_for_summarize(self, language: int) -> str:
        from model.NER import NER
        return "\n".join(
            self.clip_context(
                line_threshold = 0,
                token_threshold = 960 if language == NER.LANGUAGE.EN else 1280,
            )
        ).replace("\n\n", "\n").strip()

    # 获取用于上下文翻译任务的上下文文本
    def get_context_str_for_translate(self, language: int) -> str:
        from model.NER import NER
        return "\n".join(
            self.clip_context(
                line_threshold = 20,
                token_threshold = 768 if language == NER.LANGUAGE.EN else 1024,
            )
        ).replace("\n\n", "\n").strip()

    # 获取用于词语翻译任务的上下文文本
    def get_context_str_for_surface_translate(self) -> str:
        return "\n".join(
            self.clip_context(
                line_threshold = 10,
                token_threshold = 384,
            )
        ).replace("\n\n", "\n").strip()