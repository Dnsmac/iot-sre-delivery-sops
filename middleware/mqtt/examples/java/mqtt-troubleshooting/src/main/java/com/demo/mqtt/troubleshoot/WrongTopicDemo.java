package com.demo.mqtt.troubleshoot;

import org.eclipse.paho.client.mqttv3.*;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;

/** B9 场景1：发布与订阅 topic 不一致，演示「发了收不到」。 */
public class WrongTopicDemo {
    public static void main(String[] args) throws Exception {
        String broker = System.getenv().getOrDefault("MQTT_BROKER", "tcp://localhost:1883");
        String pubTopic = "dev/wrong/pub";
        String subTopic = "dev/wrong/sub";
        MqttClient sub = new MqttClient(broker, "wrong-sub-" + System.nanoTime(), new MemoryPersistence());
        sub.connect(new MqttConnectOptions() {{ setCleanSession(true); }});
        sub.subscribe(subTopic, 1);
        sub.setCallback(new MqttCallback() {
            public void connectionLost(Throwable cause) {}
            public void messageArrived(String t, MqttMessage m) {
                System.out.println("SUB received: " + t + " -> " + new String(m.getPayload()));
            }
            public void deliveryComplete(IMqttDeliveryToken token) {}
        });
        Thread.sleep(500);
        MqttClient pub = new MqttClient(broker, "wrong-pub-" + System.nanoTime(), new MemoryPersistence());
        pub.connect(new MqttConnectOptions() {{ setCleanSession(true); }});
        pub.publish(pubTopic, new MqttMessage("hello".getBytes()) {{ setQos(1); }});
        System.out.println("Published to " + pubTopic + ", subscribed " + subTopic + " (mismatch)");
        Thread.sleep(2000);
        pub.disconnect();
        pub.close();
        sub.disconnect();
        sub.close();
    }
}
