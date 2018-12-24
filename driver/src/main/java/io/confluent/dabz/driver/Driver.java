package io.confluent.dabz.driver;

import org.apache.kafka.clients.admin.*;
import org.apache.kafka.common.config.TopicConfig;
import org.apache.kafka.common.errors.TopicExistsException;
import org.apache.kafka.common.errors.UnknownTopicOrPartitionException;

import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
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
        try {
            DescribeTopicsResult describeTopicsResult = adminClient.describeTopics(Arrays.asList(topic));
            describeTopicsResult.all().get();
        } catch (ExecutionException e) {
            if (e.getCause() instanceof UnknownTopicOrPartitionException) {
                if (replicationFactor == -1) {
                    DescribeClusterResult describeClusterResult = adminClient.describeCluster();
                    replicationFactor = (short) describeClusterResult.nodes().get().size();
                }
                NewTopic newTopic = new NewTopic(topic, partitions, replicationFactor);
                newTopic.configs(new HashMap<String, String>()
                {{
                    put(TopicConfig.MESSAGE_TIMESTAMP_TYPE_CONFIG, "CreateTime");
                }});
                try {
                    adminClient.createTopics(Arrays.asList(newTopic)).all().get();
                } catch (TopicExistsException ex) {
                    // Ignoring safely this exception as another process might have
                    // created the topic
                } catch (ExecutionException ex) {
                    if (! (ex.getCause() instanceof TopicExistsException)) {
                        throw ex;
                    }
                }
            } else {
                throw e;
            }
        }
    }
}
