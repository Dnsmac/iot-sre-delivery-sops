# 案例：MQTT 内存水位拒连（非业务打满）

> **时间**：2026-08-11  
> **会话**：`af56bcd6-c578-46c2-b9e2-6c420f21a58d`

---

## 结论

`CONNECTION_REFUSED_SERVER_UNAVAILABLE` **不一定是业务压力打满**，可能是 JVM 堆剩余低于水位线后网关**主动拒连**；且在 Vert.x event loop 上调用 `System.gc()`，导致 `BlockedThreadChecker`（例：阻塞 ~31s）。

```text
新连接 → memoryIsOutOfWatermark（剩余 < ~10% 且持续 >5s）
       → System.gc()（堵 event loop）
       → reject SERVER_UNAVAILABLE
```

## 现场要看

- `-Xmx` / 容器 memory limit / heap used  
- 是否与 operatorCache 等大对象常驻叠加（见 OOM 案例）  
- 勿把「拒连」一律解释成「MQTT 连接数打满」

## 一句话

> 堆水位保护会主动拒 MQTT，并可能在 event loop 上 Full GC；要先看堆，再谈连接规模。
