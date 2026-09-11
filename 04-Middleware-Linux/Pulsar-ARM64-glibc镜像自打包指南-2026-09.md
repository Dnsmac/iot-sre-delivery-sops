# Pulsar ARM64 glibc 镜像自打包指南（2026-09）

> 背景：Harbor 里 `apachepulsar/pulsar-all:4.0.7`（aarch64）在 3 副本 bookie 上确定性 SIGSEGV，
> 已实锤镜像为 **musl 基座**（容器内有 `/lib/ld-musl-aarch64.so.1`）。
> 本文回答三件事：官方怎么解释的 → 先鉴别手里镜像是什么 → 自打包 glibc 镜像的完整步骤。
> 关联 case：[Pulsar-Bookie-ARM64-SIGSEGV排查-2026-09.md](Pulsar-Bookie-ARM64-SIGSEGV排查-2026-09.md)

---

## 一、官方是怎么说的（先看勘误）

**勘误：官方 3.3+/4.0 镜像基座不是 Ubuntu，是 Alpine。** 此前我说"官方一直是 glibc 基座"只对 3.0.x 成立，必须修正：

- 官方发布流程文档（https://pulsar.apache.org/contribute/release-process-maven）原文：
  ```
  # ensure that you have the most recent base image locally
  docker pull ubuntu:22.04   # for 3.0.x
  docker pull alpine:3.21    # for 3.3.x+
  ```
  多架构构建命令（3.0 起官方就发布 amd64+arm64 双架构）：
  ```
  mvn install -pl docker/pulsar,docker/pulsar-all -DskipTests \
    -Pmain,docker,docker-push \
    -Ddocker.platforms=linux/amd64,linux/arm64 \
    -Ddocker.organization=$DOCKER_USER
  ```
  （master 新 Gradle 构建：`./gradlew docker -Pdocker.platforms=linux/amd64,linux/arm64 ...`，且 Gradle 路线不再构建 pulsar-all，connectors 已按 PIP-465 拆到独立仓库）

- **但官方 Alpine 镜像做了三件事兜底 musl**（官方 Dockerfile `docker/pulsar/Dockerfile`）：
  1. 装 **gcompat**（glibc 兼容层，给 Netty native 用）；
  2. **自编 snappy-java** native 库（不用预编译二进制）；
  3. JVM 为 JLink 精简版 Corretto 21（装在 `/opt/jvm`）。

### 这对你的意义

你 Harbor 里的 musl 镜像有两种来历，**结论完全不同**：

| 来历 | 特征 | 含义 |
|---|---|---|
| **A. 官方 4.0.7 retag** | 有 `gcompat` + JVM 在 `/opt/jvm` + 有 `pulsar` 用户(UID 10000) | musl 不是根因本身（官方带补丁），崩溃另有其因（如 Corretto/JIT aarch64 bug），换官方 4.0.13 可能才有效 |
| **B. 内部用 alpine 基座自建** | 没有 `gcompat`，或 JVM 目录布局不是 `/opt/jvm` | 内部构建漏掉了官方兜底三件套，musl 直接裸奔——这正是 aports #15582 那族崩溃 |

**第一步先鉴别（30 秒）：**

> ⚠️ **勘误（2026-09-04）**：第一版命令用 `ls /usr/lib/libgcompat*` 检查 gcompat——**路径错了**。官方 Dockerfile 明确 `apk add gcompat` 且 `ENV LD_PRELOAD=/lib/libgcompat.so.0`，gcompat 装在 **`/lib`**，用 `/usr/lib` 检查会得到假阴性 `NO-GCOMPAT`。已修正如下：

```bash
kubectl exec pulsar-bookie-0 -n meta -- sh -c '
  echo "== gcompat 正确路径 =="; ls -l /lib/libgcompat.so.0 2>/dev/null || echo "NO-GCOMPAT-REAL"
  echo "== 官方兜底 env =="; env | grep -E "LD_PRELOAD|ROCKSDB_MUSL" || echo "NO-COMPAT-ENV"
  echo "== JVM 布局 =="; ls -d /opt/jvm 2>/dev/null && echo "OFFICIAL-LAYOUT"
  ls -d /opt/java/openjdk 2>/dev/null && echo "TEMURIN-LAYOUT"
  echo "== 用户 =="; id pulsar 2>/dev/null || echo "NO-PULSAR-USER"
  echo "== alpine 版本 =="; cat /etc/alpine-release 2>/dev/null'
```

