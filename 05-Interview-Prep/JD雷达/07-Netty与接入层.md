# 07 Netty 与接入层

> 三行定稿（可背）· 对齐 CoAP-TCP / Reactor + 入口 Nginx 经验

## 定义

Netty 是高性能 NIO 网络框架；接入层负责连接生命周期、编解码与背压。生产上接入前还有 **Nginx TCP 代理 + 内核参数**，和业务 Netty/Reactor 同属容量面。

## 现网有没有

**有接入层。** MQTT 侧有 Vert.x/内嵌服务；GIIC 在 **CoAP-TCP 组件**里管连接队列、Sink、并发。压测教训：全局单管道会背压整网；改为 **per-connection**；Sink 满则 **reject**。入口侧另调 **临时端口 / hash(ip+port) / max_fails**（见运维要点）。

## 面试 30 秒

> 接入层要管连接数、队列和背压。我们 GIIC 从全局单管道改成每条 TCP 独立队列；前面 Nginx 还要防端口耗尽和误摘后端。上层再用 L1 和异步写 Redis。这是「入口代理 + 网络层 + 业务热路径」一起治。

---

## 补课（可选）

- 被问 Netty 线程模型：boss/worker、勿在 IO 线程 block
- 运维摘要：[`GIIC-全栈运维优化要点.md`](../../02-EMQX-IoT-Tuning/GIIC-全栈运维优化要点.md)
