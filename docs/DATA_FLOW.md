# 数据流

本文说明数据如何从 CLI 命令流向最终终端报告。它面向需要新增 analyzer 或调整 pipeline 的维护者，重点是避免职责混杂。

## 高层流程

```text
用户命令
-> cli.scan()
-> project.build_project_report()
-> scanner.scan_project()
-> analyzers.run_analyzers()
-> models.ProjectReport
-> telemetry.ExecutionReport
-> reporters.render_terminal_report()
-> 终端输出
```

## 第 1 步：CLI 接收用户输入

`src/cli.py` 中的 Typer 命令接收：

- `path`：需要检查的项目目录
- `--verbose`：开启 info 级别日志
- `--debug`：开启 debug 级别日志

CLI 用用户路径创建 `ScanConfig`，然后传给 `build_project_report()`。

CLI 不自己扫描文件，也不知道默认运行哪些 analyzer。

## 第 2 步：Project Pipeline 协调工作

`src/project.py` 是编排层。它接收：

- `ScanConfig`
- 可选的 `AnalyzerConfig`

它执行三个动作：

1. 调用 `scan_project(config)` 得到 `ScanResult`。
2. 调用 `run_analyzers(scan_result, analyzer_config)` 得到 `ProjectAnalysis`。
3. 记录扫描、分析和整体 pipeline 的耗时。

然后组装：

```python
ProjectReport(
    root=config.root,
    total_files=len(scan_result.files),
    analysis=analysis,
)
```

当调用方需要运行过程信息时，可以使用 `build_project_execution()`，它会返回：

```python
ProjectExecution(
    report=ProjectReport(...),
    execution=ExecutionReport(...),
)
```

这样 pipeline 保持在一个清晰位置，而不会把分析职责或 telemetry 组装逻辑塞进 scanner。

## 第 3 步：Scanner 构建文件清单

`src/scanner.py` 校验项目根目录，并使用 `os.walk()` 遍历文件系统。

输入：

- `ScanConfig.root`
- `ScanConfig.exclude_dirs`

输出：

- `ScanResult`

每个文件会变成一个 `ScannedFile`：

```python
ScannedFile(
    path=absolute_path,
    relative_path=path_relative_to_root,
    suffix=lowercase_suffix,
    size=file_size,
)
```

scanner 遇到不可访问文件时会跳过，并记录 debug 日志。除了文件系统元数据，它不读取文件内容。需要内容的行为属于 analyzer。

## 第 4 步：Analyzer Runner 创建上下文

`src/analyzers/runner.py` 接收：

- `ScanResult`
- `AnalyzerConfig`
- 已注册 analyzer 实例的 iterable

runner 会把启用的 analyzer 名称映射到已注册 analyzer。未知 analyzer 名称会提前抛出 `ValueError`，避免返回部分分析结果。

runner 创建 `AnalysisContext`：

```python
AnalysisContext(
    root=scan_result.root,
    files=scan_result.files,
    config=analyzer_config,
)
```

这个 context 会传给每个启用的 analyzer。

runner 同时负责记录 analyzer 级别的执行信息：

- analyzer 名称
- 执行状态
- 耗时
- 错误信息
- 简短结果摘要

## 第 5 步：Analyzer 产出局部分析结果

每个 analyzer 返回一个 `ProjectAnalysis`，只填充自己拥有的字段。runner 会为每次 analyzer 执行创建一个 `AnalyzerExecution`。

当前行为：

- `FileTypeAnalyzer` 使用 `ScannedFile.suffix`，返回 `file_types`。
- `MarkerAnalyzer` 检查项目根目录下配置的 marker 文件，返回 `markers`。
- `TodoAnalyzer` 读取文件文本，检测 TODO/FIXME，返回 `todos`。

Analyzer 不应该修改 `ScanResult`，也不应该写输出。它们也不应该自己测量性能；耗时由 runner 统一记录。Analyzer 应该尽量是 `AnalysisContext` 加可读项目文件的确定性函数。

## 第 6 步：Runner 合并分析结果

runner 把多个局部 `ProjectAnalysis` 合并成一个 `ProjectAnalysis`。

当前合并规则：

- dict 做浅合并
- 待办事项列表按 analyzer 执行顺序拼接

只要每个 analyzer 拥有不同的报告字段，这个规则就足够。如果未来两个 analyzer 写入同一个 dict key，需要先定义所有权规则，再加入第二个写入方。

## 第 7 步：ProjectReport 成为展示契约

`ProjectReport` 包含：

- 项目根路径
- 文件总数
- 聚合后的 `ProjectAnalysis`

它还暴露兼容属性：

- `report.file_types`
- `report.markers`
- `report.todos`

Reporter 应该依赖 `ProjectReport`，而不是依赖 scanner 或 analyzer 的内部实现。

## 第 8 步：ExecutionReport 记录运行过程

`ExecutionReport` 包含：

- 项目根路径
- 总耗时
- 扫描耗时
- 分析耗时
- 文件总数
- 每个 analyzer 的 `AnalyzerExecution`
- analyzer 失败时的 `AnalyzerFailure`

它不是普通用户报告，也不应该默认渲染到终端报告中。它的用途是帮助维护者理解系统运行过程、定位慢 analyzer、确认 analyzer 是否被执行，以及为未来 debug 输出提供结构化数据。

当 CLI 使用 `--execution-report` 时，终端会在普通项目报告后追加 analyzer 耗时表格。

## 第 9 步：Reporter 渲染输出

`src/reporters/terminal.py` 把 `ProjectReport` 转成字符串。

Reporter 决定标签、排序和面向人的状态文本。它不决定 marker 是否存在，也不决定什么算 TODO。

`src/cli.py` 打印渲染后的字符串时关闭 Rich markup，这样 `[no extension]` 这类报告值会按字面显示。

## 失败行为

- 根路径不存在时抛出 `FileNotFoundError`。
- 根路径不是目录时抛出 `NotADirectoryError`。
- 单个文件不可访问时跳过，并记录 debug 日志。
- analyzer 名称未知时抛出 `ValueError`。
- 待办事项分析中遇到不可读文件时跳过，并记录 debug 日志。
- analyzer 执行失败时记录结构化 failure，并继续执行其他 analyzer。

这些选择偏向生成轻量报告，而不是因为单个文件不可读就让整个项目检查失败。
