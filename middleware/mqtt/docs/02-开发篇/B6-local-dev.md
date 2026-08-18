# B6 本地开发环境（Mosquitto / Docker / CLI）

> 优先级: **P2 开发** | 预计阅读 25 分钟 | 深度：已深化

## 本章解决什么问题

在 Windows/Linux/macOS 上 **5 分钟内拉起本仓 Broker**，用 CLI 与 Java 示例联调，理解「MQTT 无建 topic API」的含义。掌握 Docker Compose、配置文件入口，以及 `mosquitto_pub` / `mosquitto_sub` 的日常用法。

---

## 面试常问

1. 本地如何快速验证 MQTT 连通？
2. Mosquitto 默认端口有哪些？WebSocket 呢？
3. Docker 启动的 Broker 配置从哪里挂载？
4. MQTT 有没有「预建 Topic」的 API？
5. 如何用环境变量让 Java 示例连远程 Broker？

---

## 核心知识

### 启动 Broker（Docker Compose）

```powershell
cd docker
docker compose -f docker-compose-mosquitto.yml up -d
```

服务地址：**`tcp://localhost:1883`**、**`ws://localhost:9001`**；TLS 为 **`ssl://localhost:8883`**（需先生成证书，见下）。

Compose 定义（[docker-compose-mosquitto.yml](../../docker/docker-compose-mosquitto.yml)）：

| 项 | 值 |
|----|-----|
| 镜像 | `eclipse-mosquitto:2.0` |
| 容器名 | `mqtt-mosquitto` |
| 端口 | 1883（MQTT）、8883（TLS）、9001（WebSocket） |
| 配置挂载 | `mosquitto.conf`、`mosquitto.passwd`、`certs/` |

### mosquitto.conf 要点

[docker/mosquitto.conf](../../docker/mosquitto.conf) 本地开发配置含 1883、8883、9001。

- **allow_anonymous true**：仅本地学习；生产必须关闭（[A8](../01-面试篇/A8-security.md)）。
- **persistence true**：Broker 重启后保留 QoS1/2 与 retained（视会话）。
- 生产调优项见 [附录 G](../附录/G-config-reference.md)、[C1](../03-运维篇/C1-deployment.md)。

### 无「预建 Topic」

连通探测（任选其一）：

```bash
mosquitto_pub -h localhost -t dev/test/hello -m ping -q 1
```

MQTT **主题在首次 publish 时隐式存在**，Broker 不提供 REST「创建 topic」。

### CLI 快速用法

| 操作 | 命令 |
|------|------|
| 订阅（verbose） | `mosquitto_sub -h localhost -t 'dev/test/#' -v` |
| 发布 QoS1 | `mosquitto_pub -h localhost -t dev/test/hello -m hi -q 1` |
| retain | `mosquitto_pub ... -r` |
| 收一条退出 | `mosquitto_sub ... -C 1` |

完整速查：[附录 F](../附录/F-mosquitto-cli-cheatsheet.md)。

Windows 未装 CLI 时：

```powershell
docker run --rm -p 1883:1883 eclipse-mosquitto:2.0 mosquitto_sub -h host.docker.internal -t 'dev/test/#' -v
```

（Windows 下 `host.docker.internal` 指向宿主机。）

### 与 Java 示例联调

```powershell
cd examples\java
mvn -q -pl mqtt-basics compile exec:java "-Dexec.mainClass=com.demo.mqtt.HelloMqtt"
```

远程 Broker：`$env:MQTT_BROKER = "tcp://192.168.1.8:1883"`

### 停止与重置

```powershell
cd docker
docker compose -f docker-compose-mosquitto.yml down
docker compose -f docker-compose-mosquitto.yml up -d
```

### TLS 8883（本地实验）

按 [docker/certs/README.md](../../docker/certs/README.md) 用 `openssl` 生成 `ca.crt` / `server.crt` / `server.key` 后，再 `docker compose up -d`。

```bash
mosquitto_pub -h localhost -p 8883 --cafile docker/certs/ca.crt -t dev/tls/test -m hi -q 1
```

---

## 面试标准答案

### 题：如何向面试官描述本地 MQTT 环境搭建？

> 我们用 Eclipse Mosquitto 2.0 Docker 镜像，映射 1883 和 9001，配置文件挂载 allow_anonymous 仅用于开发。启动后先用 mosquitto_sub 订阅通配符，再 mosquitto_pub 或 Paho 程序发布，确认双向通路。MQTT 没有创建 topic 的步骤，主题由发布行为隐式出现。Java 侧用环境变量 MQTT_BROKER 切换环境，避免硬编码 IP。

### 题：mosquitto_pub 和 Paho publish 有什么关系？

> 二者都是 MQTT 客户端，对同一 Broker 说话，报文层等价。CLI 适合冒烟；Paho 适合业务集成。

---

## 生产环境注意点

- 本地 **allow_anonymous** 不可带入生产。
- 开发 topic 前缀 `dev/` 与生产隔离；见 [B4](B4-multi-service-conventions.md)。
- 日志：`docker logs mqtt-mosquitto`

---

## 易错点与反例（≥3）

1. **未装 Docker** — compose 失败。
2. **1883 被占用** — 端口映射失败。
3. **8883 无证书** — Broker 启动失败；先生成 certs。
4. **以为 publish 前要先建 topic** — 无此 API。
5. **防火墙拦截远程 MQTT_BROKER** — Java 超时。

---

## 动手验证

1. `cd docker` → `docker compose -f docker-compose-mosquitto.yml up -d`
2. `mosquitto_pub -h localhost -t dev/test/hello -m ping -q 1`
3. `mosquitto_sub` + `mosquitto_pub` 联调
4. 运行 HelloMqtt / SubscribeDemo / QoSDemo
5. `cd examples\java` → `mvn -q compile`

---

## 相关章节

- [B1 Paho 基础](B1-paho-basics.md) · [B8 配置管理](B8-config-management.md)
- [附录 F](../附录/F-mosquitto-cli-cheatsheet.md) · [C1 部署](../03-运维篇/C1-deployment.md)