### 鉴别实测（2026-09-04 截图）

实测结果：`/opt/jvm` 存在（OFFICIAL-LAYOUT）+ `uid=10000(pulsar) gid=0(root)`（与官方 `adduser pulsar -u 10000 -G root` 完全一致）+ Alpine 3.21.4；gcompat 一项因路径 bug 显示 NO-GCOMPAT（待 `/lib` 复测）。

官方 branch-4.0 Dockerfile 逐行核对结论（https://github.com/apache/pulsar/blob/branch-4.0/docker/pulsar/Dockerfile）：
- 基座 `alpine:3.21~3.24` + JVM = `amazoncorretto:21-alpine` 经 JLink 输出到 **`/opt/jvm`** ✅ 与实测吻合；
- 官方兜底三件套：`apk add gcompat` + **`ENV LD_PRELOAD=/lib/libgcompat.so.0`**（Netty native 用）+ **`ENV ROCKSDB_MUSL_LIBC=true`**（RocksDB 用 musl 编译版）+ `libsnappyjava.so` 自编译放 `/usr/lib`。

**当前判定：指纹高度指向官方 retag（用户布局+UID 完全一致），但 gcompat 必须用 `/lib` 路径复测定案。**
- 复测 gcompat 存在 + LD_PRELOAD 生效 → **官方镜像原封 retag，musl 已被官方兜底** → 崩溃另有其因，矛头转向 Corretto(JLink) aarch64——此时 hs_err 的 problematic frame 是唯一判决证据，自打包 Temurin glibc 镜像升级为第一优先；
- 复测确认无 gcompat → 内部构建漏兜底，musl 裸奔即根因。

### 定案（2026-09-04 二次截图）：官方镜像 retag 实锤，musl 排除

复测确认：`/lib/libgcompat.so.0` 存在 + `LD_PRELOAD=/lib/libgcompat.so.0` + `ROCKSDB_MUSL_LIBC=true` + `/opt/jvm` + `uid=10000(pulsar)` + Alpine 3.21.4 —— **官方 4.0.7 镜像原封 retag，官方兜底全部在位**。musl 从根因名单中排除。

**那为什么还崩？官方兜底剩两个已知不完全区：**

1. **gcompat 是翻译层，不是真 glibc**。它负责让 glibc 编译的 native 库（Netty tcnative 等）在 musl 上跑起来，但只保证"能加载能跑基本路径"，不保证 aarch64 所有指令路径都翻译正确——aports #15582 那族崩溃里，`init_have_lse_atomics` 的检测 bug 正好就发生在这个翻译层上。
2. **CPU 缺 LSE 原子指令**（关键嫌疑）：`init_have_lse_atomics` 检测的就是 CPU 是否支持 ARMv8.1 的 LSE 原子指令。**飞腾 FT-2000/FT-2004 等 ARMv8.0 国产 CPU 没有 LSE**（鲲鹏 920 有）。如果这套环境跑在无 LSE 的 ARM 机器（信创场景很典型），native 库的 LSE 相关路径就是雷区——且天然解释"x86 正常"。

**判决性证据只剩两个（都能马上拿）：**
- `hs_err` problematic frame（ErrorFile 已配置落 PV，崩溃频繁，报告应该已经在 `/pulsar/data/` 里）；
- `/proc/cpuinfo` 的 Features 里有没有 `atomics`（LSE）。

```bash
kubectl exec pulsar-bookie-0 -n meta -- sh -c 'ls -lt /pulsar/data/hs_err_*.log 2>/dev/null | head -3; grep -A 5 "Problematic frame" $(ls -t /pulsar/data/hs_err_*.log 2>/dev/null | head -1)'
kubectl exec pulsar-bookie-0 -n meta -- sh -c 'grep -m1 Features /proc/cpuinfo'
```

结果对应：
- Features **无 `atomics`** → 无 LSE CPU + native 库翻译层问题实锤，自打包 glibc+Temurin（运行时检测在 glibc 上是正确的）即修复；
- frame 指向 `libnetty_tcnative...` → 同上，native TLS 路径；
- frame 指向 `libjvm.so`/C2 → Corretto JIT bug，换 Temurin 基座即修复；
- frame 指向 `librocksdbjni...` → RocksDB musl 构建问题，换 glibc 镜像即绕开。

