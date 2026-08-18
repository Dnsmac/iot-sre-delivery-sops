package com.demo.pulsar;

import org.apache.pulsar.client.api.*;

import java.util.concurrent.TimeUnit;

public class ProducerDemo {
    public static void main(String[] args) throws Exception {
        String url = System.getenv().getOrDefault("PULSAR_URL", "pulsar://localhost:6650");
        String topic = "persistent://dev/test/producer-demo";
        try (PulsarClient client = PulsarClient.builder().serviceUrl(url).build();
             Producer<String> producer = client.newProducer(Schema.STRING)
                     .topic(topic)
                     .enableBatching(true)
                     .batchingMaxPublishDelay(10, TimeUnit.MILLISECONDS)
                     .compressionType(CompressionType.LZ4)
                     .blockIfQueueFull(true)
                     .create()) {
            // 同步发送
            producer.send("sync-message");
            // 异步发送（必须处理异常）
            producer.newMessage()
                    .key("device-001")
                    .value("async-message")
                    .property("source", "ProducerDemo")
                    .sendAsync()
                    .thenAccept(id -> System.out.println("Async sent: " + id))
                    .exceptionally(ex -> {
                        System.err.println("Send failed: " + ex.getMessage());
                        return null;
                    });
            producer.flush();
            Thread.sleep(500);
        }
    }
}
