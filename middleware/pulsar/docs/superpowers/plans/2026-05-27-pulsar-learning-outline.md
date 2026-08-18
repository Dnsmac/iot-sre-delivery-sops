# Apache Pulsar 学习大纲 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `docs/superpowers/specs/2026-05-27-pulsar-learning-outline-design.md` 落地为可学习、可运行、可查阅的 Pulsar 知识仓库（文档 + Java 示例 + 脚本 + 附录）。

**Architecture:** 按 Part A/B/C/D 分目录存放 Markdown 教程；`examples/java/` 多模块 Maven 工程承载可运行 Java 示例；`scripts/` 和 `docker/` 提供 Standalone 环境；附录独立成速查文件；各文档通过相对链接互引，问题百科反向索引到章节。

**Tech Stack:** Markdown、Java 8（父示例）/ Spring 模块需 JDK 17、Maven、`pulsar-client` 3.2.3、Spring Boot 3.2+（B7 独立模块）、Testcontainers、Docker Compose（Standalone）、PowerShell 脚本。

**Spec 来源:** [2026-05-27-pulsar-learning-outline-design.md](../specs/2026-05-27-pulsar-learning-outline-design.md)

---

## 文件结构总览

```
pulsar/
├── README.md                              # 仓库入口 + 学习路线
├── docs/
│   ├── INDEX.md                           # 全局导航（链接 A/B/C/D + 附录）
│   ├── part-a-interview/                  # A1-A12，每章一个 md
│   ├── part-b-java-dev/                   # B1-B12
│   ├── part-c-ops/                        # C1-C12
│   ├── part-d-problems/                   # 问题百科
│   └── appendices/                        # 附录 A-J
├── examples/java/
│   ├── pom.xml                            # 父 POM
│   ├── pulsar-basics/                     # B1-B3, B6
│   ├── pulsar-producer-tuning/            # B10
│   ├── pulsar-troubleshooting/            # B9 场景复现
│   ├── pulsar-spring/                     # B7
│   └── pulsar-loadtest/                   # C11 10W 设备压测
├── docker/
│   └── docker-compose-standalone.yml
└── scripts/
    ├── standalone-up.ps1
    ├── setup-dev-tenant.ps1
    └── verify-examples.ps1
```

**实施顺序:** Phase 0 → Phase 1（P1 面试）→ Phase 2（P2 开发）→ Phase 3（P3 扩展）→ Phase 4（交叉链接与验收）

---

## Phase 0：仓库脚手架

### Task 0: 初始化仓库结构与入口文档

**Files:**
- Create: `README.md`
- Create: `docs/INDEX.md`
- Create: `.gitignore`

- [ ] **Step 1: 创建 `.gitignore`**

```gitignore
target/
.idea/
*.iml
.classpath
.project
.settings/
.DS_Store
```

- [ ] **Step 2: 创建 `README.md`**

```markdown
# Apache Pulsar 完整学习仓库

> 面试 P1 → 开发 P2 → 扩展 P3 | Java 为主

## 学习路线

| 阶段 | 周期 | 内容 | 入口 |
|------|------|------|------|
| Phase 1 | Week 1-2 | Part A 面试核心 | [docs/part-a-interview/](docs/part-a-interview/) |
| Phase 2 | Week 3-5 | Part B Java 开发 | [docs/part-b-java-dev/](docs/part-b-java-dev/) |
| Phase 3 | Week 6+ | Part C 运维扩展 | [docs/part-c-ops/](docs/part-c-ops/) |
| 全阶段 | 随时 | Part D 问题百科 + 附录 | [docs/INDEX.md](docs/INDEX.md) |

## 快速开始

```powershell
# 启动 Standalone
.\scripts\standalone-up.ps1
# 初始化 dev tenant
.\scripts\setup-dev-tenant.ps1
# 运行 Hello World
cd examples/java/pulsar-basics
mvn -q exec:java -Dexec.mainClass="com.demo.pulsar.HelloPulsar"
```

## 设计文档

- Spec: [docs/superpowers/specs/2026-05-27-pulsar-learning-outline-design.md](docs/superpowers/specs/2026-05-27-pulsar-learning-outline-design.md)
- Plan: [docs/superpowers/plans/2026-05-27-pulsar-learning-outline.md](docs/superpowers/plans/2026-05-27-pulsar-learning-outline.md)
```

- [ ] **Step 3: 创建 `docs/INDEX.md` 骨架**

