# 模块职责

本文说明各模块的职责、输入和输出。它不是文件清单，而是维护者判断“代码应该放在哪里”的指南。

## `src/cli.py`

职责：

- 定义命令行接口。
- 把用户参数转换成配置。
- 配置 logging。
- 打印渲染后的输出。

输入：

- 命令行参数
- `ScanConfig`

输出：

- 终端输出
- 由 Typer 管理的进程退出状态

不应该做：

- 遍历文件系统
- 直接运行 analyzer 逻辑
- 手动构造报告区块

## `src/project.py`

职责：

- 协调项目检查 pipeline。
- 把扫描结果和分析结果转换成 `ProjectReport`。
- 在需要时返回包含 telemetry 的 `ProjectExecution`。

输入：

- `ScanConfig`
- 可选的 `AnalyzerConfig`

输出：

- `ProjectReport`
- `ProjectExecution`

不应该做：

- 包含 analyzer 专属检测规则
- 格式化终端输出
- 复制 scanner 的遍历逻辑

这里适合放 pipeline 级别的行为，例如默认 analyzer 配置、报告组装、总耗时记录，以及未来的项目级高层命令。

## `src/scanner.py`

职责：

- 校验项目根目录。
- 遍历项目文件。
- 应用目录排除规则。
- 生成 `ScannedFile` 元数据和 `ScanResult`。

输入：

- `ScanConfig.root`
- `ScanConfig.exclude_dirs`

输出：

- `list[ScannedFile]`
- `ScanResult`

不应该做：

- 解析 TODO、依赖、Docker 设置或安全信号
- 知道哪些 analyzer 被启用
- 渲染输出

scanner 应该保持内容无关。

## `src/analyzers/base.py`

职责：

- 定义 analyzer protocol。
- 定义传给 analyzer 的共享输入 `AnalysisContext`。

输入：

- `ScanResult` 数据
- `AnalyzerConfig`

输出：

- analyzer 实现需要遵守的类型契约

不应该做：

- 注册具体 analyzer
- 包含 analyzer 专属规则

## `src/analyzers/runner.py`

职责：

- 注册内置 analyzer 实例。
- 解析启用的 analyzer 名称。
- 构建 `AnalysisContext`。
- 把 analyzer 输出合并成 `ProjectAnalysis`。
- 记录 analyzer 级别的执行 telemetry。

输入：

- `ScanResult`
- `AnalyzerConfig`
- `Analyzer` 实例 iterable

输出：

- `ProjectAnalysis`
- `list[AnalyzerExecution]`

不应该做：

- 直接检查文件内容
- 包含 TODO、marker、dependency 或 security 检测逻辑
- 格式化报告文本

新增默认 analyzer 时，这个模块是显式注册点之一。

## `src/analyzers/file_types.py`

职责：

- 按文件后缀统计扫描到的文件。

输入：

- `ScannedFile` iterable
- 通过 `FileTypeAnalyzer` 使用时的 `AnalysisContext`

输出：

- `dict[str, int]`
- `ProjectAnalysis(file_types=...)`

不应该做：

- 读取文件内容
- 决定展示层文案，除了内部的 `[no extension]` 分组名

## `src/analyzers/markers.py`

职责：

- 检查项目根目录下配置的 marker 文件。
- 处理 README 的常见文件名变体。

输入：

- 项目根路径
- 配置的 marker 名称
- 通过 `MarkerAnalyzer` 使用时的 `AnalysisContext`

输出：

- `dict[str, bool]`
- `ProjectAnalysis(markers=...)`

不应该做：

- 评估 README 质量
- 解析 marker 文件内容
- 递归扫描 marker 文件，除非 marker 定义本身发生变化

## `src/analyzers/todos.py`

职责：

- 在可读项目文件中查找 TODO/FIXME 类记录。
- 为每条记录保留路径和行号。

输入：

- `list[ScannedFile]`
- 配置的 TODO keywords
- 从磁盘读取的文件内容

输出：

- `list[TodoItem]`
- `ProjectAnalysis(todos=...)`

不应该做：

- 决定 TODO 如何展示
- 因为单个文件不可读而让整个报告失败
- 做和配置 TODO marker 无关的大范围静态分析

