# Kubernetes Workload 面试题清单（D1）

> 题面在此；答案见 [`answers/Workload_答案.md`](answers/Workload_答案.md)  
> 学习笔记：[`../notes/D1_Workload.md`](../notes/D1_Workload.md)  
> 现网对照：`../生产服务清单.md`、`../生产服务-K8s映射表.md`

---

## 双向对照（题 ↔ 笔记）

| 笔记章节 | 题号 |
|----------|------|
| §1 控制循环 | 1、2 |
| §2 Deployment | 3～6、15～17 |
| §3 StatefulSet | 7～12、18 |
| §4 DaemonSet | 13、14、19 |
| §5 Job/CronJob | 20～22 |
| §7 HPA/PDB | 23、24 |
| §8 静态 Pod | 25 |
| §9 现网 | 22、23 |

**题量**：§一 6 + §二 12 + §三 6 + §四 4 = **28 题**

---

## 一、核心概念（必背）

| # | 问题 | 掌握 |
|---|------|------|
| 1 | 什么是声明式 API + 控制循环？ | [ ] |
| 2 | kube-controller-manager 和 Workload 控制器的关系？ | [ ] |
| 3 | Deployment 管理 Pod 的层级关系是什么？ | [ ] |
| 4 | Deployment 适用于什么场景？Pod 名重启后会怎样？ | [ ] |
| 5 | RollingUpdate 里 maxSurge、maxUnavailable 是什么？ | [ ] |
| 6 | Recreate 和 RollingUpdate 何时选？ | [ ] |

---

## 二、StatefulSet / DaemonSet / Job

| # | 问题 | 掌握 |
|---|------|------|
| 7 | Deployment 和 StatefulSet **本质区别**？ | [ ] |
| 8 | StatefulSet 三大核心特性？ | [ ] |
| 9 | 为什么 StatefulSet 必须配合 **Headless Service**？ | [ ] |
| 10 | StatefulSet 有序部署/扩缩容是什么意思？ | [ ] |
| 11 | volumeClaimTemplates 解决什么问题？ | [ ] |
| 12 | StatefulSet 的 Partition 更新策略有什么用？ | [ ] |
| 13 | DaemonSet 和 Deployment 调度逻辑有何不同？ | [ ] |
| 14 | DaemonSet 典型场景？你们集群例子？ | [ ] |
| 15 | 什么情况下 DaemonSet **不会**调度到某节点？ | [ ] |
| 16 | ReplicaSet 在滚动更新/回滚中的作用？ | [ ] |
| 17 | Job 的 backoffLimit 是什么？ | [ ] |
| 18 | CronJob 要注意哪两个并发/时间问题？ | [ ] |

---

## 三、生产与进阶

| # | 问题 | 掌握 |
|---|------|------|
| 19 | HPA 作用？能作用于哪些 Workload？ | [ ] |
| 20 | PDB 解决什么问题？ | [ ] |
| 21 | 静态 Pod 是什么？和控制平面关系？ | [ ] |
| 22 | **iot-server、Pulsar、MySQL、MetalLB Speaker** 分别是什么 Workload？ | [ ] |
| 23 | 如何用 kubectl 确认 Deploy / STS / DS？ | [ ] |
| 24 | 无状态常配 ClusterIP，有状态常配 Headless，为什么？ | [ ] |

---

## 四、陷阱题

| # | 追问 | 掌握 |
|---|------|------|
| F1 | Deployment 可以直接挂 volumeClaimTemplates 每 Pod 一块盘吗？ | [ ] |
| F2 | 删 StatefulSet 的 Pod-0，名字会变吗？ | [ ] |
| F3 | DaemonSet 会在每个节点跑多个副本吗？ | [ ] |
| F4 | Job 和 Deployment 都能跑容器，怎么选？ | [ ] |

---

## 五、自测

1. 盖住 `answers/`，每题 30 秒口述。  
2. **第 22 题**必须带现网组件名。  
3. 掌握打 `[x]`。

---

## 后续（待你补充后加题）

- [ ] 网络路由（Service/Ingress/NetworkPolicy）  
- [ ] 存储（PV/PVC/StorageClass）  
- [ ] 底层组件（kubelet、调度器）
