# Observability

本文说明 Project Butler 的 observability 设计。目标是帮助维护者理解系统运行过程、定位慢 analyzer、调试失败路径，同时避免引入过重的 tracing 或 metrics 基础设施。

当前 observability 由三部分组成：

- logging：面向运行过程的文字 trace
- telemetry：面向代码的结构化执行数据
- execution report：面向 CLI 用户的可选 analyzer 耗时表格

## 设计原则

- 默认 CLI 输出保持干净，不显示运行日志和性能表格。
- `--verbose` 显示运行 trace。
- `--execution-report` 显示 analyzer 耗时表格。
- analyzer 不自己测量耗时，耗时由 runner 统一记录。
- telemetry 不复制完整业务报告，只记录摘要和耗时。
- 不引入外部 tracing backend、metrics server 或 event bus。

## Logging

logging 由 `src/logging_utils/` 管理：

```text
src/logging_utils/
├── __init__.py
├── logger.py
└── formatters.py
```

`logger.py` 提供：

- `setup_logging(verbose: bool, debug: bool)`
- `get_logger(name: str)`

`formatters.py` 提供：

- `DEFAULT_LOG_FORMAT`
- `DEBUG_LOG_FORMAT`

业务模块应该统一使用：

```python
from logging_utils import get_logger

logger = get_logger(__name__)
```

不要在业务模块里直接调用：

```python
logging.getLogger(__name__)
```

`src/logging_config.py` 只是兼容入口，新的调用点不要继续使用它。

## Verbose Trace

`--verbose` 会显示 pipeline 和 analyzer 执行过程，例如：

```text
INFO project: Project pipeline started root=/path/to/project
INFO scanner: Scan started root=/path/to/project
INFO scanner: Scan finished root=/path/to/project files=40 duration_ms=1.80
INFO analyzers.runner: [TODOAnalyzer] started
INFO analyzers.runner: [TODOAnalyzer] scanned 40 files
INFO analyzers.runner: [TODOAnalyzer] found 0 TODOs
INFO analyzers.runner: [TODOAnalyzer] completed in 0.03s
INFO project: Project pipeline finished root=/path/to/project total_files=40 total_duration_ms=23.17
```

这些日志由 `project.py`、`scanner.py` 和 `analyzers/runner.py` 统一产生。单个 analyzer 可以记录 debug 级别的内部跳过原因，但不应该记录自己的性能耗时。

## Telemetry

telemetry 代码位于：

```text
src/telemetry/
├── __init__.py
├── execution_report.py
└── timing.py
```

`execution_report.py` 定义：

- `AnalyzerFailure`
- `AnalyzerExecution`
- `ExecutionReport`
- `ProjectExecution`
- `summarize_analysis()`

`timing.py` 定义：

- `now_ms()`
- `elapsed_ms()`

`ProjectExecution` 同时包含业务报告和执行报告：

```python
ProjectExecution(
    report=ProjectReport(...),
    execution=ExecutionReport(...),
)
```

普通调用继续使用 `build_project_report()`。需要执行过程信息时使用 `build_project_execution()`。

## Execution Report

CLI 使用 `--execution-report` 时，会在普通项目报告后追加 analyzer 耗时表格：

```text
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━┳━━━━━━━┓
┃ Analyzer         ┃ Status ┃  Time ┃ Error ┃
┣━━━━━━━━━━━━━━━━━━╋━━━━━━━━╋━━━━━━━╋━━━━━━━┫
┃ FileTypeAnalyzer ┃ OK     ┃ 0.00s ┃       ┃
┃ MarkerAnalyzer   ┃ OK     ┃ 0.00s ┃       ┃
┃ TODOAnalyzer     ┃ OK     ┃ 0.03s ┃       ┃
┗━━━━━━━━━━━━━━━━━━┻━━━━━━━━┻━━━━━━━┻━━━━━━━┛
```

表格由 `src/reporters/execution.py` 渲染。它只接收 `ExecutionReport`，不运行 analyzer，也不计算耗时。

## Error Behavior

- 单个文件不可访问：scanner 或 analyzer 跳过并记录 debug 日志。
- analyzer 名称未知：runner 抛出 `ValueError`。
- analyzer 执行失败：runner 记录 `AnalyzerFailure`，标记该 analyzer 为 `FAILED`，并继续执行其他 analyzer。
- `KeyboardInterrupt` 和 `SystemExit` 不会被 runner 捕获。
- 不返回看似完全成功但实际缺失 analyzer 结果的 execution report。

## 扩展规则

新增 analyzer 时：

1. analyzer 只返回自己的 `ProjectAnalysis` 字段。
2. runner 负责记录 `AnalyzerExecution`。
3. `summarize_analysis()` 只记录计数摘要。
4. `reporters/execution.py` 只渲染 execution table。
5. analyzer failure 是 partial failure，不应该让整个 pipeline 失败。

新增 telemetry 字段时：

1. 先判断它是不是运行过程信息。
2. 如果是，放入 `ExecutionReport` 或 `AnalyzerExecution`。
3. 如果是用户应该看到的业务结果，放入 `ProjectAnalysis`。
4. 不要把完整 TODO 列表、完整文件列表或完整 report 复制进 telemetry。

## 不要做的事

- 不要创建名为 `logging/` 的包，避免和 Python 标准库 `logging` 冲突。
- 不要让 analyzer 自己打印性能日志。
- 不要在普通报告中默认展示 execution table。
- 不要引入 OpenTelemetry、Prometheus、event bus，除非出现真实需求。
- 不要用 `dict[str, Any]` 传递 telemetry。
- 不要测试具体耗时数值，只测试字段存在、非负和输出结构。
