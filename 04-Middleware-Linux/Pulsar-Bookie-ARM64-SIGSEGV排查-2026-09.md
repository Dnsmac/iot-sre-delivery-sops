# Pulsar Bookie ARM64 SIGSEGV 反复崩溃排查（2026-09-04）

## 现象
- 3 副本 bookie（meta 命名空间，`pulsar-bookie-*`），aarch64 节点，Corretto-21.0.8.9.1，linux-aarch64。
- 全部 Ready → 陆续 SIGSEGV 崩溃（pid=1），hs_err 落 /tmp 重启即丢，problematic frame 打印超时（30s）拿不到。
- 删掉一个 Pod，其他 2 个又能 Ready，然后又崩。**x86 节点完全正常。**
- 已排除：ZGC/ZGenerational（换 G1 照崩）、Netty transport native（`-Dio.netty.transport.noNative=true` 无效）。

## 关键判断
1. **"删一个其他 Ready 又崩"不是因果**——三个 bookie 是独立崩溃，Ready 状态变化只是 quorum 抖动的连带表现。x86 正常 + aarch64 必崩，根因锁定 **aarch64 特有的 native 库路径**。
2. **noNative=true 只关 Netty 的 transport native（epoll），不关这两样**：
   - `libnetty_tcnative`（TLS/OpenSSL 路径）
   - `librocksdbjni`（BookKeeper ldb 存储统计）
3. 两条已知 bug 与现场逐字吻合：
   - **netty-tcnative ≤ 2.0.61 在 aarch64 崩溃**（`init_have_lse_atomics`，tcnative 官方 issue **#789**，复现仓库 jthurne/netty-tcnative-boringssl-2.0.61-aarch64-crash），**2.0.62 修复**。崩溃时点紧跟 `AuthHandler - Authentication success`（TLS 握手后）完全吻合。
     - 原始报告：Alpine aports <https://gitlab.alpinelinux.org/alpine/aports/-/issues/15582>（JDK21 + Alpine + aarch64 + SIGSEGV，problematic frame `libnetty_tcnative_linux_aarch_64.so+0x2330c init_have_lse_atomics+0xc`——与本 case 环境特征逐字吻合）
     - tcnative issue：<https://github.com/netty/netty-tcnative/issues/789>
     - 修复 diff：2.0.61→2.0.62 <https://github.com/netty/netty-tcnative/compare/netty-tcnative-parent-2.0.61.Final...netty-tcnative-parent-2.0.62.Final>
     - 旁证：zipkin <https://github.com/openzipkin/zipkin/issues/3532>、grpc-java <https://github.com/grpc/grpc-java/issues/10930>
   - **BookKeeper #4558：librocksdbjni 在 Corretto-21 + linux-aarch64 崩溃**（<https://github.com/apache/bookkeeper/issues/4558>，`RocksDB_getLongProperty+0x150`），报告者环境就是 Corretto 21 + aarch64 + **G1**——和"换 G1 照崩"吻合，Pulsar 4.0.3+/BK 4.17.2 修复。
4. 两次崩溃 pc 尾地址相同（ASLR 下同一指令位置）→ 确定性 native bug，非随机硬件问题。

## 修复动作（按命中率排序）
1. **先拿到 problematic frame（止血唯一确定路径）**：JVM 参数加 `-XX:ErrorFile=/pulsar/data/hs_err_%p.log`（/pulsar/data 挂 PV），崩溃后 `kubectl cp` 拷出。
2. **5 分钟最快的嫌疑排除**：bookie JVM 参数加 `-Dio.netty.handler.ssl.noOpenSsl=true`，强制 Netty 走 JDK SSL，绕开 tcnative。崩溃紧跟 TLS 认证，此嫌疑最大。
3. **确认镜像 libc**：`ls /lib/ld-musl-aarch64.so.1`。Alpine（musl）→ 换 Debian 基础镜像 tag 或升级 Pulsar ≥3.3.4 / 4.0.2（内含 tcnative 2.0.62+）。
4. **Corretto → Temurin 21 aarch64**：BK #4558 的崩溃环境正是 Corretto 21 aarch64，Corretto 的 aarch64 构建本身有前科。镜像里换 JDK 发行版，改动小。
5. **frame 若是 librocksdbjni**：升级 Pulsar ≥4.0.3 / BK ≥4.17.2；或临时把 bookie 调度到 x86 节点（nodeSelector），aarch64 上先不跑 bookie。
6. **兜底（业务不中断）**：bookie StatefulSet 加 nodeSelector 固定到 x86 节点，aarch64 修复验证后再迁回。