```markdown
# Pulsar 学习索引

## Part A 面试核心（P1）
- [A1 Pulsar 是什么](part-a-interview/A1-Pulsar是什么.md)
- [A2 核心架构](part-a-interview/A2-核心架构.md)
<!-- A3-A12 占位，Task 1-12 填充 -->

## Part B Java 开发（P2）
<!-- B1-B12 占位 -->

## Part C 运维扩展（P3）
<!-- C1-C12 占位 -->

## Part D 问题百科
- [问题索引](part-d-problems/INDEX.md)

## 附录
- [A 面试题索引](appendices/A-面试题与参考答案.md)
- [B Kafka 对照表](appendices/B-Kafka对照.md)
<!-- C-J 占位 -->
```

- [ ] **Step 4: 创建空目录**

Run:
```powershell
@(
  "docs/part-a-interview","docs/part-b-java-dev","docs/part-c-ops",
  "docs/part-d-problems","docs/appendices",
  "examples/java","docker","scripts"
) | ForEach-Object { New-Item -ItemType Directory -Force -Path "middleware\pulsar\$_" | Out-Null }
```
Expected: 目录创建成功，无报错

- [ ] **Step 5: Commit**

```bash
git add README.md docs/INDEX.md .gitignore
git commit -m "chore: scaffold pulsar learning repo structure"
```

---

### Task 1: Standalone 环境与 dev Tenant 脚本

**Files:**
- Create: `docker/docker-compose-standalone.yml`
- Create: `scripts/standalone-up.ps1`
- Create: `scripts/setup-dev-tenant.ps1`

- [ ] **Step 1: 创建 `docker/docker-compose-standalone.yml`**

```yaml
services:
  pulsar:
    image: apachepulsar/pulsar:3.2.3
    container_name: pulsar-standalone
    ports:
      - "6650:6650"
      - "8080:8080"
    command: bin/pulsar standalone
    healthcheck:
      test: ["CMD", "bin/pulsar-admin", "brokers", "healthcheck"]
      interval: 10s
      timeout: 5s
      retries: 12
```

- [ ] **Step 2: 创建 `scripts/standalone-up.ps1`**

```powershell
Set-Location (Join-Path $PSScriptRoot ".." "docker")
docker compose -f docker-compose-standalone.yml up -d
Write-Host "Pulsar Standalone: pulsar://localhost:6650  Admin: http://localhost:8080"
docker compose -f docker-compose-standalone.yml ps
```

- [ ] **Step 3: 创建 `scripts/setup-dev-tenant.ps1`**

```powershell
$admin = "http://localhost:8080"
docker exec pulsar-standalone bin/pulsar-admin tenants create dev 2>$null
docker exec pulsar-standalone bin/pulsar-admin namespaces create dev/test 2>$null
docker exec pulsar-standalone bin/pulsar-admin topics create persistent://dev/test/hello 2>$null
Write-Host "Ready: persistent://dev/test/hello"
```

- [ ] **Step 4: 验证 Standalone 启动**

Run:
```powershell
cd middleware\pulsar
.\scripts\standalone-up.ps1
Start-Sleep -Seconds 30
.\scripts\setup-dev-tenant.ps1
docker exec pulsar-standalone bin/pulsar-admin topics list dev/test
```
Expected: 输出包含 `persistent://dev/test/hello`

- [ ] **Step 5: Commit**

```bash
git add docker/ scripts/
git commit -m "feat: add standalone docker and dev tenant setup scripts"
```

---

## Phase 1：Part A 面试核心（P1）+ 附录 A/B

> 每个 Task 产出一章 Markdown + 更新 `docs/INDEX.md` 链接。  
> 章节模板统一，便于维护。

**章节模板（每章必含）：**
```markdown
# A{N} 标题
> 优先级: P1 | 面试

## 面试常问
## 核心知识
## 必答要点（表格/图）
## 易错点
## 相关章节
- 开发实践 → [B{x}](../part-b-java-dev/...)
- 问题排查 → [D{x}](../part-d-problems/...)
```

### Task 2: A1 — Pulsar 是什么

**Files:**
- Create: `docs/part-a-interview/A1-Pulsar是什么.md`
- Modify: `docs/INDEX.md`

- [ ] **Step 1: 写入 A1 完整内容**（基于 spec §A1，含 Kafka/RabbitMQ/RocketMQ 对比表、选型决策树、3.x 版本说明）

- [ ] **Step 2: 更新 `docs/INDEX.md` A1 链接**

- [ ] **Step 3: 自检** — 确认含「面试常问」≥3 条、对比表、相关章节链接

- [ ] **Step 4: Commit** — `docs: add A1 what is pulsar`

