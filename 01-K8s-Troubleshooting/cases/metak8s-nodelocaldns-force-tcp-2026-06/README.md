# 案例：metak8s 压测环境 NodeLocal DNS 偶发不通

> **时间**：2026-06  
> **环境**：metak8s 6 节点，K8s v1.26.4，meta 命名空间压测  
> **会话**：`e02a1f0b-5121-45ed-8de1-1e6ff168abef`（DNS）· `96cb4a21-a15d-4e39-8858-978dbcadb089`（ES/NFS）  
> **完整归纳**：`C:\Users\kaihong\Desktop\k8s_nginx\docs\metak8s-dns-troubleshooting-summary.md`

---

## 1. 现象

- Kuboard「网络连通性检查」偶发失败，秒级自恢复  
- Pod / Service 间通信偶发不通  
- 24h 长稳难持续通过  

## 2. 根因（DNS · 已修）

NodeLocal DNS 对 `cluster.local` 等 zone 配置 **`force_tcp`** → 缓存未命中时 **TCP 经 IPVS 访问 `10.233.0.3:53`** → 偶发 `i/o timeout`（24h 内 53 次）。

| 对比测试 | 改前 |
|----------|------|
| UDP → NodeLocal | 100/100 成功 |
| TCP → CoreDNS Service IP | 约 23%～50% 失败 |
| TCP → CoreDNS Pod IP 直连 | 50/50 成功 |

**CoreDNS 无需改**；问题在 NodeLocal + IPVS TCP 路径。

## 3. 修复（已落地）

删除 3 处 `force_tcp`，保留 `.:53` 为 `forward . /etc/resolv.conf` → rollout `nodelocaldns`。

**验收**：`dial tcp 10.233.0.3:53` 超时 **归零**；UDP 压测 200/200 通过。

## 4. 同环境 ES 写入（96cb4a21 · 参与排查）

压测期 node130：ES data 在 **NFS**，write 线程满但 CPU 不高；iot `elasticsearch-buffer` 每 pod ~30G。协助 replicas/refresh 调优建议。**与 DNS 为独立链路。**

## 5. 30 秒口述

> 10 万 k8s 压测我主要参与环境稳定性排查。一类是 NodeLocal DNS 开了 force_tcp，缓存 miss 时走 TCP 打 CoreDNS Service，IPVS 偶发超时，Kuboard 网络检查就会秒红又自恢复；去掉 force_tcp rollout 后 dial tcp 超时没了。另一类是 ES 写 NFS 导致 buffer 积压，和 DNS 分开看。

## 6. 面试边界

- **参与**环境排查与配置协助，非 K8s 网络架构 owner  
- `single-request-reopen`、外网改 114 **本次未做**  
- iot-server Pulsar `Namespace not found` **独立配置问题**
