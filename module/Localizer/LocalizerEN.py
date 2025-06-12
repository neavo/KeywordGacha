from module.Localizer.LocalizerZH import LocalizerZH

class LocalizerEN(LocalizerZH):

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
    add: str = "Add"
    edit: str = "Edit"
    none: str = "None"
    back: str = "Back"
    next: str = "Next"
    stop: str = "Stop"
    start: str = "Start"
    timer: str = "Timer"
    close: str = "Close"
    alert: str = "Alert"
    warning: str = "Warning"
    confirm: str = "Confirm"
    cancel: str = "Cancel"
    auto: str = "Auto"
    wiki: str = "Wiki"
    open: str = "Open"
    select: str = "Select"
    inject: str = "Inject"
    filter: str = "Filter"
    search: str = "Search"
    generate: str = "Generate"
    placeholder: str = "Please enter keywords …"
    task_success: str = "Task succeeded …"
    alert_no_data: str = "No valid data …"
    alert_reset_timer: str = "Confirm to reset timer?"
    alert_reset_translation: str = "Confirm to reset translation task and start a new task?"

    # 主页面
    app_close_message_box: str = "Are you sure you want to exit the application … ?"
    app_new_version: str = "Download New Version!"
    app_new_version_toast: str = "New version found, version: {VERSION}. Please click the button on the bottom left to download and update …"
    app_new_version_update: str = "Downloading {PERCENT} …"
    app_new_version_failure: str = "New version download failed …"
    app_new_version_success: str = "New version download successful …"
    app_new_version_downloaded: str = "Click to apply New Version!"
    app_new_version_waiting_restart: str = "Update completed, application will close soon …"
    app_theme_btn: str = "Theme"
    app_language_btn: str = "Language"
    app_settings_page: str = "App Settings"
    app_platform_page: str = "API"
    app_project_page: str = "Project Settings"
    app_task_page: str = "Start Task"
    app_basic_settings_page: str = "Basic Settings"
    app_expert_settings_page: str = "Expert Settings"
    app_pre_replacement_page: str = "Pre-Replacement"
    app_custom_prompt_navigation_item: str = "Custom Prompts"
    app_custom_prompt_zh_page: str = "Chinese Prompts"
    app_custom_prompt_en_page: str = "English Prompts"

    # 路径
    path_bilingual: str = "bilingual"

    # 日志
    log_crash: str = "A critical error has occurred, app will now exit, error detail has been saved to the log file …"
    log_proxy: str = "Network proxy enabled …"
    log_expert_mode: str = "Expert Mode Enabled …"
    log_api_test_fail: str = "API test failed … "
    log_task_fail: str = "Task failed …"
    log_read_file_fail: str = "File reading failed …"
    log_write_file_fail: str = "File writing failed …"
    cli_verify_folder: str = "parameter error: invalid path …"
    cli_verify_language: str = "parameter error: invalid language …"

    # 引擎
    engine_no_items: str = "No items to process were found, please check …"
    engine_task_running: str = "Task is running, please try again later …"
    engine_task_done: str = "All data has been processed, task finished …"
    engine_task_fail: str = "Reached the maximum task rounds, but some data remains unprocessed. Please check the results …"
    engine_task_stop: str = "Task stopped …"
    engine_task_save: str = "Generating output file, please wait …"
    engine_task_save_done: str = "Task results have been saved to the {PATH} directory …"
    engine_task_generation: str = "Task generation completed, {COUNT} tasks generated in total …"
    engine_task_rule_filter: str = "Rule filtering completed, {COUNT} entries that do not require translation were filtered in total …"
    engine_task_language_filter: str = "Language filtering completed, {COUNT} entries not containing the target language were filtered in total …"
    engine_task_context_search: str = "Context searhing completed, {COUNT} entries were processed in total …"
    engine_max_round: str = "Max Rounds"
    engine_current_round: str = "Current Round"
    engine_api_url: str = "API URL"
    engine_api_name: str = "API Name"
    engine_api_model: str = "API Model"
    engine_response_think: str = "Model Thinking:"
    engine_response_result: str = "Model Response:"
    engine_task_success: str = "Task time {TIME} seconds, {LINES} lines of text, input tokens {PT}, output tokens {CT}"
    engine_task_too_many: str = "Too many real-time tasks, details hidden for performance …"
    api_tester_key: str = "Testing Key:"
    api_tester_messages: str = "Task Prompts:"
    api_tester_result: str = "Tested {COUNT} APIs in total, {SUCCESS} successful, {FAILURE} failed …"
    api_tester_result_failure: str = "Failed Keys:"
    api_tester_running: str = "Task is running, please try again later …"
    ner_output_log_src: str = "Original: "
    ner_output_log_dst: str = "Translation: "
    ner_output_log_dst_choices: str = "Translation Choices:"
    ner_output_log_info: str = "Infomation: "
    ner_output_log_info_choices: str = "Infomation Choices: "
    ner_output_log_count: str = "Count: "
    ner_output_log_context: str = "Context: "

    # 应用设置
    app_settings_page_expert_title: str = "Expert Mode"
    app_settings_page_expert_content: str = "Enabling this feature will display more log information and provide more advanced setting options (takes effect after app restart)"
    app_settings_page_font_hinting_title: str = "Font Hinting"
    app_settings_page_font_hinting_content: str = "Enabling this feature will render the edges of UI fonts more smoothly (takes effect after app restart)"
    app_settings_page_scale_factor_title: str = "Global Scale Factor"
    app_settings_page_scale_factor_content: str = "Enabling this feature will scale the app interface according to the selected ratio (takes effect after app restart)"
    app_settings_page_proxy_url: str = "Example - http://127.0.0.1:7890"
    app_settings_page_proxy_url_title: str = "Network Proxy"
    app_settings_page_proxy_url_content: str = "Enabling this feature will use the set proxy address to send network requests  (takes effect after app restart)"
    app_settings_page_close: str = "The application will close, please confirm …"

    # 接口管理
    platform_page_api_test_result: str = "API test result: {SUCCESS} successful, {FAILURE} failed …"
    platform_page_api_activate: str = "Activate API"
    platform_page_api_edit: str = "Edit API"
    platform_page_api_args: str = "Edit Arguments"
    platform_page_api_test: str = "Test API"
    platform_page_api_delete: str = "Delete API"
    platform_page_widget_add_title: str = "API List"
    platform_page_widget_add_content: str = "Add and manage any LLM API compatible with Google, OpenAI and Anthropic formats here"

    # 接口编辑
    platform_edit_page_name: str = "Please enter API name …"
    platform_edit_page_name_title: str = "API Name"
    platform_edit_page_name_content: str = "Please enter API name, only for display within the app, no practical effect"
    platform_edit_page_api_url: str = "Please enter API URL …"
    platform_edit_page_api_url_title: str = "API URL"
    platform_edit_page_api_url_content: str = "Please enter API URL, pay attention to whether /v1 needs to be added at the end"
    platform_edit_page_api_key: str = "Please enter API Key …"
    platform_edit_page_api_key_title: str = "API Key"
    platform_edit_page_api_key_content: str = "Please enter API Key, e.g., sk-d0daba12345678fd8eb7b8d31c123456. Multiple keys can be entered for polling, one key per line"
    platform_edit_page_thinking_title: str = "Use Thinking Mode First"
    platform_edit_page_thinking_content: str = "For models both thinking mode and normal mode, prioritize using thinking mode"
    platform_edit_page_model: str = "Please enter Model Name …"
    platform_edit_page_model_title: str = "Model Name"
    platform_edit_page_model_content: str = "Current model in use: {MODEL}"
    platform_edit_page_model_edit: str = "Manual Input"
    platform_edit_page_model_sync: str = "Fetch Online"

    # 参数编辑
    args_edit_page_top_p_title: str = "top_p"
    args_edit_page_top_p_content: str = "Please set with caution, incorrect values may cause abnormal results or request errors"
    args_edit_page_temperature_title: str = "temperature"
    args_edit_page_temperature_content: str = "Please set with caution, incorrect values may cause abnormal results or request errors"
    args_edit_page_presence_penalty_title: str = "presence_penalty"
    args_edit_page_presence_penalty_content: str = "Please set with caution, incorrect values may cause abnormal results or request errors"
    args_edit_page_frequency_penalty_title: str = "frequency_penalty"
    args_edit_page_frequency_penalty_content: str = "Please set with caution, incorrect values may cause abnormal results or request errors"
    args_edit_page_document_link: str = "Click to view documentation"

    # 模型列表
    model_list_page_title: str = "Available Model List"
    model_list_page_content: str = "Click to select the model to use"
    model_list_page_fail: str = "Failed to get model list, please check API configuration …"

    # 项目设置
    project_page_source_language_title: str = "Source Language"
    project_page_source_language_content: str = "Set the language of the input text in the current project"
    project_page_target_language_title: str = "Target Language"
    project_page_target_language_content: str = "Set the language of the output text in the current project"
    project_page_input_folder_title: str = "Input Folder"
    project_page_input_folder_content: str = "The current input folder is"
    project_page_output_folder_title: str = "Output Folder (Can not be same as input folder)"
    project_page_output_folder_content: str = "The current output folder is"
    project_page_output_folder_open_on_finish_title: str = "Open Output Folder on Task Completion"
    project_page_output_folder_open_on_finish_content: str = "When enabled, the output folder will be automatically opened upon task completion"
    project_page_traditional_chinese_title: str = "Output Chinese in Traditional Characters"
    project_page_traditional_chinese_content: str = "When enabled, Chinese text will be output in Traditional characters if the target language is set to Chinese"

    # 开始翻译
    task_page_status_idle: str = "Idle"
    task_page_status_testing: str = "Testing"
    task_page_status_nering: str = "Extracting"
    task_page_status_stopping: str = "Stopping"
    task_page_indeterminate_saving: str = "Saving cache …"
    task_page_indeterminate_stoping: str = "Stopping task …"
    task_page_card_time: str = "Elapsed Time"
    task_page_card_remaining_time: str = "Remaining Time"
    task_page_card_line: str = "Processed Lines"
    task_page_card_remaining_line: str = "Remaining Lines"
    task_page_card_speed: str = "Average Speed"
    task_page_card_token: str = "Total Tokens"
    task_page_card_task: str = "Real Time Tasks"
    task_page_alert_pause: str = "Stopped tasks can be resumed at any time. Confirm to stop the task … ?"
    task_page_continue: str = "Continue Task"
    task_page_export: str = "Export Task Data"
    task_page_timer: str = "Waiting time before delayed startup"

    # 基础设置
    basic_settings_page_max_workers_title: str = "Concurrent Task Threshold"
    basic_settings_page_max_workers_content: str = (
        "Maximum number of tasks executing simultaneously"
        "<br>"
        "Proper configuration can significantly speed up task completion"
        "<br>"
        "Please refer to the API platform's documentation for settings, 0 = Automatic"
    )
    basic_settings_page_rpm_threshold_title: str = "Requests Per Minute Threshold"
    basic_settings_page_rpm_threshold_content: str = (
        "Maximum total number of tasks executed per minute, i.e., the <font color='darkgoldenrod'><b>RPM</b></font> threshold"
        "<br>"
        "Some platforms may limit the request rate"
        "<br>"
        "Please refer to the API platform's documentation for settings, 0 = unlimited"
    )
    basic_settings_page_token_threshold_title: str = "Task Length Threshold"
    basic_settings_page_token_threshold_content: str = "The maximum number of text tokens contained in each task"
    basic_settings_page_request_timeout_title: str = "Request Timeout"
    basic_settings_page_request_timeout_content: str = (
        "The maximum time (seconds) to wait for the model's response when making a request"
        "<br>"
        "If no reply is received after the timeout, the task will be considered failed"
    )
    basic_settings_page_max_round_title: str = "Maximum Rounds"
    basic_settings_page_max_round_content: str = "After completing a round of tasks, failed tasks will be retried in a new round until all are completed or the round threshold is reached"

    # 专家设置
    expert_settings_page_output_choices_title: str = "Output Choices Data"
    expert_settings_page_output_choices_description: str = "Include choices data in the output for proofreading, disabled by default"
    expert_settings_page_output_kvjson_title: str = "Output KVJSON File"
    expert_settings_page_output_kvjson_description: str = "Generate KVJSON format data file when outputting results, disabled by default"

    # 质量类通用
    quality_import: str = "Import"
    quality_import_toast: str = "Data imported …"
    quality_export: str = "Export"
    quality_export_toast: str = "Data exported …"
    quality_save: str = "Save"
    quality_save_toast: str = "Data saved …"
    quality_merge_duplication: str = "Duplicate data merged …"
    quality_preset: str = "Preset"
    quality_reset: str = "Reset"
    quality_reset_toast: str = "Data reset …"
    quality_reset_alert: str = "Confirm reset to default data … ?"
    quality_select_file: str = "Select File"
    quality_select_file_type: str = "Support Format (*.json *.xlsx)"
    quality_delete_row: str = "Delete Row"
    quality_switch_regex: str = "Regex Switch"

    # 前置替换
    pre_replacement_page_head_title: str = "Pre-Replacement"
    pre_replacement_page_head_content: str = (
        "Before the task begins, matched parts of the original text will be replaced by specified text, processed in top-down order"
        "<br>"
        "For games using the <font color='darkgoldenrod'><b>RPGMaker MV/MZ</b></font> engine:"
        "<br>"
        "• Importing the <font color='darkgoldenrod'><b>actors.json</b></font> file from the <font color='darkgoldenrod'><b>data</b></font> or <font color='darkgoldenrod'><b>www\\data</b></font> folder in the game directory can restore actor codes to plain text"
    )
    pre_replacement_page_table_row_01: str = "Original"
    pre_replacement_page_table_row_02: str = "Replacement"
    pre_replacement_page_table_row_03: str = "Regex"

    # 自定义提示词 - 中文
    custom_prompt_zh_page_head: str = "Custom Chinese Prompts (SakuraLLM model not supported)"
    custom_prompt_zh_page_head_desc: str = (
        "Add extra translation requirements such as story settings and writing styles via custom prompts"
        "<br>"
        "Note: The prefix and suffix are fixed and cannot be modified"
        "<br>"
        "The custom prompts on this page will only be used when the <font color='darkgoldenrod'><b>translation language is set to Chinese</b></font>"
    )

    # 自定义提示词 - 英文
    custom_prompt_en_page_head: str = "Custom English Prompts (SakuraLLM model not supported)"
    custom_prompt_en_page_head_desc: str = (
        "Add extra translation requirements such as story settings and writing styles via custom prompts"
        "<br>"
        "Note: The prefix and suffix are fixed and cannot be modified"
        "<br>"
        "The custom prompts on this page will only be used when the <font color='darkgoldenrod'><b>translation language is set to non-Chinese</b></font>"
    )