# Store Sales 项目日志

## 项目概览

- 项目名称：`Kaggle Store Sales`
- 仓库路径：`/Users/du/Desktop/codex/Store Sales`
- GitHub 仓库：`https://github.com/Zer0dzxdzx/Kaggle.Store-Sales`
- 当前目标：围绕 Kaggle `Store Sales - Time Series Forecasting` 比赛，建立可迭代的时序预测工程基线，并逐步提升验证与榜单表现。
- 结构化实验记录文件：`docs/experiment_log.csv`

## 记录规则

后续建议每次发生下面任一事件时追加一条日志：

- 新增或重构核心模块
- 修正影响训练/验证正确性的逻辑
- 更新重要文档
- 完成一次有意义的实验
- 调整验证方案、特征方案或模型方案

如果需要快速回顾实验版本、分数、结论和下一步，优先查看 `docs/experiment_log.csv`。本文件更适合记录阶段性里程碑和背景说明。

建议每条日志至少包含：

- 日期
- 目标
- 改动内容
- 结果
- 风险/问题
- 下一步

## 时间线

### 2026-04-15

#### 阶段 1：初始化项目与基线流水线

- 本地初始化 Git 仓库，并建立基础目录结构。
- 创建了模块化训练框架，核心模块包括：
  - `src/store_sales/data.py`
  - `src/store_sales/features.py`
  - `src/store_sales/modeling.py`
  - `src/store_sales/pipeline.py`
  - `src/store_sales/cli.py`
- 建立了从原始 CSV 到训练、验证、递归预测、提交文件导出的完整流程。
- 默认模型采用 `HistGradientBoostingRegressor`，同时预留 `LightGBM` 可选后端接口。
- 在特征侧加入了：
  - 日历特征
  - 滞后特征
  - 滚动统计特征
  - 油价特征
  - 节假日/事件特征
  - 门店静态特征
  - 发薪日与地震冲击特征
- 为验证过程实现了递归预测逻辑，避免多步预测时错误使用未来真实销量。
- 对 `transactions` 的使用加了时间边界，避免验证阶段聚合到未来信息。

结果：

- 项目形成了可运行的 baseline。
- 生成了 `README.md`、`pyproject.toml` 和基础忽略规则。
- 在合成数据上完成了端到端 smoke test。

相关提交：

- `b8972b8` `feat: add modular store sales baseline pipeline`

#### 阶段 2：发布到 GitHub

- 配置远端 `origin` 为 `git@github.com:Zer0dzxdzx/Kaggle.Store-Sales.git`。
- 将本地 `main` 分支首次推送到 GitHub 仓库。

结果：

- 本地与远端仓库打通，后续可以直接基于 `origin/main` 继续迭代。

#### 阶段 3：补充比赛说明文档

- 新增了 `docs/store_sales_competition_guide.md`，系统整理比赛目标、数据表结构、评估指标、验证方案、特征工程重点、建模路线与常见坑。
- 将比赛说明入口挂到 `README.md`。
- 对公开镜像中“测试窗口 15 天/16 天”表述不一致的问题进行了说明，并明确建议以手头原始 `test.csv` 的真实日期范围为准。
- 将 `README.md` 中默认验证窗口的说法调整为“本地默认验证窗口”，避免把工程参数写成官方题面事实。
- 将 `.DS_Store` 加入 `.gitignore`。

结果：

- 仓库文档从“仅有使用说明”升级为“包含比赛理解、建模建议与工程记录入口”的状态。

相关提交：

- `ac0009d` `docs: add detailed store sales competition guide`

#### 阶段 4：补充项目日志

- 新增本文件 `docs/project_log.md`，用于持续记录项目进展、关键设计决策、验证结果与后续计划。
- 将项目日志入口挂到 `README.md`。

当前状态：

- 仓库具备基础建模能力与文档说明能力。
- 代码和文档均已过一轮子代理复核。
- 目前尚未在真实 Kaggle 原始数据上完成一次正式训练与提交验证。

下一阶段里程碑：

1. 下载并放置真实 Kaggle 原始 CSV，跑通首次正式训练。
2. 记录首个真实验证分数与首个公开榜单分数。
3. 增加多窗口时序验证，避免只盯最后一个窗口。
4. 继续迭代节假日处理、促销特征与更强模型。

## 日志模板

后续可以直接复制下面这段继续追加：

```md
### YYYY-MM-DD

#### 阶段 X：标题

- 目标：
- 改动：
- 结果：
- 风险/问题：
- 下一步：

相关提交：

- `commit_hash` `commit message`
```
