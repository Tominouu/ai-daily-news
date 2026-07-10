# 🤖 Bilan IA — Daily AI News Briefing

每天早上自动汇总顶级AI新闻源，通过邮件发送结构化简报（含音频版本）。

## ✨ 功能

- **15个以上RSS源** — TechCrunch、OpenAI、Anthropic、arXiv、Le Monde、Hugging Face等
- **AI摘要** — 每条新闻用Mistral（免费层）总结2-3句话
- **每日邮件** — 每天UTC 6:00（巴黎8:00）通过Gmail SMTP发送
- **音频版本** — 生成MP3附件随邮件发送（gTTS）
- **100%免费** — GitHub Actions + 免费API层

## 📋 先决条件

- 一个 [GitHub](https://github.com) 账号
- 一个 [Mistral](https://console.mistral.ai) API密钥（免费层，每天约需500个token）
- 一个 Gmail/Google Workspace 账号及**应用专用密码**（用于邮件发送）

## 🚀 安装

### 1. 创建仓库并克隆

```bash
gh repo create ai-daily-news --public --clone
cd ai-daily-news
```

### 2. 复制文件

将所有项目文件复制到仓库目录中。

### 3. 添加GitHub Secrets

```bash
gh secret set MISTRAL_API_KEY          # 在 https://console.mistral.ai 获取
gh secret set GMAIL_USER               # 你的 Gmail 地址
gh secret set GMAIL_APP_PASSWORD       # 在 https://myaccount.google.com/apppasswords 获取
```

### 4. 推送并测试

```bash
git push
gh workflow run "Bilan IA Quotidien"
```

## 📁 项目结构

```
├── .github/workflows/
│   └── daily-news.yml     # GitHub Actions workflow（cron 6:00 UTC）
├── scripts/
│   └── main.py            # 主脚本：抓取RSS → 摘要 → 邮件
├── config/
│   └── sources.json       # RSS源配置
├── requirements.txt       # Python依赖
└── README.md
```

## 📡 RSS源

| 来源 | 内容 |
|---|---|
| TechCrunch AI | 科技创业与AI新闻 |
| The Verge AI | 科技与文化 |
| VentureBeat AI | 商业AI |
| Ars Technica AI | 深度技术分析 |
| MIT Tech Review | 前沿研究 |
| Google AI | Google研究博客 |
| Meta AI | Meta研究博客 |
| OpenAI | OpenAI博客 |
| Anthropic | Anthropic博客 |
| DeepMind | DeepMind博客 |
| Hugging Face | 开源ML社区 |
| arXiv IA | 学术预印本 |
| Le Monde IA | 法国新闻（法语） |
| France-Info IA | 法国新闻（法语） |
| Papers With Code | 研究论文与代码 |

## 📧 邮件示例

邮件以HTML格式发送，包含：
- 按来源分组的摘要新闻
- 摘要末尾的"当日趋势"部分
- 顶部进度条：
  - 所有来源的状态概览
  - 所有文章的可点击链接
- 作为附件附带的MP3音频版本

## 🔧 自定义

### 添加/移除RSS源

编辑 `config/sources.json`：

```json
[
  {"name": "源名称", "url": "https://example.com/rss"}
]
```

### 变更发送时间

编辑 `.github/workflows/daily-news.yml` 中的cron表达式：

```yaml
on:
  schedule:
    - cron: "0 6 * * *"   # 每天6:00 UTC
```

### 切换AI模型

`scripts/main.py` 中编辑 `model` 参数：

```python
model="mistral-small-latest"  # 或 mistral-medium-latest, mistral-large-latest
```

## 📊 配额

| 服务 | 每日用量 | 免费层限制 |
|---|---|---|
| Mistral API | ~500 tokens | 500K tokens/天 |
| Gmail SMTP | 1封邮件 | 500封/天 |
| GitHub Actions | ~2分钟运行时间 | 2000分钟/月 |
| gTTS | 1个音频 | 无限制 |

## 📄 许可证

MIT
