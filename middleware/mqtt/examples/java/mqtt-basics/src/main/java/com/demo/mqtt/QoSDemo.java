package com.demo.mqtt;

import org.eclipse.paho.client.mqttv3.*;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;

/** 对比 QoS0 与 QoS1 发布（Broker 需运行） */
public class QoSDemo {
    public static void main(String[] args) throws Exception {
        String broker = System.getenv().getOrDefault("MQTT_BROKER", "tcp://localhost:1883");
        String topic = "dev/test/qos-demo";
        for (int qos : new int[] {0, 1}) {
            MqttClient c = new MqttClient(broker, "qos-demo-" + qos + "-" + System.nanoTime(), new MemoryPersistence());
            c.connect();
            MqttMessage m = new MqttMessage(("qos=" + qos).getBytes());
            m.setQos(qos);
            c.publish(topic, m);
            System.out.println("Published qos=" + qos);
            c.disconnect();
            c.close();
        }
    }
}
