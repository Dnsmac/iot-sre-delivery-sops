# D1 学习记录：Kubernetes Workload（计算负载）

> W1 · 手册 D1 · 后续将补充：网络路由、存储、底层组件（另文）  
> **与面试题双向对齐**：[`../interview/Workload_面试题清单.md`](../interview/Workload_面试题清单.md)  
> 学习日期：________

---

## 0. K8s 概念四分法（本文范围）

| 大类 | 本文 | 后续文档 |
|------|------|----------|
| **计算 Workload** | ✅ 本文 | — |
| 网络路由 | — | 待补（Service/Ingress/MetalLB 见 D2） |
| 存储 | — | 待补（PV/PVC/StorageClass） |
| 底层组件 | — | 待补（kubelet、控制平面等） |

---

## 1. 核心机制：声明式 API + 控制循环

```text
期望状态（YAML）  ←对比→  实际状态（集群）
         ↑ 不一致则调谐
    控制器（kube-controller-manager 内）
```

| 要点 | 说明 |
|------|------|
| 声明式 | 只描述「要什么」，不写逐步操作 |
| 控制循环 | 各控制器死循环对比期望 vs 实际，自动修复 |
| 管理者 | Deployment / StatefulSet / DaemonSet / Job 等逻辑在 **kube-controller-manager** |

**比喻**：Deployment 像值班经理——柜台要始终有 N 杯完好奶茶（Pod）；打翻一杯就补一杯。

---

## 2. Deployment — 无状态应用

### 2.1 层级关系

```text
Deployment → ReplicaSet → Pod
```

- **Deployment 不直接管 Pod**，管 ReplicaSet；RS 管 Pod 副本。
- 滚动更新时：新建 RS、逐步扩新缩旧；**保留旧 RS** 便于回滚。

### 2.2 适用场景

| 项 | 说明 |
|----|------|
| 场景 | Web、API 网关、**iot-server** 等无状态服务 |
| Pod 身份 | 名称含随机串，重建后 **会变** |
| 顺序 | 无启动顺序要求，副本 **地位平等** |
| 存储 | 可挂共享卷；无「每 Pod 独立盘」强需求 |
| 访问 | 常配 **ClusterIP** Service 做负载均衡 |

### 2.3 更新策略

| 策略 | 行为 |
|------|------|
| **RollingUpdate**（默认） | `maxSurge`：最多多几个副本；`maxUnavailable`：最多几个不可用 |
| **Recreate** | 先删光旧 Pod 再建新 Pod → **会断服** |

---

## 3. StatefulSet — 有状态应用

### 3.1 解决什么问题

Deployment 搞不定：**固定身份、启动顺序、每副本独立盘**。

### 3.2 核心特性

| 特性 | 说明 |
|------|------|
| **稳定网络标识** | 固定 Pod 名如 `app-0`、`app-1`，重启 **不变** |
| **有序部署/扩缩/删** | 如必须先 `app-0` 再 `app-1` |
| **独立持久化** | `volumeClaimTemplates` 每 Pod 一个 PVC，跟着 Pod 走 |

### 3.3 必须配合 Headless Service

- **Headless Service**：`clusterIP: None`
- 为每个 Pod 提供 **稳定 DNS**：`<pod名>.<svc>.<ns>.svc.cluster.local`
- 面试句：**StatefulSet 必须配 Headless Service**（稳定标识 + 服务发现）

### 3.4 更新策略

| 策略 | 说明 |
|------|------|
| **RollingUpdate** | 可用 **Partition**：如 `Partition=2` 只更新序号 ≥2 的 Pod（金丝雀/灰度） |
| **OnDelete** | 仅手动删 Pod 才重建更新 |

### 3.5 适用场景（对应你现网）

| 组件 | 典型 Workload |
|------|---------------|
| Pulsar、MySQL、Redis、ES | **StatefulSet**（集群 + 有状态 + PVC） |
| Nacos、MinIO | 常为 STS 或 Operator，以现网为准 |

---

## 4. DaemonSet — 节点级守护

### 4.1 工作原理

- **每个（或部分）节点恰好一个** Pod；新节点加入 → 自动起一个；节点移除 → Pod 回收。
- **不盯副本总数**，盯 **节点覆盖率**。
- 调度特点：可视为 **绕过常规「凑副本数」思维**，按节点铺满（仍受污点/容忍影响）。

### 4.2 典型场景

| 场景 | 例子 |
|------|------|
| 监控采集 | Node Exporter |
| 日志 | Fluentd、Filebeat |
| 网络 | Calico/Cilium Agent |
| **你现网** | **MetalLB Speaker**（6 节点 → 6 个 Speaker） |

### 4.3 何时不会调度到某节点

- 节点有 **污点（Taint）**，且 Pod **没有对应 Toleration** → 该节点 **不** 跑该 DaemonSet Pod。

---

## 5. Job 与 CronJob — 一次性/定时任务

### 5.1 Job

| 项 | 说明 |
|----|------|
| 目标 | 让指定数量 Pod **成功跑完并退出**（exit 0） |
| 失败重试 | **backoffLimit** 控制重试次数 |
| 并行 | 可并行多 Pod 加速批处理 |