### Task 3: A2 — 核心架构

**Files:**
- Create: `docs/part-a-interview/A2-核心架构.md`

- [ ] **Step 1: 写入 A2** — 含 ASCII 架构图、写入/读取路径、组件表、Broker 无状态精确定义、Metadata Store ZK/Oxia 说明

- [ ] **Step 2: Commit** — `docs: add A2 architecture`

### Task 4: A3-A6（层级、Topic、订阅、ACK）

**Files:**
- Create: `docs/part-a-interview/A3-多租户层级.md`
- Create: `docs/part-a-interview/A4-Topic体系.md`
- Create: `docs/part-a-interview/A5-订阅模式.md`
- Create: `docs/part-a-interview/A6-ACK与投递语义.md`

- [ ] **Step 1: 写入 A3** — Tenant/Namespace/Topic、Isolation Policy

- [ ] **Step 2: 写入 A4** — 五种 Topic 类型、分区机制、海量 Topic 问题、Compaction vs Retention

- [ ] **Step 3: 写入 A5** — 四种订阅模式完整对比表、Key_Shared 策略、vs Kafka

- [ ] **Step 4: 写入 A6** — 三种语义、单条/累积 ACK、Cursor vs Offset、重复消费原因

- [ ] **Step 5: 更新 INDEX.md 四个链接**

- [ ] **Step 6: Commit** — `docs: add A3-A6 interview core`

### Task 5: A7-A12（保留、异常、Schema、高级、BK、性能）

**Files:**
- Create: `docs/part-a-interview/A7-保留与清理策略.md`
- Create: `docs/part-a-interview/A8-重试与DLQ.md`
- Create: `docs/part-a-interview/A9-Schema注册.md`
- Create: `docs/part-a-interview/A10-高级特性.md`
- Create: `docs/part-a-interview/A11-BookKeeper深入.md`
- Create: `docs/part-a-interview/A12-性能与规模.md`

- [ ] **Step 1-6: 按 spec 逐章写入，每章含面试常问 + 易错点**

- [ ] **Step 7: 更新 INDEX.md**

- [ ] **Step 8: Commit** — `docs: add A7-A12 interview core`

### Task 6: 附录 A — 面试题索引（含参考答案链接）

**Files:**
- Create: `docs/appendices/A-面试题与参考答案.md`

- [ ] **Step 1: 写入 50 题**，每题格式：

```markdown
### Q1. Pulsar 架构是怎样的？
**要点:** Broker 无状态 / BookKeeper 持久化 / Metadata Store
**详见:** [A2 核心架构](../part-a-interview/A2-核心架构.md)
**参考答案摘要:** （3-5 句）
```

- [ ] **Step 2: 按架构/对比/Topic/订阅/保留/异常/Schema/高级/性能/多租户 10 类分组**

- [ ] **Step 3: 更新 INDEX.md 附录链接**

- [ ] **Step 4: Commit** — `docs: add appendix A interview questions with answers`

### Task 7: 附录 B — Kafka 对照表

**Files:**
- Create: `docs/appendices/B-Kafka对照.md`

- [ ] **Step 1: 写入对照表** — 架构/消费模型/保留/多租户/订阅/Geo/协议/运维/选型决策 9 维度

- [ ] **Step 2: Commit** — `docs: add appendix B kafka comparison`

### Task 8: Phase 1 验收

- [ ] **Step 1: 链接检查** — `docs/INDEX.md` 中 Part A 12 章 + 附录 A/B 均可点击

- [ ] **Step 2: 面试覆盖检查** — spec §8 的 50 题每题在附录 A 有对应条目且链接到 Part A 章节

- [ ] **Step 3: Commit** — `chore: phase 1 interview docs complete`

---

## Phase 2：Part B Java 开发（P2）+ 可运行示例 + 附录 C-F/I/J

### Task 9: Java 父 POM 与 pulsar-basics 模块

**Files:**
- Create: `examples/java/pom.xml`
- Create: `examples/java/pulsar-basics/pom.xml`
- Create: `examples/java/pulsar-basics/src/main/java/com/demo/pulsar/HelloPulsar.java`
- Create: `examples/java/pulsar-basics/src/test/java/com/demo/pulsar/HelloPulsarTest.java`

