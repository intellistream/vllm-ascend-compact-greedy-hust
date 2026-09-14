# 精确分布式采样研究计划

项目负责人及当前唯一作者：张书豪（ShuhaoZhangTony）。组织：intellistream。
状态：研究孵化；尚无本课题的真实在线性能资格。本文是研究施工记录，不是投稿论文正文。

## 目标与时间

目标会议为 **OSDI ’27**。截至 2026-09-14，官方初步 CFP 的摘要截止为
2026-12-01 22:59 UTC，全文截止为 2026-12-08 22:59 UTC；北京时间分别为
12 月 2 日、12 月 9 日 06:59。CFP 仍为 preliminary，投稿前复核。
[官方 CFP](https://www.usenix.org/conference/osdi27/call-for-papers)。

ASPLOS ’27 九月截止已过；NSDI ’27 秋季摘要注册已于 9 月 10 日结束，不能把
9 月 17 日全文截止当作新课题可直接进入的窗口。
[ASPLOS](https://www.asplos-conference.org/asplos2027/cfp/)；
[NSDI](https://www.usenix.org/conference/nsdi27/call-for-papers)。

工作题目：**面向混合请求的精确分布式采样：按需通信与有界回退**。

研究问题：在词表分片和动态批次中，如何根据输出需求及候选充分性，控制 logits
物化、通信轮次与补算成本，在保持指定采样语义的前提下取得可重复的端到端净收益？

## 贡献边界

- 局部 argmax、Gumbel-Max、分布式归一化、候选质量阈值均不单独宣称原创。
- 混合 greedy/随机、图兼容、少量 logprobs 和 LM-head 融合已有相关工作。
- 待验证增量：按输出契约组织跨卡执行，以可检查的条件决定紧凑信息是否足够；
  仅为不充分请求扩展，并显式约束通信轮数、内存寿命与批次等待。
- 当前 mod 为 greedy 种子实现，旧 enable_reduce_sample 的 +4.42% 不是本课题收益。
- 只减少失败行的工作不等于其他行可独立继续 decode；必须单独测批次屏障影响。

## 假设和退出条件

| 假设 | 反证与退出条件 |
|---|---|
| H1：混合请求使整批完整路径产生可测额外成本 | 同条件 profile 无显著关键路径占比，或简单按行实现已解决，则收窄课题 |
| H2：充分性检查加有界回退能取得精确且更低的总成本 | 检查、扩展、collective 启动或图切换吃掉收益，则拒绝该路径 |
| H3：成本选择优于始终完整/固定预算/简单倍增 | held-out 工作负载无优势，不能把调参后的单点作为贡献 |

必须对比原版 HUST、上一保留版本、当前 greedy mod、简单按行策略和适用的高效精确
sampler。不能只赢慢 PyTorch 基线。负结果和不确定结果保留，不晋升。

## 最小设计

1. 保留原 Transformer batch 与 LM-head GEMM；首版只改变后处理和通信。
2. 为每个请求记录：采样变换顺序、返回字段及 raw/processed 语义、随机数契约、
   request identity/generation、行映射；未审阅的 processor 走完整路径。
3. 对纯 top-p，在处理后完整目标分布上计算归一化量；合并局部候选得到全局 top-K。
   只有候选质量达到 p 才在该候选内确定 nucleus。K 是内部预算，不改变用户 top-k。
4. 失败行扩展预算；达到预登记轮数即回退。各 rank 使用一致的请求映射和 collective
   顺序。图兼容不能靠逐步 CPU tensor.item() 判断，也不能假定动态 shape 免费。
5. 原始/处理后 logprobs、top-k 并列、NaN/Inf、全掩码、温度零、min-p 和组合过滤
   必须分别定义；未定义不能以近似替代。初始 reference 只覆盖精确有理数质量和纯 top-p。
6. 通过第一阶段归因后，再研究按行输出的融合 LM-head；显式计入权重重读和 GEMM 效率。

## 首轮实验

| 实验 | 输入/变量 | 产物 |
|---|---|---|
| E0 参考协议 | 有理数质量、分片、K、阈值、并列/零质量/平坦/集中分布 | 精确支持集及逆 CDF 对照；CPU model-only |
| E1 候选充分性 | 真实模型 logits，真实处理顺序，K 与 top-p 扫描 | 充分率、最小支持集、失败聚集性；离线证据 |
| E2 组件归因 | 原完整、整批回退、按行紧凑、有界精确回退 | 实际通信字节/轮次、GEMM、采样、同步及图开销 |
| E3 在线净收益 | 固定到达率与闭环吞吐、请求混合比例、随机与突发混合 | TPOT/TTFT/P99、SLO goodput、每类请求退化与资源成本 |

性能不预设成功百分比。记录重复次数、配对顺序和置信区间；正确性与净收益同时通过才保留。
主张可迁移性前必须有第二模型；主张跨硬件前必须有第二硬件的独立证据。
GPU 上可用的基线不能直接拿论文百分比与 Ascend 数字比较。

## 里程碑

| 日期 | 交付与决策 |
|---|---|
| 09-21 | E0、输出契约表、强基线版本及相关工作差异表；关闭主要正确性漏洞 |
| 10-05 | E1 和首个受约束设备组件；判断候选检查/通信是否值得继续 |
| 10-19 | E2，固定与自适应策略的完整成本归因；失败则调整研究问题 |
| 11-02 | E3 多模型/混合负载、负结果与消融；判断能否形成系统贡献 |
| 11-16 | 冻结主实验和可重建 artifact；研究主张逐条绑定证据 |
| 11-25 | 作者论文初稿审阅、补关键反例；未通过质量门则顺延而非夸大 |
| 12-01 / 12-08 UTC | 摘要注册 / 全文提交目标；实际投稿由作者执行 |

## 操作与归属

本仓库独立孵化，不改 StateAxis 主任务的工作树或保留版本。原 dev9 patch 与 baseline bundles
保留。每次关键 runtime 修改都新建 mod 版本，记录 pins、文件 SHA、资格、回退。
研究参考模型版本单列，不冒充已安装 runtime。

引擎通用逻辑归 vllm-hust，Ascend 元数据/路径选择归 vllm-ascend-hust，算子/编译器逻辑归
triton-ascend-hust。迁入 runtime 前将依赖固定为本项目 submodule，禁止使用外部可变工作树。
现有 baseline bundle 是恢复既有实验 pin 的历史入口，不表示新设备环境已完成资格。

源码与 CPU 工作不授权服务或设备操作。后续真机遵守物理 NPU4–7、保护 0–3、r153 默认、
每臂独立 r113 恢复以及 /data 存储约束。不得与其他任务抢占设备。

## 本地参考验证

```bash
python -I -B research/test_reference.py
python -I -B research/run_reference.py --output /data/statecentric-builds/sampling-reference-new
```

第二条命令拒绝覆盖，写入源码 SHA、参数和 model-only 结果。不导入 Torch、不访问设备、
不输出推理性能。相关工作见 [related-work.md](related-work.md)，当前施工见 [task_plan.md](task_plan.md)。
