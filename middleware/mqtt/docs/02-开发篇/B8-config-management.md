# B8 配置管理（环境变量、密钥、Profile）

> 优先级: **P2 开发** | 预计阅读 30 分钟 | 深度：已深化

## 本章解决什么问题

把 MQTT 连接参数从 **硬编码** 迁到 **可环境切换的配置体系**：Broker URL、clientId 规则、认证、TLS、cleanSession、keepAlive 等如何在 dev/stg/prod 间一致管理，并与本仓 Java 示例的 `MQTT_BROKER` 环境变量、Spring `application-{profile}.yml` 对齐。避免密钥进 Git、避免生产误连开发 Broker。

---

## 面试常问

1. MQTT 配置哪些必须外置？哪些可以默认？
2. 设备 clientId 和后端服务 clientId 策略有何不同？
3. 密码如何注入 K8s / Spring Boot？
4. `cleanSession` 在生产能否一律 true？
5. Profile 切换时如何防止连错 Broker？

---

## 核心知识

### 配置项清单

| 键 | 含义 | 开发默认 | 生产 |
|----|------|----------|------|
| `broker-url` / `MQTT_BROKER` | `tcp://` 或 `ssl://` | `tcp://localhost:1883` | 集群 VIP + TLS |
| `client-id` | 会话标识 | 随机后缀 | 服务：实例唯一；设备：出厂 ID |
| `username` / `password` | 认证 | 空（匿名） | 强密码 / 证书 |
| `clean-session` | 会话持久 | `true` | 设备常 `false` |
| `keep-alive-interval` | 心跳秒 | `60` | 统一平台值 |
| `connection-timeout` | TCP 连接超时 | `30` | 视网络 |
| `automatic-reconnect` | 自动重连 | `true` | `true` + 告警 |
| `max-inflight` | QoS1/2 窗口 | 默认 | 压测后调 |

附录全集：[G 配置参考](../附录/G-config-reference.md)。

### 本仓示例：环境变量

[HelloMqtt.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/HelloMqtt.java)、[SubscribeDemo.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/SubscribeDemo.java)、[QoSDemo.java](../../examples/java/mqtt-basics/src/main/java/com/demo/mqtt/QoSDemo.java) 统一：

```java
String broker = System.getenv().getOrDefault("MQTT_BROKER", "tcp://localhost:1883");
```

PowerShell：

```powershell
$env:MQTT_BROKER = "tcp://dev-broker.corp:1883"
$env:MQTT_USERNAME = "dev_svc"   # 自扩展读取，示例未内置
```

Linux：

```bash
export MQTT_BROKER=ssl://mqtt.prod.example:8883
mvn -q compile exec:java -Dexec.mainClass=com.demo.mqtt.SubscribeDemo
```

**原则：** 示例代码只演示协议；**认证逻辑**在业务项目用配置文件或 Secret 注入，不要提交 `.env` 到仓库。

### Spring Boot 结构化配置

```yaml
# application.yml — 默认值
mqtt:
  broker-url: tcp://localhost:1883
  client-id: order-service-${random.uuid}
  username: ""
  password: ""
  clean-session: true
  keep-alive-interval: 60
  connection-timeout: 30
  automatic-reconnect: true
  topics:
    telemetry: acme/iot/+/telemetry
    command: acme/iot/{deviceId}/command
```

```yaml
# application-prod.yml — 仅覆盖差异
mqtt:
  broker-url: ssl://mqtt.prod.example:8883
  client-id: order-service-${HOSTNAME}
  clean-session: true
```

绑定类：

```java
@ConfigurationProperties(prefix = "mqtt")
public record MqttProperties(
    String brokerUrl,
    String clientId,
    String username,
    String password,
    boolean cleanSession,
    int keepAliveInterval) {}
```

与 [B7](B7-spring-mqtt.md) 的 `MqttPahoClientFactory` `@Bean` 注入 `MqttProperties` 即可。

### 密钥与 Profile

| 环境 | Broker | 密钥来源 |
|------|--------|----------|
| local | [B6](B6-local-dev.md) Docker | 匿名或本地 passwd 文件 |
| stg |  staging 集群 | CI Secret / Vault |
| prod | 生产集群 | K8s `Secret`、云厂商凭据库 |

```
禁止：application-prod.yml 里 password: MyPwd123
推荐：password: ${MQTT_PASSWORD}  由部署平台注入
```

Spring Profile：`spring.profiles.active=prod` 时只加载 `application-prod.yml` 差异；**基线**放 `application.yml`。

### clientId 策略（设备 vs 服务）

