# 故事草稿 · BSC 国产化 IoT + 运维子系统交付

> 可并入 W7 简历 bullet / 面试模块故事。卖点：**部署工程化 + 交付稳定性**，不卖「性能优化负责人」。  
> 证据目录：[`01-K8s-Troubleshooting/cases/bsc-iot-meta-k8s-delivery/`](../../01-K8s-Troubleshooting/cases/bsc-iot-meta-k8s-delivery/README.md)

## 背景

国产化 K8s 环境交付 IoT 业务和运维子系统。交付物包含 iot-web、iot-server、规则引擎、数据流、atomic、mcp、zlmedia，以及 MySQL InnoDBCluster、Mimir、Loki、Grafana、Categraf、alert-service、dfr、gas 等组件。源交付包：`C:\Users\kaihong\Desktop\bsc\k8s`。

## 冲突

1. 配置分散：约 26 处硬编码 IP 分布在 7 个文件，换环境容易漏改。
2. 部署链路长：镜像 pull → import → deploy 分属不同机器，版本断链要等 Pod 起不来才发现。
3. 访问入口复杂：无域名、节点 80 被 Kuboard 占用，且 Ingress 与 iot-web 维护两套重复路由。
4. 资源与伸缩不可控：多数组件没有 request/limit，HPA 指标有抖动。
5. 重复部署不可靠：Job 模板不可变、初始化失败可能被静默吞掉。

## 行动

1. 拆成运维子系统与 IoT 两个 `settings.env`，用脚本按模式同步配置。
2. 建立统一 `images.txt` 镜像清单；部署前扫描 YAML image 并调 Harbor API 预检。
3. Ingress 改 catch-all，业务路由唯一权威收敛到 `iot-web`；Grafana 直连用于排障。
4. 全组件补 request/limit，调整 MySQL buffer pool、dfr request 与 gas HPA 指标。
5. deploy 脚本处理旧 Job、依赖顺序、rollout 等待和失败显式退出。
6. 输出业务网/运维网端口最小化说明，供客户审批与后续复用。

## 结果

- 实施人员只需改两个环境文件，重复执行 `deploy-all.sh`、`deploy-iot.sh`。
- 镜像缺失从 Pod 启动失败前移到部署前预检。
- 纯 IP 可访问业务与 Grafana，运维流量保留独立入口。
- 部署、验收、问题定位口径沉淀在交付手册与排查记录中。

## 30 秒口径

> 这次交付不是简单 apply YAML。我先把 26 处死 IP 收敛到两个 settings.env，再把镜像导入和部署预检串起来；入口侧用 catch-all Ingress 解决无域名问题，并把路由权威收敛到 iot-web；最后补齐资源、HPA、Job 幂等和端口最小化。实施侧从改几十个 YAML，变成改两个环境文件加两个一键脚本。

## 简历 bullet（草稿）

- 主导/参与国产化 K8s 上 IoT + 运维子系统离线交付：将约 26 处死 IP 收敛到两个 settings.env，补齐镜像预检、资源/HPA 与 Job 幂等，形成一键部署与可重复验收口径。

## 诚实边界

- 不夸大为「性能优化负责人」：这是部署工程化与交付稳定性改造。
- 不虚构百分比收益：本次可讲清问题规模、方案取舍和验收口径；有实测数字后再替换。
