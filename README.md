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
- 使用 [DeepSeek - 点击查看教程](https://github.com/neavo/KeywordGacha/wiki/DeepSeek) 处理一本书只要 `几毛钱` + `一分钟`
- 也可以通过运行 [一键包 - 点击查看教程](https://github.com/neavo/KeywordGachaServer) 来获得 `完全免费` 的服务（需要 8G 以上显存的 Nvidia 显卡）

## 使用流程 🛸
- 从 [发布页](https://github.com/neavo/KeywordGacha/releases) 或 [百度网盘](https://pan.baidu.com/s/1_JXmKvnar6PGHlIbl0Mi2Q?pwd=9e54) 下载应用
- 打开配置文件 `config.json`，填入 API 信息，默认为使用本地接口
- 双击 `01_启动.bat` 启动应用，处理流程结束后，结果会保存在 `output` 文件夹内
- 其中：
  - `*_日志.txt` - 抓取到的词语的原文、上下文、翻译建议、角色信息总结等详细信息，用于人工确认
  - `*_列表.json` - 通用词表，可以导入 [AiNiee - 替换词典](https://github.com/NEKOparapa/AiNiee)、[绿站 - 术语表](https://books.fishhawk.top/workspace/katakana) 等处使用
  - `*_ainiee.json` - [AiNiee - 提示字典](https://github.com/NEKOparapa/AiNiee) 功能专用词语表
  - `*_galtransl.json` - [GalTransl - GPT 字典](https://github.com/xd2333/GalTransl) 功能专用词语表

## 应用效果 ⚡
- `抓取`、`分析` 和 `翻译` 效果取决于模型的能力，使用 💪 ~~更昂贵~~ 更强力  的模型可以显著提升效果
- 是的，氪金可以变强
- 总体来说 `在线接口` 的效果和速度都远好于 `本地接口`，建议使用 `在线接口` 

## 文本格式 🏷️
- 支持从 `.txt`、`.csv`、`.json` 三种文件中读取文本
- 大部分主流的 `小说` 和 `游戏脚本` 数据格式都可以直接或者通过转换被 KG 识别
- 输入路径是文件夹时，会读取文件夹内所有的 `.txt`、`.csv` 和 `.json` 文件
- 当应用目录下有 `input` 文件夹时，会自动读取 `input` 内所有的 `.txt`、`.csv` 和 `.json` 文件
- 具体可见 [Wiki - 支持的文件格式](https://github.com/neavo/KeywordGacha/wiki/%E6%94%AF%E6%8C%81%E7%9A%84%E6%96%87%E4%BB%B6%E6%A0%BC%E5%BC%8F)

## 近期更新 📅
- 20240925 v0.5.1
  - 修正 - 接口测试功能不能执行的问题

- 20240921 v0.5.0
  - 新增 - 快速模式
    - 可以节约一半左右的 `时间` 和 `Token`
    - 不执行 `语义分析` 步骤，所以无法提供 `角色性别` 与 `故事总结`
  - 调整 - 使用本地接口时，自动设置请求频率阈值
  - 调整 - 模型版本更新至 `kg_ner_20240912`

- 20240909 v0.4.1
  - 调整 - 优化规则以尝试减少结果中的杂质
    - 更严格的 `Prompt`
    - 更严格的 `上下文` 与 `出现次数` 的匹配规则
    - 在不同测试用例中，减少了 `20%-40%` 不等的角色实体杂质
  - 修正 - 一些常见的 JSON 解析错误
  - 修正 - 汉字词语翻译时偶尔翻译成拼音的问题

- 20240826 v0.4.0
  - 新增 - 初步完成对 `韩文` 的支持
    - 完全不懂 `韩文`，所以无法评估表现水平
    - 寻求懂 `韩文` 的用户协助测试
  - 调整 - 优化了 NER 实体识别步骤的执行速度
    - `CPU` 和 `GPU` 版本都提速了一倍左右

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
    "translate_context_per": [
        1,
        "是否翻译人名实体上下文，1 - 翻译，0 - 不翻译，比较慢，根据需求自己决定是否开启。"
    ],
    "translate_context_other": [
        0,
        "是否翻译其他实体上下文，1 - 翻译，0 - 不翻译，比较慢，根据需求自己决定是否开启。"
    ]
}
```
## 常见问题 📥
- 处理 `小说` 时
  - 注意单行不要太长
  - 目前模型能处理的单行最大长度约为500字，过长的句子会被截断

- 处理 `游戏文本` 时
  - 建议使用 [SExtractor](https://github.com/satan53x/SExtractor) 、[Translator++](https://dreamsavior.net/translator-plusplus/) 导出的文本
  - [MTool](https://afdian.com/a/AdventCirno) 导出的文本抓取效果很不稳定
  - 如果抓取效果不好，可以多试几种导出工具和导出格式，往往会有奇效

## 开发计划 📈
- [x] 支持 [Translator++](https://dreamsavior.net/translator-plusplus/) 导出的 CSV 文本
- [X] 添加 对 组织、道具、地域 等其他名词类型的支持
- [X] 添加 对 `英文内容` 的支持
- [X] 添加 对 `中文内容` 的支持
- [X] 添加 对 `韩文内容` 的支持
- [ ] 添加 对 `俄文内容` 的支持
- [X] 添加 对 GPU 加速的支持
- [X] 添加 全自动生成模式

## 问题反馈 😥
- 运行时的日志保存在程序目录下的 `KeywordGacha.log` 等日志文件内
- 反馈问题的时候请附上这些日志文件
