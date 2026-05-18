# 生产服务 → K8s 概念映射（W1 主交付物）

> 目的：把「赶鸭子上架跑起来」变成面试能讲的结构。每项填 **你怎么暴露端口、怎么做健康检查、出过什么问题**。

| 组件 | 在 K8s 里是什么 | Service / Ingress | 配置来源 | 资源 limits 是否设过 | 生产问题（脱敏） |
|------|-----------------|-------------------|----------|----------------------|------------------|
| MetalLB | | LoadBalancer | | | |
| Nacos | | | ConfigMap/Secret? | | |
| Pulsar 集群 | StatefulSet 典型 | | | | |
| MySQL 三主 | StatefulSet + PVC | Headless? | | | |
| Redis 集群 | | | | | |
| ES 集群 | | | | | |
| MinIO | | | | | |
| iot-server | Deployment | | Nacos 拉配置 | | |
| 达梦 | 集群内/集群外? | | | | |

## 与实验室的对应关系（W2 用）

| 生产现象（你填） | 实验室复现方式 |
|------------------|----------------|
| 例：Pod OOM | limits 故意设小 + 压测 |
| 例：探针误杀 | 错误 command / 短 initialDelay |
| 例：Service 不通 | selector 标签错误 |
