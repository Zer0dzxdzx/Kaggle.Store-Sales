# Store Sales 文档导航

这份导航用于快速判断“现在该读哪份文档”。README 负责项目首页；这里负责把学习记录、验证协议、实验结果和公开展示材料分层整理。

## 1. 5 分钟阅读路线

如果只想快速判断这个项目值不值得继续看，按这个顺序读：

| 顺序 | 文档 | 用途 |
| --- | --- | --- |
| 1 | [README](../README.md) | 项目做什么、当前最好结果、怎么运行 |
| 2 | [最终结果总结](final_result_summary.md) | 当前 champion、public score、失败实验和残余风险 |
| 3 | [项目案例复盘](case_study.md) | 把项目串成完整数据科学案例 |

## 2. 按读者意图选择入口

| 你的目标 | 优先阅读 |
| --- | --- |
| 想复现结果 | [可复现性说明](reproducibility.md) |
| 想确认没有时间序列泄漏 | [验证协议](validation_protocol.md) |
| 想知道为什么某些方案不提交 | [Submission gate](submission_gate.md) |
| 想看完整实验记录 | [结构化实验日志](experiment_log.csv) |
| 想看从 EDA 到建模的主线 | [项目案例复盘](case_study.md) |
| 想继续升级项目 | [进阶升级路线图](advanced_roadmap.md) |

## 3. 复现实验和提交

如果目标是把项目跑起来，优先看这些：

| 文档 | 解决什么问题 |
| --- | --- |
| [可复现性说明](reproducibility.md) | 环境安装、数据放置、验证命令、submission 生成 |
| [验证协议](validation_protocol.md) | 为什么使用 August / pre-test explicit windows |
| [Submission gate](submission_gate.md) | 什么候选可以提交，什么候选应该 block |
| [结构化实验日志](experiment_log.csv) | 每次关键实验的配置、分数、结论和下一步 |

## 4. 学习和复盘路径

如果目标是真正理解这个项目，而不是只看最终分数，按阶段读：

| 阶段 | 文档 | 你应该掌握什么 |
| --- | --- | --- |
| 读题 | [比赛题目说明](store_sales_competition_guide.md) | 预测粒度、时间边界、RMSLE、可用信息 |
| 读数据 | [数据表阅读记录](data_tables_reading.md) | 每张表的业务含义、merge 方式和泄漏风险 |
| 读代码 | [Baseline 阅读记录](baseline_reading.md) | pipeline 如何从原始 CSV 生成 validation 和 submission |
| EDA | [EDA 解读记录](eda_interpretation.md) | 销量、促销、节假日、门店差异带来的建模假设 |
| 误差分析 | [误差分析阅读记录](error_analysis_reading.md) | 为什么要按 family/store/promotion/fold 拆误差 |
| 特征实验 | [特征实验记录](feature_experiments.md) | 如何判断一个特征保留、回滚或继续改 |
| 进阶路线 | [进阶升级路线图](advanced_roadmap.md) | 项目从完整版本升级到进阶版本的方向 |

## 5. 模型和验证报告

| 报告 | 说明 |
| --- | --- |
| [EDA 报告](../reports/eda/eda_report.md) | 数据分布和可视化分析 |
| [基础误差分析](../reports/error_analysis/error_analysis_report.md) | family、store、promotion、fold 误差拆解 |
| [Fold 3 交叉误差](../reports/fold3_cross_error/fold3_cross_error_report.md) | 定位 late fold 变差来源 |
| [School supplies 专题](../reports/family_focus/school_office_supplies/family_focus_report.md) | 失败实验背后的目标切片分析 |
| [模型对比](../reports/model_comparison/comparison_report.md) | seasonal naive、ridge、HistGBDT 等对比 |
| [August LightGBM 验证](../reports/validation/august_lightgbm/validation_window_report.md) | 当前 champion 的主验证报告 |
| [LightGBM tuning](../reports/validation/lightgbm_tuning/comparison_report.md) | 第一轮参数候选对比 |
| [Feature ablation](../reports/feature_ablation/lightgbm_baseline_fast300/ablation_report.md) | 第一轮特征组消融 |

## 6. 公开展示材料

| 文档 | 用法 |
| --- | --- |
| [项目总结](resume_project_summary.md) | 简历项目描述和结果口径 |

岗位定制回答和私人备考材料不放入公开仓库。

## 7. 当前状态

- 当前 best submission：`lightgbm_baseline`
- Kaggle public score：`0.50834`
- 主验证协议：`August / pre-test explicit windows + recursive forecasting + stability checks`
- 当前测试：`11` 个轻量 pytest sanity checks
- CI：GitHub Actions 已配置，push / pull request 到 `main` 时运行 `python -m pytest -q`

## 8. 不要误读的地方

- `school_supplies_aug_promo` 是有价值的失败实验，不是当前默认方案。
- 不同验证口径下的 RMSLE 不能直接比较。
- `transactions.csv` 不能直接按未来日期 merge，只能做历史聚合。
- 当前项目适合作为数据分析 / 数据科学实习作品集，但还不是 leaderboard 级竞赛最终解。
