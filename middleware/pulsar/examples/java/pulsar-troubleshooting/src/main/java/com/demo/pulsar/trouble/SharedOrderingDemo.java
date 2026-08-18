package com.demo.pulsar.trouble;

import org.apache.pulsar.client.api.*;

import java.util.concurrent.TimeUnit;

/**
 * 对比 Shared（可能乱序）与 Key_Shared（同 Key 有序）。
 */
public class SharedOrderingDemo {
    public static void main(String[] args) throws Exception {
        String url = System.getenv().getOrDefault("PULSAR_URL", "pulsar://localhost:6650");
        String topic = "persistent://dev/test/ordering-demo";
        SubscriptionType type = args.length > 0 && "key_shared".equals(args[0])
                ? SubscriptionType.Key_Shared : SubscriptionType.Shared;
        try (PulsarClient client = PulsarClient.builder().serviceUrl(url).build();
             Consumer<String> consumer = client.newConsumer(Schema.STRING)
                     .topic(topic)
                     .subscriptionName("order-sub-" + type.name())
                     .subscriptionType(type)
                     .subscribe()) {
            for (int i = 0; i < 5; i++) {
                Message<String> msg = consumer.receive(2, TimeUnit.SECONDS);
                if (msg == null) break;
                System.out.println(type + " key=" + msg.getKey() + " seq=" + msg.getValue());
                consumer.acknowledge(msg);
            }
        }
    }
}
