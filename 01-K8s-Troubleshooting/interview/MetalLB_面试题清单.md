# MetalLB 面试高频题清单

> 题面在此文件；**答案**见 [`answers/MetalLB_答案.md`](answers/MetalLB_答案.md)  
> 与 [`../notes/D2_MetalLB.md`](../notes/D2_MetalLB.md) **逐节对齐**；笔记有而题里没有的已补在 **§四**。  
> 现网：`meta/iot-web` → `192.168.27.190`、`first-pool`、Layer2、node6、80+1883

---

## 双向对照（题 ↔ 笔记）

**题 → 笔记**：每题答案在 `answers/`；笔记章节见下表右列。  
**笔记 → 题**：`D2_MetalLB.md` 每节已标注对应题号；题有而笔记原先没有的见 §9、§7.1、§7.2、§8.6～8.7、§6.1。

| D2 笔记章节 | 覆盖题号 |
|-------------|----------|
| §1 MetalLB 是什么 | 19、21 |
| §2 核心组件 | 9、28 |
| §3、§3.1 地址分配 / CRD | 8、12、13、22、23、33 |
| §4 L2、§4.1 优化、§4.2 测试 | 1、2、3、14、15、25、30 |
| §5 BGP、§5.1 丢包 | 1、4、26、27 |
| §6、§6.1 对比与陷阱 | 1、F1～F5 |
| §7、§7.1 Service、§7.2 strictARP | 5、10、11、17、18、19、21、24、32 |
| §8 现网、§8.6～8.8 排错 | 12、16、20、29、31、34 |
| §9 云 LB / keepalived | 6、7 |

---

## 一、你今天看到的 8 题（必背）

| # | 问题 | 掌握 |
|---|------|------|
| 1 | MetalLB 有哪两种模式？区别是什么？ | [ ] |
| 2 | Layer2 模式的 Leader 是怎么选举的？ | [ ] |
| 3 | 为什么说 Layer2 有单点瓶颈？如何优化？ | [ ] |
| 4 | BGP 模式下，为什么节点故障会导致丢包？ | [ ] |
| 5 | 什么情况下需要开启 strictARP？ | [ ] |
| 6 | MetalLB 和云厂商的 LoadBalancer 有什么区别？ | [ ] |
| 7 | Layer2 和 keepalived 有什么异同？ | [ ] |
| 8 | MetalLB 的 IP 地址从哪里来？ | [ ] |

---

## 二、补充高频题（建议一并背）

| # | 问题 | 掌握 |
|---|------|------|
| 9 | Controller 和 Speaker 分别做什么？ | [ ] |
| 10 | 外部流量从 VIP 到 Pod 的完整路径？MetalLB 和 CNI 分工？ | [ ] |
| 11 | MetalLB 和 Ingress 区别？IoT（MQTT 1883）为什么常用 LB 而不是 Ingress？ | [ ] |
| 12 | Service 类型 LoadBalancer 一直 Pending，怎么排查？ | [ ] |
| 13 | IPAddressPool / L2Advertisement 是什么？多环境多 VIP 怎么规划？ | [ ] |
| 14 | Layer2 故障转移要多久？受哪些因素影响？ | [ ] |
| 15 | 为什么删 Pod 不能当故障转移测试？Leader 节点宕机呢？ | [ ] |
| 16 | 如何确认当前是哪个节点在宣告 VIP？（结合 Events） | [ ] |
| 17 | Service 上为什么既有 EXTERNAL-IP 又有 NodePort？ | [ ] |
| 18 | kube-proxy 的 iptables 和 ipvs 对 MetalLB 有影响吗？ | [ ] |
| 19 | 裸机 K8s 为什么需要 MetalLB？不用 NodePort 行不行？ | [ ] |
| 20 | 你们项目里 iot-web 的 LB 方案怎么讲？（结合生产） | [ ] |

---

## 三、追问陷阱（面试官可能深挖）

| # | 追问 | 掌握 |
|---|------|------|
| F1 | L2 模式下流量一定只经过一个节点吗？BGP 一定没有瓶颈吗？ | [ ] |
| F2 | ARP 欺骗/冲突会导致什么问题？ | [ ] |
| F3 | MetalLB 能做 L7 吗？ | [ ] |
| F4 | 多个 LoadBalancer Service 能共用同一个 VIP 吗？ | [ ] |
| F5 | MetalLB 和 Calico/Flannel 的 BGP 是一回事吗？ | [ ] |

---

## 四、来自 D2 笔记的补充题（笔记先有 → 题清单补；答案亦已回写进 `D2_MetalLB.md`）

| # | 问题 | 对应笔记 | 掌握 |
|---|------|----------|------|
| 21 | MetalLB **负责什么、不负责什么**？和 CNI、kube-proxy 如何分工？ | §1、§7 | [ ] |
| 22 | 创建 `type=LoadBalancer` 的 Service 后，**分配到可访问**的完整流程？ | §3 | [ ] |
| 23 | 注解 `metallb.universe.tf/ip-allocated-from-pool` 表示什么？ | §8.2 | [ ] |
| 24 | LoadBalancer 为何同时有 **ClusterIP** 和 **EXTERNAL-IP**？集群内互访走哪个？ | §8.4 | [ ] |
| 25 | Layer2 里 **memberlist / gossip** 是干什么的？和 VRRP 比呢？ | §4 | [ ] |
| 26 | **ECMP** 是什么？BGP 如何通过 ECMP 缓解 L2 单点瓶颈？ | §5 | [ ] |
| 27 | BGP 模式上游路由器一般要配哪些（AS、Neighbor、MD5 等）？为何说**非开箱即用**？ | §5 | [ ] |
| 28 | Speaker 为什么是 **DaemonSet**？Controller 为何通常只有 **1 个** Pod？ | §2、§8.1 | [ ] |
| 29 | 同一池 `first-pool` 给 **meta / meta-test / meta-biz** 各分 VIP，会冲突吗？环境如何隔离？ | §8.3 | [ ] |
| 30 | **gracePeriod** 和 **ARP 缓存** 分别如何影响 L2 故障转移时间？ | §4 | [ ] |
| 31 | VIP 已分配、Events 正常，但 **访问不通**，和 Endpoints/后端 Pod 有关吗？怎么查？ | §7、§8.4 | [ ] |
| 32 | **ClusterIP / NodePort / LoadBalancer** 三种 Service 区别？IoT 为何常用 LB？ | §7、§8.4 | [ ] |
| 33 | **IPAddressPool、L2Advertisement、BGPAdvertisement** 三者关系？ | §3、§8.2 | [ ] |
| 34 | 如何检查 **metallb-system** 里 Controller/Speaker 是否正常？ | §8.1、§8.5 | [ ] |

---

## 五、自测方式

1. 盖住 `answers/`，每题 **30 秒** 口述。  
2. **必背**：§一 8 题 + §四 中与现网相关的 20、23、29、34。  
3. 第 20 题带：**first-pool、.190、node6、layer2、1883**。  
4. 掌握后在「掌握」列打 `[x]`。

**题量统计**：§一 8 + §二 12 + §三 5 + §四 14 = **39 题**。

---

## 六、相关学习文档

- 原理 + 现网：`../notes/D2_MetalLB.md`
- W1 手册 D2：`../W1_每日学习手册.md`