## `src/reporters/terminal.py`

职责：

- 把 `ProjectReport` 渲染成适合终端展示的文本。

输入：

- `ProjectReport`

输出：

- `str`

不应该做：

- 运行 analyzer
- 检查文件系统
- 修改报告数据

未来 reporter 也应该保持同样的输入输出形态。

## `src/reporters/execution.py`

职责：

- 把 `ExecutionReport` 渲染成 analyzer 耗时表格。

输入：

- `ExecutionReport`

输出：

- Rich `Table`

不应该做：

- 运行 analyzer
- 计算 analyzer 耗时
- 修改 telemetry 数据

## `src/telemetry/execution_report.py`

职责：

- 定义 analyzer 执行记录。
- 定义项目执行报告。
- 生成分析结果摘要。

输入：

- `ProjectAnalysis`
- `ProjectReport`
- 计时起点
- analyzer 执行元数据

输出：

- `AnalyzerExecution`
- `ExecutionReport`
- `ProjectExecution`
- 简短 result summary

不应该做：

- 替代业务报告
- 读取文件系统
- 打印终端输出
- 引入外部 tracing 或 metrics backend

## `src/telemetry/timing.py`

职责：

- 提供轻量计时 helper。

输入：

- 计时起点

输出：

- 当前毫秒时间
- elapsed 毫秒耗时

不应该做：

- 读取项目状态
- 记录日志
- 知道 analyzer 或 report 结构

Telemetry 的职责是帮助维护者理解系统运行过程。它应该记录摘要和耗时，不应该复制完整项目分析结果。

## `src/observability.py`

职责：

- 作为旧 import 路径的兼容入口。
- 从 `telemetry` re-export telemetry 类型和 helper。

输入：

- 同 `telemetry`

输出：

- 同 `telemetry`

不应该做：

- 承载新的 telemetry 实现
- 增加新的执行逻辑

## `src/models.py`

职责：

- 定义 pipeline 各层共享的 dataclass 契约。

输入：

- 除构造参数外，没有运行时输入

输出：

- 类型明确的模型实例

不应该做：

- 包含业务逻辑
- import 具体 analyzer
- 渲染输出

保持 model 小而稳定。如果某个 dataclass 开始出现较多行为，需要判断这些行为是否应该放到 scanner、analyzer、reporter 或编排层。

## `src/config.py`

职责：

- 提供默认配置值。
- 提供带默认值的具体配置 dataclass。
- 规范化 `ScanConfig.root`。

输入：

- 用户提供的根路径
- 可选的排除目录、marker、keyword、enabled analyzer 覆盖值

输出：

- `ScanConfig`
- `AnalyzerConfig`

不应该做：

- 解析命令行参数
- 在没有明确产品需求前读取外部配置文件
- 注册 analyzer 实例

## `src/logging_utils/logger.py`

职责：

- 配置 Python logging 级别和格式。
- 提供 `get_logger()` 作为未来统一 logger 获取入口。

输入：

- `verbose`
- `debug`
- logger 名称

输出：

- 已配置的进程 logging
- `logging.Logger`

不应该做：

- 输出应用报告
- 决定命令行为

## `src/logging_utils/formatters.py`

职责：

- 定义 logging format 常量。
- 为未来 JSON formatter 或结构化 formatter 预留清晰位置。

输入：

- 无

输出：

- `DEFAULT_LOG_FORMAT`
- `DEBUG_LOG_FORMAT`

不应该做：

- 调用 `logging.basicConfig()`
- 读取 CLI 参数
- import 业务模块

## `src/logging_config.py`

职责：

- 作为旧 import 路径的兼容入口。
- 从 `logging_utils` re-export `setup_logging()` 和 `get_logger()`。

输入：

- 同 `logging_utils.logger`

输出：

- 同 `logging_utils.logger`

不应该做：

- 承载新的 logging 实现
- 增加新的配置逻辑

## `src/main.py`

职责：

- 保留可执行入口和向后兼容 wrapper。

输入：

- 兼容 wrapper 接收的路径字符串

输出：

- wrapper 返回的终端报告字符串

不应该做：

- 成为主要编排模块
- 复制 CLI 行为
