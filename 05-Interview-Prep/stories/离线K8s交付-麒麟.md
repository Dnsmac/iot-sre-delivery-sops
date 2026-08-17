# 故事草稿 · 麒麟离线 K8s 交付一次过

> 可并入 W7 简历 bullet / 面试模块故事。卖点：**交付闭环 + 排障深度**，不卖「压测负责人」。

## 背景

国产化机房麒麟 V10，完全离线部署 K8s v1.26 + Harbor + Redis/Pulsar；六台分工（NFS/Spray、Harbor、四节点）。

## 冲突 / 难点

物料闭包不足、验收误报、模拟断外网伤 Spray、CNI Sandbox 导致 Redis 重启、Pulsar JWT Secret 缺失、传包截断。

## 行动

版本化交付包（B00～B09）、preflight、按角色 iptables、固定 JWT、Sandbox/Helm pending SOP；文档「重装必读」。

## 结果

脚本迭代至 v1.0.14；中间件可 deployed；踩坑沉淀为本仓 `cases/kylin-offline-k8s-v1.26/`。

## 简历 bullet（草稿）

- 主导/参与麒麟离线 Kubernetes 交付：分包物料校验、Harbor 导入验收口径修正、Calico Sandbox 与 Pulsar JWT 排障，沉淀可复用 SOP，支撑重装一次验收。

## 追问准备

- Sandbox 怎么证伪？→ 新 Pod 正常 vs 坏 Pod 仅 lo  
- 为何不用 curl 验 Harbor？→ 匿名 manifest 401，pull 才是节点路径  
- 现场客户只给私钥？→ 公钥应已在节点；`verify-spray-ssh`；勿 lab-setup  