不管鉴别结果是 A 还是 B，**自打包一份纯 glibc 镜像都是最优解**：
- 是 B → 直接修复；
- 是 A → 它同时是**判决性实验**：换成 glibc 基座后还崩，就彻底排除 musl，矛头指向 Corretto JIT（换 Temurin 基座顺带也换掉了 JDK 发行版，一石二鸟）。

---

## 二、自打包方案 A（推荐）：bin tarball + Temurin 基座

**为什么这条最省事：**
- `apache-pulsar-4.0.13-bin.tar.gz` 是**纯 Java、架构无关**的二进制发行包，清华镜像直接下，不碰 Docker Hub；
- 基座 `eclipse-temurin:21-jre-jammy` 官方就是多架构（含 arm64、Ubuntu 22.04 glibc），Docker Hub 或国内加速器都拉得到；
- **不需要源码构建**，不用 JDK 编译 Pulsar，不碰 mvn/gradle；
- 总耗时 20-40 分钟（网络下载占大头），产物约 1.5-2GB。

### 步骤 1：在一台能联网的机器上准备三样东西

```bash
mkdir -p pulsar-build && cd pulsar-build

# 1) 基座镜像（arm64）
docker pull --platform linux/arm64 eclipse-temurin:21-jre-jammy
# 国内加速器拉不动就在 /etc/docker/daemon.json 加:
# "registry-mirrors": ["https://docker.m.daocloud.io"]

# 2) Pulsar 二进制包（清华镜像，架构无关）
curl -LO https://mirrors.tuna.tsinghua.edu.cn/apache/pulsar/pulsar-4.0.13/apache-pulsar-4.0.13-bin.tar.gz
# 校验 sha512（可选但建议）：
curl -LO https://mirrors.tuna.tsinghua.edu.cn/apache/pulsar/pulsar-4.0.13/apache-pulsar-4.0.13-bin.tar.gz.sha512
sha512sum -c apache-pulsar-4.0.13-bin.tar.gz.sha512

# 3) 确认 bin 包里有没有 connectors/offloaders（决定等不等于 pulsar-all）
tar -tzf apache-pulsar-4.0.13-bin.tar.gz | grep -E "connectors/.*\.nar" | head -3
tar -tzf apache-pulsar-4.0.13-bin.tar.gz | grep -E "offloaders/.*\.nar" | head -3
```

> **pulsar vs pulsar-all 的差别**：`pulsar-all` = `pulsar` + IO connectors + offloaders（+Presto SQL）。
> 你的 helm chart 现在三个组件（zk/bookie/broker）全用 `pulsar-all`，但核心消息收发只用得到 bin 包主体。
> 如果 tarball 里没有 connectors/offloaders 而你又确实用到 Functions/IO，额外下载
> `pulsar-io-4.0.13.nar` 分发包解压进镜像（见步骤 3 的可选层）；只做消息收发就直接跳过。

### 步骤 2：写 Dockerfile

```dockerfile
FROM eclipse-temurin:21-jre-jammy

ARG PULSAR_VERSION=4.0.13
ENV PULSAR_HOME=/pulsar
ENV PATH=${PULSAR_HOME}/bin:${PATH}

# bookie/broker 启动脚本依赖 python3(apply-config-from-env.py)；ps/grep 是运维排障基本件
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 procps net-tools dnsutils curl \
    && rm -rf /var/lib/apt/lists/*

COPY apache-pulsar-${PULSAR_VERSION}-bin.tar.gz /tmp/
RUN tar -xzf /tmp/apache-pulsar-${PULSAR_VERSION}-bin.tar.gz -C /opt \
    && mv /opt/apache-pulsar-${PULSAR_VERSION} ${PULSAR_HOME} \
    && rm -f /tmp/apache-pulsar-*.tar.gz \
    && mkdir -p ${PULSAR_HOME}/data ${PULSAR_HOME}/logs \
    && chmod +x ${PULSAR_HOME}/bin/*.py ${PULSAR_HOME}/bin/pulsar* ${PULSAR_HOME}/bin/bookkeeper

# （可选） Functions/IO connectors：仅当 tarball 缺 connectors 且你要用时打开
# COPY pulsar-io-4.0.13.nar ${PULSAR_HOME}/connectors/

WORKDIR ${PULSAR_HOME}
CMD ["bin/pulsar", "standalone"]
```

