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

### 2026-04-16

#### 阶段 5：跑通真实数据 baseline

- 使用 `data/raw/` 中的真实 Kaggle 原始数据运行了当前 `HistGradientBoostingRegressor` 基线。
- 成功生成：
  - `artifacts/validation_metrics.json`
  - `artifacts/validation_predictions.csv`
  - `artifacts/submission.csv`
- 本次运行使用：
  - `train_start_date=2015-01-01`
  - `validation_horizon=16`
  - `model_type=hist_gbdt`
  - `random_state=42`

结果：

- 首个真实离线验证分数为 `RMSLE = 0.423002`
- Kaggle 公开榜分数为 `0.58410`
- 验证集行数为 `28,512`
- 提交文件行数为 `28,512`
- 预测值最小值为 `0.0`，最大值约为 `13031.17`

结论：

- 当前仓库已经从“工程基线可运行”进入“真实比赛基线已落地”的阶段。
- 后续所有实验都可以围绕这次真实 baseline 做对照，不需要再从合成数据结果出发。
- 公开榜分数明显高于单窗口离线分数，说明当前离线验证可能偏乐观；下一步应优先增加多窗口验证，而不是只追单次 holdout。

下一步：

1. 增加多窗口验证，检查离线分数与公开榜的相关性。
2. 把这次真实 baseline 作为 `experiment_log.csv` 中的主参照版本。
3. 尝试更稳的季节性/分组特征，或切换到更强的 `LightGBM` 后端。

#### 阶段 6：实现多窗口验证与自动实验日志

- 在 pipeline 中新增多窗口验证能力：
  - `validation_windows` 控制验证窗口数量
  - `validation_step_days` 控制相邻窗口间隔
  - 每个窗口都会输出独立的 `validation_predictions_fold_*.csv`
  - 汇总输出到 `validation_summary.csv`
- 在 metrics 中新增多窗口汇总指标：
  - `validation_rmsle_mean`
  - `validation_rmsle_std`
  - `validation_rmsle_min`
  - `validation_rmsle_max`
  - 每折起止日期、训练行数、验证行数与预测文件路径
- 新增 `src/store_sales/experiment_log.py`，支持在 CLI 运行结束后自动追加结构化实验日志。
- CLI 新增参数：
  - `--validation-windows`
  - `--validation-step-days`
  - `--log-experiment`
  - `--experiment-name`
  - `--experiment-log-path`
  - `--data-snapshot`
  - `--experiment-conclusion`
  - `--experiment-next-action`

结论：

- 后续实验可以直接用多窗口均值和标准差判断稳定性，不再只依赖最后一个 holdout。
- 实验记录可以由命令行自动写入，减少手工记录遗漏。

#### 阶段 7：新增 EDA 可视化报告

- 新增 `src/store_sales/eda.py`，用于生成可复现的 EDA 报告。
- 报告输出目录为 `reports/eda/`，包含：
  - `eda_report.md`
  - `figures/*.png`
  - `tables/*.csv`
- 当前 EDA 覆盖：
  - 全局每日销售趋势
  - family 销售排名
  - family 零销量比例
  - 星期周期
  - 促销与销售关系
  - 油价与月销售趋势
  - 节假日/事件日期平均销售
  - 门店 type/cluster 销售差异
  - 多窗口验证 fold 分数

结论：

- EDA 报告用于解释当前模型误差来源和指导下一轮特征工程。
- 下一步应结合验证误差分组，进一步检查哪些 family/store 是 public score 偏高的主要来源。

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
