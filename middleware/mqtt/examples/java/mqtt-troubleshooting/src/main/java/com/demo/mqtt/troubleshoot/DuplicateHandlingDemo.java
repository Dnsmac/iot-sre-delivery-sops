package com.demo.mqtt.troubleshoot;

import org.eclipse.paho.client.mqttv3.*;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;

import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/**
 * B9 场景2：QoS1 重复投递时业务幂等（messageId 去重）。
 */
public class DuplicateHandlingDemo {
    private final Set<String> seen = ConcurrentHashMap.newKeySet();

    public static void main(String[] args) throws Exception {
        String broker = System.getenv().getOrDefault("MQTT_BROKER", "tcp://localhost:1883");
        String topic = "dev/dedup/demo";
        DuplicateHandlingDemo handler = new DuplicateHandlingDemo();

        MqttClient sub = new MqttClient(broker, "dedup-sub-" + System.nanoTime(), new MemoryPersistence());
        sub.connect(new MqttConnectOptions() {{ setCleanSession(true); }});
        sub.subscribe(topic, 1);
        sub.setCallback(new MqttCallback() {
            public void connectionLost(Throwable cause) {}
            public void messageArrived(String t, MqttMessage m) throws Exception {
                String payload = new String(m.getPayload());
                String msgId = payload.contains("id=") ? payload : payload;
                if (!handler.seen.add(msgId)) {
                    System.out.println("DUPLICATE skipped: " + msgId);
                    return;
                }
                System.out.println("PROCESS ok: " + msgId);
            }
            public void deliveryComplete(IMqttDeliveryToken token) {}
        });

        MqttClient pub = new MqttClient(broker, "dedup-pub-" + System.nanoTime(), new MemoryPersistence());
        pub.connect(new MqttConnectOptions() {{ setCleanSession(true); }});
        String body = "id=evt-1001";
        MqttMessage msg = new MqttMessage(body.getBytes());
        msg.setQos(1);
        pub.publish(topic, msg);
        pub.publish(topic, msg);
        System.out.println("Published same payload twice (QoS1). Expect one PROCESS, one DUPLICATE skipped.");
        Thread.sleep(2000);
        pub.disconnect();
        pub.close();
        sub.disconnect();
        sub.close();
    }
}
