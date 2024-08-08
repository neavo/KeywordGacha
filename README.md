<h1><p align='center' >KeywordGacha</p></h1>
<div align=center><img src="https://img.shields.io/github/v/release/neavo/KeywordGacha"/>   <img src="https://img.shields.io/github/license/neavo/KeywordGacha"/>   <img src="https://img.shields.io/github/stars/neavo/KeywordGacha"/></div>
<p align='center' >使用 OpenAI 兼容接口自动生成小说、漫画、字幕、游戏脚本等任意文本中的词语表的翻译辅助工具</p>

&ensp;
&ensp;


## 概述 📢
- [KeywordGacha](https://github.com/neavo/KeywordGacha)，简称 KG，使用 AI 技术来自动生成文本中词语表的次世代工具
- 从长篇文本中一键 `抓取实体词语`、`自动翻译`、`自动总结`
- 相较传统工具，具有高命中、语义化、智能总结角色信息等特色，对文本的兼容性更好
- 极大的提升 `小说`、`漫画`、`字幕`、`游戏脚本` 等内容译前准备时制作词语表的工作效率
- 随机选取 [绿站榜单作品](https://books.fishhawk.top) 作为测试样本，与人工校对制作的词表对比，命中率约为 `80%-90%`

> <img src="image/01.jpg" style="width: 80%;" alt="image/01.jpg">

> <img src="image/02.jpg" style="width: 80%;" alt="image/02.jpg">
  
## 要求 🖥️
- 兼容所有 OpenAI 标准的 AI 大模型接口
- 可以使用 ChatGPT 系列、Claude 系列 或 众多国产模型 接口
- 也可以运行 `本地模型` 来获得 `完全免费` 的服务（需要 8G 以上显存的 Nvidia 显卡）

## 使用流程 🛸
- 从 [发布页](https://github.com/neavo/KeywordGacha/releases) 下载 `KeywordGacha_DEV_*.zip` 并本地并解压缩
- 打开配置文件 `config.json` ，填入 API 信息，如使用本地接口则不需要修改
- [可选] Nvidia 显卡用户双击 `02_启用应用内GPU加速` 启用 GPU 加速
- 双击 `01_启动.bat`，按提示操作即可
- 流程执行完毕后，会生成类似于 `角色实体_日志.txt` 与 `角色实体_列表.json` 的结果文件
- `*_日志.txt` 中包含抓取到的词语的原文、上下文、翻译建议、角色信息总结等信息
- 参考日志中的信息完成 `*_列表.json` 后，可以直接导入到 [AiNiee](https://github.com/NEKOparapa/AiNiee) 等翻译器中使用

## 抓取效果 ⚡
- `抓取`、`总结` 和 `翻译` 效果取决于模型的能力，使用 💪 ~~更昂贵~~ 更强力  的模型可以显著提升效果
- 是的，氪金可以变强
- 各家的旗舰模型的如 [GPT4o](https://chatgpt.com/)、[Claude 3.5 Sonnet](https://claude.ai/) 效果十分好
- 本地小模型的效果也还不错
- 总体来说在线接口的效果远好于本地模型，推荐使用在线模型，便宜的就行
- 在本页后续的 `傻瓜教程 📖` 章节中有使用 `在线模型 `和 `本地模型` 的相关教程

## 近期更新 📅
- 20240808
  - 新增 - 接口测试 功能
  - 新增 - 非人名实体上下文翻译 功能，默认关闭
  - 调整 - NER 模型更新，抓取能力显著强化
    - 特别是对非角色实体的抓取能力
  - 调整 - 处理速度优化
    - 优化了 `语义分析` 的流程，用更少的步骤达到了更好的效果，速度 +100%
    - 在 Nvidia 显卡上可以启用 GPU 加速了，`NER 实体识别` 步骤，速度 +500%

- 20240724
  - 调整 - 现在三种格式都可以从文件夹中批量读取了
  - 修正 - 出现次数为 0 导致的除数问题

- 20240720
  - 调整 - 现在词语翻译会自动填充到列表文件中了
  - 调整 - 优化 NER 模型 与 校验步骤，继续提升抓取能力
  - 调整 - 优化后的 增强模式 已经足够快了，所以移除了原本的 快速模式

- 20240716
  - 新增 - 对组织、物品等其他实体种类的识别

- 20240716
  - 调整 - 继续优化抓取能力
  - 调整 - 一些样式和兼容性调整
  - 新增 - 网络请求频率阈值 设置选项

- 20240712
  - 调整 - 使用了新的 NER 分词前端，处理速度和命中率有了显著的提升
    - 随机选取 [绿站榜单作品](https://books.fishhawk.top) 作为测试样本，与人工校对制作的词表对比
    - 命中率约为 `80%-90%`
    - 现在 `快速模式` 也可以处理纯汉字词语了

## 文本格式 🏷️
- 目前支持三种不同的输入文本格式
- 对文本内容没什么要求，`小说` 、`字幕`、`游戏脚本` 等都可以直接读取
- 文件中 每一行/每一条 的长度不要超过500字，太长的话请先手动处理一下
- 输入路径是文件夹时，会读取文件夹内所有的 `txt`、`csv` 和 `json` 文件
- 当前目录下有 `data 文件夹` 、`all.orig.txt` 或 `ManualTransFile.json` 文件，会自动识别

## 格式示例 📑
- 当文件后缀名为 .json 时，会将其内容按以下模式处理，这也是 [MTool](https://afdian.net/a/AdventCirno) 导出翻译原文的格式

```json
  {
      "原文": "译文",
      "原文": "译文",
      "原文": "译文"
  }
```

- 当文件后缀名为 .txt 时，会将其内容按以下模式处理，即每行一句的纯文本内容，使用 [SExtractor](https://github.com/satan53x/SExtractor) 可以抓取这样的文本
  
```
      原文<换行符>
      原文<换行符>
      原文<换行符>
```

- 当路径为一个文件夹时，会读取其内所有的 .csv 文件中每一行的第一列，使用 [Translator++](https://dreamsavior.net/translator-plusplus/) 可以抓取这样的文本
  
```csv
      原文,<无视剩下的列>
      原文,<无视剩下的列>
      原文,<无视剩下的列>
```

## 设置说明 🎚️

```json
{
    "api_key": [
        "sk-no-key-required",
        "接口密钥，从接口平台方获取，使用在线接口时一定要设置正确。"
    ],
    "base_url": [
        "http://localhost:8080/v1",
        "请求地址，从接口平台方获取，使用在线接口时一定要设置正确。"
    ],
    "model_name": [
        "glm-4-9b-chat",
        "模型名称，从接口平台方获取，使用在线接口时一定要设置正确。"
    ],
    "count_threshold": [
        3,
        "出现次数阈值，出现次数低于此值的词语会被过滤掉，调低它可以抓取更多低频词语。"
    ],
    "request_timeout": [
        180,
        "网络请求超时时间，如果频繁出现 timeout 字样的网络错误，可以调大这个值。"
    ],
    "request_frequency_threshold": [
        4,
        "网络请求频率阈值，单位为 次/秒，值可以小于 1，如果频繁出现 429 代码的网络错误，可以调小这个值，特别很多便宜的中转。",
        "使用 DeepSeeker 等不限制并发数的接口可以调大，可以极大的加快处理的速度。"
    ],
    "translate_surface": [
        1,
        "是否翻译词语，1 - 翻译，0 - 不翻译，启用词语翻译后会自动完成词表。"
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

## 傻瓜教程 📖
- [推荐 👏] 如果愿意出一点小钱（一本书几毛钱）来获得快速且高质量的抓取结果，请查看 [此教程](doc/deepseek.md)
- 如果希望完全白嫖又正好拥有一块 8G+（最好 12G+）的 Nvidia 显卡，请使用 [KeywordGachaServer](https://github.com/neavo/KeywordGachaServer) 搭建本地接口

## 最佳实践 💰
- 处理 `游戏文本` 时，建议使用 [Translator++](https://dreamsavior.net/translator-plusplus/) 导出的文本，[MTool](https://afdian.net/a/AdventCirno) 导出的文本有时效果较差

## 开发计划 📈
- [x] 支持 [Translator++](https://dreamsavior.net/translator-plusplus/) 导出的 CSV 文本
- [X] 添加 对 组织、道具、地域 等其他名词类型的支持
- [ ] 添加 对 `英文内容` 的支持
- [ ] 添加 对 `中文内容` 的支持
- [ ] 添加 对 `韩文内容` 的支持
- [X] 添加 对 GPU 加速的支持
- [X] 添加 全自动生成模式

## 问题反馈 😥
  - 运行时的日志保存在程序目录下的 `KeywordGacha.log` 等日志文件内
  - 反馈问题的时候请附上这些日志文件
