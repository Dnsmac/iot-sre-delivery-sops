# 案例：kh-iot-server 堆内存 OOM / 卡死（operatorCache）

> **类型**：现网稳定性 / JVM 堆泄漏  
> **时间**：2026-08-17  
> **环境**：v3 · Docker 容器 `kh-iot-server-1` · JDK 11 · G1 · `-Xmx8G`  
> **现网源码（只读）**：`D:\gerrit\iot-server`  
> **业务仓归档**：`docs/device/ExtendDeviceClusterConfiguration-operatorCache-OOM分析.md`

---

## 一句话结论

**不是内存给小了，也不是设备数失控。**  
`ExtendDeviceClusterConfiguration.operatorCache` 无界缓存了 **5050 个** `ExtendDeviceOperator`（与现网设备数一致），每台 **3～15 MB** 物模型常驻堆，合计 Dominator **~5.7 GB / 8 GB**，触发 Full GC 风暴卡死。加 6G→8G 只能推迟 2～3 天。

---

## 文档索引

| 文件 | 用途 |
|------|------|
| [`排查复盘.md`](排查复盘.md) | **主文档**：现象 → 排查过程 → 根因 → 与他人结论对照 → 修复优先级 |
| [`SOP-现场诊断命令.md`](SOP-现场诊断命令.md) | jstat / jcmd / jstack 命令清单 |
| [`SOP-MAT分析步骤.md`](SOP-MAT分析步骤.md) | Eclipse MAT 打开 dump、OQL、Histogram 计数 |

---

## 关键数字（面试可背）

| 指标 | 值 |
|------|-----|
| 现网设备数 | **~5000 台出头** |
| `ExtendDeviceOperator` 实例（MAT OQL） | **5,050** |
| Dominator Retained | **6,078,323,032 B（≈5.66 GiB，占堆 78%）** |
| 单台 Operator retained | **3.4 MB～15.6 MB**（超级设备更大） |
| Old 区（jstat） | **长期 96%+** |
| FGC / YGC | **2955 ≈ 2965**（几乎每次 YGC 伴随 Full GC） |
| FGCT | **12,406 s**（99%+ GC 时间在 Full GC） |

---

## 和本仓其它目录的关系

| 位置 | 关系 |
|------|------|
| `02-EMQX-IoT-Tuning/` | **本案例归属**（iot-server JVM / 设备注册表） |
| `docs/现网仓库只读约束.md` | 证据写本仓，不改 `iot-server` |
| `docs/cascade/历史参考/crash-analysis-2026-04-19.md`（业务仓） | 4 月 OOM：RedisClusterManager 修复7 **相邻隐患**，非本次 5.7G 主因 |
| `skills/templates/BUG排查专项模板.md` | BSP 交付包格式参考 |

---

## 修复优先级（合并版）

| 优先级 | 措施 | 改哪里 |
|--------|------|--------|
| **P0** | `operatorCache` → Caffeine `maximumSize` + `expireAfterAccess` | `ExtendDeviceClusterConfiguration.java` |
| **P0** | 订阅 `allDeviceUnRegisterEvent` → `invalidate(deviceId)` | 同上（对齐已废弃 `DeviceMetadataAop`） |
| **P0'** | 父类 `Caffeine.newBuilder()` 补 `maximumSize` | 同上第 66 行 |
| **P1** | 历史补报 `writeDeviceMessageToTs` 绕开 `registry.getDevice()` | `HistoryMessageManagerImpl.java` |
| **P1'** | 级联/设备心跳 **10s → 60s**（止血，约 ×6 降速） | 调度配置 |
| **P2** | RedisClusterManager topic 订阅清理（修复7） | jetlinks-supports 或 cluster Bean 补丁 |
| **P3** | 定时任务管道加 `.timeout()` | 各 Scheduler |

**不要**仅靠调大 `-Xmx` 作为长期方案。
