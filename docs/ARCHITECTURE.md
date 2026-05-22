# 架构说明

Project Butler 是一个轻量级命令行项目检查工具。核心设计目标是把扫描、分析、编排和展示分开，让后续新增 analyzer 时，不需要把 `scanner` 或 `reporter` 变成职责混杂的模块。

当前架构刻意保持简单：

```text
CLI
-> project 编排层
-> scanner
-> analyzer runner
-> project report
-> reporter
```

## 设计原则

- `scanner` 只发现文件并记录文件元数据。
- `analyzer` 解释扫描结果并产出分析结果。
- `project` 编排层负责把扫描和分析串起来。
- `reporter` 只把已经生成的报告格式化到目标输出。
- `telemetry` 记录运行过程、耗时和 analyzer 执行摘要。
- 配置显式定义，并使用 dataclass。
- 模型是层与层之间的共享契约，应该保持小而稳定。

这个边界很重要，因为未来 analyzer 的逻辑可能差异很大。TODO analyzer 需要读取文件内容，Docker analyzer 可能只检查 Docker 相关文件，Dependency analyzer 可能解析依赖清单，Security analyzer 可能应用风险更高的启发式规则。除非扫描契约本身不够用，否则这些 analyzer 不应该要求修改文件扫描器。

## 主要分层

### CLI 层

`src/cli.py` 负责命令行相关行为：

- Typer 命令定义
- 用户传入的路径参数
- logging 开关
- 把渲染结果输出到终端

它不应该检查文件、不应该直接运行 analyzer 逻辑，也不应该知道每个报告区块是如何计算出来的。

### 编排层

`src/project.py` 负责项目级 pipeline。它知道完整流程：

1. 扫描项目
2. 运行配置启用的 analyzers
3. 组装 `ProjectReport`

这一层存在的原因是让 `scanner.py` 保持纯粹，只处理扫描。

### Scanner 层

`src/scanner.py` 遍历文件系统并返回 `ScanResult`。它把每个文件记录成 `ScannedFile`：

- 绝对路径
- 相对项目根目录的路径
- 小写后缀
- 字节大小

`scanner` 不判断什么是 TODO、不判断 README 是否合格，也不判断依赖是否安全。它只给 analyzer 提供稳定的文件清单。

### Analyzer 层

`src/analyzers` 包含分析逻辑。每个 analyzer 实现 `analyzers/base.py` 里的轻量协议：

```python
class Analyzer(Protocol):
    name: str

    def analyze(self, context: AnalysisContext) -> ProjectAnalysis:
        ...
```

`analyzers/runner.py` 负责：

- 根据名称解析启用的 analyzer
- 拒绝未知 analyzer 名称
- 创建 `AnalysisContext`
- 把各 analyzer 的结果合并成 `ProjectAnalysis`

当前 analyzer：

- `FileTypeAnalyzer`：基于扫描元数据统计文件后缀
- `MarkerAnalyzer`：检查 README、Dockerfile 等项目标记文件
- `TodoAnalyzer`：读取文件并提取 TODO/FIXME

### Reporter 层

`src/reporters/terminal.py` 把 `ProjectReport` 转成适合终端展示的文本。`src/reporters/execution.py` 把 `ExecutionReport` 转成 analyzer 耗时表格。它们不扫描、不分析，也不修改报告数据。

未来如果增加 JSON、Markdown 或 HTML reporter，也应该保持同样模式：接收 report，返回展示结果。

### Telemetry 层

`src/telemetry/` 定义轻量运行时 telemetry：

- `execution_report.py`：定义 `AnalyzerExecution`、`ExecutionReport`、`ProjectExecution` 和结果摘要函数
- `timing.py`：定义 `now_ms()` 和 `elapsed_ms()`

Telemetry 不替代业务报告。普通用户看到的仍是 `ProjectReport` 经 reporter 渲染后的结果；`ExecutionReport` 面向 debug、性能观察和未来可能的 debug 输出。

