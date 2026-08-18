# C1 部署：Mosquitto 开发与 EMQX 生产

> 优先级: **P3 运维** | 预计阅读 30 分钟 | 深度：已深化

## 本章解决什么问题

建立 **开发—预发—生产** 三套 Broker 部署心智：本地用 Docker Mosquitto 快速验证协议与客户端；生产用 **EMQX 集群 + 负载均衡 + TLS**，避免把单机 Mosquitto 直接扛全量设备。读完能画出端口、证书、命名空间与 Helm 发布顺序。

---

## 面试常问

1. Mosquitto 和 EMQX 分别适合什么环境？能否生产单机 Mosquitto？
2. MQTT 常用端口 1883/8883/8083/8084 各是什么？
3. K8s 里 EMQX 用 StatefulSet 还是 Deployment？为什么？
4. 多可用区部署 MQTT 要注意什么？
5. 开发环境与生产 ACL、匿名策略如何隔离？

---

## 核心知识

### 角色分工

| 环境 | Broker | 典型规模 | 本仓入口 |
|------|--------|----------|----------|
| 本地开发 | Mosquitto 2.x Docker | 数十连接 | `docker/docker-compose-mosquitto.yml` |
| CI/联调 | Mosquitto 或 EMQX 单节点 | 数百连接 | 与生产配置结构对齐 |
| 生产 | EMQX 5.x 集群 | 万～百万连接 | Helm / 安装包 + LB |

### 开发：Mosquitto

```text
开发者 → tcp://localhost:1883 → Mosquitto 容器
         ws://localhost:9001   （可选 WebSocket 调试）
```

- 本仓 `docker compose` 拉起 compose。
- `mosquitto.conf`：`listener 1883`、`persistence true`；生产前务必关闭 `allow_anonymous`。
- 密码与 ACL：`mosquitto.passwd`、`acl_file`（见 [附录 G](../附录/G-config-reference.md)）。

### 生产：EMQX

```text
设备 ──TLS 8883──► LB(Nginx/云 LB) ──► EMQX 节点 × N
                      │
                      ├── 管理 API 18083（内网）
                      └── Dashboard（仅运维网段）
```

- **前置 LB**：四层 TCP 透传 8883，会话粘滞 **非必须**（MQTT 有 ClientID）；管理面走 HTTPS。
- **Helm 关键项**：`replicaCount`、`resources`、`persistence`（会话/规则状态）、`service.type`、证书 Secret。
- **命名**：K8s Namespace 按环境隔离，如 `mqtt-prod` / `mqtt-staging`；ClientID、主题前缀与 [B4](../02-开发篇/B4-multi-service-conventions.md) 一致。

### 端口速查

| 端口 | 协议 | 用途 |
|------|------|------|
| 1883 | MQTT TCP | 明文（仅内网/开发） |
| 8883 | MQTT over TLS | 生产设备接入 |
| 8083/8084 | MQTT over WS/WSS | Web、小程序 |
| 18083 | HTTP | EMQX Dashboard/API |

---

## 生产环境注意点

- **禁止** 生产开放匿名与 1883 公网暴露；证书链与设备 CA 要版本化管理。
- Mosquitto 与 EMQX **配置项名称不同**，迁移时逐项对照（`max_connections` vs `zone` 等）。
- 发布顺序：先扩 Broker 容量 → 再灰度设备批次；回滚保留上一版 Helm values。
- 日志：容器 stdout + 集中采集；CONNECT/DISCONNECT 审计合规场景要开。
- 与 Pulsar/Kafka 同机部署时，**网络分区** 优先保证 MQTT 接入层可用（见 [C4](C4-bridge.md)）。

---

## 易错点与反例

1. **生产单机 Mosquitto 扛 10W 连接** — 文件句柄、单线程模型不适合；应用 EMQX 集群（见 [C11](C11-loadtest-connections.md)）。
2. **LB 七层终止 TLS 但未配置 WebSocket 升级** — 8084 场景连接失败。
3. **开发 `allow_anonymous true` 抄到生产** — 未授权发布/订阅。
4. **Helm 未设 resource limit** — 节点 OOM 拖垮整池 Pod。
5. **ClientID 无环境前缀** — 预发与生产抢会话导致互踢。

---

## 动手验证

```powershell
# 本仓 Mosquitto
cd docker; docker compose -f docker-compose-mosquitto.yml up -d
mosquitto_pub -h localhost -t dev/deploy/test -m "ok" -q 1
mosquitto_sub -h localhost -t dev/deploy/test -C 1

# 检查监听
docker compose -f docker/docker-compose-mosquitto.yml ps
```

EMQX 单节点试用（需自行拉镜像）：

```bash
docker run -d --name emqx -p 1883:1883 -p 8883:8883 -p 18083:18083 emqx/emqx:5
curl -u admin:public http://localhost:18083/api/v5/status
```

---

## 相关章节

- [C2 容量](C2-capacity.md) | [C8 高可用](C8-ha-cluster.md) | [C9 升级](C9-upgrade.md)
- [B6 本地开发](../02-开发篇/B6-local-dev.md) | [P10 K8s 问题](../04-问题百科/P10-k8s.md)
- [附录 F Mosquitto CLI](../附录/F-mosquitto-cli-cheatsheet.md)
