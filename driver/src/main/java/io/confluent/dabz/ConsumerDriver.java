package io.confluent.dabz;

import com.fasterxml.jackson.databind.deser.std.NumberDeserializers;
import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.apache.kafka.common.serialization.BytesDeserializer;
import org.apache.log4j.Logger;

import java.io.FileReader;
import java.io.IOException;
import java.util.Arrays;
import java.util.Properties;
import java.util.UUID;

public class ConsumerDriver extends Driver {
    static Logger log = Logger.getLogger(ProducerDriver.class.getName());
    private String configFile;
    private String topic;
    private int expectedNumberOfThreads;

    public ConsumerDriver(String configFile, String topic, int expectedNumberOfThreads) {
        this.configFile = configFile;
        this.topic = topic;
        this.expectedNumberOfThreads = expectedNumberOfThreads;
    }

    @Override
    public void run() {
        Properties properties = new Properties();
        try {
            properties.load(new FileReader(configFile));
            properties.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, BytesDeserializer.class);
            properties.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, BytesDeserializer.class);
            properties.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
            properties.put(ConsumerConfig.GROUP_ID_CONFIG, "cow-driver-" + UUID.randomUUID().toString());
        } catch (IOException e) {
            log.error("can not read properties file", e);
        }

        for (int numThread = 0; numThread < expectedNumberOfThreads; numThread++) {
            Thread thread = new Thread(() -> {
                KafkaConsumer kafkaConsumer= new KafkaConsumer(properties);
                kafkaConsumer.subscribe(Arrays.asList(topic));

                while (this.getRunning()) {
                    ConsumerRecords<Integer, Byte[]> consumerRecords = kafkaConsumer.poll(1000);
                    // If we reach the end of topic, seek to beginning
                    if (consumerRecords.count() <= 0) {
                        kafkaConsumer.seekToBeginning(consumerRecords.partitions());
                        ConsumerStatistics.getShared().getTotalTimePartionHasBeenReset().addAndGet(1);
                        continue;
                    }

                    ConsumerStatistics.getShared().getTotalNumberOfMessagesConsumed().addAndGet(consumerRecords.count());

                    for (ConsumerRecord consumerRecord: consumerRecords) {
                        ConsumerStatistics.getShared().getTotalSizeOfMessagesConsumed().addAndGet(consumerRecord.serializedKeySize() + consumerRecord.serializedValueSize());
                    }
                }
                kafkaConsumer.close();
            });

            thread.start();
        }
    }
}