## 根因实锤（09-04 12:25 更新）
- `kubectl exec` 确认 `/lib/ld-musl-aarch64.so.1` 存在 → Harbor 镜像 `192.168.104.208/meta/kh-meta/common/apachepulsar/pulsar-all:4.0.7` 是 **Alpine/musl 基座**（aarch64）。
- 全部现象闭环：x86 正常（崩溃路径 aarch64 特有）、空闲不崩一连就崩（native 库在 I/O 路径触发）、换 G1/ZGC 没用（非 GC 问题）、探针 connection reset 是崩后结果非原因。
- **修复：换 glibc 基座镜像**——官方 `apachepulsar/pulsar-all:4.0.7`（默认非 alpine）retag 为 `4.0.7-glibc` 推 Harbor，换 image；Pod 内验证无 ld-musl + os-release 非 alpine。
- 换完可摘 noOpenSsl/noNative 恢复性能，`-XX:ErrorFile` 保留。验收 = 3 副本 + 服务连接写入跑 24h 不崩；稳定则不需要 2 副本降级方案（留作兜底）。
- 沉淀规矩：**aarch64 离线交付的中间件镜像一律 glibc 基座**，alpine 在 ARM 上是雷。

## 获取 arm64 glibc 镜像的三条路（09-04 12:40 更新）

背景：官方 3.0 起支持 arm64（PR-19432），但 Docker Hub 多架构发布不稳定（apache/pulsar#21655：latest 一度只有 arm64；3.1.0 RC 只有 amd64，committer 邮件确认需 `-Ddocker.platforms=linux/arm64` 自建）。**是"个别 tag 缺 arm64"，不是全缺。**

**路 0（零成本先试）**：换更新的 4.0.x tag 碰运气，可能已有 arm64 且白赚后续修复（当前 4.0 LTS 最新为 4.0.13）：
```bash
docker manifest inspect apachepulsar/pulsar-all:4.0.13 | grep -B2 architecture
docker manifest inspect apachepulsar/pulsar-all:4.0.12 | grep -B2 architecture
docker manifest inspect streamnative/pulsar-all:4.0.13 2>/dev/null | grep -B2 architecture  # streamnative 渠道
```
哪个 grep 出 arm64 就拉哪个，save → load → retag 进 Harbor（之前步骤不变）。

**路 1（最可控，自建）**：官方 bin tarball 是纯 Java、架构无关；JDK 基座 `eclipse-temurin:21-jre-jammy` 本身就是多架构（含 arm64）。在任何能联网的机器上：
```bash
# 1. 拉两个多架构镜像（配加速器：docker.m.daocloud.io 等）
docker pull --platform linux/arm64 eclipse-temurin:21-jre-jammy
# 2. tarball 从清华镜像下（4.0.13 在 current 列表内；老版本走 archive.apache.org）
curl -LO https://mirrors.tuna.tsinghua.edu.cn/apache/pulsar/pulsar-4.0.13/apache-pulsar-4.0.13-bin.tar.gz
# 3. Dockerfile
cat > Dockerfile <<'EOF'
FROM eclipse-temurin:21-jre-jammy
RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 sudo procps curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
ADD apache-pulsar-4.0.13-bin.tar.gz /opt/
RUN mv /opt/apache-pulsar-4.0.13 /pulsar
ENV PATH=/pulsar/bin:$PATH PULSAR_ROOT_LOGGER=INFO,CONSOLE
WORKDIR /pulsar
USER 10000:0
CMD ["bin/pulsar"]
EOF
docker build --platform linux/arm64 -t pulsar-all:4.0.13-glibc-arm64 .
docker save -o pulsar-4.0.13-glibc-arm64.tar pulsar-all:4.0.13-glibc-arm64
# → 拖进内网 → docker load → retag 推 192.168.104.208 → 改 image
```
注意：此为 `pulsar`（核心）镜像等价物；真需要 connectors/offloaders 再额外下 `apache-pulsar-offloaders-*.tar.gz` 解到 /pulsar/offloaders。helm 里 broker/bookie/zk 用核心镜像就够。
**路 2（借人）**：找到构建 musl 版镜像的同事，用同一条内部构建流水线，把基座 FROM 换成 `ubuntu:22.04`/`eclipse-temurin:21-jre-jammy` 重推——他们的流水线本来就出 arm64 镜像。

### 路 1 的离线变体（无外网时的主方案，09-04 20:15 补充）

**关键洞察：现 Alpine 镜像的 `/pulsar` 目录就是完整发行版解包**——Pulsar bin tarball 是纯 Java、架构无关，直接多阶段 COPY，不需要官方 tarball、不需要外网：

