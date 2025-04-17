class Base():

    # 事件
    class Event():

        PLATFORM_TEST_DONE: int = 100                           # API 测试完成
        PLATFORM_TEST_START: int = 101                          # API 测试开始
        TRANSLATION_START: int = 200                            # 翻译开始
        TRANSLATION_STOP: int = 210                             # 翻译停止
        TRANSLATION_STOP_DONE: int = 220                        # 翻译停止完成
        TRANSLATION_UPDATE: int = 230                           # 翻译状态更新
        TRANSLATION_MANUAL_EXPORT: int = 240                    # 翻译结果手动导出
        CACHE_FILE_AUTO_SAVE: int = 300                         # 缓存文件自动保存
        PROJECT_STATUS: int = 400                               # 项目状态检查
        PROJECT_STATUS_CHECK_DONE: int = 410                    # 项目状态检查完成
        APP_UPDATE_CHECK: int = 500                             # 检查更新
        APP_UPDATE_CHECK_DONE: int = 510                        # 检查更新 - 完成
        APP_UPDATE_DOWNLOAD: int = 520                          # 检查更新 - 下载
        APP_UPDATE_DOWNLOAD_UPDATE: int = 530                   # 检查更新 - 下载进度更新
        APP_UPDATE_EXTRACT: int = 540                           # 检查更新 - 解压
        APP_TOAST_SHOW: int = 600                               # 显示 Toast
        GLOSSARY_REFRESH: int = 700                             # 术语表刷新
        APP_SHUT_DOWN: int = 1000                               # 应用关闭

    # 任务状态
    class Status():

        IDLE: int = 100                                         # 无任务
        TESTING: int = 200                                      # 运行中
        TRANSLATING: int = 300                                  # 运行中
        STOPPING: int = 400                                     # 停止中

    # 接口格式
    class APIFormat():

        OPENAI: str = "OpenAI"
        GOOGLE: str = "Google"
        ANTHROPIC: str = "Anthropic"
        SAKURALLM: str = "SakuraLLM"

    # 接口格式
    class ToastType():

        INFO: str = "INFO"
        ERROR: str = "ERROR"
        SUCCESS: str = "SUCCESS"
        WARNING: str = "WARNING"

    # 翻译状态
    class TranslationStatus():

        UNTRANSLATED: str = "UNTRANSLATED"                      # 待翻译
        TRANSLATING: str = "TRANSLATING"                        # 翻译中
        TRANSLATED: str = "TRANSLATED"                          # 已翻译
        TRANSLATED_IN_PAST: str = "TRANSLATED_IN_PAST"          # 过去已翻译
        EXCLUDED: str = "EXCLUDED"                              # 已排除
        DUPLICATED: str = "DUPLICATED"                          # 重复条目

    # 构造函数
    def __init__(self) -> None:
        pass