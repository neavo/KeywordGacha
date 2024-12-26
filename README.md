<h1><p align='center' >KeywordGacha</p></h1>
<div align=center><img src="https://img.shields.io/github/v/release/neavo/KeywordGacha"/>   <img src="https://img.shields.io/github/license/neavo/KeywordGacha"/>   <img src="https://img.shields.io/github/stars/neavo/KeywordGacha"/></div>
<p align='center'>使用 OpenAI 兼容接口自动生成小说、漫画、字幕、游戏脚本等内容文本中实体词语表的翻译辅助工具</p>

&ensp;
&ensp;


## 概述 📢
- [KeywordGacha](https://github.com/neavo/KeywordGacha)，简称 KG，使用 AI 技术来自动生成 `实体词语表` 的次世代工具
- `实体词语表` 可以在一定程度上解决在长篇文本翻译过程中 `人名` 等实体词语翻译版本不统一的问题
- 根据 `中、英、日、韩` 文本内容自动生成 `实体词语表`，并且 `自动翻译`、`自动总结`、`自动分析`
- 相较传统工具，具有高命中、语义化、智能总结角色信息等特色，对文本的兼容性更好
- 极大的提升 `小说`、`漫画`、`字幕`、`游戏脚本` 等内容译前准备时制作词语表的工作效率
- 随机选取 [绿站榜单作品](https://books.fishhawk.top) 作为测试样本，与人工校对制作的词表对比，命中率约为 `80%-90%`

> <img src="image/01.jpg" style="width: 80%;" alt="image/01.jpg">

> <img src="image/02.jpg" style="width: 80%;" alt="image/02.jpg">

## 特别说明 ⚠️
- 如您在翻译过程中使用了 [KeywordGacha](https://github.com/neavo/KeywordGacha)，请在作品信息或发布页面的显要位置进行说明！

## 配置要求 🖥️
- 兼容 OpenAI 标准的 AI 大模型接口
- 注意，`SakuraLLM` 系列模型只具有翻译功能，无法进行文本分析，不能与 `KG` 配合使用

## 使用流程 🛸
- 从 [发布页](https://github.com/neavo/KeywordGacha/releases) 或 [百度网盘](https://pan.baidu.com/s/1_JXmKvnar6PGHlIbl0Mi2Q?pwd=9e54) 下载应用
- 打开配置文件 `config.json`，填入 API 信息，推荐在以下两种方式中选择其一：
  - [DeepSeek - 点击查看教程](https://github.com/neavo/KeywordGacha/wiki/DeepSeek)，需付费但便宜，速度快，质量高，无显卡要求 `👈👈 推荐`
  - [本地接口 - 点击查看教程](https://github.com/neavo/KeywordGachaServer)，免费，速度较慢，质量稍差，理论上支持所有 4G 以上显存的显卡
- 双击 `01_启动.bat` 启动应用，处理流程结束后，结果会保存在 `output` 文件夹内
- 其中：
  - `*_日志.txt` - 抓取到的词语的原文、上下文、翻译建议、角色信息总结等详细信息，用于人工确认
  - `*_列表.json` - 通用词表，可以导入 [AiNiee - 替换词典](https://github.com/NEKOparapa/AiNiee)、[绿站 - 术语表](https://books.fishhawk.top/workspace/katakana) 等处使用
  - `*_ainiee.json` - [AiNiee - 提示字典](https://github.com/NEKOparapa/AiNiee) 功能专用词语表
  - `*_galtransl.json` - [GalTransl - GPT 字典](https://github.com/xd2333/GalTransl) 功能专用词语表
- 遵循 [常见问题](https://github.com/neavo/KeywordGacha#%E5%B8%B8%E8%A7%81%E9%97%AE%E9%A2%98-) 里的建议以获得最佳的使用效果

## 文本格式 🏷️
- 支持从 `.txt`、`.csv`、`.json`、`.xlsx` 文件中读取文本
- 大部分主流的 `小说` 和 `游戏脚本` 数据格式都可以直接或者通过转换被 `KG` 识别
- 输入路径是文件夹时，会读取文件夹内所有的 `.txt`、`.csv` 、`.json` 和 `.xlsx` 文件
- 当应用目录下有 `input` 文件夹时，会自动读取 `input` 内所有的 `.txt`、`.csv` 、`.json` 和 `.xlsx` 文件
- 具体可见 [支持的文件格式](https://github.com/neavo/KeywordGacha/wiki/%E6%94%AF%E6%8C%81%E7%9A%84%E6%96%87%E4%BB%B6%E6%A0%BC%E5%BC%8F)

## 近期更新 📅
- 20241226 v0.8.2
  - 一些细节优化
  
- 20241218 v0.8.1
  - 重新设计了工作流程，得益于此：
    - 英文与韩文分析能力强化
    - 非角色类实体分析能力显著强化
    - 较大幅度的减少了 `时间` 与 `Token` 消耗
  - 配套本地模型切换至 `Qwen2.5-7B`，使用本地模型的同学请一并更新 -> [KeywordGachaServer](https://github.com/neavo/KeywordGachaServer)

- 20241213 v0.7.0
  - 分析能力提升，主要来自于：
    - NER 模型更新
    - 参考文本匹配机制优化

## 设置说明 🎚️

```json
{
    "api_key": [
        "no_key_required",
        "接口密钥，从接口平台方获取，使用在线接口时一定要设置正确。"
    ],
    "base_url": [
        "http://localhost:8080/v1",
        "请求地址，从接口平台方获取，使用在线接口时一定要设置正确。"
    ],
    "model_name": [
        "no_name_required",
        "模型名称，从接口平台方获取，使用在线接口时一定要设置正确。"
    ],
    "count_threshold": [
        1,
        "出现次数阈值，出现次数低于此值的词语会被过滤掉以节约时间。"
    ],
    "request_timeout": [
        180,
        "网络请求超时时间，如果频繁出现 timeout 字样的网络错误，可以调大这个值。"
    ],
    "request_frequency_threshold": [
        3,
        "网络请求频率阈值，单位为 次/秒，值可以小于 1，如果频繁出现 429 代码的网络错误，可以调小这个值。",
        "使用 llama.cpp 运行的本地模型时，将根据 llama.cpp 的配置调整自动设置，无需手动调整这个值。",
        "使用 DeepSeek 等不限制并发数的在线接口时可以调大这个值。"
    ],
    "context_translate_per": [
        1,
        "是否翻译人名实体上下文，1 - 翻译，0 - 不翻译，比较慢，根据需求自己决定是否开启。"
    ],
    "context_translate_other": [
        0,
        "是否翻译其他实体上下文，1 - 翻译，0 - 不翻译，比较慢，根据需求自己决定是否开启。"
    ]
}
```
## 常见问题 📥
- 分析 `小说文本` 的最佳实践
  - 提前移除 `作者评论`、`出版社信息` 等与故事内容无关的文本
  - 目前模型能处理的单行最大长度约为 `500` 字，过长的句子会被截断，超长单行文本请提前手动分行

- 处理 `游戏文本` 的最佳实践
  - 使用 [Translator++](https://dreamsavior.net/translator-plusplus/) 导出游戏文本为 `csv` 或 `xlsx` 格式
  - 对于 `RPGMaker MV/MZ` 游戏
    - 复制 `Actors.json` 到指定位置以启用 [角色代码还原](https://github.com/neavo/KeywordGacha/wiki/%E8%A7%92%E8%89%B2%E4%BB%A3%E7%A0%81%E8%BF%98%E5%8E%9F) 功能
  - 如果抓取效果不好，可以多试几种导出工具和导出格式，有时候会有奇效

## 开发计划 📈
- [X] 添加 对 `英文内容` 的支持
- [X] 添加 对 `中文内容` 的支持
- [X] 添加 对 `韩文内容` 的支持
- [ ] 添加 对 `俄文内容` 的支持

## 问题反馈 😥
- 运行时的日志保存在程序目录下的 `*.log` 等日志文件内
- 反馈问题的时候请附上这些日志文件