Analyzer 失败属于 partial failure：runner 会把失败记录成 `AnalyzerFailure`，标记该 analyzer 为 `FAILED`，然后继续执行其他 analyzer。根路径无效、配置非法和未知 analyzer 名称仍然是 fatal error。

当前实现只使用 Python 标准库 `logging` 和 `perf_counter()`，没有引入外部 tracing 或 metrics 系统。

### Model 层

`src/models.py` 定义层之间共享的数据契约：

- `ScanConfig`
- `ScannedFile`
- `ScanResult`
- `TodoItem`
- `ProjectAnalysis`
- `ProjectReport`

这些模型刻意使用明确的 dataclass，而不是松散的 dict。这样重构更安全，测试也能围绕明确字段编写。

### Config 层

`src/config.py` 定义默认值和具体配置 dataclass：

- `ScanConfig`：项目根目录和排除目录
- `AnalyzerConfig`：启用的 analyzer 名称和 analyzer 相关设置

当前项目没有引入运行时 YAML/TOML 配置，因为默认值和测试已经足够。只有出现明确调用方需求时，才应该增加外部配置文件。

## 扩展点

新增 analyzer 的推荐步骤：

1. 在 `src/analyzers/` 下新增模块。
2. 实现一个带唯一 `name` 的 analyzer class。
3. 返回 `ProjectAnalysis`，并且只填充该 analyzer 拥有的字段。
4. 如果需要注册，加入 `analyzers/runner.py` 的 `DEFAULT_ANALYZERS`。
5. 如果默认启用，加入 `config.py` 的 `DEFAULT_ANALYZERS`。
6. 只有当新结果需要展示时，才扩展 `ProjectAnalysis` 和 reporter。
7. 为 analyzer 行为和 runner 集成补充聚焦测试。

优先写 analyzer 内部的小 helper。不要过早创建庞大的共享工具模块。只有当两个 analyzer 真正出现重复解析逻辑时，再抽取共享代码。

新增 telemetry 字段时：

1. 先判断它是否用于理解执行过程，而不是业务报告内容。
2. 如果是运行过程信息，放入 `ExecutionReport` 或 `AnalyzerExecution`。
3. 如果是用户应该看到的项目分析结果，放入 `ProjectAnalysis` 和 reporter。
4. 不要把完整分析结果复制进 telemetry，只记录计数和摘要。

新增 failure 字段时：

1. 如果是 analyzer 运行失败，放入 `AnalyzerFailure`。
2. 如果是项目分析结果的一部分，不要放进 telemetry。
3. 不要为了 partial failure 捕获 `BaseException`。

## 必须保护的边界

- 不要让 `scanner.py` 解析项目语义。
- 不要让 `reporters` 决定分析结果。
- 不要让 analyzer 打印用户输出。
- 不要把 telemetry 数据混进普通业务报告展示。
- 在静态注册没有变痛苦之前，不要引入动态插件加载。
- 除非报告结构真的变得动态，否则不要用通用 dict 替代 dataclass。

## 已知取舍

`ProjectAnalysis` 当前是固定字段的 dataclass。这很简单，也利于类型检查；代价是每新增一个需要展示的 analyzer，可能都要增加字段。以当前规模看，这是合理取舍。如果未来 analyzer 数量变多且结果形状差异很大，可以考虑改成 analyzer 专属 result dataclass，再增加更灵活的聚合层。

`AnalyzerConfig` 当前集中管理配置。优点是设置一眼可见；代价是新增 analyzer 设置时需要修改这个共享 dataclass。除非 analyzer 配置明显变复杂，否则不要急着拆成多个 per-analyzer config class。

`ExecutionReport` 不默认展示给终端用户。CLI 只有在使用 `--execution-report` 时才会追加 analyzer 耗时表格。这保持了普通报告的简洁，也为未来增加 `--debug-report` 或 JSON 输出保留空间。
