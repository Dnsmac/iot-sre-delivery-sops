# IoT 连接与模块（W1～W3 · v3）

> 目录名 `EMQX` 为历史命名；现网 **内嵌 MqttServer(:1883) + EventBus**；Pulsar 用于 **级联** 等场景。  
> **MQTT/Pulsar 原理**：[`../middleware/`](../middleware/README.md)

| 周 | 手册 | 交付 |
|----|------|------|
| **W1** | [`W1_全景信心手册.md`](W1_全景信心手册.md) | 全链路骨架 + JD雷达 |
| W2 | `W2_连接手册.md`（W1 §9 后） | 全链路定稿、连接治理、协议卡片 |
| W3 | `W3_稳定性手册.md`（W2 §9 后） | `IoT稳定性排查SOP.md` |
| **W4～W5** | [`W4-W5_模块故事手册.md`](W4-W5_模块故事手册.md) | `iot-server模块故事.md` |
| **W6** | [`W1_压测复盘手册.md`](W1_压测复盘手册.md) | [`40万压测参与复盘.md`](40万压测参与复盘.md) + [`GIIC-15万压测参与复盘.md`](GIIC-15万压测参与复盘.md) + [`GIIC-全栈运维优化要点.md`](GIIC-全栈运维优化要点.md)（`docs/ops`） |

### 现网稳定性案例

| 案例 | 说明 |
|------|------|
| [`cases/kh-iot-server-operatorCache-OOM-2026-08-17/`](cases/kh-iot-server-operatorCache-OOM-2026-08-17/) | **v3 堆 OOM 卡死**：5050 台 × operatorCache 无界 · MAT Dominator 5.7G |

路径：[`../05-Interview-Prep/学习路径与面试串讲.md`](../05-Interview-Prep/学习路径与面试串讲.md)
