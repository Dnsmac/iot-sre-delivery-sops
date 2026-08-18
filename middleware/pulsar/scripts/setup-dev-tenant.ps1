docker exec pulsar-standalone bin/pulsar-admin tenants create dev 2>$null
docker exec pulsar-standalone bin/pulsar-admin namespaces create dev/test 2>$null
docker exec pulsar-standalone bin/pulsar-admin topics create persistent://dev/test/hello 2>$null
Write-Host "Ready: persistent://dev/test/hello"
