# SOP：kh-iot-server 堆内存卡死 — 现场诊断命令

> 容器名按现网改；PID 一般为 1 或 `docker top` 查看后的 Java PID。

---

## 1. 是否 GC 风暴（30 秒判断）

```bash
docker exec kh-iot-server-1 jstat -gcutil 7 1000 10
```

| 指标 | 危险信号 |
|------|----------|
| O（Old） | 持续 **> 90%** |
| FGC / YGC | **接近 1:1** |
| FGCT | 远大于 YGCT（99%+ 时间在 Full GC） |

---

## 2. 堆里什么对象多

```bash
docker exec kh-iot-server-1 jcmd 7 GC.heap_info
docker exec kh-iot-server-1 jcmd 7 GC.class_histogram | head -30
docker exec kh-iot-server-1 jcmd 7 GC.class_histogram | grep -E "HashMap|JSONObject|JetLinks|byte|ExtendDevice"
```

---

## 3. 是否死锁（通常不是主因）

```bash
docker exec kh-iot-server-1 jstack 7 | head -300
docker exec kh-iot-server-1 jstack 7 | grep -A 20 "BLOCKED\|deadlock"
```

GC 风暴时线程多在 WAITING，**无死锁也仍会卡死**。

---

## 4. 抓 dump

```bash
# 全量（大，11G+）
docker exec kh-iot-server-1 jcmd 7 GC.heap_dump /application/static/upload/emergency-dump.hprof

# 更轻：先 GC 再 live dump
docker exec kh-iot-server-1 jcmd 7 GC.run
sleep 5
docker exec kh-iot-server-1 jcmd 7 GC.heap_dump /application/static/upload/live-dump.hprof
```

---

## 5. 强制 GC 后对比（区分泄漏 vs 临时对象）

```bash
docker exec kh-iot-server-1 jcmd 7 GC.run
sleep 5
docker exec kh-iot-server-1 jcmd 7 GC.class_histogram | grep -E "JSONObject|HashMap |ExtendDevice"
# 10 分钟后再跑一次，数量仍涨 → 泄漏
```

---

## 6. 级联资源监控（若接口可用）

```bash
curl -s http://127.0.0.1:8848/cascade/monitor/resource
curl -s http://127.0.0.1:8848/cascade/monitor/overview
```

---

## 7. 紧急恢复

```bash
docker restart kh-iot-server-1
docker exec kh-iot-server-1 jstat -gcutil 7 5000
```

重启后 Old 若在数小时内再次爬升到 90%+ → 确认慢泄漏/常驻集过大。
