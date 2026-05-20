# Project Butler - AGENTS.md

# Project Goal

这是一个长期可维护的 AI-assisted software engineering project。

目标不是快速堆功能，而是：
- 建立工程化 AI 工作流
- 保持可维护架构
- 建立测试与 review 习惯
- 保持系统长期可理解

---

# Engineering Principles

- 保持架构简单
- 避免 over-engineering
- scanner 只负责扫描
- analyzer 只负责分析
- report 只负责展示
- 不允许模块职责混乱
- 优先可读性，而不是“炫技”

---

# Testing Rules

- 每个新功能必须包含测试
- pytest 必须保持绿色
- 不允许带 failing tests 提交
- 优先小而独立的测试

---

# Review Rules

完成任务前必须：
1. review 修改文件
2. 检查模块职责
3. 检查隐藏耦合
4. 检查 over-engineering
5. 解释架构影响

---

# Documentation Rules

如果架构发生变化：

必须更新：
- docs/ARCHITECTURE.md
- docs/DATA_FLOW.md
- Mermaid diagrams

如果没有变化：
明确说明：
"No architecture doc update required"

---

# Git Rules

- 保持小 commit
- commit message 必须有意义
- 不允许 giant commits

Good:
- "Introduce analyzer abstraction"
- "Add TODO analyzer"

Bad:
- "update"
- "fix stuff"

---

# Coding Rules

- 优先 dataclass，而不是 loose dict
- 避免硬编码配置
- 避免 giant functions
- 优先明确 typing
- 优先 composition，而不是复杂继承

---

# AI Workflow

推荐工作流：

Spec
→ Implementation
→ Review
→ pytest
→ Documentation update
→ git commit

不允许跳过 review 和测试。