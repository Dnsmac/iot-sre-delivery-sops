# 公云 IoT 对照（AWS / Azure / 阿里）

> JD-14 §1.7 · 深度目标 **L0→L1**

---

## L0 · 30 秒定义

公有云 IoT 把「设备接入、身份、规则、影子、消息路由」托管成托管服务；自建平台（JetLinks/iot-server）是 **同能力域的自研实现**，组件名不同、链路思想相近。

---

## L1 · 我们平台有没有

| 云能力 | 自建近似 | 现网 |
|--------|----------|------|
| 设备注册/身份 | MySQL 产品+设备+密钥 | ✅ |
| Device Shadow | 最新态表 + Redis 会话 | ⚠️ 概念对齐，非 AWS API |
| Rules Engine | EventBus + 规则引擎 | ✅ |
| 消息桥接 | Pulsar 级联 | ✅ |
| 时序存储 | ES / TDengine | ✅ ES 主 |

**诚实**：未在生产使用 AWS IoT Core / Azure IoT Hub。

---

## L2 · 我的证据（STAR）

暂无公云落地；用 **「我们对照过架构，现网是自研栈」** 即可。

---

## L3 · 深挖

| AWS IoT Core | 一句话 |
|--------------|--------|
| Thing / Registry | 设备实体与证书 |
| Device Shadow | desired/reported JSON 文档 |
| Rules | SQL-like 规则触发 Lambda/Kinesis |
| Jobs | OTA 批量任务 |

**面试用法**：「我熟悉自建链路；公云 IoT 我按组件对照理解，便于和云原生团队沟通。」

---

## 还不懂 / 下一步

- [ ] AWS IoT Core 官方「概念」页 20min
- [ ] 画一张「AWS Shadow ↔ 我们最新态+下行」对照草图
