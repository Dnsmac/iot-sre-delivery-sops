# JVM 硬核 · L4 口播稿（10 月深度月 · W4 主战场）

> 定位：Java 后端岗 JVM 是 L4 分水岭——能说「这堆为什么这样配」才是资深。15 题 = GC 器 / 调优 / OOM 类型 / 内存账 / 工具链 / 泄漏，每题 40~60s 口径。
> 用法：遮口径自测；配套 [03-JVM](../work/Java_Interview/面试题/03-JVM.md) 补细节 + [追问包 Day D](举一反三-超简历追问包.md) 变体。
> 事实索引：[数字与边界-唯一索引](数字与边界-唯一索引.md)。七维连追主脚本是 [面试连环深追脚本](面试连环深追脚本.md)；本稿只提供 JVM 机制弹药，不把每题伪装成生产 L4。
> OOM 案例只讲 `-Xmx8G`、约 5050 台、Dominator 约 5.7G/78%；32G 是 GIIC 15W 容量规划线，严禁混线。

## 项目锚点分级

| 能钩项目 | 题号 | 口径 |
|---|---|---|
| operatorCache OOM | J3、J9、J13～J15 | 可讲真实数字、工具链、根因和优化方向 |
| GIIC 15W 容量规划 | J4、J8、J9、J11 | 只讲 32G 是规划档位，不倒灌成 OOM 现场 |
| 了解级/通用机制 | J1～J2、J5～J7、J10、J12 | 没有实战证据时只讲 JVM 原理 |

## 🔥 高频题补强

| 题号 | Why/代价 | 2~3 追问 |
|---|---|---|
| J7 G1 停顿模型 | 停顿目标越小，吞吐和 mixed GC 频率代价越高 | `MaxGCPauseMillis` 能不能越小越好？Mixed GC 为什么会频繁？怎么判断是堆太小还是对象晋升太快？ |
| J9 8G vs 32G | 8G 是事故现场，32G 是容量规划；只能方法论对照 | 为什么不能说 32G 是事故堆？加堆为什么不是根治？怎么证明是缓存无界？ |
| J11 容器内存账 | 只看 Xmx 会漏掉线程栈、Direct、元空间，可能被 OOMKiller 杀 | RSS 比堆大很多看什么？MaxRAMPercentage 和 Xmx 能不能混用？线程数如何进内存账？ |
| J15 泄漏治理 | 有界缓存会带来回源和命中率波动，需要监控代价 | 怎么验证淘汰生效？TTL 和 maximumSize 分别解决什么？怎么防修复后下游被回源打穿？ |

---

## 一、GC 器与内存模型（J1～J5）

**J1 · 堆结构分代？为什么分代？** 40s
口径：新生代（Eden + S0/S1）+ 老年代 + 元空间（1.8 起移出堆）。分代依据「弱分代假设」：大多数对象朝生夕死，新生代用复制算法快回收，活下来的晋升老年代用标记整理/清除。具体新生代大小要看 GC 器、自适应策略和现场参数，不能把估算值当现网配置。

**J2 · 一次 Minor GC 发生什么？** 40s
口径：Eden 满触发，存活对象复制到 Survivor，年龄 +1，年龄到阈值（默认 15）或 Survivor 放不下就晋升老年代。触发点、晋升、大对象（直接老年代）三条路径都要知道。

**J3 · 什么时候触发 Full GC？** 40s
口径：老年代分配失败、元空间压力、显式 `System.gc()`、promotion failed、大对象把老年代顶穿等都可能触发 Full GC。Direct buffer 分配接近上限时，JDK/框架可能先触发引用处理或显式 GC 尝试回收不可达直接缓冲；回收不足时更直接的结果通常是 `OutOfMemoryError: Direct buffer memory`，不能断言“达到 DirectMemory 上限必然 Full GC”。→ 我项目已证的是 operatorCache 堆常驻集导致连环 Full GC/OOM。
边界：这是 operatorCache 堆 OOM 案例，不扩展成所有 Full GC 都有项目实战。

**J4 · 对象内存怎么算？指针压缩？** 40s
口径：对象头（mark word + 类型指针）+ 实例数据 + 对齐填充到 8 字节倍数。压缩指针把 64 位引用压到 32 位（`-XX:+UseCompressedOops`），通常在约 32G 以内更容易保留；但是否启用要看 JVM 版本和实际参数，面试只作为通用原理，不说“现网正好卡上限”。

**J5 · 一个对象的引用关系（强/软/弱/虚）？** 40s
口径：强引用只要可达就不回收；软引用通常在内存压力下回收（SoftReference）；弱引用在下一次 GC 可回收（ThreadLocal 的 key）；虚引用用于回收通知（DirectByteBuffer 的 Cleaner）。**Caffeine 默认对 key/value 使用强引用**；只有显式配置 `weakKeys`、`weakValues` 或 `softValues` 才使用弱/软引用，容量淘汰与引用强度是两套独立机制。

---

## 二、G1 调优（J6～J9）

**J6 · G1 和 CMS 最大区别？** 40s
口径：CMS 老年代「标记-清除」有碎片，碎片化到担保失败就退化成串行 Full GC（秒级 STW，已废弃）；G1 把堆切成等大 Region，跨代回收，只回收价值高的 Region（Garbage First 得名），可预测停顿。

