package com.demo.pulsar.trouble;

import org.apache.pulsar.client.api.*;

import java.util.concurrent.TimeUnit;

/**
 * 演示：ackTimeout 过短导致重复投递。
 */
public class DuplicateConsumeDemo {
    public static void main(String[] args) throws Exception {
        String url = System.getenv().getOrDefault("PULSAR_URL", "pulsar://localhost:6650");
        String topic = "persistent://dev/test/duplicate-demo";
        try (PulsarClient client = PulsarClient.builder().serviceUrl(url).build();
             Consumer<String> consumer = client.newConsumer(Schema.STRING)
                     .topic(topic)
                     .subscriptionName("dup-sub")
                     .ackTimeout(2, TimeUnit.SECONDS)
                     .subscribe()) {
            Message<String> msg = consumer.receive(5, TimeUnit.SECONDS);
            if (msg != null) {
                System.out.println("Processing slowly (5s)... id=" + msg.getMessageId());
                Thread.sleep(5000);
                consumer.acknowledge(msg);
            }
        }
    }
}
