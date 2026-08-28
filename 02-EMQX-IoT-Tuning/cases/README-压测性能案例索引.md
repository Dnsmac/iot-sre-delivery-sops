# 压测 / 性能优化案例索引（2026 H2）

> 从会话归档沉淀到本仓的**可面试证据**。现网仓 `D:\gerrit\iot-server` 只读；数字以本表与各案例 README 为准，未实测的不写虚假「优化后 %」。

| 案例 | 主题 | 会话来源 | 状态 |
|------|------|----------|------|
| [`kh-iot-server-operatorCache-OOM-2026-08-17/`](kh-iot-server-operatorCache-OOM-2026-08-17/) | 堆 OOM：5050 台 × 物模型常驻 ~6G | `38135fdd-…` | **已入库** |
| [`openapi-superdevice-tps-2026-08/`](openapi-superdevice-tps-2026-08/) | OpenAPI 五接口未达 100 TPS；拓扑缓存 / 物模型节点缓存 | `17004195-…` + hotfix_36630 | **本次入库** |
| [`es-nfs-write-bottleneck-2026-08/`](es-nfs-write-bottleneck-2026-08/) | 压测期 ES 写 NFS 堵死；iot buffer/dead 积压 | `96cb4a21-…` | **本次入库** |
| [`mqtt-memory-watermark-refuse-2026-08/`](mqtt-memory-watermark-refuse-2026-08/) | 堆水位触发 MQTT 拒连 + eventloop 上 System.gc | `af56bcd6-…` | **本次入库** |
| [`redis-camellia-pool-pressure-2026-08/`](redis-camellia-pool-pressure-2026-08/) | 压测下 camellia 多路复用窄、连接池不同步超时 | `f470e5dc-…` | **本次入库** |
| （挂链）[`../GIIC-15万压测参与复盘.md`](../GIIC-15万压测参与复盘.md) | GIIC 15W 长稳 / 协议侧改造 | 既有 | 已有 |
| （挂链）[`../GIIC-全栈运维优化要点.md`](../GIIC-全栈运维优化要点.md) | Nginx/sysctl/MySQL 三层 | 既有 | 已有 |

## 会话对照（辅助）

| UUID | 一句话 |
|------|--------|
| `96cb4a21-…` | node130 压测：ES NFS IO + iot elasticsearch-buffer |
| `38135fdd-…` | operatorCache MAT / OQL 5050 |
| `889e9961-…` | 日志噪音：checkCommLink / 非法 MQTT（可观测性，非主卖点） |
| `2f1dcfd8-…` | 授权平台本地缓存脏扇出 / 级联相关（正确性为主） |
| `af56bcd6-…` | memory watermark 拒连 |
| `17004195-…` | OpenAPI 五接口 TPS 方案与 PR |
| `f470e5dc-…` | k8s/nginx 环境侧：Redis/camellia/R2DBC 超时 |

## 面试怎么卖（诚实）

1. **旗舰**：GIIC 15W（参与协议/网关侧 + 协助入口/库）  
2. **深度排障**：operatorCache OOM（MAT 铁证）  
3. **接口性能**：五接口瓶颈分层（缓存 vs E2E 等设备）  
4. **存储链路**：ES 写 NFS → buffer/dead（基础设施判断力）  
5. **中间件压测**：camellia 上游窄路 vs 直连 Cluster  

禁止吹：全平台压测方案 owner、未复测的「优化后 TPS=xxx」。
