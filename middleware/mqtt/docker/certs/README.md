# 开发用 TLS 证书

**仅用于本地 Mosquitto 8883 实验**，勿用于生产。

在 `docker/certs` 目录执行（需已安装 `openssl`）：

```bash
openssl req -x509 -new -nodes -days 3650 -keyout ca.key -out ca.crt -subj "/CN=MQTT-Dev-CA"
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -subj "/CN=localhost"
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 3650
```

然后启动 Broker：

```powershell
cd docker
docker compose -f docker-compose-mosquitto.yml up -d
```

验证 TLS：

```bash
mosquitto_pub -h localhost -p 8883 --cafile docker/certs/ca.crt -t dev/tls/test -m hi -q 1
```

`*.key` 已加入 `.gitignore`，证书需在本地生成。