| 类型 | 策略 | 原因 |
|------|------|------|
| 后端微服务 | `服务名-实例ID` 或随机 UUID | 避免多副本互踢；会话可 clean |
| 网关 | 固定网关 ID | 桥接状态可追踪 |
| 设备 | 出厂唯一、终身不变 | cleanSession=false 时恢复会话与下行 |

反例：设备每次启动 `device-${random}` 导致 **下行堆积无法投递**。

### TLS 与 URI

- 开发：`tcp://localhost:1883`
- 生产：`ssl://host:8883` + truststore / 双向证书
- WebSocket：`wss://` 与 [B6](B6-local-dev.md) 的 9001 仅用于调试

### 与 Topic 规范联动

主题前缀不要散落在十个 `@Value` 里；用 `mqtt.topics.*` 或配置中心单表维护，与 [B4](B4-multi-service-conventions.md) 文档一致。发布 command 时 **用模板替换 `{deviceId}`**，避免字符串拼接 bug。

### 环境差异矩阵

详见 [附录 J](../附录/J-env-diff-matrix.md)、[B12 环境模型](B12-environment-models.md)。迁移检查：[附录 I](../附录/I-env-migration-checklist.md)。

---

## 面试标准答案

### 题：MQTT 配置生产要注意什么？

> 第一，Broker 地址和 TLS 随环境切换，禁止写死 localhost。第二，认证信息从环境变量或 Secret 注入，不进版本库。第三，clientId 对设备和服务要分开策略，避免随机 ID 造成会话无法恢复。第四，cleanSession 不是越大越安全，设备需要持久会话时必须为 false 并配合 QoS1 下行。第五，topic 前缀与 ACL 在 Broker 侧强制，应用配置只是第二道防线。上线前用 staging 账号跑一遍 publish/subscribe 冒烟。

### 题：为什么示例用环境变量而不是配置文件？

> 示例模块是极简 Maven 工程，没有 Spring Boot，用 MQTT_BROKER 环境变量零依赖切换 Broker，适合培训和 CI。真实 Spring 项目用 ConfigurationProperties 更合适，因为能类型校验、多字段、Profile 分层。两者并不矛盾：CLI 和容器注入环境变量，Spring 再把环境变量映射到 properties（Spring Boot 天然支持 MQTT_BROKER 绑定到 mqtt.broker-url 的 relaxed binding）。

---

## 生产环境注意点

- **配置审计**：谁改了 `application-prod.yml` 的 broker-url。
- **启动校验**：`@PostConstruct` 检查 broker-url 不以 `tcp://localhost` 出现在 prod profile。
- **轮换密码**：Broker 与客户端同步轮换，避免只改一端。
- **只读挂载**：容器内配置文件只读，Secret 内存挂载。
- 结合 [A8 安全](../01-面试篇/A8-security.md) 关闭匿名、启用 ACL。

---

## 易错点与反例（≥3）

1. **把 mosquitto.passwd 提交 Git** — 泄露；反例：仓库已有 passwd 模板未 .gitignore 生产副本。
2. **prod profile 仍指向 localhost:1883** — 连到空或错环境；反例：复制 yml 未改 url。
3. **设备 cleanSession=true 却要离线必达下行** — 断线丢订阅；反例：抄后端配置到固件。
4. **clientId 仅服务名无实例后缀** — K8s 三副本互踢；反例：三个 pod 都是 `order-service`。
5. **topic 硬编码 dev/test 上线** — ACL 拒发或数据进错租户；反例：HelloMqtt 的 topic 原样投产。

---

## 动手验证

1. 本地默认：不设置变量，运行 HelloMqtt 连 `localhost:1883`（先 [B6](B6-local-dev.md)）。
2. 切换 Broker：`$env:MQTT_BROKER="tcp://127.0.0.1:1883"` 验证与 localhost 等价。
3. 故意错误：`$env:MQTT_BROKER="tcp://127.0.0.1:19999"` 观察 `MqttException` 连接超时。
4. Spring 自练：建 `application-dev.yml` / `application-prod.yml`，`spring.profiles.active=dev` 打印绑定的 `mqtt.broker-url`。
5. 对照 [附录 G](../附录/G-config-reference.md) 列出本团队必填项检查表。

---

## 相关章节

- [B1 Paho 基础](B1-paho-basics.md) · [B6 本地开发](B6-local-dev.md) · [B7 Spring Integration](B7-spring-mqtt.md)
- [B4 Topic 规范](B4-multi-service-conventions.md) · [B12 环境模型](B12-environment-models.md)
- [A8 安全](../01-面试篇/A8-security.md) · [附录 J 环境矩阵](../附录/J-env-diff-matrix.md)
