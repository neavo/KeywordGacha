<h1><p align='center' >KeywordGacha</p></h1>
<div align=center><img src="https://img.shields.io/github/v/release/neavo/KeywordGacha"/>   <img src="https://img.shields.io/github/license/neavo/KeywordGacha"/>   <img src="https://img.shields.io/github/stars/neavo/KeywordGacha"/></div>
<p align='center'>使用 AI 能力分析 小说、游戏、字幕 等文本内容并生成术语表的次世代翻译辅助工具</p>


&ensp;
&ensp;


## 概述 📢
- [KeywordGacha](https://github.com/neavo/KeywordGacha)，简称 KG，使用 AI 技术来自动生成 `实体词语表` 的次世代工具
- `实体词语表` 可以在一定程度上解决在长篇文本翻译过程中 `人名` 等实体词语翻译版本不统一的问题
- 根据 `中、英、日、韩` 文本内容自动生成 `实体词语表`，并且 `自动翻译`、`自动总结`、`自动分析`
- 相较传统工具，具有高命中、语义化、智能总结角色信息等特色，对文本的兼容性更好
- 极大的提升 `小说`、`漫画`、`字幕`、`游戏文本` 等内容译前准备时制作词语表的工作效率
- 随机选取 [绿站榜单作品](https://books.fishhawk.top) 作为测试样本，与人工校对制作的词表对比，命中率约为 `80%-90%`

> <img src="image/01.jpg" style="width: 80%;" alt="image/01.jpg">

> <img src="image/02.jpg" style="width: 80%;" alt="image/02.jpg">

## 特别说明 ⚠️
- 如您在翻译过程中使用了 [KeywordGacha](https://github.com/neavo/KeywordGacha)，请在作品信息或发布页面的显要位置进行说明！
- 如您的项目涉及任何商业行为或者商业收益，在使用 [KeywordGacha](https://github.com/neavo/KeywordGacha) 前，请先与作者联系以获得授权！

## 配置要求 🖥️
- 兼容 `OpenAI` 标准的 AI 大模型接口
- 兼容 [LinguaGacha](https://github.com/neavo/LinguaGacha) `使用 AI 能力一键翻译小说、游戏、字幕的次世代文本翻译器` 👈👈
- 注意，`SakuraLLM` 系列模型只具有翻译功能，无法进行文本分析，不能与 `KG` 配合使用

## 使用流程 🛸
- 从 [发布页](https://github.com/neavo/KeywordGacha/releases) 或 [百度网盘](https://pan.baidu.com/s/1_JXmKvnar6PGHlIbl0Mi2Q?pwd=9e54) 下载应用
- 打开配置文件 `config.json`，填入 API 信息，推荐在以下两种方式中选择其一：
  - [DeepSeek - 点击查看教程](https://github.com/neavo/KeywordGacha/wiki/DeepSeek)，需付费但便宜，速度快，质量高，无显卡要求 `👈👈 推荐`
  - [本地接口 - 点击查看教程](https://github.com/neavo/OneClickLLAMA)，免费，速度较慢，质量稍差，理论上支持所有 8G 以上显存的显卡
- 双击 `app.exe` 启动应用，处理流程结束后，结果会保存在 `output` 文件夹内
- 其中：
  - `*_日志.txt` - 抓取到的词语的原文、参考文本、翻译建议、角色信息总结等详细信息，用于人工确认
  - `*_列表.json` - 通用词表，可以导入 [LinguaGacha 译前替换](https://github.com/neavo/LinguaGacha) 等处使用
  - `*_术语表.json` - [LinguaGacha 术语表](https://github.com/neavo/LinguaGacha) 功能专用词语表
  - `*_galtransl.json` - [GalTransl GPT 字典](https://github.com/xd2333/GalTransl) 功能专用词语表
- 遵循 [常见问题](https://github.com/neavo/KeywordGacha#%E5%B8%B8%E8%A7%81%E9%97%AE%E9%A2%98-) 里的建议以获得最佳的使用效果

## 文本格式 🏷️
- 在任务开始时，`KG` 将读取指定的文件或文件夹（及其子目录）内所有支持的文件，包括但是不限于：
  - 字幕（.srt .ass）
  - 电子书（.txt .epub）
  - [RenPy](https://www.renpy.org) 导出游戏文本（.rpy）
  - [MTool](https://afdian.com/a/AdventCirno) 导出游戏文本（.json）
  - [SExtractor](https://github.com/satan53x/SExtractor) 导出游戏文本（.txt .json .xlsx）
  - [Translator++](https://dreamsavior.net/translator-plusplus) 导出游戏文本（.csv .xlsx）
- 当应用目录下有 `input` 文件夹时，将自动识别 `input` 文件夹内的文件
- 更多格式将持续添加，你也可以在 [ISSUES](https://github.com/neavo/KeywordGacha/issues) 中提出你的需求

## 近期更新 📅
- 20250218 v0.12.1
  - 细节优化与修正 

- 20250214 v0.12.0
  - 调整 增强对姓名代码的识别能力
  - 调整 重新设计了文件读取流程，现在：

- 20250211 v0.11.3
  - 细节优化与修正 

- 20250201 v0.11.2
  - 优化 韩文 分析能力
  - 优化 CPU 模式的兼容性
  - 优化 支持 DeepSeek-R1 等思考模型
  - 修正 一些兼容性问题
  - 感谢不愿透露姓名的 @PiDanShouRouZhouXD 同学提供本次模型更新的训练算力支持

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
        2,
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
    "context_translate_mode": [
        2,
        "是否翻译参考文本，0 - 不翻译，1 - 全部翻译，2 - 只翻译角色实体"
    ]
}
```
## 常见问题 📥
- 分析 `小说文本` 的最佳实践
  - 提前移除 `作者评论`、`出版社信息` 等与故事内容无关的文本
  - 目前模型能处理的单行最大长度约为 `500` 字，过长的句子会被截断，超长单行文本请提前手动分行

- 处理 `游戏文本` 的最佳实践
  - 使用 [Translator++](https://dreamsavior.net/translator-plusplus/) 导出游戏文本为 `xlsx` 格式
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
