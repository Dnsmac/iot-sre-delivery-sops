# W3 / W6：中间件（IoT 场景 · Pulsar 优先）

> **原理补课**：[`../middleware/`](../middleware/README.md)（mqtt · pulsar · kafka）  
> **本目录交付**：现网叙事 + 排障 SOP（L1 证据）

| 周 | 交付 |
|----|------|
| W3 | `IoT稳定性排查SOP.md`（可与 02 目录联交） |
| W6 | `中间件排障手册.md` **Pulsar 章**（积压 + 设备峰值） |

解锁：W2 §9（W3）；W5 §9（W6）。

---

## 关联实战案例（交付复盘）

麒麟离线集群上 Redis / Pulsar 安装坑（JWT Secret、Helm pending、Sandbox、ARM64 64KB 页 / Proxy OOM）：

→ [`../01-K8s-Troubleshooting/cases/kylin-offline-k8s-v1.26/`](../01-K8s-Troubleshooting/cases/kylin-offline-k8s-v1.26/)

| SOP | 主题 |
|-----|------|
| `SOP-Redis-Sandbox坏网.md` | Redis 重启 / Calico Sandbox |
| `SOP-Pulsar-JWT-Secret.md` | Pulsar asymmetric-key + pending-install |
| 踩坑清单 #19～#22 | ARM64：Redis 7.2.5（64KB 页）、Pulsar 内存对齐、SSH 静默失败 |
