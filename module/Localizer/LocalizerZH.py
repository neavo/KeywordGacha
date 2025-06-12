

class LocalizerZH():

    # 保留
    switch_language: str = (
        "请选择应用语言，新的语言设置将在下次启动时生效 …"
        "\n"
        "Select application language, changes will take effect on restart …"
    )
    switch_language_toast: str = (
        "应用语言切换成功，请重启应用生效 …"
        "\n"
        "Language switched successfully, please restart the application for changes to take effect …"
    )

    # 通用
    add: str = "新增"
    edit: str = "修改"
    none: str = "无"
    back: str = "返回"
    next: str = "下一个"
    stop: str = "停止"
    start: str = "开始"
    timer: str = "定时器"
    close: str = "关闭"
    alert: str = "提醒"
    warning: str = "警告"
    confirm: str = "确认"
    cancel: str = "取消"
    auto: str = "自动"
    wiki: str = "功能说明"
    open: str = "打开"
    select: str = "选择"
    inject: str = "注入"
    filter: str = "过滤"
    search: str = "搜索"
    generate: str = "生成"
    placeholder: str = "请输入关键词 …"
    task_success: str = "任务执行成功 …"
    alert_no_data: str = "没有有效数据 …"
    alert_reset_timer: str = "将重置定时器，是否确认 … ？"
    alert_reset_translation: str = "将重置尚未完成的翻译任务，是否确认开始新的翻译任务 … ？"

    # 主页面
    app_close_message_box: str = "确定是否退出程序 … ？"
    app_new_version: str = "点击下载更新版本！"
    app_new_version_toast: str = "已找到新版本，版本号为 {VERSION}，请点击左下角按钮下载更新 …"
    app_new_version_update: str = "正在下载 {PERCENT} …"
    app_new_version_failure: str = "新版本下载失败 … "
    app_new_version_success: str = "新版本下载成功 … "
    app_new_version_downloaded: str = "点击应用新版本！"
    app_new_version_waiting_restart: str = "更新完成，应用即将关闭 …"
    app_theme_btn: str = "变换自如"
    app_language_btn: str = "字字珠玑"
    app_settings_page: str = "应用设置"
    app_platform_page: str = "接口管理"
    app_project_page: str = "项目设置"
    app_task_page: str = "开始任务"
    app_basic_settings_page: str = "基础设置"
    app_expert_settings_page: str = "专家设置"
    app_pre_replacement_page: str = "前置替换"
    app_custom_prompt_navigation_item: str = "自定义提示词"
    app_custom_prompt_zh_page: str = "中文提示词"
    app_custom_prompt_en_page: str = "英文提示词"

    # 路径
    path_bilingual: str = "双语对照"

    # 日志
    log_crash: str = "出现严重错误，应用即将退出，错误信息已保存至日志文件 …"
    log_proxy: str = "网络代理已启用 …"
    log_expert_mode: str = "专家模式已启用 …"
    log_api_test_fail: str = "接口测试失败 … "
    log_task_fail: str = "任务失败 …"
    log_read_file_fail: str = "文件读取失败 …"
    log_write_file_fail: str = "文件写入失败 …"
    cli_verify_folder: str = "参数发生错误：无效的路径 …"
    cli_verify_language: str = "参数发生错误：无效的语言 …"

    # 引擎
    engine_no_items: str = "没有找到需要处理数据，请确认 …"
    engine_task_running: str = "任务正在执行中，请稍后再试 …"
    engine_task_done: str = "所有数据均已处理，任务已结束 …"
    engine_task_fail: str = "已到最大任务轮次，仍有部分数据未处理，请检查处理结果 …"
    engine_task_stop: str = "任务已停止 …"
    engine_task_save: str = "正在生成输出文件，等稍候 …"
    engine_task_save_done: str = "任务结果已保存至 {PATH} 目录 …"
    engine_task_generation: str = "任务生成已完成，共生成 {COUNT} 个任务 …"
    engine_task_rule_filter: str = "规则过滤已完成，共过滤 {COUNT} 个无需翻译的条目 …"
    engine_task_language_filter: str = "语言过滤已完成，共过滤 {COUNT} 个不包含目标语言的条目 …"
    engine_task_context_search: str = "参考文本搜索已完成，共处理 {COUNT} 个条目 …"
    engine_max_round: str = "最大轮次"
    engine_current_round: str = "当前轮次"
    engine_api_url: str = "接口地址"
    engine_api_name: str = "接口名称"
    engine_api_model: str = "接口模型"
    engine_response_think: str = "模型思考内容："
    engine_response_result: str = "模型回复内容："
    engine_task_success: str = "任务耗时 {TIME} 秒，文本行数 {LINES} 行，输入消耗 {PT} Tokens，输出消耗 {CT} Tokens"
    engine_task_too_many: str = "实时任务较多，暂时停止显示详细结果以提升性能 …"
    api_tester_key: str = "测试密钥："
    api_tester_messages: str = "任务提示词："
    api_tester_result: str = "共测试 {COUNT} 个接口，成功 {SUCCESS} 个，失败 {FAILURE} 个 …"
    api_tester_result_failure: str = "失败的密钥："
    api_tester_running: str = "任务正在执行中，请稍后再试 …"
    ner_output_log_src: str = "原文："
    ner_output_log_dst: str = "译文："
    ner_output_log_dst_choices: str = "译文候选："
    ner_output_log_info: str = "备注："
    ner_output_log_info_choices: str = "备注候选："
    ner_output_log_count: str = "出现次数："
    ner_output_log_context: str = "参考文本："

    # 应用设置
    app_settings_page_expert_title: str = "专家模式"
    app_settings_page_expert_content: str = "启用此功能后，将显示更多日志信息并提供更多高级设置选项（将在应用重启后生效）"
    app_settings_page_font_hinting_title: str = "字体优化"
    app_settings_page_font_hinting_content: str = "启用此功能后，应用内 UI 字体的边缘渲染将更加圆润（将在应用重启后生效）"
    app_settings_page_scale_factor_title: str = "全局缩放比例"
    app_settings_page_scale_factor_content: str = "启用此功能后，应用界面将按照所选比例进行缩放（将在应用重启后生效）"
    app_settings_page_proxy_url: str = "示例 - http://127.0.0.1:7890"
    app_settings_page_proxy_url_title: str = "网络代理"
    app_settings_page_proxy_url_content: str = "启用此功能后，将使用设置的代理地址发送网络请求（将在应用重启后生效）"
    app_settings_page_close: str = "应用即将关闭，请确认 …"

    # 接口管理
    platform_page_api_test_result: str = "接口测试结果：成功 {SUCCESS} 个，失败 {FAILURE} 个 …"
    platform_page_api_activate: str = "激活接口"
    platform_page_api_edit: str = "编辑接口"
    platform_page_api_args: str = "编辑参数"
    platform_page_api_test: str = "测试接口"
    platform_page_api_delete: str = "删除接口"
    platform_page_widget_add_title: str = "接口列表"
    platform_page_widget_add_content: str = "在此添加和管理任何兼容 Google、OpenAI、Anthropic 格式的 LLM 模型接口"

    # 接口编辑
    platform_edit_page_name: str = "请输入接口名称 …"
    platform_edit_page_name_title: str = "接口名称"
    platform_edit_page_name_content: str = "请输入接口名称，仅用于应用内显示，无实际作用"
    platform_edit_page_api_url: str = "请输入接口地址 …"
    platform_edit_page_api_url_title: str = "接口地址"
    platform_edit_page_api_url_content: str = "请输入接口地址，请注意辨别结尾是否需要添加 /v1"
    platform_edit_page_api_key: str = "请输入接口密钥 …"
    platform_edit_page_api_key_title: str = "接口密钥"
    platform_edit_page_api_key_content: str = "请输入接口密钥，例如 sk-d0daba12345678fd8eb7b8d31c123456，填入多个密钥可以轮询使用，每行一个"
    platform_edit_page_thinking_title: str = "优先使用思考模式"
    platform_edit_page_thinking_content: str = "对于同时支持思考模式和普通模式的模型，优先使用思考模式"
    platform_edit_page_model: str = "请输入模型名称 …"
    platform_edit_page_model_title: str = "模型名称"
    platform_edit_page_model_content: str = "当前使用的模型为 {MODEL}"
    platform_edit_page_model_edit: str = "手动输入"
    platform_edit_page_model_sync: str = "在线获取"

    # 参数编辑
    args_edit_page_top_p_title: str = "top_p"
    args_edit_page_top_p_content: str = "请谨慎设置，错误的值可能导致结果异常或者请求报错"
    args_edit_page_temperature_title: str = "temperature"
    args_edit_page_temperature_content: str = "请谨慎设置，错误的值可能导致结果异常或者请求报错"
    args_edit_page_presence_penalty_title: str = "presence_penalty"
    args_edit_page_presence_penalty_content: str = "请谨慎设置，错误的值可能导致结果异常或者请求报错"
    args_edit_page_frequency_penalty_title: str = "frequency_penalty"
    args_edit_page_frequency_penalty_content: str = "请谨慎设置，错误的值可能导致结果异常或者请求报错"
    args_edit_page_document_link: str = "点击查看文档"

    # 模型列表
    model_list_page_title: str = "可用的模型列表"
    model_list_page_content: str = "点击选择要使用的模型"
    model_list_page_fail: str = "获取模型列表失败，请检查接口配置 …"

    # 项目设置
    project_page_source_language_title: str = "原文语言"
    project_page_source_language_content: str = "设置当前项目中输入文本的语言"
    project_page_target_language_title: str = "译文语言"
    project_page_target_language_content: str = "设置当前项目中输出文本的语言"
    project_page_input_folder_title: str = "输入文件夹"
    project_page_input_folder_content: str = "当前输入文件夹为"
    project_page_output_folder_title: str = "输出文件夹（不能与输入文件夹相同）"
    project_page_output_folder_content: str = "当前输出文件夹为"
    project_page_output_folder_open_on_finish_title: str = "任务完成时打开输出文件夹"
    project_page_output_folder_open_on_finish_content: str = "启用此功能后，将在任务完成时自动打开输出文件夹"
    project_page_traditional_chinese_title: str = "使用繁体输出中文"
    project_page_traditional_chinese_content: str = "启用此功能后，在译文语言设置为中文时，将使用繁体字形输出中文文本"

    # 开始任务
    task_page_status_idle: str = "无任务"
    task_page_status_testing: str = "测试中"
    task_page_status_nering: str = "提取中"
    task_page_status_stopping: str = "停止中"
    task_page_indeterminate_saving: str = "缓存保存中 …"
    task_page_indeterminate_stoping: str = "正在停止任务 …"
    task_page_card_time: str = "累计时间"
    task_page_card_remaining_time: str = "剩余时间"
    task_page_card_line: str = "处理行数"
    task_page_card_remaining_line: str = "剩余行数"
    task_page_card_speed: str = "平均速度"
    task_page_card_token: str = "累计消耗"
    task_page_card_task: str = "实时任务数"
    task_page_alert_pause: str = "停止的任务可以随时继续执行，是否确定停止任务 … ？"
    task_page_continue: str = "继续任务"
    task_page_export: str = "导出任务数据"
    task_page_timer: str = "请设置延迟启动前要等待的时间"

    # 基础设置
    basic_settings_page_max_workers_title: str = "并发任务阈值"
    basic_settings_page_max_workers_content: str = (
        "同时执行的任务数量的最大值"
        "<br>"
        "合理设置可以显著加快任务的完成速度，请参考 API 平台的文档进行设置，0 = 自动"
        ""
        ""
    )
    basic_settings_page_rpm_threshold_title: str = "每分钟任务数量阈值"
    basic_settings_page_rpm_threshold_content: str = (
        "每分钟执行的任务总数量的最大值，即 <font color='darkgoldenrod'><b>RPM</b></font> 阈值"
        "<br>"
        "部分平台会对网络请求的速率进行限制，请参考 API 平台的文档进行设置，0 = 无限制"
        ""
        ""
    )
    basic_settings_page_token_threshold_title: str = "任务长度阈值"
    basic_settings_page_token_threshold_content: str = "每个任务所包含的文本的最大 Token 数量"
    basic_settings_page_request_timeout_title: str = "超时时间阈值"
    basic_settings_page_request_timeout_content: str = (
        "发起请求时等待模型回复的最长时间（秒），超时仍未收到回复，则会判断为任务失败"
        ""
        ""
    )
    basic_settings_page_max_round_title: str = "任务轮次阈值"
    basic_settings_page_max_round_content: str = "当完成一轮任务后，将在新的轮次中对失败的任务进行重试，直到全部完成或达到轮次阈值"

    # 专家设置
    expert_settings_page_output_choices_title: str = "输出候选数据"
    expert_settings_page_output_choices_description: str = "在输出结果时包含候选数据以供校对使用，默认禁用"
    expert_settings_page_output_kvjson_title: str = "输出 KVJSON 文件"
    expert_settings_page_output_kvjson_description: str = "在输出结果时生成 KVJSON 格式的数据文件，默认禁用"

    # 质量类通用
    quality_import: str = "导入"
    quality_import_toast: str = "数据已导入 …"
    quality_export: str = "导出"
    quality_export_toast: str = "数据已导出 …"
    quality_save: str = "保存"
    quality_save_toast: str = "数据已保存 …"
    quality_merge_duplication: str = "已合并重复数据 …"
    quality_preset: str = "预设"
    quality_reset: str = "重置"
    quality_reset_toast: str = "数据已重置 …"
    quality_reset_alert: str = "是否确认重置为默认数据 … ？"
    quality_select_file: str = "选择文件"
    quality_select_file_type: str = "支持的数据格式 (*.json *.xlsx)"
    quality_delete_row: str = "删除行"
    quality_switch_regex: str = "切换正则模式"

    # 前置替换
    pre_replacement_page_head_title: str = "前置替换"
    pre_replacement_page_head_content: str = (
        "在任务开始前，将原文中匹配的部分替换为指定的文本，执行的顺序为从上到下依次替换"
        "<br>"
        "对于 <font color='darkgoldenrod'><b>RPGMaker MV/MZ</b></font> 引擎的游戏："
        "<br>"
        "• 导入游戏目录的 <font color='darkgoldenrod'><b>data</b></font> 或者 <font color='darkgoldenrod'><b>www\\data</b></font> 文件夹内的 <font color='darkgoldenrod'><b>actors.json</b></font> 文件可以将角色代码还原为明文"
    )
    pre_replacement_page_table_row_01: str = "原文"
    pre_replacement_page_table_row_02: str = "替换"
    pre_replacement_page_table_row_03: str = "正则"

    # 自定义提示词 - 中文
    custom_prompt_zh_page_head: str = "自定义中文提示词"
    custom_prompt_zh_page_head_desc: str = (
        "通过自定义提示词可以实现自定义的任务要求"
        "<br>"
        "注意：前缀与后缀部分固定不可修改，只有 <font color='darkgoldenrod'><b>译文语言设置为中文时</b></font> 才会使用本页中的自定义提示词"
        ""
        ""
    )

    # 自定义提示词 - 英文
    custom_prompt_en_page_head: str = "自定义英文提示词"
    custom_prompt_en_page_head_desc: str = (
        "通过自定义提示词可以实现自定义的任务要求"
        "<br>"
        "注意：前缀与后缀部分固定不可修改，只有 <font color='darkgoldenrod'><b>译文语言设置为非中文时</b></font> 才会使用本页中的自定义提示词"
        ""
        ""
    )