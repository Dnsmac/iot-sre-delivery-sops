# 案例：压测下 Redis / Camellia 连接超时

> **时间**：2026-08  
> **环境**：k8s meta（iot-server ↔ camellia-proxy ↔ redis-cluster）  
> **会话**：`f470e5dc-cd75-481c-af1e-85cb1d2694e5`（同会话含大量探针/运维排查，本案例只抽性能相关）

---

## 1. 典型症状

- `RedisCommandTimeoutException`（数秒～10s）  
- 伴随 `R2dbcTimeoutException: Connection acquisition timed out`  
- Redis Cluster 本身可能仍 `cluster_state: ok`、延迟很低 → **瓶颈在代理与连接池，不在 Redis 算力**

---

## 2. 根因归纳

| 点 | 说明 |
|----|------|
| **窄路上游** | iot-server 连接池较大（如 80）挤进 camellia，camellia 上游到 Redis 连接少 → 压测排队超时 |
| **生命周期不同步** | camellia 重启/重建上游后，iot 池里仍握着旧连接 → 命令无人响应直到 timeout |
| **冷启动** | 滚动重启后 readiness 过早接流量，池未热好 |
| **误判** | 缩业务连接池往往错；压测环境更该考虑 **直连 Redis Cluster** 或加宽 camellia 上游 |

---

## 3. 取舍（面试）

1. 压测环境：iot-server **直连 Redis Cluster**（少一跳多路复用）。  
2. 必须经 camellia：对齐空闲回收 / 假连接探测，避免「旧连接傻等 10s」。  
3. readiness 给足预热时间。  
4. 与 GIIC 入口调优同属「全栈」：应用池 + 代理 + 中间件一起看。

## 4. 一句话

> Redis 集群健康也会超时：压测流量经 camellia 多路复用时上游通道不够，或代理重建后业务池握着假连接；先分清是 Cluster 慢还是代理/池的问题。
