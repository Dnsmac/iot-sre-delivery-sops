package com.demo.mqtt;

import org.eclipse.paho.client.mqttv3.*;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;

public class HelloMqtt {
    public static void main(String[] args) throws Exception {
        String broker = System.getenv().getOrDefault("MQTT_BROKER", "tcp://localhost:1883");
        String topic = "dev/test/hello";
        String clientId = "hello-pub-" + System.currentTimeMillis();
        MqttClient pub = new MqttClient(broker, clientId, new MemoryPersistence());
        MqttConnectOptions opts = new MqttConnectOptions();
        opts.setCleanSession(true);
        opts.setAutomaticReconnect(true);
        pub.connect(opts);
        MqttMessage msg = new MqttMessage("hello mqtt".getBytes());
        msg.setQos(1);
        pub.publish(topic, msg);
        System.out.println("Published to " + topic);
        pub.disconnect();
        pub.close();
        String subId = "hello-sub-" + System.currentTimeMillis();
        MqttClient sub = new MqttClient(broker, subId, new MemoryPersistence());
        sub.connect(new MqttConnectOptions() {{ setCleanSession(true); }});
        sub.subscribe(topic, 1);
        sub.setCallback(new MqttCallback() {
            public void connectionLost(Throwable cause) {}
            public void messageArrived(String t, MqttMessage m) {
                System.out.println("Received: " + new String(m.getPayload()));
            }
            public void deliveryComplete(IMqttDeliveryToken token) {}
        });
        Thread.sleep(2000);
        sub.disconnect();
        sub.close();
    }
}
