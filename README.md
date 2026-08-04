# 企析智体 CorpLens（CorpShift × FirmLens）

**企析智体 / CorpLens** —— 企业转型需求分析智能体。

## 快速开始

```powershell
.\start.bat
```

1. 首页填写 **API Key**（可选）→ 保存到本机 `.env`  
2. 或直接 **一键生成演示（邻里宠洗）**

## API Key 安全（重要）

- Key **只**保存在本机 `.env`  
- `.env` 已在 `.gitignore`，**不要**提交到 GitHub  
- 不要把 Key 写进 README、截图、示例文件  
- 公开前可运行：`python scripts/check_repo_secrets.py`

## 思考流如何保护「方法」又不必开「私有包」

独特辩驳思考已沉淀为通用 Skill：

`prompts/skills/corplens_dialectic.md`

各席分析会自动嵌入该 Skill；**输出中不会出现内部行业案例名**。  
公开演示模板为「社区宠物洗护」，与内部案例分离。

## 配置示例（`.env.example`）

```env
TRANSFORM_AGENT_MOCK=1
LLM_PROVIDER=siliconflow
OPENAI_API_KEY=
OPENAI_MODEL=Qwen/Qwen2.5-14B-Instruct
```

## 声明

输出为讨论草案，不构成咨询、投资或法律意见。
