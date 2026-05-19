# 生产服务 → K8s 概念映射（W1 作业，D7 提交）

> 在 [`W1_每日学习手册.md`](W1_每日学习手册.md) D1～D6 每天边学边填；D7 必须 **9 行全填**。

| 组件 | 在 K8s 里是什么 | Service / Ingress | 配置来源 | 资源 limits 是否设过 | 生产问题（脱敏） |
|------|-----------------|-------------------|----------|----------------------|------------------|
| MetalLB | Controller Deploy + Speaker DS（6 节点） | 为 LB Service 分 VIP | IPAddressPool `first-pool` | — | L2 宣告；Event: node6 layer2 |
| iot-web（meta） | Deployment（后端 3 Pod） | **LoadBalancer** VIP 192.168.27.190 | Nacos 等 | 待填 | 80 HTTP + **1883 MQTT**；ClusterIP 10.233.40.193 |
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
