package com.demo.pulsar.spring;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.pulsar.annotation.PulsarListener;
import org.springframework.stereotype.Component;

@SpringBootApplication
public class PulsarSpringApp {
    public static void main(String[] args) {
        SpringApplication.run(PulsarSpringApp.class, args);
    }

    @Component
    static class Listener {
        @PulsarListener(subscriptionName = "spring-demo-sub", topics = "persistent://dev/test/spring-demo")
        void listen(String message) {
            System.out.println("Spring received: " + message);
        }
    }
}
