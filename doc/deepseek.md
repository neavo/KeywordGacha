## 获取接口
- 打开 [DeepSeek 开放平台](https://platform.deepseek.com)，注册账号，完成认证并充值；
- 打开 [API Keys 页面](https://platform.deepseek.com/api_keys)，生成一个Key并复制保存，Key 的名字可以随便写；

## 设置应用
- [可选步骤，需 Nvidia 显卡] 双击 `02_启用应用内GPU加速.bat`，等待自动配置完成，如果失败，可以多重试几次；
- 用文本编辑器打开 `config.json` 文件，然后：
  - 将 `sk-no-key-required` 替换为前面生成的 `API Key`
  - 将 `http://localhost:8080/v1` 替换为 `https://api.deepseek.com`
  - 将 `glm-4-9b-chat` 替换为 `deepseek-chat`
  - 将 `request_frequency_threshold` 下面的数值修改为 `32`
- 修改完后，你的 `config.json` 文件中的内容看起来应该与下面的示例相似，这就完成设置了。

```json
{
    "api_key": [
        "sk-d0daba12345678fd8eb7b8d31c123456",
        "接口密钥，从接口平台方获取，使用在线接口时一定要设置正确。"
    ],
    "base_url": [
        "https://api.deepseek.com",
        "请求地址，从接口平台方获取，使用在线接口时一定要设置正确。"
    ],
    "model_name": [
        "deepseek-chat",
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
        32,
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
