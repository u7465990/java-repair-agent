# Model catalog

探测时间：2026-11-24。接口共返回 191 个模型；控制台免费额度页显示 136 个。

过滤掉 embedding / audio / image / video / OCR / rerank 后，140 个是文本候选；其中 72 个能正常对话，**69 个支持 tool calling**（下表）。

| 模型 | 建议用途 |
|---|---|
| MiniMax-M2.5 | 开发冒烟 |
| deepseek-v4.1-flash | 开发冒烟 |
| deepseek-v4.1-flash-1017 | 开发冒烟 |
| deepseek-v4-flash-0731 | 开发冒烟 |
| glm-5.1 | 候选 |
| glm-5.2 | 候选 |
| deepseek-v4-pro-0813 | 最终取数 |
| glm-5.3 | 最终取数 |
| glm-5.3-prime | 最终取数 |
| glm-5 | 候选 |
| kimi-k2.6 | 候选 |
| kimi-k2.5 | 候选 |
| deepseek-v4-pro | 最终取数 |
| kimi-k2.7-code | 候选 |
| gui-plus-2026-02-26 | 最终取数 |
| qwen-flash | 开发冒烟 |
| glm-5.2-fast-preview | 开发冒烟 |
| qwen-doc-turbo | 开发冒烟 |
| qwen-flash-2025-07-28 | 开发冒烟 |
| kimi-k3 | 最终取数 |
| qwen-flash-character-2026-02-26 | 开发冒烟 |
| qwen-long | 候选 |
| qwen-max | 最终取数 |
| qwen-max-longcontext | 最终取数 |
| qwen-deep-search-planning | 候选 |
| kimi-k3.1-pro | 最终取数 |
| qwen-plus-2025-04-28 | 最终取数 |
| qwen-plus | 最终取数 |
| qwen-plus-2025-01-25 | 最终取数 |
| qwen-plus-2025-11-05 | 最终取数 |
| qwen-flash-character | 开发冒烟 |
| qwen-plus-character | 最终取数 |
| qwen-plus-2025-12-01 | 最终取数 |
| qwen-plus-latest | 最终取数 |
| qwen3-coder-flash | 开发冒烟 |
| qwen3-coder-flash-2025-07-28 | 开发冒烟 |
| qwen3.5-122b-a10b | 开发冒烟 |
| qwen-plus-2025-07-14 | 最终取数 |
| qwen3.5-27b | 开发冒烟 |
| qwen3.5-35b-a3b | 开发冒烟 |
| qwen3-vl-plus | 最终取数 |
| qwen3.5-flash | 开发冒烟 |
| qwen3.5-flash-2026-02-23 | 开发冒烟 |
| qwen3.5-397b-a17b | 候选 |
| qwen3.6-35b-a3b | 开发冒烟 |
| qwen3.5-plus | 最终取数 |
| qwen3.5-plus-2026-04-20 | 最终取数 |
| qwen3.6-27b | 开发冒烟 |
| qwen3.7-flash | 开发冒烟 |
| qwen3.5-plus-2026-02-15 | 最终取数 |
| qwen3.7-max-2026-05-17 | 最终取数 |
| qwen3.7-max | 最终取数 |
| qwen3.6-flash | 开发冒烟 |
| qwen3.6-plus-2026-04-02 | 最终取数 |
| qwen3.6-plus | 最终取数 |
| qwen3.7-flash-2026-07-15 | 开发冒烟 |
| qwen3.7-max-2026-05-20 | 最终取数 |
| qwen3.7-max-preview | 最终取数 |
| qwen3.8-27b | 开发冒烟 |
| qwen3.7-max-2026-06-08 | 最终取数 |
| qwen3.7-plus-2026-05-26 | 最终取数 |
| qwen3.8-flash | 开发冒烟 |
| qwen3.8-2.4t-a95b | 开发冒烟 |
| qwen4-max | 最终取数 |
| qwen3.8-max-0902 | 最终取数 |
| qwen3.7-plus | 最终取数 |
| qwen3.8-max | 最终取数 |
| tongyi-xiaomi-analysis-flash | 开发冒烟 |
| tongyi-xiaomi-analysis-pro | 最终取数 |

说明：
- “开发冒烟”= 便宜/小参数模型，用来查工具与环境问题；
- “最终取数”= 能力更强，留到写报告时跑 5–10 个 bug；
- 控制台显示 136、接口返回 191，是因为接口包含多版本快照、非文本模型和未上架模型；以免费额度页实际可开启的为准。

完整名单（接口返回顺序已排序，共 191 个）：