**J7 · G1 的停顿模型？怎么算？** 40s
口径：目标是 MaxGCPauseMillis 内回收尽可能多垃圾；停顿来源 = Young GC（只清新生代 Region）+ Mixed GC（新生代 + 部分高价值老年代 Region）+ 并发标记（SATB）。停顿和吞吐是跷跷板：停顿卡小 → young 被压 → mixed 频繁。

**J8 · G1 调优三个参数 + 两个别乱设？** 40s
口径：三调：① MaxGCPauseMillis 按 SLA 给（别一味给小）；② InitiatingHeapOccupancyPercent（IHOP）默认 45%，老年代分配快就下调，提前启动 mixed 防满；③ 堆和 Region 大小。两不设：不设 Xmn（G1 自己算 young）、不设 SurvivorRatio。
分级：通用机制 + GIIC 容量规划可钩。没有现场参数证据时，不说“我把 IHOP 从多少调到多少”。

**J9 · 8G OOM 和 32G 容量规划怎么分开讲？** 60s（红线题）
口径：先拆两条线。OOM 现场是 `-Xmx8G`，约 5050 台设备后 operatorCache 把老年代顶满，Dominator 约 5.7G/78%，触发连环 Full GC/OOM；根因是 DeviceOperator/物模型 JSON 对象树缓存无界。32G 是 GIIC 15W 长连接容量规划线，考虑连接、会话、物模型、Login 尖刺和 G1 大堆稳定性，不能倒灌成 OOM 现场堆大小。教训：大堆不是保险，有界缓存才是。

---

## 三、OOM 类型与内存账（J10～J12）

**J10 · OOM 只有堆满这一种吗？** 40s
口径：不止。① 堆 OOM（泄漏/大对象）；② 元空间 OOM（动态生成类，CGLIB/Groovy 大量代理类）；③ 堆外 DirectMemory OOM（Netty/IO 缓冲，NMT 或 pmap 对账）；④ 线程数爆（OOM: unable to create native thread，每线程 1M 栈）。项目里已证的是 operatorCache 堆 OOM；其他三类按了解级机制回答。

**J11 · 容器里 JVM 内存账怎么算全？** 40s
口径：limit ≠ 堆。总账 = 堆 + 元空间 + 线程栈（线程数 × 1M）+ 堆外 Direct + JIT 代码缓存 + 本地库，全部 < cgroup limit，否则被 OOMKiller 无声 kill（没日志）。JDK11 默认感知容器，Xmx 和 MaxRAMPercentage 择一别混用。

**J12 · 堆外内存怎么排查？** 40s
口径：`-XX:NativeMemoryTracking=summary` + `jcmd <pid> VM.native_memory`，或 pmap/ps 看 RSS 和堆的差值。Netty 池化缓冲、DirectByteBuffer、mmap 是三大惯犯。
分级：了解级/通用排查。没有堆外 OOM 事故证据，不主动说生产踩过。

---

## 四、工具链与泄漏（J13～J15）

**J13 · jstat / jstack / jmap / jcmd 各干什么？** 40s
口径：jstat 看分代趋势（`-gcutil 1s` 连打）；jstack 看线程/死锁；jmap `-histo` 对象分布、`-dump` 堆快照；jcmd 全能（GC.heap_info / Thread.print / VM.flags / VM.native_memory）。线上安全姿势：先 histo 后 dump，大堆 dump 前确认磁盘 + STW 影响。

**J14 · 大堆 dump 拿不下来怎么办？（通用大堆场景）** 40s
口径：大 dump 拿不下来就在**容器内轻量分析**：`jmap -histo:live` 看对象分布、`jcmd GC.class_histogram`、`jmap -dump:live,format=b,file=` 只 dump 存活对象压缩、MAT 里用 dominator tree 定位；再不行 jcmd 采样 + 多次 histo 差值找「涨的对象」。项目实战只讲 `-Xmx8G` operatorCache OOM；dump 文件大小、传输过程如无证据不主动报具体数。

**J15 · 「只增不减」类泄漏，通用发现 + 止血 + 根治？** 40s
口径：发现 = jstat Old 爬坡不回落 + 两次 histo 差值；方案 = 找出写入路径，增加容量上限、过期、失效与水位告警。同族问题包括静态 Map、Caffeine 无界、ThreadLocal、监听器未反注册、本地会话表。本项目已完成定位并提出方案，补丁待 Gerrit 正式流程合入，暂无复测收益。

---

## 自检（10 月 W4 出口）

- [ ] 15 题各 40~60s 脱稿，🔥 题（J7/J9/J11/J15）必过
- [ ] 能一句话拆开「8G OOM vs 32G GIIC」：8G 是事故现场；32G 是 15W 容量规划
- [ ] 能背出 OOM 四种 + 各自排查工具
- [ ] J10/J12 只讲通用机制，不硬说堆外/元空间生产事故
- [ ] J8 不编具体调参前后值

---

## 同步记录

| 日期 | 动作 |
|------|------|
| 2026-09-02 | 建 JVM 硬核 15 题（GC器/内存模型/G1调优/OOM类型/内存账/工具链/泄漏），10 月 W4 主战场 |
