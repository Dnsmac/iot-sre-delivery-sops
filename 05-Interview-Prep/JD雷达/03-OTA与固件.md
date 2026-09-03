# 03 OTA 与固件

> 三行定稿（可背）· 与 GIIC 压测弱相关，防概念空

## 定义

OTA 是远程下发固件/配置并确认版本；要管分片、校验、回滚与升级状态机。

**我们项目**：平台管「任务 + 状态机 + 下发指令」，固件包存 URL，**设备自行 HTTP 下载**；平台侧不做固件分片传输，靠 **sign/signMethod（MD5/SHA256）** 做完整性校验。

## 现网有没有

**有，且是完整平台能力**（`device-manager` 模块），不是概念层：

| 能力 | 代码/表 | 说明 |
|------|---------|------|
| 固件包管理 | `FirmwareController` / `dev_firmware` | url、sign、signMethod、size、versionOrder |
| 设备当前版本 | `DeviceFirmwareController` / `dev_firmware_info` | 设备上报或升级成功后镜像 |
| 升级任务 | `FirmwareUpgradeTaskController` / `dev_firmware_upgrade_task` | 绑定产品+固件，deploy 生成 per-device 历史 |
| 升级历史 | `dev_firmware_upgrade_history` | 单设备升级状态机，主键 `md5(taskId+deviceId)` |
| 级联同步 | `DevFirmwareInfoDataHandler` | 上下级平台同步 `dev_firmware_info` |

**两种升级模式**（`FirmwareUpgradeMode`）：

- **push**：平台主动发 `UpgradeFirmwareMessage`，带 url/sign/version/taskId
- **pull**：设备发 `RequestFirmwareMessage`，平台回 `RequestFirmwareMessageReply`（含下载地址）

**我近阶段主战场**仍是 **接入长连接与 Login/Token**（GIIC 压测），不是 OTA 方案 owner；但 OTA 下行和属性下发走**同一条会话路由**——`DeviceRegistry → messageSender()`，集群里会话在 Redis，路由到持有连接的 Pod。

## 面试 30 秒

> OTA 在我们平台是完整能力：上传固件包、建任务、按设备生成升级记录，再 push 或等设备 pull。状态机是 waiting → pushed → processing → success/failed。固件文件不在平台分片传，只下发 URL 和签名校验信息，设备自己下载。下行走 DeviceOperator.messageSender，和 GIIC 接入一样依赖会话在哪台 Pod、Redis 路由。我近期证据在 15 万级稳连，OTA 能讲清链路和状态机，但不吹成个人主责。

---

## 我们项目怎么做（补课 · 可展开）

### 1. 端到端链路

```text
[管理端]
  上传固件 → dev_firmware（url/sign/version）
  创建任务 → dev_firmware_upgrade_task
  POST /firmware/upgrade/task/{id}/_deploy → 批量写 dev_firmware_upgrade_history（waiting）

[平台下发]
  push 模式：
    手动：WebSocket 订阅 /device-firmware/publish?taskId=… → DeviceFirmwarePublishProvider
    自动：DeviceFirmwareService @PostConstruct 每 30s 扫 waiting+在线设备 → publishTaskUpgrade
  pull 模式：
    设备 RequestFirmwareMessage → @Subscribe("/device/*/*/firmware/pull") → 回 url/sign

[设备侧]
  HTTP 下载固件包 → 本地校验 sign → 刷写 → 上报 progress / report

[平台收敛]
  @Subscribe("/device/*/*/firmware/progress") → 更新 history 状态/进度
  @Subscribe("/device/*/*/firmware/report")   → 更新 dev_firmware_info 当前版本
  定时器 30s：pushed/processing 超 timeoutSeconds → failed（升级超时）
```

协议 Topic（official / GIIC 一致）：

- 下行：`/*/firmware/upgrade`（UpgradeFirmwareMessage）
- 上行：`/*/firmware/upgrade/progress`、`/*/firmware/report`、`/*/firmware/pull`

`application.yml` 里 GIIC 下行类型含 `upgradeFirmware/readFirmware/pullFirmware`。

### 2. 状态机（面试常问）

**任务级**（`FirmwareUpgradeTaskState`）：`waiting → processing → canceled`

**设备级**（`FirmwareUpgradeState`）：

