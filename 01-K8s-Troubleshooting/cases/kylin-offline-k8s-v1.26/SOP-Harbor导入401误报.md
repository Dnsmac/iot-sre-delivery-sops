# SOP · Harbor 导入 verify HTTP 401

| 字段 | 内容 |
|------|------|
| 场景 | 110 离线导入业务镜像后验收 |
| 现象 | `docker push` 成功，脚本报 `manifest HTTP 401` |
| 影响 | 误判导入失败，反复重推 |

## 1. 快速定界

```bash
H=192.168.27.110
# curl 常 401（不可作唯一依据）
curl -s -o /dev/null -w '%{http_code}\n' \
  -H 'Accept: application/vnd.docker.distribution.manifest.v2+json' \
  "http://${H}/v2/meta/kh-meta/common/sig-storage/nfs-subdir-external-provisioner/manifests/v4.0.2"

# 节点真实用法
docker logout "$H"
docker pull "${H}/meta/kh-meta/common/sig-storage/nfs-subdir-external-provisioner:v4.0.2"
```

## 2. 根因

部分 Harbor 对**匿名 curl** `/v2/.../manifests` 仍返回 401；业务侧是 **匿名 docker/crictl pull**。

## 3. 修复

- 以匿名 pull 成功为准 → 继续装簇  
- 脚本 v1.0.14+：`verify-harbor-images.sh` / `05-import` **只认 pull**  

```bash
bash /opt/offline/scripts/field/verify-harbor-images.sh
```

## 4. 防复发

- 文档写明：curl 401 ≠ 未入库  
- meta 项目保持 public（匿名可拉）
