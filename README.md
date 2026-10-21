# Foreign Trade Digital Employee | 外贸数字员工

**A human-in-the-loop, draft-only AI assistant for international trade email workflows.**  
**一款面向外贸邮件的 AI 辅助工具：分析询盘、生成回复草稿、保留人工审核，不自动向客户发送邮件。**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-pytest-informational)](https://docs.pytest.org/)
[![Status](https://img.shields.io/badge/Status-early--stage-orange)](#project-status--项目现状)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Project scope / 项目定位**  
> This repository contains a Python-based email processing and history-learning engine. It is **not** a packaged desktop application and does **not** send customer emails automatically. The original code in this repository is distributed under the [MIT License](LICENSE); third-party dependencies remain under their own licenses.  
> 当前公开仓库为 Python 邮件处理与历史学习引擎，**不包含可直接安装的桌面安装包**，也**不会自动发送客户邮件**。本仓库原创代码已采用 [MIT 开源许可证](LICENSE)，第三方依赖遵循各自许可。

## Features | 功能

- **IMAP mailbox reading / 邮件读取：** Read recent customer emails and filter out non-customer messages. / 读取近期邮件，筛除非客户询盘。
- **AI-assisted analysis / AI 辅助分析：** Analyze customer intent, translate messages, identify missing or risky commercial information and generate reply drafts using a configurable SiliconFlow-compatible LLM. / 识别客户意图、翻译邮件、识别缺失和风险信息，生成回复建议。
- **Human approval by design / 人工审核：** The system saves replies to the mailbox's **Drafts** folder via IMAP. It does **not** automatically send emails. / 回复只写入草稿箱，发送前必须人工审查。
- **Output validation / 输出校验：** Validate mandatory sections and guard against unsupported commercial claims; retry invalid model output through a repair prompt. / 对回复结构、商业承诺等进行规则校验，不符合要求时进行修复。
- **History learning / 历史学习：** Optional, manually initiated learning from eligible recent Inbox and Sent messages, with local SQLite storage and reply-style/context retrieval. / 手动触发历史邮件学习，使用本地 SQLite 保存必要的回复风格与上下文。
- **Incremental processing / 增量处理：** Track processed Message-IDs to reduce duplicate processing or draft creation. / 记录已处理的邮件编号，降低重复处理和重复草稿风险。
- **WeCom notifications / 企业微信提醒：** Optional internal group notifications after successful processing. / 可选的企业微信群内部提醒，通知失败不阻塞邮件处理。

## How it works | 工作流程

```text
IMAP inbox -> customer inquiry filter -> AI analysis
                                      -> output validation / repair
                                      -> reply draft -> IMAP Drafts
                                      -> processed-ID record
                                      -> optional WeCom notification

Optional, manually triggered history learning:
IMAP Inbox + Sent -> filtering -> local SQLite memory / style profile
```

**Safety boundary:** Incoming customer text and historical emails are treated as untrusted input. The `skills/foreign-trade-reply/SKILL.md` instructions and `agent/output_gate.py` enforce drafting and review rules. AI-generated content must still be checked by a human, including pricing, payment, product claims, delivery dates and personal data.

**安全边界：** 客户邮件和历史内容都可能包含不可信指令。虽然已有规则与输出校验，但模型生成内容仍须人工核对，尤其是价格、交期、付款、库存和客户隐私。

## Repository layout | 目录结构

| Path | Purpose / 用途 |
| --- | --- |
| `run_foreign_trade_agent.py` | Email processing entry point / 邮件处理入口 |
| `learn_history.py` | Manually run initial history learning / 手动启动初始历史学习 |
| `mail_reader/` | IMAP connection, parsing and filtering / 邮件读取与筛选 |
| `mail_writer/` | Reply construction and draft saving / 回复草稿生成与保存 |
| `agent/` | LLM workflow and output gate / 模型流程与输出校验 |
| `llm/` | Provider abstraction and SiliconFlow integration / 模型适配 |
| `history_learning/` | Local SQLite history, style and context / 本地历史记忆 |
| `wecom/` | Optional WeCom notifications / 企业微信通知 |
| `skills/foreign-trade-reply/` | Reply policy and format / 回复规则与格式 |
| `tests/` | Python tests / 自动化测试 |
| `docs/superpowers/` | Design notes and implementation plans / 设计说明 |

## Getting started | 快速开始

**Requirements:** Python 3.10+; an IMAP-enabled email account with access to its Drafts folder; a SiliconFlow API key if you plan to run AI processing. Network access is required for email and API calls. / 需要 Python 3.10 以上、支持 IMAP 的邮箱及对应授权码，调用 AI 时需要 SiliconFlow API Key。

```bash
git clone https://github.com/z4304101/foreign_trade_digital_employee.git
cd foreign_trade_digital_employee
python3 -m venv .venv
source .venv/bin/activate            # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Copy the sample configuration: / 复制示例配置（**不要提交真实密钥**）：

```bash
cp .env.example .env                  # Windows: copy .env.example .env
```

Edit `.env` with **your own** test mailbox, provider credentials and optional WeCom webhook. Passwords, customer emails, history databases and runtime outputs must remain private.

### Run tests first | 先运行测试

```bash
python -m pytest -q
```

The repository includes unit/integration-style tests, but a **current end-to-end pass, live mailbox compatibility, and CI status have not been independently verified**. Please run the tests locally and inspect results before relying on the project. / 仓库有测试文件，但这里不虚构测试通过率或生产验证结果，请先在本机运行测试。

### Process email | 处理邮件

**Caution:** The following command uses your configured mailbox and can create **real drafts**. Test with a dedicated mailbox first. / 以下命令会连接实际邮箱并可能真实创建草稿，建议先用测试邮箱。

```bash
python run_foreign_trade_agent.py
```

### Initial history learning | 初始历史学习

Run only when you explicitly intend to scan eligible recent mail. History learning is separate from normal processing and does not auto-send customer emails. / 仅在确认需要读取历史邮件时手动运行：

```bash
python learn_history.py
```

History-learning data is stored locally under `runtime/`, which is ignored by Git. The service may send **selected email content or contextual extracts** to the configured third-party AI provider when analyzing or generating replies. Do not use real customer data without appropriate authorization and a privacy review. / 历史数据库保存在本地，但 AI 调用可能将必要邮件片段提交至第三方模型服务，请先确认客户数据处理授权。

## Configuration | 环境变量

| Variable | Description |
| --- | --- |
| `EMAIL_USER` | IMAP mailbox account / 邮箱账号 |
| `EMAIL_AUTH_CODE` | IMAP authorization code / 邮箱授权码 |
| `EMAIL_IMAP_HOST`, `EMAIL_IMAP_PORT` | IMAP server and port / IMAP 地址与端口 |
| `LLM_PROVIDER` | Supported value in this version: `siliconflow` |
| `SILICONFLOW_API_KEY` | AI provider API key / 模型密钥 |
| `SILICONFLOW_MODEL` | Model ID supported by your SiliconFlow account |
| `SILICONFLOW_BASE_URL` | SiliconFlow OpenAI-compatible base URL |
| `SENDER_NAME`, `SENDER_TITLE`, `SENDER_COMPANY` | Optional reply signature / 可选签名 |
| `WECOM_WEBHOOK_URL` | Optional internal WeCom notification webhook |

See [`.env.example`](.env.example) for placeholder values. **Never commit .env, API keys, customer messages or personal data.**

## Project status | 项目现状

This is an **early-stage, publicly visible Python project** with an existing test suite and an evolving implementation. The repository presently has **no packaged macOS/Windows desktop installer**, no published CI workflow, and no confirmed current test-pass claim. Desktop packaging and improved CI/documentation are possible future work, not existing features of this branch.

这是持续开发中的公开 Python 项目，不应将其他本地分支、打包成果或外部项目的开发进度误认为本仓库 `main` 分支已交付的功能。

## Contributing | 参与贡献

Issues describing reproducible problems and small, focused improvements are welcome. Avoid pasting confidential customer communications or secrets into public issues or pull requests. Please include a minimal anonymized reproduction and relevant test information. / 欢迎提交可复现的问题或小范围改进，请脱敏，不要公开真实客户邮件与密钥。

## Licensing and attribution | 授权与署名

**License: [MIT](LICENSE).** Copyright (c) 2026 z4304101. The original project code and documentation in this repository may be used, modified and redistributed under the MIT License provided the copyright notice and license are retained. Third-party packages, APIs and dependencies remain subject to their own licenses.

**本仓库采用 [MIT License](LICENSE)。** 原创代码及文档允许在保留版权声明及许可证的前提下使用、修改及再分发；第三方 SDK、依赖、服务与其他人的内容仍遵守各自许可。本仓库的代码由维护者自行开发，并在后期使用 Codex 等 AI 编码工具辅助开发及测试。

Maintained in [z4304101/foreign_trade_digital_employee](https://github.com/z4304101/foreign_trade_digital_employee). / 项目维护地址如上。
