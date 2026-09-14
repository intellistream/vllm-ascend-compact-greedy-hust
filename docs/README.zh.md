# Ascend 紧凑采样 mod

作者与维护者：**张书豪（Shuhao Zhang，@ShuhaoZhangTony）**。本项目不设指导老师。

这是 vLLM-HUST + vLLM-Ascend-HUST 的默认关闭源码 mod：普通 greedy decode
仅交换各 TP 分片最大值和 token ID，其他批次回到完整 logits 与原 sampler。
它只修改 Ascend 后端五个文件，不依赖 StateAxis 的状态治理模块。

独立仓库提供补丁、SHA 清单、底座增量 Git bundle、重建工具、CPU 测试和回退说明。
执行命令见[主页](../README.md)。两个实验底座的最终 commit 尚未在上游仓库发布，
因此先从公开祖先和本仓库 bundle 恢复精确源码；不要直接用最新 main 替代实验 pin。

本版本是**实验性源码 mod**，不是热加载插件。安装候选后，将
`stateaxis_compact_greedy: true` 合并进原 `additional-config`；不要同时开启
`enable_reduce_sample`。关闭新开关需要全体 worker 重启；完整回退使用原版 backend
产物并删除新配置。重建工具本身不安装包、不运行设备或切换在线服务。

当前通过的是源码与 CPU 验证；真实 worker 激活、NPU 数值/通信、API 回退切换和
本 mod 的端到端收益仍待验收。旧 dev8 开关的 +4.42% 不属于本 mod 的性能结果。
