# 案例：BSC IoT + 运维子系统 K8s 离线交付

> **类型**：国产化 K8s 业务交付 / 部署工程化复盘  
> **时间**：2026-08  
> **交付源码**：`C:\Users\kaihong\Desktop\bsc\k8s`（本仓只沉淀结论与面试口径，不复制镜像 tar、Secret、内部 IP 全量清单）  
> **范围**：运维子系统（MySQL InnoDBCluster、Mimir、Loki、Grafana、Categraf、alert-service、dfr、gas）+ IoT 业务（iot-web、iot-server、atomic、data-stream、rule-engine、rule-editor、mcp、zlmedia）

---

## 1. 交付主线

```text
制包机 pull → 内网 docker 机 import Harbor → kubectl 机 deploy
两包：operation（运维）+ iot（业务），同属 meta 命名空间
```

核心改造不是「把 YAML 堆起来」，而是把实施动作收敛成：

1. 两个 `settings.env` 单点配置：运维子系统与 IoT 业务分离。
2. 两个一键部署脚本（`deploy-all.sh` / `deploy-iot.sh`）：配置同步 → 前置预检 → 按依赖 apply → rollout 验证。
3. 一份 `images.txt` 镜像清单：pull / import / 部署前 Harbor 校验共用，避免版本断链。

---

## 2. 价值点（问题 → 方案 → 可验证结果）

| 问题 | 处理 | 结果 |
|------|------|------|
| 约 26 处硬编码 IP 散落 7 个文件 | 按模式收敛到两个 `settings.env`，脚本同步到 ConfigMap/Secret | 换环境只改环境变量，减少漏改与重复审核 |
| Ingress 无域名、节点 80 被 Kuboard 占用 | Ingress 改 catch-all + NodePort；Grafana `:30300` 直连保留排障入口 | 纯 IP 可访问，业务路由唯一权威收敛到 `iot-web` |
| 运维 Ingress 与 `iot-web` 维护两套重复路由 | 归档运维 Ingress，只保留 catch-all 与 `/grafana/` | 降低「改一忘一」风险，接受可控的一跳代理 |
| 镜像缺失要到 Pod 启动才暴露 | 扫描 YAML 全部 image，部署前调 Harbor tags API；不可达降级告警 | 缺镜像在部署前中止，定位从 Pod 事件前移到交付预检 |
| 多数组件无 request/limit，HPA 指标抖动 | 全组件补资源；MySQL buffer pool 128M→4G；dfr request 500m→1 核；gas 去掉内存 HPA | 资源水位可评估，HPA 触发条件更贴近负载 |
| Job 模板不可变、失败被 `\|\| true` 吞掉 | apply 前清理旧 Job；失败显式退出 | 重复部署可执行，关键初始化失败不再静默 |
| 业务网/运维网边界不清 | 输出端口最小化决策说明，按用户侧、运维侧、不对业务网开放归类 | 客户审批清单可直接复用，减少暴露面 |

---

## 3. 关键踩坑

1. **Ingress host 不能填 IP**：apiserver 校验要求 DNS name；最终不写 `host`，由 catch-all 匹配任意 Host。此前只做配置同步未 apply，因此错误结论晚暴露。
2. **幂等不能只看「变化数=0」**：入口地址临时替换后再还原，模式匹配不到测试 IP，显示 0 变化但文件仍残留错误值；规则需覆盖多端口形态，并以内容抽查验证。
3. **kubectl 机未必有 Docker**：镜像导入与集群部署是两台机器、两种前置条件；预检拆开，不能把 Docker 当作 deploy-all 必需项。
4. **Grafana 导入 Job 三类失败**：Secret 键名、旧 Job 模板、MinIO 对象缺失都要分别前置校验。
5. **隐藏死 IP 不在常规入口配置里**：`iot-server` 的 OTLP、Grafana/Loki API 地址需读源码确认，最终改为集群内 Service。

---

## 4. 验收口径

- `kubectl get pods -n meta`：运维子系统与 IoT 业务关键 Pod Ready。
- `kubectl get innodbcluster -n meta`：MySQL 集群 ONLINE。
- Mimir/Loki readiness 通过；Grafana `/api/health` 返回 database ok。
- HTTP 入口可打开业务页面；`/grafana/` 可打开监控页面。
- 设备侧 TCP 端口（如 MQTT/CoAP）按端口决策说明连通。
- 部署脚本重复执行不产生错误残留；配置还原后抽查 YAML 无测试 IP。

---

## 5. 源文档索引（桌面交付包）

| 源文件 | 用途 |
|--------|------|
| `bsc/k8s/交付手册.md` | 实施入口、架构、前置条件、配置单点、一键部署 |
| `bsc/k8s/K8S业务系统部署与运维手册.md` | 业务部署与运维操作 |
| `bsc/k8s/问题排查与解决记录.md` | 问题、根因、修复、预防 |
| `bsc/k8s/西安实验室端口开放与最小化决策说明.md` | 业务网/运维网端口决策 |
| `bsc/k8s/operation/offline-deploy/README-offline.md` | 运维子系统实施入口 |
| `bsc/k8s/iot/offline-deploy/README-offline.md` | IoT 业务实施入口 |

## 6. 面试一句话

> 我把国产化 IoT 与运维子系统整理成两个 settings.env + 两个一键部署脚本：先收敛 26 处死 IP，再补镜像预检、资源限制、Job 幂等和端口最小化；让实施人员不再在几十个 YAML 里找配置，缺镜像也能在部署前发现。