```dockerfile
# 基座 = 内网 Harbor 里任意 arm64 glibc 镜像（ubuntu/kylin/jdk 均可）
FROM 192.168.104.208/<现有glibc基座>:<tag>
COPY --from=192.168.104.208/meta/<现有pulsar镜像>:<tag> /pulsar /pulsar
# JDK：优先用基座自带的 glibc 版 JDK；若基座无 JDK，
# 从麒麟节点本地 JDK21 抄（tar 打进去），勿直接用现镜像里的 musl 版 corretto
ENV JAVA_HOME=<基座JDK路径> PATH=/pulsar/bin:$JAVA_HOME/bin:$PATH
WORKDIR /pulsar
```

要点：
- 只需改 FROM 与 JDK 路径两处；现镜像的 command/args/PULSAR_MEM/PULSAR_GC 等 env 原样保留（Kuboard workload 层面不动的部分不受影响）。
- **JDK 必须是 glibc 版**：现镜像的 Corretto-Alpine 是 musl 静态构建，其 JVM dlopen glibc 的 .so 同样有混链风险；麒麟节点/内网 yum 一般有 OpenJDK。
- glibc 兼容性方向是"新基座 glibc ≥ .so 编译期 glibc"，麒麟的 glibc 版本大概率满足。
- 若 Harbor 实在没有 glibc 基座：退而求其次在麒麟节点上 `docker import` 一个麒麟根文件系统 tar 包当基座（节点 OS 本身就是 glibc）。

### 路内盲试开关（换镜像前的并行尝试，只动 broker env）

bookie 已被 `journalRemoveFromPageCache=false` 救活 → 证明"关一个开关救一个组件"路线有效。broker 无 frame 可查，按嫌疑度盲试（每改一次滚动重启，观察 121s 存活周期是否消失）：

**头号嫌疑（09-04 20:25 从 classpath 挖出）：circe-checksum native。** broker classpath 含 `org.apache.bookkeeper-circe-checksum-4.17.2.jar`；配置 `managedLedgerDigestType=CRC32C`（默认）→ broker 写 entry 用 circe native 算 CRC32C。证据链：
1. circe 的 .so 与 bookie 实锤的 libnativeio.so 同体系（BookKeeper 自带、glibc 构建、同 loader）
2. 崩溃时机完美吻合：ManagedLedger 建 ledger 后立刻写 LEDGER_CREATED marker——SIGSEGV 恰打在 `Ensemble for ledger: 59` 下一行
3. bookie 侧 entry log 全空 → 数据没到 bookie，崩在 broker 本地 checksum/序列化阶段
4. netty epoll 排除（连 ZK/连 bookie 的 netty 早就跑通）；tcnative 已关；rocksdb broker 不加载

**止血开关：broker env 加 `managedLedgerDigestType=CRC32`**（纯 Java 校验和，绕开 circe native；digest 按 ledger 记录，无数据兼容风险）。次选 `-Dio.netty.transport.noNative=true`。

**09-04 20:04 重启复盘（关键：开关尚未生效）。** 用户重启 broker-1 后贴回启动日志：bootstrap 4 秒 ready，全程无异常；但日志末尾 ServiceConfiguration dump 明确打印 `managedLedgerDigestType=CRC32C` → **这轮重启没有包含止血开关，不构成测试**。开关来源是 init 容器逐行 Applying/Updating broker.conf 的 ConfigMap，需要在该 ConfigMap（或 helm values 对应字段）里加 `managedLedgerDigestType = CRC32` 一行。下次重启后在启动日志里搜 `Updating config managedLedgerDigestType = CRC32C -> CRC32` 确认生效。另注意：
- broker 存活 14 分钟不能作为好转证据——崩溃触发条件是"建 ledger 后写第一笔"，只要 atomic-center 没连上产生写入，broker 不写 ledger 就不会崩；判断好转必须确认生产端恢复收发。
- 本轮日志再坐实版本事实：Pulsar **4.0.7**（非 4.0.13）、JDK 21.0.8 Corretto（/opt/jvm，glibc）、circe-checksum-4.17.2.jar 在 classpath。
- 容器 cgroup 内存很紧：`os.memory.total=256MB / max=768MB`，堆 -Xmx384m + ZGC + AlwaysPreTouch。OOM 与 SIGSEGV 是两回事，别混淆，但后续调优要留意。

