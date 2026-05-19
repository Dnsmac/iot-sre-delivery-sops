# Kubernetes Workload 面试题参考答案

> 详述见 [`../../notes/D1_Workload.md`](../../notes/D1_Workload.md)

---

## 一、核心概念

### 1. 声明式 API + 控制循环？

- **声明式**：YAML 只写期望状态（要几个副本、什么镜像）。
- **控制循环**：控制器不断对比 **期望 vs 实际**，不一致就调谐（创建/删除/更新 Pod）。
- **结果**：Pod 挂了会自动重建，无需人工逐步操作。

### 2. kube-controller-manager 与 Workload？

- Deployment、StatefulSet、DaemonSet、Job 等控制器的 **逻辑代码** 运行在 **kube-controller-manager** 里。
- 各控制器是 **独立控制循环**，监听对应资源类型。

### 3. Deployment 层级？

```text
Deployment → ReplicaSet → Pod
```

Deployment 管 RS；RS 管 Pod 副本数与标签选择。

### 4. Deployment 场景与 Pod 名？

- **场景**：Web、API、**iot-server** 等无状态服务。
- **Pod 名**：含随机后缀（如 `xxx-7d8f9`），**重建后会变**。
- 副本地位平等，无严格启动顺序。

### 5. maxSurge / maxUnavailable？

| 参数 | 含义 |
|------|------|
| **maxSurge** | 滚动时最多可 **多出** 期望副本数几个（如 25% 或 1） |
| **maxUnavailable** | 滚动时最多允许多少个 **不可用** |

用于控制滚动 **速度** 与 **可用性** 平衡。

### 6. Recreate vs RollingUpdate？

| 策略 | 行为 | 何时用 |
|------|------|--------|
| **RollingUpdate** | 逐步替换，默认 | 要 **不断服** |
| **Recreate** | 先全删旧再建新 | 必须停旧版才能跑新版（会断服） |

---

## 二、StatefulSet / DaemonSet / Job

### 7. Deployment vs StatefulSet 本质区别？

**网络标识 + 存储是否要稳定、有序。**

- Deploy：Pod 名随机、并行扩缩、适合无状态。
- STS：固定 Pod 名、有序启停、每 Pod 独立 PVC，适合数据库/MQ 集群。

### 8. StatefulSet 三大特性？

1. **稳定网络标识**（`app-0`、`app-1`…）
2. **有序**部署、扩缩、删除
3. **每 Pod 独立持久化**（volumeClaimTemplates → PVC）

### 9. 为何必须 Headless Service？

- `clusterIP: None` → 不为虚拟 IP 做负载均衡，而是 **直接解析到各 Pod DNS**。
- 每个 Pod 有稳定 DNS：`<pod>.<svc>.<ns>.svc.cluster.local`。
- 有状态集群需要 **按序号访问指定实例**（如主从、分片）。

### 10. 有序部署/扩缩？

- 扩缩容、滚动时按 **序号 0→1→2** 顺序，不能乱序同时起。
- 保证如 MySQL/Pulsar 等 **集群初始化顺序**。

### 11. volumeClaimTemplates？

- 在 STS 里声明 **每 Pod 自动创建一个 PVC 模板**。
- Pod-0 得 pvc-0，Pod-1 得 pvc-1，**数据跟 Pod 身份绑定**，重建同名 Pod 可挂回原盘。

### 12. StatefulSet Partition？

- `RollingUpdate.Partition=N`：只更新序号 **≥ N** 的 Pod。
- 用于 **金丝雀/灰度**：先更新高序号实例，验证后再更新 Partition=0 全量。

### 13. DaemonSet vs Deployment 调度？

| | Deployment | DaemonSet |
|---|------------|-----------|
| 目标 | 维持 **N 个** Pod（全局） | **每个节点 1 个**（或部分节点） |
| 思维 | 副本数 | **节点覆盖率** |
| 新节点 | 可能不立刻有 Pod | **自动**在该节点起一个 |

### 14. DaemonSet 典型场景？你们例子？

- 监控 Node Exporter、日志 Fluentd、**CNI Agent**。
- **现网**：**MetalLB Speaker** — 6 节点 → 6 个 Speaker Pod。

### 15. DaemonSet 不调度到某节点？

- 节点有 **Taint（污点）**，Pod 无匹配 **Toleration（容忍）** → 不调度到该节点。

### 16. ReplicaSet 作用？

- 持有一批 **同模板 Pod**，保证副本数。
- 滚动更新：新 RS 扩容、旧 RS 缩容；**旧 RS 保留** 便于 **一键回滚**。

### 17. Job backoffLimit？

- Pod 失败（非 0 退出）时，Job 最多 **重试几次**。
- 超过则 Job 标记失败，不再无限重启。

### 18. CronJob 注意点？

1. **并发策略**：上一次 Job 没跑完，下一次是否还触发（Allow/Forbid/Replace）。
2. **错过调度**：节点宕机错过时间点，是否补跑（startingDeadlineSeconds）。

---

## 三、生产与进阶

### 19. HPA？

- **HorizontalPodAutoscaler**：按 CPU/内存/自定义指标 **自动改副本数**。
- 作用于 **Deployment、StatefulSet、ReplicaSet** 等（看 API 版本与配置）。

### 20. PDB？

- **PodDisruptionBudget**：在 **自愿驱逐**（维护、drain 节点）时，限制 **同时不可用 Pod 的上限**。
- 防止维护时服务 **全灭**。

### 21. 静态 Pod？

- 由节点 **kubelet** 直接管理，**不经过调度器**。
- apiserver 挂了，节点上静态 Pod 仍可运行。
- 常用于 **自托管集群** 的 apiserver、etcd 等。

### 22. 现网 Workload 对应？

| 组件 | Workload |
|------|----------|
| iot-server / iot-web 后端 | **Deployment** |
| Pulsar、MySQL、Redis、ES | **StatefulSet**（以 `kubectl get sts` 为准） |
| MetalLB Speaker | **DaemonSet** |
| MetalLB Controller | **Deployment**（通常 1 副本） |

### 23. kubectl 如何确认？

```bash
kubectl get deploy,sts,ds -n <ns>
kubectl get deploy iot-server -n meta
kubectl get sts -n <pulsar-ns>
kubectl get ds -n metallb-system
```

看 **_KIND** 列或 `describe` 的 `Controlled By`。

### 24. ClusterIP vs Headless？

| 类型 | 行为 | 适用 |
|------|------|------|
| **ClusterIP** | 虚拟 IP，kube-proxy 负载到后端 | **无状态** 多副本均匀访问 |
| **Headless**（None） | 无 ClusterIP，DNS 指向 **各 Pod** | **StatefulSet** 按 Pod 名访问 |

---

## 四、陷阱题

| # | 简答 |
|---|------|
| F1 | 每 Pod 独立盘用 **STS + volumeClaimTemplates**；Deploy 不以此为主 |
| F2 | **不会变**；删 Pod-0 重建仍叫 `app-0` |
| F3 | **不会**；每节点默认 **一个**（除非特殊配置） |
| F4 | **跑完就结束**用 Job；**长期服务**用 Deploy/STS |

---

## 五、复习检查

- [ ] 能画 Deploy → RS → Pod  
- [ ] 能讲 STS 三条 + Headless  
- [ ] 能讲 DaemonSet + MetalLB Speaker 例子  
- [ ] 现网 4 类组件 Workload 对口  
