package com.demo.mqtt.troubleshoot;

import org.eclipse.paho.client.mqttv3.*;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;

/** B9 场景8：Retain 最后一条 + 空 payload retain 清除。 */
public class RetainDemo {
    public static void main(String[] args) throws Exception {
        String broker = System.getenv().getOrDefault("MQTT_BROKER", "tcp://localhost:1883");
        String topic = "dev/retain/demo";
        String mode = args.length > 0 ? args[0] : "read";

        if ("set".equalsIgnoreCase(mode)) {
            MqttClient pub = new MqttClient(broker, "retain-set-" + System.nanoTime(), new MemoryPersistence());
            pub.connect(new MqttConnectOptions() {{ setCleanSession(true); }});
            MqttMessage msg = new MqttMessage("last-known-value".getBytes());
            msg.setQos(1);
            msg.setRetained(true);
            pub.publish(topic, msg);
            System.out.println("Published retain=" + topic);
            pub.disconnect();
            pub.close();
            return;
        }
        if ("clear".equalsIgnoreCase(mode)) {
            MqttClient pub = new MqttClient(broker, "retain-clear-" + System.nanoTime(), new MemoryPersistence());
            pub.connect(new MqttConnectOptions() {{ setCleanSession(true); }});
            MqttMessage msg = new MqttMessage(new byte[0]);
            msg.setQos(1);
            msg.setRetained(true);
            pub.publish(topic, msg);
            System.out.println("Cleared retain on " + topic);
            pub.disconnect();
            pub.close();
            return;
        }
        MqttClient sub = new MqttClient(broker, "retain-read-" + System.nanoTime(), new MemoryPersistence());
        sub.connect(new MqttConnectOptions() {{ setCleanSession(true); }});
        sub.subscribe(topic, 1);
        sub.setCallback(new MqttCallback() {
            public void connectionLost(Throwable cause) {}
            public void messageArrived(String t, MqttMessage m) {
                System.out.println("Retain read: " + new String(m.getPayload()) + " retained=" + m.isRetained());
            }
            public void deliveryComplete(IMqttDeliveryToken token) {}
        });
        System.out.println("Subscribed (will get retained if any). Use: set | clear | read");
        Thread.sleep(3000);
        sub.disconnect();
        sub.close();
    }
}
