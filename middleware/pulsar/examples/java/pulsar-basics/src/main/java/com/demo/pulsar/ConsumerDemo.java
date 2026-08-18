package com.demo.pulsar;

import org.apache.pulsar.client.api.*;

import java.util.concurrent.TimeUnit;

public class ConsumerDemo {
    public static void main(String[] args) throws Exception {
        String url = System.getenv().getOrDefault("PULSAR_URL", "pulsar://localhost:6650");
        String topic = "persistent://dev/test/producer-demo";
        try (PulsarClient client = PulsarClient.builder().serviceUrl(url).build();
             Consumer<String> consumer = client.newConsumer(Schema.STRING)
                     .topic(topic)
                     .subscriptionName("consumer-demo-sub")
                     .subscriptionType(SubscriptionType.Shared)
                     .receiverQueueSize(100)
                     .ackTimeout(30, TimeUnit.SECONDS)
                     .deadLetterPolicy(DeadLetterPolicy.builder()
                             .maxRedeliverCount(3)
                             .deadLetterTopic("persistent://dev/test/producer-demo-dlq")
                             .build())
                     .messageListener((c, msg) -> {
                         try {
                             System.out.println("Got: " + msg.getValue() + " key=" + msg.getKey());
                             c.acknowledge(msg);
                         } catch (Exception e) {
                             c.negativeAcknowledge(msg);
                         }
                     })
                     .subscribe()) {
            System.out.println("Listening... Ctrl+C to stop");
            Thread.sleep(5000);
        }
    }
}