盲试顺序：
1. 清 core（`rm -f /pulsar/core.*`）→ broker env 加 `managedLedgerDigestType=CRC32` → 滚动重启 → 观察 30min
2. 若仍崩：叠 `-Dio.netty.transport.noNative=true` 再试
3. 业务侧止损：atomic-center 等 MQ 流量临时走备用通道，修好切回。

顺带确认：broker 启动日志开头 `Node does not exist: /loadbalance/brokers/... exit 1` 是 helm 脚本清理旧注册节点的正常动作，非故障；`os.version=4.19.90-89.11.v2401.ky10` 确认节点为麒麟 V10；`java.home=/opt/jvm` 证明镜像维护同事有改基座重推的能力与流水线（原路 2 现成）。

## 教训
- `noNative=true` ≠ 关闭所有 native；SSL 和 RocksDB 是另外两条独立 native 路径。
- aarch64 上跑中间件优先选 **Debian 基础镜像 + glibc**，避开 Alpine/musl；JDK 发行版优先 Temurin（Corretto aarch64 有已知崩溃案例）。
- hs_err 必须从第一天就落到持久卷，`/tmp` 在容器重启后必丢。

## 判决性 frame 到手：BookKeeper NativeIO（09-04 19:00 更新）

hs_err（6KB，ErrorFile 已生效落 journal 目录）关键内容：

- `SIGSEGV (SEGV_ACCERR)`，Corretto-21.0.8.9.1 aarch64，**G1 + `-Dio.netty.handler.ssl.noOpenSsl=true` 已生效仍崩 → tcnative 嫌疑正式排除**。
- 崩溃线程：`ForceWriteThread`，Java 栈完整可见：
  `JournalChannel.forceWrite → PageCacheUtil.bestEffortRemoveFromPageCache → NativeIOImpl.posix_fadvise → NativeIOJni.<clinit> → NativeUtils.loadLibraryFromJar → System.load`（dlopen 阶段 SEGV）。
- **根因**：BookKeeper jar 内自带的 `libnativeio.so`（glibc 构建）在 Alpine gcompat 翻译层上 dlopen 即崩。官方 musl 兜底只覆盖了 snappy（自编译）和 rocksdb（`ROCKSDB_MUSL_LIBC=true`），**nativeio 这个 .so 是兜底死角**。
- 启动 197s 后 journal 首次 forceWrite 触发 fadvise → 完美解释"空闲不崩、一连就崩"。
- CPU Features 含 `atomics` → **LSE 存在，"国产 CPU 无 LSE"假设排除**。

**止血方案（不换镜像）**：bookkeeper.conf 加 `journalRemoveFromPageCache=false`，彻底绕开 NativeIO 加载路径。代价仅是 journal 写后不做 posix_fadvise 页缓存剔除（多占一点 page cache），无正确性影响。

## broker 同款 SIGSEGV：切换条件触发（09-04 19:45 更新）

bookie 止血后，**broker 也 SIGSEGV**（Corretto-21.0.8.9.1 aarch64，崩溃摘要打到了容器 stdout，hs_err 落在 `/tmp/hs_err_pidN.log`——重启即丢，Problematic frame 被 Kuboard 界面弹窗遮挡未取到）。

崩溃前日志显示业务链路其实已通：topic 创建成功（ensemble=3 bookie 全注册）、managed ledger 初始化完成、`/status.html` 健康检查 200——然后运行中 native 崩溃。与 bookie"空闲不崩、一连就崩"同款模式。

**判决升级**：bookie 崩在 nativeio（已绕开），broker 又崩在别的 native 路径 → **gcompat 在 aarch64 上对 JNI 整体不可信**，不再逐个 .so 绕行，直接执行 glibc 自打包镜像方案（见上文"路 1"，20-40 分钟）。

执行清单：
1. 外网机器走"路 1"出 `pulsar-all:4.0.13-glibc-arm64`（temurin 21-jre-jammy 基座，天然 glibc + 多架构）
2. `docker save` → 拖内网 → `docker load` → retag 推 192.168.104.208
3. Kuboard 逐个改 workload 镜像：**bookie → broker → zk**（同一 musl 家族，全部换；zk 目前没崩但只是还没走到雷区）
4. broker 的 PULSAR_GC 顺手加 `-XX:ErrorFile=/pulsar/data/hs_err_%p.log`（新镜像上也保留，证据落持久卷）
5. 换镜像前清掉 `/pulsar/core.*`（崩溃转储，防磁盘打满）
6. 观察窗口 24h：journalRemoveFromPageCache=false 保留无害，不回退

**后续观察**：若关掉后又崩在别的 .so，说明 gcompat+aarch64 对 JNI 整体不可信，放弃逐个绕行，直接上 glibc 自打包镜像（主干方案不变）。

