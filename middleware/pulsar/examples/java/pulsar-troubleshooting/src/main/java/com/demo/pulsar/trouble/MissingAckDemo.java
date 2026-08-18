package com.demo.pulsar.trouble;

import org.apache.pulsar.client.api.*;

/**
 * 演示：异步发送不处理 exceptionally，失败时静默无感知。
 * 排查：pulsar-admin topics stats persistent://dev/test/missing-ack-demo
 */
public class MissingAckDemo {
    public static void main(String[] args) throws Exception {
        String url = System.getenv().getOrDefault("PULSAR_URL", "pulsar://localhost:6650");
        String topic = "persistent://dev/test/missing-ack-demo";
        try (PulsarClient client = PulsarClient.builder().serviceUrl(url).build();
             Producer<String> producer = client.newProducer(Schema.STRING).topic(topic).create()) {
            // BAD: 无 exceptionally
            producer.newMessage().value("test").sendAsync();
            System.out.println("Sent (async, no callback) - check stats for msgIn");
            Thread.sleep(1000);
        }
    }
}