```text
MiniMax-M2.5
MiniMax/MiniMax-M2.1
MiniMax/MiniMax-M2.5
MiniMax/MiniMax-M2.7
MiniMax/MiniMax-M3
MiniMax/MiniMax-M3.1-Flash
MiniMax/speech-02-hd
MiniMax/speech-02-turbo
MiniMax/speech-2.8-hd
MiniMax/speech-2.8-turbo
Xing/Xing4.1-Preview
ZHIPU/GLM-5
ZHIPU/GLM-5.1
ZHIPU/GLM-5.2
ZHIPU/GLM-5.3
ZHIPU/GLM-5.3-Flash
ZHIPU/GLM-5.3-FlashX
antdigital/Ling-3.1-flash
cmaas-glm-5.3
cmaas-qwen3.8-flash
deepseek-r1-distill-llama-70b
deepseek-r1-distill-qwen-1.5b
deepseek-v4-flash-0731
deepseek-v4-pro
deepseek-v4-pro-0813
deepseek-v4.1-flash
deepseek-v4.1-flash-1017
fun-asr-flash-2026-06-15
glm-5
glm-5.1
glm-5.2
glm-5.2-fast-preview
glm-5.3
glm-5.3-prime
gui-plus
gui-plus-2026-02-26
kimi-k2.5
kimi-k2.6
kimi-k2.7-code
kimi-k3
kimi-k3.1-pro
kimi/kimi-k2.6
kimi/kimi-k2.7-code
kimi/kimi-k2.7-code-highspeed
kimi/kimi-k2.8-preview
kimi/kimi-k3
kimi/kimi-k3.1-pro
kimi/kimi-k3.1-pro-highspeed
qwen-1.8b-chat
qwen-1.8b-longcontext-chat
qwen-14b-chat
qwen-72b-chat
qwen-7b-chat
qwen-audio-3.0-asr-flash
qwen-audio-3.0-realtime-flash
qwen-audio-3.0-realtime-plus
qwen-audio-3.1-realtime-flash
qwen-audio-3.1-realtime-plus
qwen-deep-research
qwen-deep-research-2025-12-15
qwen-deep-search-planning
qwen-doc-turbo
qwen-flash
qwen-flash-2025-07-28
qwen-flash-character
qwen-flash-character-2026-02-26
qwen-image-2.0
qwen-image-2.0-2026-03-03
qwen-image-2.0-pro
qwen-image-2.0-pro-2026-03-03
qwen-image-2.0-pro-2026-04-22
qwen-image-2.0-pro-2026-06-22
qwen-image-2.1-pro
qwen-image-3.0
qwen-image-3.0-pro
qwen-long
qwen-max
qwen-max-0107
qwen-max-1201
qwen-max-longcontext
qwen-mt-flash
qwen-mt-lite
qwen-mt-plus
qwen-mt-uni
qwen-plus
qwen-plus-2025-01-25
qwen-plus-2025-04-28
qwen-plus-2025-07-14
qwen-plus-2025-11-05
qwen-plus-2025-12-01
qwen-plus-character
qwen-plus-latest
qwen-turbo-0919
qwen-turbo-2024-11-01
qwen-vl-ocr
qwen-vl-ocr-2025-11-20
qwen1.5-0.5b-chat
qwen1.5-1.8b-chat
qwen1.5-110b-chat
qwen1.5-14b-chat
qwen1.5-32b-chat
qwen1.5-72b-chat
qwen1.5-7b-chat
qwen2-0.5b-instruct
qwen2-1.5b-instruct
qwen2-57b-a14b-instruct
qwen2-7b-instruct
qwen2.5-0.5b-instruct
qwen2.5-1.5b-instruct
qwen2.5-math-1.5b-instruct
qwen3-asr-flash-realtime
qwen3-coder-flash
qwen3-coder-flash-2025-07-28
qwen3-livetranslate-flash
qwen3-livetranslate-flash-2025-12-01
qwen3-omni-flash
qwen3-omni-flash-realtime-2025-09-15
qwen3-s2s-flash-realtime-2025-09-22
qwen3-tts-flash
qwen3-tts-flash-realtime
qwen3-vl-plus
qwen3.5-122b-a10b
qwen3.5-27b
qwen3.5-35b-a3b
qwen3.5-397b-a17b
qwen3.5-flash
qwen3.5-flash-2026-02-23
qwen3.5-livetranslate-flash-realtime
qwen3.5-livetranslate-flash-realtime-2026-05-19
qwen3.5-ocr
qwen3.5-omni-flash
qwen3.5-omni-flash-2026-03-15
qwen3.5-omni-flash-realtime
qwen3.5-omni-flash-realtime-2026-03-15
qwen3.5-omni-plus
qwen3.5-omni-plus-2026-03-15
qwen3.5-omni-plus-realtime
qwen3.5-omni-plus-realtime-2026-03-15
qwen3.5-plus
qwen3.5-plus-2026-02-15
qwen3.5-plus-2026-04-20
qwen3.6-27b
qwen3.6-35b-a3b
qwen3.6-flash
qwen3.6-flash-2026-04-16
qwen3.6-plus
qwen3.6-plus-2026-04-02
qwen3.7-flash
qwen3.7-flash-2026-07-15
qwen3.7-max
qwen3.7-max-2026-05-17
qwen3.7-max-2026-05-20
qwen3.7-max-2026-06-08
qwen3.7-max-preview
qwen3.7-plus
qwen3.7-plus-2026-05-26
qwen3.7-text-embedding
qwen3.7-text-embedding-flash
qwen3.7-text-rerank
qwen3.8-2.4t-a95b
qwen3.8-27b
qwen3.8-flash
qwen3.8-livetranslate-flash-realtime
qwen3.8-max
qwen3.8-max-0902
qwen3.8-omni-flash
qwen3.8-omni-flash-realtime
qwen4-max
siliconflow/deepseek-r1-0528
siliconflow/deepseek-v3-0324
siliconflow/deepseek-v3.1-terminus
siliconflow/deepseek-v3.2
stepfun/step-3.7-flash
stepfun/step-5-preview
tongyi-intent-detect-v3
tongyi-xiaomi-analysis-flash
tongyi-xiaomi-analysis-pro
unisound/unisound-u2
vanchin/deepseek-ocr
vanchin/deepseek-r1
vanchin/deepseek-v3
vanchin/deepseek-v3.1-terminus
vanchin/deepseek-v3.2-think
vanchin/deepseek-v4-pro
vanchin/deepseek-v4-pro-0813
vanchin/deepseek-v4.1-flash
vanchin/deepseek-v4.1-flash-1017
wan2.7-image
wan2.7-image-pro
xiaomi/mimo-v2.6-pro-ultraspeed
z-image-turbo
```