> **构建机在哪**：有 arm64 Linux 机器（比如你 node4 那台 VM 能临时联网）直接 `docker build`，原生最快；
> 只有 x86 机器也行——`docker build --platform linux/arm64 .`（走 qemu 模拟，apt 解压会慢几分钟但能成）。

```bash
docker build --platform linux/arm64 -t pulsar-all:4.0.13-glibc .
```

### 步骤 3：构建完当场验基座（别等进内网才发现不对）

```bash
docker run --rm pulsar-all:4.0.13-glibc sh -c '
  ls /lib/ld-musl-aarch64.so.1 2>/dev/null && echo MUSL-BAD || echo GLIBC-OK
  head -2 /etc/os-release
  java -version 2>&1 | head -1
  ls /pulsar/bin/pulsar /pulsar/bin/bookkeeper'
# 期望：GLIBC-OK + Ubuntu 22.04 + Temurin 21 + 两个可执行文件都在
```

### 步骤 4：导出 → 进内网 → 推 Harbor

```bash
# 联网机：
docker save pulsar-all:4.0.13-glibc -o pulsar-all-4.0.13-glibc-arm64.tar
# （tar 约 1.5-2GB，U 盘/内网共享搬运；堡垒机 500MB 限制注意分卷：split -b 400m）

# 内网 arm64 机器（或集群任一节点）：
docker load -i pulsar-all-4.0.13-glibc-arm64.tar
docker tag pulsar-all:4.0.13-glibc \
  192.168.104.208/meta/kh-meta/common/apachepulsar/pulsar-all:4.0.13-glibc
docker push 192.168.104.208/meta/kh-meta/common/apachepulsar/pulsar-all:4.0.13-glibc
```

### 步骤 5：helm 切镜像 + 滚动更新

```bash
# zk → bookie → broker 顺序滚
helm upgrade <release> <chart> -n meta \
  --set images.zookeeper.tag=4.0.13-glibc \
  --set images.bookkeeper.tag=4.0.13-glibc \
  --set images.broker.tag=4.0.13-glibc
```

---

## 三、方案 B：官方源码构建（知道就行，不建议）

官方 README（4.0+ 分支）给的自建方式：

```bash
git checkout v4.0.13   # branch-4.0 需要 JDK 21
./gradlew docker -Pdocker.platforms=linux/arm64 -Pdocker.tag=4.0.13
# 3.x 及以前是 Maven：
mvn clean install -DskipTests
mvn package -Pdocker,-main -am -pl docker/pulsar-all -DskipTests -Ddocker.platforms=linux/arm64
```

**为什么不推荐**：全量源码构建需要 JDK 21 + Maven/Gradle 环境 + 磁盘 20G+（官方 release 文档专门提醒 buildx 缓存超 10G 必须先 prune）+ 1 小时以上，而且**产物仍然是 alpine 基座**——等于绕一大圈回到 musl，除非你逐行抄官方 Dockerfile 的 gcompat 兜底。你的诉求是"glibc"，方案 A 十几行 Dockerfile 就够。

---

## 四、切换后清单

1. **容器内验基座**（进 Pod 再看一眼，和步骤 3 同款命令）；
2. **参数处置**：`noOpenSsl`/`noNative` 摘掉（glibc 下走回 native 高性能路径）；`-XX:ErrorFile=/pulsar/data/hs_err_%p.log` **永久保留**；G1 保留（别急着回 ZGC，一次只留一个变量）；
3. **验收标准不变**：3 副本 + 服务正常连接写入，**24h 不崩**；
4. **如果还崩**：从 PV 拿 `hs_err` 看 Problematic frame——此时 musl 已彻底排除，看 frame 指向 `libjvm.so`（JIT bug，Temurin 换发行版再试）还是别的 `.so`，拿着 frame 来找我；
5. 沉淀规矩：**aarch64 离线交付的中间件镜像，基座一律 glibc（ubuntu/debian/temurin-jammy），禁用 alpine**——除非你愿意像官方那样逐项补 gcompat + 自编 native。

## 附：官方解释出处

- 官方发布流程（含 base image 说明、多平台构建命令）：https://pulsar.apache.org/contribute/release-process-maven
- 官方 README 自建镜像章节（`Build custom docker images`）：https://github.com/apache/pulsar/tree/branch-4.0
- musl 崩溃族原始报告：https://gitlab.alpinelinux.org/alpine/aports/-/issues/15582
- tcnative 修复（2.0.62）：https://github.com/netty/netty-tcnative/issues/789