- [ ] **Step 1: 父 POM**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.demo.pulsar</groupId>
  <artifactId>pulsar-examples</artifactId>
  <version>1.0.0-SNAPSHOT</version>
  <packaging>pom</packaging>
  <modules>
    <module>pulsar-basics</module>
    <module>pulsar-producer-tuning</module>
    <module>pulsar-troubleshooting</module>
    <module>pulsar-spring</module>
    <module>pulsar-loadtest</module>
  </modules>
  <properties>
    <java.version>17</java.version>
    <pulsar.version>3.2.3</pulsar.version>
    <maven.compiler.source>17</maven.compiler.source>
    <maven.compiler.target>17</maven.compiler.target>
  </properties>
</project>
```

- [ ] **Step 2: pulsar-basics/pom.xml** — 依赖 `pulsar-client`、`junit-jupiter`、`testcontainers`（scope test）

- [ ] **Step 3: 写入 `HelloPulsar.java`**

```java
package com.demo.pulsar;

import org.apache.pulsar.client.api.*;

public class HelloPulsar {
    public static void main(String[] args) throws Exception {
        String url = System.getenv().getOrDefault("PULSAR_URL", "pulsar://localhost:6650");
        String topic = "persistent://dev/test/hello";
        try (PulsarClient client = PulsarClient.builder().serviceUrl(url).build()) {
            try (Producer<String> producer = client.newProducer(Schema.STRING).topic(topic).create()) {
                producer.send("hello pulsar");
            }
            try (Consumer<String> consumer = client.newConsumer(Schema.STRING)
                    .topic(topic)
                    .subscriptionName("hello-sub")
                    .subscriptionType(SubscriptionType.Exclusive)
                    .subscribe()) {
                Message<String> msg = consumer.receive(5, java.util.concurrent.TimeUnit.SECONDS);
                if (msg != null) {
                    System.out.println("Received: " + msg.getValue());
                    consumer.acknowledge(msg);
                }
            }
        }
    }
}
```

- [ ] **Step 4: 写入 Testcontainers 测试 `HelloPulsarTest.java`**

```java
package com.demo.pulsar;

import org.apache.pulsar.client.api.*;
import org.junit.jupiter.api.Test;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import static org.junit.jupiter.api.Assertions.*;

@Testcontainers
class HelloPulsarTest {
    @Container
    static GenericContainer<?> pulsar = new GenericContainer<>("apachepulsar/pulsar:3.2.3")
            .withExposedPorts(6650)
            .withCommand("bin/pulsar", "standalone");

    @Test
    void produceAndConsume() throws Exception {
        String url = "pulsar://" + pulsar.getHost() + ":" + pulsar.getMappedPort(6650);
        try (PulsarClient client = PulsarClient.builder().serviceUrl(url).build()) {
            String topic = "persistent://public/default/test-" + System.nanoTime();
            try (Producer<String> p = client.newProducer(Schema.STRING).topic(topic).create()) {
                p.send("ok");
            }
            try (Consumer<String> c = client.newConsumer(Schema.STRING)
                    .topic(topic).subscriptionName("t").subscribe()) {
                Message<String> m = c.receive(10, java.util.concurrent.TimeUnit.SECONDS);
                assertNotNull(m);
                assertEquals("ok", m.getValue());
                c.acknowledge(m);
            }
        }
    }
}
```

- [ ] **Step 5: 运行测试**

Run: `cd middleware\pulsar\examples\java\pulsar-basics && mvn test -q`
Expected: BUILD SUCCESS（需 Docker 运行中）

- [ ] **Step 6: Commit** — `feat: add pulsar-basics hello example with testcontainers`

### Task 10: B1-B3 文档 + Producer/Consumer 示例

**Files:**
- Create: `docs/part-b-java-dev/B1-Java客户端基础.md`
- Create: `docs/part-b-java-dev/B2-生产者.md`
- Create: `docs/part-b-java-dev/B3-消费者.md`
- Create: `examples/java/pulsar-basics/src/main/java/com/demo/pulsar/ProducerDemo.java`
- Create: `examples/java/pulsar-basics/src/main/java/com/demo/pulsar/ConsumerDemo.java`
- Create: `examples/java/pulsar-basics/src/main/java/com/demo/pulsar/KeySharedConsumerDemo.java`

- [ ] **Step 1: B1 文档** — Client 生命周期、Schema 类型、一个 JVM 一个 Client

- [ ] **Step 2: `ProducerDemo.java`** — 同步/异步、`sendAsync().exceptionally()`、Key、Properties

- [ ] **Step 3: B2 文档** — 链接 ProducerDemo，含 Batching/压缩配置说明（代码注释 + 文档表格）

- [ ] **Step 4: `ConsumerDemo.java`** — MessageListener、ACK/NACK、DLQ 配置

- [ ] **Step 5: `KeySharedConsumerDemo.java`** — Key_Shared + STICKY 策略

- [ ] **Step 6: B3 文档** — 四种模式选型表、链接三个 Demo

- [ ] **Step 7: 本地运行验证**

Run:
```powershell
cd middleware\pulsar\examples\java\pulsar-basics
mvn -q exec:java -Dexec.mainClass="com.demo.pulsar.ProducerDemo"
mvn -q exec:java -Dexec.mainClass="com.demo.pulsar.ConsumerDemo"
```
Expected: Producer 发送成功，Consumer 打印消息

- [ ] **Step 8: Commit** — `feat: add B1-B3 docs and producer/consumer demos`

### Task 11: B4-B8 文档 + Spring 模块

**Files:**
- Create: `docs/part-b-java-dev/B4-多服务协作.md`
- Create: `docs/part-b-java-dev/B5-大数据量注意点.md`
- Create: `docs/part-b-java-dev/B6-本地开发.md`
- Create: `docs/part-b-java-dev/B7-Spring集成.md`
- Create: `docs/part-b-java-dev/B8-配置管理.md`
- Create: `examples/java/pulsar-spring/pom.xml`
- Create: `examples/java/pulsar-spring/src/main/java/com/demo/pulsar/spring/PulsarSpringApp.java`
- Create: `examples/java/pulsar-spring/src/main/resources/application-dev.yml`

- [ ] **Step 1: B4** — Topic/订阅命名规范、多服务独立 Subscription 图示、Schema Maven 模块协作

- [ ] **Step 2: B5** — 大数据量配置表（直接来自 spec §B5）

- [ ] **Step 3: B6** — Standalone 操作、`pulsar-admin` 常用命令、链接 `scripts/`

- [ ] **Step 4: B8** — dev/staging/prod 三份 YAML 模板

```yaml
# application-dev.yml
spring:
  pulsar:
    client:
      service-url: pulsar://localhost:6650
