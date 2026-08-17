# SOP：Eclipse MAT 分析 kh-iot-server heap dump

---

## 1. 打开 dump

1. 安装 [Eclipse MAT](https://eclipse.dev/mat/)
2. **File → Open Heap Dump** → 选 `emergency-dump.hprof` 或 `.hprof.gz`
3. 若提示 leak detection → 选 **Yes**
4. 大 dump 解析慢（10+ 分钟），`MemoryAnalyzer.ini` 可调 `-Xmx12g`

**截断警告**：若 log 出现 `Invalid HPROF file: Expected to read another ... bytes`，Dominator 结论仍可参考，精确计数优先用 Histogram。

---

## 2. 定因：Dominator Tree

1. 打开 **dominator_tree** 标签（或 Overview → Dominator Tree）
2. 找 Retained 最大的对象
3. 本次案例 Top1：`org.jetlinks.pro.device.metadata.ExtendDeviceClusterConfiguration`（~5.7 GB）

**Path to GC Roots**：

1. 右键该对象 → **Path To GC Roots** → **exclude weak references**
2. 展开看引用链：`operatorCache` → `HistoryMessageManagerImpl` / `MqttServerDeviceGateway` / `history-log-worker`

---

## 3. 数 Operator 个数（验证设备数）

### 方法 A：Histogram（推荐）

1. **Histogram**
2. 搜索：`ExtendDeviceOperator`
3. 看 **# Objects** 列 → 本次 **5,050**

### 方法 B：OQL

**Query → OQL Query**，执行：

```sql
SELECT o.@objectId FROM org.jetlinks.pro.device.metadata.ExtendDeviceOperator o
```

看结果窗口底部：**Total: 5,050 entries**

> ❌ `SELECT COUNT(*) FROM ...` — 不支持  
> ❌ `SELECT COUNT(o) FROM ...` — 部分版本报 Method COUNT not found

### 单台占多少内存

```sql
SELECT o.@objectId, o.@retainedHeapSize FROM org.jetlinks.pro.device.metadata.ExtendDeviceOperator o
```

点 **@retainedHeapSize** 列头降序。本次：**3.4 MB～15.6 MB/台**。

---

## 4. Leak Suspects Report

Overview → **Leak Suspects** → 自动生成可疑泄漏报告（dump 完整时可用）。

---

## 5. 堡垒机下不了 11G dump 时

在服务器装 MAT 或用 ParseHeapDump 命令行，只导出报告：

```bash
# 示例路径按服务器 MAT 安装调整
ParseHeapDump.sh emergency-dump.hprof org.eclipse.mat.api:suspects
# 下载生成的 *_Leak_Suspects.zip（通常几 MB）
```

或本机只下载 **Histogram 截图 + Dominator Top3 截图** 作为证据。

---

## 6. 结果判读速查

| MAT 结果 | 含义 |
|----------|------|
| ExtendDeviceOperator ≈ 设备台数 | key 没失控，问题在 **单条太大 + 不淘汰** |
| ExtendDeviceOperator >> 设备台数 | 还有级联/历史 deviceId 被缓存 |
| Dominator 是 ExtendDeviceClusterConfiguration | 修 `operatorCache`（P0） |
| Dominator 是 RedisClusterManager 相关 | 走 4 月修复7 路线（P2） |