**配套**：崩溃时写到 /pulsar/core.1 的 core dump 要清理防磁盘打满。

## bookie 日志反向验证：bookie 健康，崩溃潮汐 = broker 死亡循环的镜像（09-04 20:10 更新）

取 bookie（10.234.10.95，应为 bookie-2）11:17–11:47 共 30 分钟日志，逐段定性：

**1. bookie 本身零异常。** 全程只有 INFO/WARN，没有 ERROR、没有 journal 回放/Dirty file、没有写盘超时——之前布置的 bookie 三项检查全部落空，bookie 洗清嫌疑。

**2. 连接潮汐 = broker 反复 SIGSEGV 的指纹。** 客户端 IP（10.234.10.94 / 10.234.182.90 / 10.234.182.94 / 10.234.10.99 / 10.234.182.95，即各 broker/proxy pod）以约 2 分钟为周期"批量连入→认证成功→批量断开"，换下一批 IP 重复。这是 3 个 broker 各自崩溃重启时 TCP 连接全断/重建的直接投影，与 Kuboard 里 broker 反复 Restart 完全对应。

**3. 每轮存活期 ≈ 2 分钟，规律极强。** 11:20:30 连入 → 11:22:33 断开；11:27:31 → 11:29:34；11:39:22 → 11:41:24；11:43:01 → 11:45:03，全部约 121s。broker 起来后稳定跑约 2 分钟才崩——与 bookie 当初"启动 197s 首次 forceWrite 才崩"同款"定时炸弹"模式，指向某个首次触发的 native 路径（疑似 ManagedLedger 首次 flush/sync 或 netty native 传输首次使用）。

**4. Ledger fencing 连环出现，ledger 号一路递增。** 每轮连入后 `Ledger: 31/33/37/44/48/52 fenced by ...`——broker 重启恢复 topic 时 fence 旧 ledger、切新 ledger（编号持续增长），属恢复流程的正常动作，不是 bookie 故障。

**5. 数据面几乎为空。** `GarbageCollectorThread` entry log usage buckets 全 0（该 bookie 上没有任何 ≥10% 占用的 entry log），`db-storage-cleanup` 持续删除 ledger 18/20/23/25/27/29/31/33/37/44/48/52 的索引——ledger 建了但没写入实质数据，崩溃后被当垃圾清掉。证明 broker→bookie 建 ledger/写 entry 的链路没有被 bookie 卡住，写路径挂起的责任在 broker 侧崩溃。

**结论**：证据链闭环，bookie 排查正式收工。根因维持判决——gcompat/aarch64 对 JNI 不可信，直接执行 glibc 自打包镜像方案（bookie → broker → zk）。

## broker-0 案发第一现场（09-04 20:15 更新）

broker 日志直接捕获 SIGSEGV 全过程，关键证据：

1. **崩溃时机精确到毫秒级：正在建 ledger 的瞬间**。11:55:34.8xx 批量连上 3 个 bookie → ledger 58 创建成功 → 11:55:35.029 `Ensemble: [bookie-0, bookie-1] for ledger: 59` 打出的**下一行就是 SIGSEGV**。broker 死在 ZK 建元数据后、向 bookie 写第一笔数据前后的 native 调用中。所谓"建 topic 挂起"从此有了精确解释：每次都死在同一微操步上。
2. **hs_err 本身残缺**：`timeout occurred during error reporting in step "printing problematic frame" after 30 s` + `[ timer expired, abort... ]`——JVM 错误报告器试图解析/打印崩溃帧时自己也卡死 30 秒后放弃。**Problematic frame 一行是空的**，说明崩得很深（error handler 无法安全回溯），`/tmp/hs_err_pid1.log` 即使抢到也没有 frame 信息。此路彻底堵死，不再追 hs_err。
3. **core dump 又落了 `/pulsar/core.1`**：每次崩溃都在写，磁盘风险持续累积，换镜像前必须清理（已在执行清单第 5 条）。
4. 崩溃瞬间 kube-probe `/status.html` 仍 200（JVM 还在挣扎上报错误），30 秒后进程才 abort——这解释了之前"日志看着还活着就崩了"的观感。
5. 顺带排除两个疑点：ensemble 只选 [bookie-0, bookie-1] 两个是 chart 默认 ensembleSize=2 + "not adhering to Placement Policy" 仅是提示（bookie-2 与前两者跨域约束），非故障；proxy 侧 "Pulsar Handshake was not completed" 是 broker-1 恰在崩溃窗口的下游症状。

**行动**：无新增排查项，全力推进 glibc 自打包镜像方案。
