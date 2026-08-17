# SOP · Spray SSH 私钥（实验室 vs 现场）

| 字段 | 内容 |
|------|------|
| 场景 | Kuboard-Spray 装簇 SSH |
| 现象 | lab-setup 报 Permission denied；或现场不知如何用客户私钥 |

## 1. 两种模式

| 环境 | 做法 |
|------|------|
| **实验室** | `lab-setup-spray-ssh-key.sh` 生成密钥并 `ssh-copy-id` 到节点 |
| **现场** | 客户只给 **一把私钥**；公钥应已在各节点 `authorized_keys` |

## 2. 实验室坑

`ssh-copy-id` 成功后验证未带 `-i`，误报失败。  
修复：验证必须 `-i KEY -o IdentitiesOnly=yes`。

```bash
ssh -i /opt/offline/keys/kuboard_spray -o IdentitiesOnly=yes \
  -o BatchMode=yes root@192.168.27.105 'echo OK'
bash /opt/offline/scripts/field/verify-spray-ssh.sh
```

## 3. 现场（客户只给私钥）

```bash
mkdir -p /opt/offline/keys
cp /path/from-customer/key.pem /opt/offline/keys/kuboard_spray
chmod 600 /opt/offline/keys/kuboard_spray
# 无 .pub 时可推导：
ssh-keygen -y -f /opt/offline/keys/kuboard_spray > /opt/offline/keys/kuboard_spray.pub

export ENV_FILE=/opt/offline/env.conf
bash /opt/offline/scripts/field/verify-spray-ssh.sh
```

Spray UI：添加私钥 → 粘贴内容 → 装簇选该密钥。

**禁止**现场跑 lab-setup 覆盖客户钥匙。

## 4. 配好私钥后还会要密码吗？

| 环节 | 配好后 |
|------|--------|
| Kuboard-Spray 装簇 | 否（UI 选用该密钥） |
| `install-all-middleware` / NFS（v1.0.15+） | 否（`ssh_node` 自动 `-i`） |
| 旧脚本裸 `ssh`、或 105 无私钥文件 | **仍会要密码** |

前提：客户公钥已在 105～108 的 `authorized_keys`，且 `verify-spray-ssh.sh` 全 OK。

## 5. 控制面脚本也会 SSH（不要密码）

`install-all-middleware.sh` / NFS 检查会从 **105** SSH 到 106～108。  
须与 Spray 使用**同一把客户私钥**：

```bash
# 105 上也要有私钥（可从 109 拷）
mkdir -p /opt/offline/keys
# scp root@109:/opt/offline/keys/kuboard_spray /opt/offline/keys/
chmod 600 /opt/offline/keys/kuboard_spray
# env.conf
SPRAY_SSH_KEY_PATH="/opt/offline/keys/kuboard_spray"
```

v1.0.15+ 的 `ssh_node` 会自动 `-i` 该私钥；**配好后不应再要密码**。  
若仍要密码：公钥未进节点，或 105 上没有私钥文件。

## 6. 防复发

- 现场禁止依赖 root 密码跑中间件脚本  
- 装簇前：`verify-spray-ssh.sh` 四台全 OK  
- 105 与 109 私钥路径一致
