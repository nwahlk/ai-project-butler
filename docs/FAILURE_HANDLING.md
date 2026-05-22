# Failure Handling

本文说明 Project Butler 的 failure handling 策略。目标是让 analyzer failure 不影响整个系统，同时把失败信息结构化地暴露给维护者。

核心原则：

- analyzer failure 是 partial failure。
- pipeline/config failure 是 fatal failure。
- 文件级问题通常是 warning/debug，不应该默认中断整个系统。
- failure 必须进入结构化 telemetry，不能只存在于日志里。
- 不做全局 retry，不引入复杂 fault framework。

## Failure Levels

### Fatal Failure

Fatal failure 会终止当前命令。

当前包括：

- 项目根路径不存在
- 项目根路径不是目录
- 启用了未知 analyzer 名称
- CLI/config 非法
- reporter 无法渲染输出

这些失败说明 pipeline 无法可信地继续执行，因此应该 fail fast。

### Partial Failure

Partial failure 不终止整个 pipeline。

当前包括：

- 单个 analyzer 抛出 `Exception`
- analyzer 内部 bug
- analyzer 无法完成自己的整体分析

runner 会：

1. 记录 error log。
2. 创建 `AnalyzerFailure`。
3. 创建 status 为 `failed` 的 `AnalyzerExecution`。
4. 跳过该 analyzer 的分析结果。
5. 继续执行后续 analyzer。

注意：runner 只捕获 `Exception`，不捕获 `BaseException`。因此 `KeyboardInterrupt` 和 `SystemExit` 会继续向上抛出。

### Warning / Debug

Warning/debug 表示局部输入不可用，但 analyzer 或 scanner 仍然可以继续。

当前包括：

- 单个文件 stat 失败
- 单个文件不可读
- 单个文件 decode 或 read 失败，但 analyzer 可以跳过该文件

这类问题不应该升级成 analyzer failure，除非 analyzer 无法再产出可信结果。

## Structured Failure

结构化 failure 定义在 `src/telemetry/execution_report.py`：

```python
@dataclass(frozen=True)
class AnalyzerFailure:
    analyzer: str
    error_type: str
    message: str
    recoverable: bool = True
```

`AnalyzerExecution` 通过 `failure` 字段引用它：

```python
@dataclass(frozen=True)
class AnalyzerExecution:
    name: str
    status: str
    duration_ms: float
    failure: AnalyzerFailure | None = None
    result_summary: dict[str, int] = field(default_factory=dict)
```

`status` 当前使用：

- `ok`
- `failed`

不要把 analyzer failure 放进 `ProjectAnalysis`。`ProjectAnalysis` 表达项目分析结果；`AnalyzerFailure` 表达运行过程中的失败。

## Execution Report Output

`--execution-report` 会展示 analyzer 状态和错误摘要：

```text
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Analyzer         ┃ Status ┃  Time ┃ Error              ┃
┣━━━━━━━━━━━━━━━━━━╋━━━━━━━━╋━━━━━━━╋━━━━━━━━━━━━━━━━━━━━┫
┃ FileTypeAnalyzer ┃ OK     ┃ 0.00s ┃                    ┃
┃ MarkerAnalyzer   ┃ OK     ┃ 0.00s ┃                    ┃
┃ TODOAnalyzer     ┃ FAILED ┃ 0.02s ┃ RuntimeError: boom ┃
┗━━━━━━━━━━━━━━━━━━┻━━━━━━━━┻━━━━━━━┻━━━━━━━━━━━━━━━━━━━━┛
```

这个表格由 `src/reporters/execution.py` 渲染。它只负责展示，不负责决定 failure 策略。

## Runner Rules

`src/analyzers/runner.py` 是 analyzer isolation 的边界。

它应该：

- 校验 enabled analyzer 名称。
- 对每个 analyzer 单独计时。
- 捕获 analyzer 抛出的 `Exception`。
- 记录 `AnalyzerFailure`。
- 继续执行后续 analyzer。
- 只 merge 成功 analyzer 的 `ProjectAnalysis`。

它不应该：

- 捕获 `BaseException`。
- 对本地 analyzer 做 retry。
- 把失败 analyzer 伪装成成功。
- 在失败后返回完整成功状态。
- 决定用户业务报告的展示文案。

## Retry Strategy

当前不做 retry。

原因：

- 当前 analyzer 都是本地 deterministic 操作。
- 文件读取失败通常 retry 也不能解决。
- retry 会让日志和耗时变难解释。
- retry 容易掩盖 analyzer bug。

未来只有这些 analyzer 可能需要 retry：

- AI analyzer
- network dependency analyzer
- external command analyzer

如果需要 retry，应该由具体 analyzer 自己显式实现，而不是 runner 全局 retry。

## Testing Rules

必须覆盖：

- 一个 analyzer 失败，后续 analyzer 仍执行。
- failed analyzer 被记录为 `status == "failed"`。
- failed analyzer 带有 `AnalyzerFailure`。
- 成功 analyzer 的结果仍进入 partial `ProjectAnalysis`。
- unknown analyzer name 仍然抛 `ValueError`。
- `KeyboardInterrupt` 不被吞。
- execution report 显示 `Status` 和 `Error`。

不要测试：

- 具体耗时数值。
- 完整 traceback 文本。
- 日志行号。

## Common Mistakes

- catch 后直接 `pass`。
- catch `BaseException`。
- failure 只写日志，不进入 `ExecutionReport`。
- analyzer failed 但 `status` 仍是 `ok`。
- 把 failure 放进普通业务 report。
- 因为单个文件不可读就让整个 analyzer failed。
- 对所有 analyzer 做统一 retry/backoff。
- 引入复杂 error registry、event bus、circuit breaker。