| 状态 | 含义 |
|------|------|
| waiting | 任务已 deploy，待下发 |
| pushed | 已发 UpgradeFirmware / 已回 pull 地址 |
| processing | 设备上报 progress，未完成 |
| success | progress complete=true |
| failed | 失败原因 / 响应超时 / 升级超时 |
| canceled | 任务停止 |

关键约束：

- deploy 时过滤：当前 `versionOrder` 已 ≥ 目标固件则跳过；可选 `versionCheck`
- 排除已有更高版本 history（waiting/pushed/processing/success）
- push 只更新 `state=waiting` 的行，防设备过快响应把状态冲掉
- `serverId=Cluster.id()`：push 任务绑创建节点，多实例不重复推

### 3. 和「分片 / 校验 / 回滚」怎么答

| JD 概念 | 我们项目 |
|---------|----------|
| 分片传输 | **平台不分片**；整包 URL，设备端下载（常见 OTA 做法） |
| 校验 | 平台存 `sign` + `signMethod`（MD5/SHA256），随 UpgradeFirmware / pull reply 带给设备 |
| 回滚 | **无平台自动回滚**；可再建任务推旧版，或设备本地 A/B（看端侧） |
| 状态机 | 上表；`stage`/`progress`/`errorReason`/`completeTime` 在 history 表 |
| 生效窗口 | `effectiveStartTime/effectiveEndTime`（按小时段，如仅夜间升级） |
| 超时 | history 级 `timeoutSeconds` + `upgradeTime`；30s 批处理标 failed |

### 4. 下行怎么到设备（和接入的关系）

```text
DeviceFirmwareService.publishTaskUpgrade
  → deviceRegistry.getDevice(deviceId)
  → operator.messageSender().send(UpgradeFirmwareMessage)
  → 集群：查 Redis 会话所在 serverId → RPC/路由到对应 Pod → 网关编码 → GIIC/MQTT/…
```

OTA 下发前会打 session 日志（`LostDeviceSession` 表示设备不在线）。**这和属性写、功能调用是同一条路**，所以我能讲「会话路由」而不必假装深度做过 OTA 压测。

### 5. EventBus 在 OTA 里的角色

设备固件消息进 EventBus 后，由 `@Subscribe` 消费（`SpringMessageBroker` 注册）：

- `/device/*/*/firmware/report` → `syncDeviceFirmwareInfo`
- `/device/*/*/firmware/progress` → `updateProgress`
- `/device/*/*/firmware/pull` → `handlePullFirmware`

前端看升级进度：`FirmwareHistorySubscriptionProvider`（WebSocket 订阅 history 变更）。

### 6. 级联 / 超级设备

- 级联：`DevFirmwareInfoDataHandler` 同步下级 `dev_firmware_info` 到上级
- 超级设备：`SuperDeviceManagerImpl` 用 `dev_firmware_info.version` 判断 KaihongOS 5.0.1 兼容路径

### 7. 诚实边界（防穿帮）

- **做过**：读链路、排过 OTA 下发/session/连接池问题（`DeviceFirmwareService` 注释里可见压测优化：短事务、异步镜像、无长事务占连接池）
- **没做主责**：大规模 OTA 压测、端侧刷写策略、差分包算法
- **GIIC 压测**：OTA 不是主战场；若问性能，答「下行与会话绑定，瓶颈在连接数/路由，不在固件包传输」

---

## 面试追问速答

**Q：谁负责分片？**  
A：平台只给 URL+签名，分片/断点续传在设备或 CDN，不在 iot-server。

**Q：怎么知道升级成功？**  
A：设备发 `UpgradeFirmwareProgressMessage`，`complete=true && success=true` 后 history→success，并异步写 `dev_firmware_info`。

**Q：多 Pod 会不会重复推？**  
A：history 带 `serverId`，自动 push 只扫本节点；手动 push 也 filter `Cluster.id()`。

**Q：pull 和 push 选型？**  
A：push 适合平台主动、批量在线设备；pull 适合设备定时拉取、弱网或超级设备批量问任务。

---

## 补课（可选）

- 代码入口：`DeviceFirmwareService.java`（核心）、`FirmwareUpgradeTaskService.deploy`
- 表：`dev_firmware` / `dev_firmware_info` / `dev_firmware_upgrade_history` / `dev_firmware_upgrade_task`
- 协议：`khlinks-giic-protocol/.../TopicMessageCodec.java` 固件相关枚举
- 部署脚本：`deploy/upgrade/20251113/fix_firmware_lock.sql`（历史锁问题）
