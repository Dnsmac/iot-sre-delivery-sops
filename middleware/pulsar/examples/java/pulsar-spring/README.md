# pulsar-spring

独立 Spring Boot 模块（使用 `spring-boot-starter-parent`），不在父 POM 聚合构建中。

```bash
cd pulsar-spring
mvn spring-boot:run -Dspring-boot.run.profiles=dev
```

需先启动 Standalone 并创建 Topic `persistent://dev/test/spring-demo`。