app:
  pulsar:
    tenant: dev
    namespace: test
```

- [ ] **Step 5: pulsar-spring 模块** — Spring Boot 3.2 + `@PulsarListener` 最小示例

- [ ] **Step 6: B7 文档** — 链接 Spring 示例

- [ ] **Step 7: Commit** — `feat: add B4-B8 docs and spring example`

### Task 12: B9 排障文档 + troubleshooting 示例

**Files:**
- Create: `docs/part-b-java-dev/B9-排障手册.md`
- Create: `examples/java/pulsar-troubleshooting/pom.xml`
- Create: `examples/java/pulsar-troubleshooting/src/main/java/com/demo/pulsar/trouble/MissingAckDemo.java`
- Create: `examples/java/pulsar-troubleshooting/src/main/java/com/demo/pulsar/trouble/DuplicateConsumeDemo.java`
- Create: `examples/java/pulsar-troubleshooting/src/main/java/com/demo/pulsar/trouble/SharedOrderingDemo.java`

- [ ] **Step 1: B9 文档** — 五步方法论 + 12 场景完整表格（现象/定位/解决/预防），每场景链接对应 Demo 或 admin 命令

- [ ] **Step 2: `MissingAckDemo.java`** — 演示异步发送无 exceptionally → 配合 `topics stats` 排查

- [ ] **Step 3: `DuplicateConsumeDemo.java`** — ackTimeout 过短触发重复

- [ ] **Step 4: `SharedOrderingDemo.java`** — Shared 乱序 vs Key_Shared 对比

- [ ] **Step 5: 文档中写排查命令示例**

```powershell
docker exec pulsar-standalone bin/pulsar-admin topics stats persistent://dev/test/hello
docker exec pulsar-standalone bin/pulsar-admin topics peek-messages persistent://dev/test/hello -s hello-sub -n 5
```

- [ ] **Step 6: Commit** — `feat: add B9 troubleshooting docs and repro demos`

### Task 13: B10-B11 性能调优文档 + tuning 示例

**Files:**
- Create: `docs/part-b-java-dev/B10-性能调优.md`
- Create: `docs/part-b-java-dev/B11-性能验证.md`
- Create: `examples/java/pulsar-producer-tuning/pom.xml`
- Create: `examples/java/pulsar-producer-tuning/src/main/java/com/demo/pulsar/tuning/BatchCompareBenchmark.java`

- [ ] **Step 1: B10 文档** — 金字塔 L0-L5、决策树、参数表、分区估算公式（spec §B10 全文）

- [ ] **Step 2: `BatchCompareBenchmark.java`**

```java
// 同一 Topic 先后跑：batchingEnabled=false vs true + LZ4
// 输出 TPS 和 P99 延迟对比
public class BatchCompareBenchmark {
    public static void main(String[] args) throws Exception {
        int count = 50_000;
        benchmark(false, CompressionType.NONE, count);
        benchmark(true, CompressionType.LZ4, count);
    }
    // benchmark 方法：计时 + producer.flush()
}
```

- [ ] **Step 3: B11 文档** — stats 对比法、Java 埋点模板、BatchCompareBenchmark 运行说明

- [ ] **Step 4: 运行 Benchmark（Standalone 已启动）**

Run: `mvn -q exec:java -Dexec.mainClass="com.demo.pulsar.tuning.BatchCompareBenchmark" -f examples/java/pulsar-producer-tuning/pom.xml`
Expected: 输出两组 TPS，Batching 组明显高于非 Batching

- [ ] **Step 5: Commit** — `feat: add B10-B11 performance docs and batch benchmark`

### Task 14: B12 环境模型文档

**Files:**
- Create: `docs/part-b-java-dev/B12-环境模型.md`
- Create: `docs/appendices/I-环境迁移清单.md`
- Create: `docs/appendices/J-环境差异矩阵.md`

- [ ] **Step 1: B12 文档** — Standalone/Cluster/K8s 对比、dev/压测/prod 矩阵、14 项迁移清单、K8s 7 坑、B12.7 环境×调优表

- [ ] **Step 2: 附录 I** — 14 项 Checklist 独立可打印表格

- [ ] **Step 3: 附录 J** — 环境差异速查矩阵

- [ ] **Step 4: Commit** — `docs: add B12 environment models and appendices I/J`

### Task 15: 附录 C-F（开发速查）

**Files:**
- Create: `docs/appendices/C-Java客户端速查.md`
- Create: `docs/appendices/D-性能参数速查.md`
- Create: `docs/appendices/E-排查决策树.md`
- Create: `docs/appendices/F-pulsar-admin速查.md`

- [ ] **Step 1: 附录 C** — Producer/Consumer/Reader 常用 API 一行一例

- [ ] **Step 2: 附录 D** — B10 参数精华表

- [ ] **Step 3: 附录 E** — B9+B10 决策树 Mermaid 或 ASCII 版

- [ ] **Step 4: 附录 F** — 15+ admin 命令 + 使用场景

- [ ] **Step 5: 更新 INDEX.md 全部附录链接**

- [ ] **Step 6: Commit** — `docs: add appendices C-F developer cheatsheets`

### Task 16: `scripts/verify-examples.ps1` + Phase 2 验收

**Files:**
- Create: `scripts/verify-examples.ps1`

- [ ] **Step 1: 验证脚本** — 依次 `mvn test` 各模块、检查 exit code

```powershell
$modules = @("pulsar-basics","pulsar-troubleshooting","pulsar-producer-tuning")
foreach ($m in $modules) {
  Push-Location "examples/java/$m"
  mvn -q test
  if ($LASTEXITCODE -ne 0) { throw "Failed: $m" }
  Pop-Location
}
Write-Host "All examples passed"
```

- [ ] **Step 2: 运行验收**

Run: `.\scripts\verify-examples.ps1`
Expected: All examples passed

- [ ] **Step 3: Commit** — `chore: add verify-examples script, phase 2 complete`

---

## Phase 3：Part C 运维扩展（P3）+ 10W 压测项目 + 附录 G/H

### Task 17: C1-C6 运维文档

**Files:**
- Create: `docs/part-c-ops/C1-集群部署.md`
- Create: `docs/part-c-ops/C2-硬件规划.md`
- Create: `docs/part-c-ops/C3-BookKeeper调优.md`
- Create: `docs/part-c-ops/C4-Broker调优.md`
- Create: `docs/part-c-ops/C5-监控告警.md`
- Create: `docs/part-c-ops/C6-安全.md`

- [ ] **Step 1-6: 按 spec §5 逐章写入** — 每章含配置示例、指标阈值、与 B10 L4 升级信号交叉链接

- [ ] **Step 7: Commit** — `docs: add C1-C6 ops docs`

### Task 18: C7-C10 + C12 文档

**Files:**
- Create: `docs/part-c-ops/C7-跨机房复制.md`
- Create: `docs/part-c-ops/C8-分层存储.md`
- Create: `docs/part-c-ops/C9-升级迁移.md`
- Create: `docs/part-c-ops/C10-故障预案.md`
- Create: `docs/part-c-ops/C12-源码导读.md`

- [ ] **Step 1-5: 写入文档** — C10 Runbook 至少 6 个故障场景（Bookie 磁盘满、Backlog、OOM、元数据不一致等）

- [ ] **Step 2: Commit** — `docs: add C7-C10 C12 ops docs`

### Task 19: C11 — 10W 设备压测实战

**Files:**
- Create: `docs/part-c-ops/C11-十万设备压测.md`
- Create: `examples/java/pulsar-loadtest/pom.xml`
- Create: `examples/java/pulsar-loadtest/src/main/java/com/demo/pulsar/loadtest/DeviceSimulator.java`
- Create: `examples/java/pulsar-loadtest/src/main/java/com/demo/pulsar/loadtest/LoadTestRunner.java`
- Create: `examples/java/pulsar-loadtest/src/main/resources/loadtest.properties`

- [ ] **Step 1: C11 文档** — 压测目标、Topic 设计（少量 Topic + deviceId Key）、分区数公式、阶梯压测矩阵、必看指标、环境要求（必须 Cluster）

- [ ] **Step 2: `DeviceSimulator.java`**

```java
// 模拟单设备：deviceId 作 Key，可配置 msg/s 和 payload 大小
public class DeviceSimulator implements Runnable {
    private final Producer<byte[]> producer;
    private final String deviceId;
    private final int intervalMs;
    private final byte[] payload;

