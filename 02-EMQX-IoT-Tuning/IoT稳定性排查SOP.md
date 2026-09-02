# IoT 稳定性排查 SOP（故事 #3 · operatorCache OOM 实例）

> **用途**：回答「线上故障怎么处理」——把「排查做过、无 SOP」变成「现象→命令→根因→修复→结果」五段。
> **实例**：kh-iot-server 堆内存 OOM / 卡死（operatorCache），素材见 [`cases/kh-iot-server-operatorCache-OOM-2026-08-17/`](cases/kh-iot-server-operatorCache-OOM-2026-08-17/)。
> **口述稿**：[`../05-Interview-Prep/口述稿/W3-稳定性.md`](../05-Interview-Prep/口述稿/W3-稳定性.md)

---

## 一、通用 SOP 骨架（五段 · 可套任意故障）

```text
现象（1 句 + 数字 + 时长）
  → 现场采样（jstat / jcmd / jstack，30 秒先判断是不是 GC/泄漏）
  → 定因（dump + MAT Dominator / OQL）
  → 止血（重启 / 限流 / 关副本）
  → 长期（改代码 / 缓存上限 / 换盘）+ 验证标准
```

> **铁律（以后第一眼查什么）**：`Old 长期 >90% + FGC≈YGC` → 先怀疑**堆常驻集过大**，不是调 `-Xmx`；`class_histogram` 只能看「有什么类」，定因必须 **dump + Dominator Tree**。

---

## 二、现象（真实数字）

| 现象 | 数字 |
|------|------|
| 卡死 | 跑 ~2.7 天后接口超时、消息停滞；**6G 和 8G 堆都一样卡** |
| `jstat -gcutil` | **Old 96.41%** 恒定；YGC≈FGC；**FGCT 12406 s**（99% 时间在 Full GC） |
| `jstack` | 319 线程无死锁，大量 WAITING（GC 风暴特征） |
| `class_histogram` | 1800 万 `JSONObject`、1800 万 `HashMap`、20 万 `JetLinksDeviceMetadata` |

> **一句话现象**：`6G/8G 都卡 + Old 长期 >90% + FGC≈YGC` → 堆常驻集过大，不是内存给小了。

---

## 三、排查命令（3 条 · 可复制）

```bash
# 1. 判断是不是 GC 风暴（30 秒）
docker exec kh-iot-server-1 jstat -gcutil 7 1000 10

# 2. 堆里什么对象多
docker exec kh-iot-server-1 jcmd 7 GC.class_histogram | grep -E "HashMap|JSONObject|JetLinks|ExtendDevice"

# 3. 抓 dump（堡垒机限制时先 GC 再 live dump，文件更小）
docker exec kh-iot-server-1 jcmd 7 GC.run
sleep 5
docker exec kh-iot-server-1 jcmd 7 GC.heap_dump /application/static/upload/live-dump.hprof
```

> 详见 [`SOP-现场诊断命令.md`](cases/kh-iot-server-operatorCache-OOM-2026-08-17/SOP-现场诊断命令.md)（含强 GC 后对比区分「泄漏 vs 临时对象」）。

---

## 四、根因（MAT Dominator → OQL 闭环）

**Dominator Tree**：Top1 = `ExtendDeviceClusterConfiguration`，Retained **6,078,323,032 B（≈5.66 GiB，占堆 78%）**。

**Path to GC Roots**：

```text
ExtendDeviceClusterConfiguration（operatorCache）
  └── ExtendDeviceClusterConfiguration$1（ClusterDeviceRegistry 匿名子类）
        ├── registry ← HistoryMessageManagerImpl（history-log-worker 补报）
        └── registry ← MqttServerDeviceGateway × N
```

**OQL 验证「5000 台」**：

```sql
SELECT o.@objectId FROM org.jetlinks.pro.device.metadata.ExtendDeviceOperator o
-- Total: 5,050 entries  →  与现网 ~5000 台一致，key 没失控
SELECT o.@objectId, o.@retainedHeapSize FROM ...ExtendDeviceOperator o
-- 单台 3.4 MB ~ 15.6 MB
```

**根因公式**：

```text
5050 个 cache key（= 设备数，有限）
× 每台 3～15 MB 物模型对象树（~3600 HashMap/台）
× operatorCache 无 maximumSize / 无 TTL / 注销不 invalidate
≈ Dominator 5.7 GB → 8G 堆剩 <2G → Full GC 风暴 → 卡死
```

> **关键结论（面试金句）**：`设备数有限 ≠ 内存安全`——`有限 key × 胖 value × 不淘汰` 照样 OOM。histogram 里上千万 HashMap 是每台物模型 JSON 展开的**枝叶**，不是上千万台设备。

---

## 五、修复与验证

| 优先级 | 措施 | 改哪 |
|--------|------|------|
| **P0** | `operatorCache` → Caffeine `maximumSize` + `expireAfterAccess` | `ExtendDeviceClusterConfiguration.java` |
| **P0** | 订阅 `allDeviceUnRegisterEvent` → `invalidate(deviceId)` | 同上（对齐已废弃 `DeviceMetadataAop`） |
| **P1** | 历史补报 `writeDeviceMessageToTs` 绕开 `registry.getDevice()` | `HistoryMessageManagerImpl.java` |
| **P1** | 心跳 **10s → 60s**（止血，约 ×6 降速） | 调度配置 |
| **P2** | RedisClusterManager 订阅清理（4 月遗留，非本次主因） | jetlinks-supports |

**紧急恢复**：`docker restart kh-iot-server-1`，重启后 `jstat` 观察 Old 是否数小时内再爬升。

**验证标准**：

| 检查项 | 通过 |
|--------|------|
| 72h `jstat` Old | 稳定 < 70% |
| MAT `ExtendDeviceOperator` 个数 | ≤ maximumSize，随下线下降 |
| Dominator Retained | < 500 MB |

---

## 六、面试 90 秒（可背）

> 现网 kh-iot-server 跑两三天就卡死，6G 和 8G 堆都一样。我用 `jstat` 看 Old 区长期 96%，Full GC 次数几乎等于 Young GC，FGCT 一万多秒——这是堆常驻集过大，不是内存给小了。抓了 heap dump 用 MAT 看 Dominator，发现 `ExtendDeviceClusterConfiguration` 一个对象占了堆的 78%。沿 GC Root 追到 `operatorCache`：一个无界 Map 缓存了 5050 个 DeviceOperator，和 5000 台设备数一致，但每台物模型在堆里占 3 到 15 兆，合计约 5.7G 把堆吃满了。histogram 里上千万 HashMap 是物模型 JSON 展开的内部节点，不是上千万设备。修复方向是给 operatorCache 加 Caffeine 上限和过期、设备注销时 invalidate，历史补报不要每条都走 registry.getDevice；加内存只能推迟，不能根治。

---

## 七、自检

- [ ] 五段完整：现象数字 → 3 条命令 → 根因公式 → 修复 → 验证标准
- [ ] 能说清「5.7G / 78% / 5050 × 3~15MB」三个数字
- [ ] 能主动说「有限 key × 胖 value × 不淘汰」这个反直觉结论
- [ ] 能区分主因（operatorCache）与副因（RedisClusterManager / 心跳 10s）
