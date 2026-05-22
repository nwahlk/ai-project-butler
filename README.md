# Project Butler

Project Butler 是一个轻量级命令行工具，用于扫描代码项目并生成简单的分析报告。

项目刻意围绕清晰职责边界组织：

- scanner 负责发现文件
- analyzer 负责解释项目数据
- project 编排层负责串起 pipeline
- reporter 负责展示结果
- telemetry 负责记录运行过程和性能摘要

## 使用

```bash
project-butler scan PATH
```

本地开发时，如果没有安装 package，可以使用：

```bash
PYTHONPATH=src python -m cli scan PATH
```

显示 analyzer 执行耗时：

```bash
project-butler scan PATH --execution-report
```

## 开发

运行测试：

```bash
.venv/bin/pytest -q
```

## 文档

面向维护者的 Living Documentation：

- [架构说明](docs/ARCHITECTURE.md)：系统边界、设计原则和扩展点
- [数据流](docs/DATA_FLOW.md)：数据如何从 CLI 输入流向终端报告
- [模块职责](docs/MODULES.md)：每个模块的职责、输入和输出
- [Observability](docs/OBSERVABILITY.md)：logging、telemetry 和 execution report 设计
- [Failure Handling](docs/FAILURE_HANDLING.md)：partial failure、结构化错误和 retry 策略
- [架构图](docs/diagrams/architecture.mmd)：当前架构的 Mermaid flowchart
