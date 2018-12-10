package io.confluent.dabz;

import org.apache.kafka.clients.admin.AdminClient;
import org.apache.kafka.clients.admin.DescribeTopicsResult;
import org.apache.kafka.clients.admin.KafkaAdminClient;
import org.apache.kafka.clients.admin.NewTopic;

import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.util.Arrays;
import java.util.Properties;
import java.util.concurrent.ExecutionException;

public abstract class Driver implements Runnable {
    private Boolean running = true;

    public void setRunning(boolean running) {
        this.running = running;
    }

    public Boolean getRunning() {
        return running;
    }

    public abstract  void run();

    public void createTopic(String configFile, String topic, short replicationFactor, short partitions) throws IOException, ExecutionException, InterruptedException {
        Properties properties = new Properties();
        properties.load(new FileReader(configFile));

        AdminClient adminClient = KafkaAdminClient.create(properties);
        DescribeTopicsResult describeTopicsResult = adminClient.describeTopics(Arrays.asList(topic));
        if (describeTopicsResult.values().size() > 0) {
            return;
        }
        NewTopic newTopic = new NewTopic(topic, partitions, replicationFactor);
        adminClient.createTopics(Arrays.asList(newTopic)).all().get();
    }
}
