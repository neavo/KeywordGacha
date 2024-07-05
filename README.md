# KeywordGacha 📖
#### 使用 OpenAI 兼容接口来抓取小说、漫画、字幕、游戏脚本等任意文本中的词汇表的翻译辅助工具

　　　　

## 概述 📢
- [KeywordGacha](https://github.com/neavo/KeywordGacha)，简称 KG，是一个使用 AI 技术来抽取文本中词汇表的次世代工具
- 相较传统工具，具有高命中、语义化、智能总结角色信息等特色，对文本的兼容性更好
- 一键从长篇文本中抽取角色名称、组织名称等专有名词的词汇表，并且自动翻译、自动总结
- 可以极大的提升 小说、漫画、字幕、游戏脚本 等文本内容的译前准备时制作统一词汇表的工作效率

> <img src="image/01.jpg" style="width: 75%;" alt="image/01.jpg">

> <img src="image/02.png" style="width: 75%;" alt="image/02.png">
  
## 要求 🖥️
- 兼容 OpenAI 接口格式的大语言模型 API
- KG 的开发环境是本地运行的 [Qwen2-7B-Instruct](https://huggingface.co/Qwen/Qwen2-7B-Instruct-GGUF)

## 使用 🛸
- 从 [发布页](https://github.com/neavo/KeywordGacha/releases) 下载 KG 并解压缩到本地
- 打开配置文件 `config.json` ，填入 API 信息，如使用本地接口则不需要修改
- 双击 `KeywordGacha.exe`，按提示操作即可
- 流程执行完毕后，会生成结果文件 `角色姓名_日志.txt` 与 `角色姓名_列表.json`
- `角色姓名_日志.txt` 中包含抓取到的词汇的原文、上下文、翻译建议、角色信息总结等信息
- 参考日志中的信息完成 `角色姓名_列表.json` 后，可以直接导入到 [AiNiee](https://github.com/NEKOparapa/AiNiee) 等翻译器中使用
- 注意，为保证质量，KG 并不会直接为你填充词汇表类翻译，请认真审阅日志后手动完成词汇表

## 效果 ⚡
- 抓取和翻译效果取决于模型本身的水平，使用 💪 ~~更昂贵~~ 更强力  的 模型可以显著提升效果
- 是的，氪金可以变强
- 但是即使只使用运行在本地电脑上的小规模开源模型，效果和效率也远超传统工具
- 如果你拥有一块至少 8G 显存的 Nvidia 显卡，可以通过一键包 [KeywordGachaServer](https://github.com/neavo/KeywordGachaServer) 来使用本地模型
- 注意：用于 `分词` 与用于 `翻译` 的服务器端配置不一样
- 所以务必严格按照 [KeywordGachaServer](https://github.com/neavo/KeywordGachaServer) 内的说明一步一步搭建环境，请勿直接复制其他应用中的配置

## 近期更新
- 20240706
  - 新增 智能总结 功能
  - 新增 重复词根检测 功能

- 20240702
  - 增加 请求超时时间、并发任务数量 的设置项目
  - 增加 对 [Translator++](https://dreamsavior.net/translator-plusplus/) 导出的 CSV 文本的支持
  - 调整 优化了对混杂有游戏代码的文本的兼容性

## 文本格式 🆗
- 目前支持三种不同的输入文本格式，其中 [Translator++](https://dreamsavior.net/translator-plusplus/) 导出的 CSV 文件的抓取效果似乎比较好
- 文件中 每一行/每一条 应只包含一个句子，太长的话请先手动处理一下
- 如当前目录下有 `all.orig.txt` 或 `ManualTransFile.json` 文件，会自动识别
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
        "api_key": "sk-no-key-required", // 你所使用 API 接口的密钥，从接口平台方获取，默认为本地接口
        "base_url": "译文http://localhost:8080/v1", // 你所使用 API 接口的地址，从接口平台方获取，默认为本地接口
        "model_name": "qwen2-7b-instruct", // 你所使用 API 接口的模型名称，从接口平台方获取，默认为本地接口

        "max_workers": 4, // 网络请求等任务并发执行的最大数量，如果频繁出现网络超时或者拒绝服务错误，可以调小这个值
        "request_timeout": 120, // 网络请求等任务并发执行的最大数量，如果频繁出现网络超时或者拒绝服务错误，可以调大这个值

        "translate_surface_mode": "1", // 词汇的后处理模式，默认为 1 即日中翻译，设为 0 可以跳过此步骤，以节约 Token 与 时间
        "translate_context_mode": "1", // 上下文的后处理模式，默认为 1 即日中翻译，设为 0 可以跳过此步骤，以节约 Token 与 时间
    }
  ```

## 语言能力 🗣️

- 较新的模型比如 [GPT4o](https://chatgpt.com/)、[Claude 3.5 Sonnet](https://claude.ai/) 等具有超乎想象多语言能力，但是也十分昂贵
- [Qwen2](https://github.com/QwenLM/Qwen2) 在处理中文的表现上称得上优秀，处理日文水平也算堪用，7B 版本只需要 8G 显存，推荐使用

## 开发计划 🎢

- [x] 支持 [Translator++](https://dreamsavior.net/translator-plusplus/) 导出的 CSV 文本
- [ ] 添加 对 组织、道具、地域 等其他名词类型的支持
- [ ] 添加 对英文文本的支持

## 问题反馈 😥
  - 运行时的日志保存在程序目录下的 `KeywordGacha.log` `KeywordGacha.log.1` 等文件
  - 反馈问题的时候请附上这些日志文件

## 友情提醒 💰
  - KG 会将 `全部的文本` 发送至 AI 进行处理，这个过程会消耗大量的 Token
  - 如使用在线接口，请关注你的账单！