### 5.2 CronJob

- 类似 **crontab**，按时间表创建 Job。
- 注意：**并发策略**（任务重叠）、**错过调度**（startingDeadlineSeconds 等）。

### 5.3 适用场景

备份、报表、定期清理、一次性迁移脚本等——**不是**长期对外提供服务的 iot-web 这类。

---

## 6. 对比总表（面试必背）

| 维度 | Deployment | StatefulSet | DaemonSet | Job/CronJob |
|------|------------|-------------|-----------|-------------|
| 状态 | 无状态 | 有状态 | 节点守护 | 跑完即结束 |
| Pod 名 | 随机变 | 稳定有序 | 随节点 | 一次性 |
| 扩缩顺序 | 并行 | **有序** | 每节点 1 个 | 完成数导向 |
| 存储 | 可共享 | **每 Pod 独立 PVC** | 视场景 | 视场景 |
| 典型 Service | ClusterIP | **Headless** | 常 HostNetwork/无对外 | 常无 |
| 你现网例子 | **iot-server** | Pulsar/MySQL/Redis/ES | **MetalLB Speaker** | （按项目） |

### 6.1 四句话本质

| 问题 | 答案 |
|------|------|
| Deployment vs StatefulSet？ | **网络标识 + 存储是否必须稳定、有序** |
| DaemonSet 特殊在哪？ | **按节点覆盖**，不是凑副本数 |
| Job 失败？ | **backoffLimit** 重试 |
| StatefulSet 必须配什么？ | **Headless Service** |
| DaemonSet 不调度？ | 节点 **污点** 且 Pod **不容忍** |

---

## 7. 生产配套：HPA 与 PDB

| 对象 | 作用 | 场景 |
|------|------|------|
| **HPA** | 按 CPU/内存/自定义指标自动改 **Deployment/STS/RS** 副本数 | 突发流量扩容、闲时缩容 |
| **PDB** | 限制 **自愿中断** 时最多几个 Pod 同时不可用 | 节点维护、驱逐时保住最低可用 |

Workload 只管「跑起来几个 Pod」；**HPA/PDB** 管弹性与维护底线。

---

## 8. 其他：ReplicaSet 与静态 Pod

### 8.1 ReplicaSet（幕后）

- 用户常只写 Deployment，底层 **RS 持 Pod**。
- 更新 = 新 RS 扩容 + 旧 RS 缩容；旧 RS 保留用于 **回滚**。

### 8.2 静态 Pod（了解）

| 项 | 说明 |
|----|------|
| 谁管 | 节点 **kubelet** 直接管，**不经 API Server 调度** |
| 特点 | 控制平面挂了，节点上静态 Pod 仍可运行 |
| 用途 | 常跑 **apiserver、etcd** 等控制平面组件（自托管集群） |

---

## 9. 结合现项目（与 `生产服务清单` 对照）

| 组件 | 推断 Workload | 你要在集群确认的 |
|------|---------------|------------------|
| iot-server / iot-web 后端 | **Deployment** | `kubectl get deploy -n meta` |
| Pulsar | **StatefulSet** | `kubectl get sts -n <ns>` |
| MySQL 三主 | **StatefulSet** | 同上 + PVC |
| Redis / ES | **StatefulSet** 或 Operator | 同上 |
| MetalLB Speaker | **DaemonSet** | `kubectl get ds -n metallb-system` |
| MetalLB Controller | **Deployment**（通常 1 副本） | 同上 |

> MySQL/Pulsar 等 **PVC** 见 [`D4_存储.md`](D4_存储.md) §8。

**D1 填写命令**：

```bash
kubectl get deploy,sts,ds -A | findstr /i "iot pulsar mysql redis es nacos minio metallb"
kubectl get deploy <名> -n <ns> -o wide
kubectl describe deploy|sts|ds <名> -n <ns>
```

---

## 10. 自检（D1 Workload）

- [ ] 能画 Deployment → RS → Pod
- [ ] 能说出 STS 三条：固定名、有序、独立 PVC
- [ ] 能解释 DaemonSet 与 Deployment 调度差异
- [ ] 能对应现网至少 **3 个** 组件的 Workload 类型
- [ ] 知道 STS 为什么要 Headless Service

---

## 11. 面试复习（题 ↔ 笔记）

| 笔记节 | 题号见 |
|--------|--------|
| §2 Deployment | 1～6、15～17 |
| §3 StatefulSet | 7～12、18 |
| §4 DaemonSet | 13、14、19 |
| §5 Job/CronJob | 20～22 |
| §7 HPA/PDB | 23～24 |
| §8 静态 Pod | 25 |
| §9 现网 | 26～28 |

- 题清单：[`../interview/Workload_面试题清单.md`](../interview/Workload_面试题清单.md)  
- 答案：[`../interview/answers/Workload_答案.md`](../interview/answers/Workload_答案.md)

---

## 12. 参考

- Workloads：https://kubernetes.io/docs/concepts/workloads/
- Deployment：https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
- StatefulSet：https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/
- DaemonSet：https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/
- Job：https://kubernetes.io/docs/concepts/workloads/controllers/job/