    public DeviceSimulator(Producer<byte[]> producer, String deviceId, int intervalMs, int payloadBytes) {
        this.producer = producer;
        this.deviceId = deviceId;
        this.intervalMs = intervalMs;
        this.payload = new byte[payloadBytes];
    }

    @Override
    public void run() {
        while (!Thread.currentThread().isInterrupted()) {
            try {
                producer.newMessage().key(deviceId).value(payload).sendAsync();
                Thread.sleep(intervalMs);
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        }
    }
}
```

- [ ] **Step 3: `LoadTestRunner.java`** — 读取 `loadtest.properties`：`device.count`、`topic`、`partitions`、`threads`、`payload.bytes`；线程池启动 N 个 DeviceSimulator；输出 TPS

- [ ] **Step 4: `loadtest.properties` 默认配置**

```properties
pulsar.url=pulsar://localhost:6650
topic=persistent://dev/test/device-telemetry
device.count=1000
threads=50
interval.ms=1000
payload.bytes=512
partitions=8
```

- [ ] **Step 5: 文档说明** — 1000 设备本地冒烟；10W 设备需 Cluster + 多机分布式运行 LoadTestRunner

- [ ] **Step 6: 冒烟运行（1000 设备）**

Run: `mvn -q exec:java -Dexec.mainClass="com.demo.pulsar.loadtest.LoadTestRunner" -f examples/java/pulsar-loadtest/pom.xml`
Expected: 输出 TPS > 0，无异常退出

- [ ] **Step 7: Commit** — `feat: add C11 100k device loadtest doc and simulator`

### Task 20: 附录 G/H

**Files:**
- Create: `docs/appendices/G-配置参考.md`
- Create: `docs/appendices/H-学习资源.md`

- [ ] **Step 1: 附录 G** — Broker/Bookie/Client 关键配置参数（各 20+ 条，含默认值和说明）

- [ ] **Step 2: 附录 H** — 官方文档、BookKeeper 论文、StreamNative 博客、版本说明链接

- [ ] **Step 3: Commit** — `docs: add appendices G/H`

---

## Phase 4：Part D 问题百科 + 全局交叉链接 + 最终验收

### Task 21: Part D 问题百科

**Files:**
- Create: `docs/part-d-problems/INDEX.md`
- Create: `docs/part-d-problems/P1-消息丢失.md`
- Create: `docs/part-d-problems/P2-重复消费.md`
- Create: `docs/part-d-problems/P3-消息乱序.md`
- Create: `docs/part-d-problems/P4-积压.md`
- Create: `docs/part-d-problems/P5-性能不足.md`
- Create: `docs/part-d-problems/P6-连接问题.md`
- Create: `docs/part-d-problems/P7-Schema问题.md`
- Create: `docs/part-d-problems/P8-内存溢出.md`
- Create: `docs/part-d-problems/P9-本地与集群差异.md`
- Create: `docs/part-d-problems/P10-K8s问题.md`
- Create: `docs/part-d-problems/P11-Bookie磁盘满.md`

- [ ] **Step 1: `INDEX.md`** — 按现象索引表（spec §6 全部条目 + 链接）

- [ ] **Step 2: 每个 P{x}.md 统一模板**

```markdown
# 现象：消息丢失
> 优先级: P1 | 链接: A6, B9-场景1

## 典型现象
## 原因列表（按概率排序）
## 排查步骤（命令 + 代码检查点）
## 解决方案
## 预防措施
## 相关示例
- [MissingAckDemo](../../examples/java/pulsar-troubleshooting/...)
```

- [ ] **Step 3: Commit** — `docs: add part D problem encyclopedia`

### Task 22: 实战项目索引页

**Files:**
- Create: `docs/projects/INDEX.md`
- Create: `docs/projects/P1-订单系统.md`
- Create: `docs/projects/P2-Schema演进.md`
- Create: `docs/projects/P3-上集群迁移.md`

- [ ] **Step 1: 写入 7 个实战项目**（spec §9），每个含：目标、前置章节、步骤清单、验收标准

- [ ] **Step 2: 10W 压测项目链接 C11 + pulsar-loadtest 模块**

- [ ] **Step 3: 更新 README.md 和 INDEX.md 加入 projects 链接**

- [ ] **Step 4: Commit** — `docs: add hands-on projects index`

### Task 23: 全局交叉链接与 INDEX 完善

**Files:**
- Modify: `docs/INDEX.md`
- Modify: `README.md`

- [ ] **Step 1: 补全 INDEX.md** — Part A 12 章、Part B 12 章、Part C 12 章、Part D 11 篇、附录 A-J、Projects 全部链接

- [ ] **Step 2: 每章末尾「相关章节」链接抽查** — 至少 A5↔B3↔P3、A6↔B9↔P1、B10↔D5、B12↔P9↔I↔J

- [ ] **Step 3: Commit** — `docs: complete cross-links and index`

### Task 24: 最终验收

- [ ] **Step 1: 文档覆盖自检**（对照 spec）

| Spec 章节 | 对应文件 | 状态 |
|-----------|---------|------|
| A1-A12 | docs/part-a-interview/A*.md | ☐ |
| B1-B12 | docs/part-b-java-dev/B*.md | ☐ |
| C1-C12 | docs/part-c-ops/C*.md | ☐ |
| Part D | docs/part-d-problems/P*.md | ☐ |
| 附录 A-J | docs/appendices/*.md | ☐ |
| 实战项目 | docs/projects/*.md | ☐ |

- [ ] **Step 2: 代码验收**

Run:
```powershell
cd middleware\pulsar
.\scripts\standalone-up.ps1
.\scripts\setup-dev-tenant.ps1
.\scripts\verify-examples.ps1
```
Expected: All examples passed

- [ ] **Step 3: 面试题覆盖** — 附录 A 50 题均可通过链接到达 Part A 章节

- [ ] **Step 4: Commit** — `chore: pulsar learning repo v1.0 complete`

---

## Spec 覆盖自检

| Spec 要求 | 对应 Task |
|-----------|----------|
| Part A 面试 12 章 | Task 2-5 |
| 附录 A 50+ 面试题 | Task 6 |
| 附录 B Kafka 对照 | Task 7 |
| Part B Java 开发 B1-B12 | Task 10-14 |
| B9 12 场景排障 | Task 12 + Task 21 P1-P10 |
| B10 性能金字塔+决策树 | Task 13 + 附录 D/E |
| B12 环境差异+迁移清单 | Task 14 + 附录 I/J |
| Part C C1-C12 | Task 17-19 |
| C11 10W 压测 | Task 19 |
| Part D 问题百科 | Task 21 |
| 附录 C-J | Task 15, 14, 20 |
| 实战项目 7 个 | Task 22 |
| Java 示例可运行 | Task 9-13, 19 |
| Standalone 环境 | Task 1 |
| 学习路径 README | Task 0 |

**无遗漏。**

---

## 执行建议

| 批次 | Task 范围 | 预估 | 产出 |
|------|----------|------|------|
| 第 1 天 | Task 0-1 | 2h | 脚手架 + Standalone |
| 第 2-4 天 | Task 2-8 | 3 天 | Part A + 附录 A/B（P1 完成） |
| 第 5-10 天 | Task 9-16 | 5 天 | Part B + Java 示例 + 附录 C-F/I/J（P2 完成） |
| 第 11-14 天 | Task 17-20 | 4 天 | Part C + 压测 + 附录 G/H（P3 完成） |
| 第 15-16 天 | Task 21-24 | 2 天 | 问题百科 + 交叉链接 + 验收 |

**优先执行顺序:** Task 0 → 1 → 9（Hello World 跑通）→ 2-8（面试文档）→ 10-16（开发文档+示例）→ 其余按需。
