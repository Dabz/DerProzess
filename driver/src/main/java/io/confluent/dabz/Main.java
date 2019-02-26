package io.confluent.dabz;

import io.confluent.dabz.driver.ConsumerDriver;
import io.confluent.dabz.driver.Driver;
import io.confluent.dabz.driver.ProducerDriver;
import io.confluent.dabz.influx.InfluxDBClient;
import io.confluent.dabz.metrics.ConsumerMetrics;
import io.confluent.dabz.metrics.Metrics;
import io.confluent.dabz.metrics.ProducerDriverMetrics;
import org.apache.commons.cli.*;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.log4j.Logger;

import java.io.IOException;

public class Main {
    static Logger log = Logger.getLogger(Main.class.getName());
    Thread metricThread;
    Metrics metrics;

    public static void main(String[] args) throws IOException {
        Main main = new Main();
        main.run(args);
    }

    public void run(String args[]) throws IOException {
        CommandLine cmdLine = null;
        Driver driver = null;
        Integer testDuration = 10;
        InfluxDBClient influxDBClient = InfluxDBClient.getShared();

        try {
            cmdLine = parseOptions(args);
        } catch (ParseException e) {
            HelpFormatter formatter = new HelpFormatter();
            formatter.printHelp( "java -jar driver.jar", getOptions());
            log.error("Unexpected error while parsing options", e);
            System.exit(1);
        }

        if (cmdLine.hasOption("h")) {
            HelpFormatter formatter = new HelpFormatter();
            formatter.printHelp( "java -jar driver.jar", getOptions());
            System.exit(0);
        }

        if (cmdLine.hasOption("influx")) {
            if (! cmdLine.hasOption("test")) {
                log.error("when --influx is specified, --test option is required");
                System.exit(1);
            }
            influxDBClient.configure(cmdLine.getOptionValue("influx"), cmdLine.getOptionValue("test"));
        }

        if (cmdLine.hasOption("producer")) {
            driver = startProducerTest(cmdLine);
        }
        else if (cmdLine.hasOption("consumer")) {
            driver = startConsumerTest(cmdLine);
        } else if (cmdLine.hasOption("latency")) {
            // TODO
        } else {
            HelpFormatter formatter = new HelpFormatter();
            formatter.printHelp( "java -jar driver.jar", getOptions());
            System.exit(0);
        }

        if (cmdLine.hasOption("d")) {
            testDuration = Integer.valueOf(cmdLine.getOptionValue("duration"));
        }

        if (influxDBClient.isOnline()) {
            influxDBClient.writeAnnotation("start testing");
        }

        driver.run();

        try {
            Thread.sleep(testDuration * 1000);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }

        driver.setRunning(false);
        metrics.setRunning(false);

        if (influxDBClient.isOnline()) {
            influxDBClient.writeAnnotation("stop testing");
        }
    }

    private Driver startProducerTest(CommandLine cmdLine) {
        String topic = "__driver";
        String configFile = null;
        int payloadSize = 4092;
        int numThread = Runtime.getRuntime().availableProcessors();
        short partitions = 50;
        short replication = -1;

        /*
         Required arguments
         */
        if (! cmdLine.hasOption("c")) {
            System.err.println("-c/--config option is required");
            System.err.println("Example of minimalistic properties file:");
            System.err.println(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG + "=localhost:9092");
            System.exit(1);
        }
        configFile = cmdLine.getOptionValue("c");

        /*
         Optional arguments
         */
        if (cmdLine.hasOption("n")) {
            numThread = Integer.parseInt(cmdLine.getOptionValue("n"));
        }
        if (cmdLine.hasOption("t")) {
            topic = cmdLine.getOptionValue("t");
        }
        if (cmdLine.hasOption("s")) {
            payloadSize = Integer.parseInt(cmdLine.getOptionValue("s"));
        }
        if (cmdLine.hasOption("rf")) {
            replication = Short.parseShort(cmdLine.getOptionValue("rf"));
        }
        if (cmdLine.hasOption("pt")) {
            partitions = Short.parseShort(cmdLine.getOptionValue("pt"));
        }

        ProducerDriver producerDriver = new ProducerDriver(configFile, topic, numThread, payloadSize, replication, partitions);
        metrics = ProducerDriverMetrics.getShared();
        metrics.setMinimalist(cmdLine.hasOption("m"));
        metricThread = new Thread(metrics);
        metricThread.setDaemon(true);
        metricThread.start();
        return producerDriver;
    }


    private Driver startConsumerTest(CommandLine cmdLine) {
        String topic = "__driver";
        String configFile;
        int payloadSize = 4092;
        int numThread = Runtime.getRuntime().availableProcessors();

        /*
         Required arguments
         */
        if (! cmdLine.hasOption("c")) {
            System.err.println("-c/--config option is required");
            System.err.println("Example of minimalistic properties file:");
            System.err.println(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG + "=localhost:9092");
            System.exit(1);
        }
        configFile = cmdLine.getOptionValue("c");

        /*
         Optional arguments
         */
        if (cmdLine.hasOption("n")) {
            numThread = Integer.parseInt(cmdLine.getOptionValue("n"));
        }
        if (cmdLine.hasOption("t")) {
            topic = cmdLine.getOptionValue("t");
        }

        ConsumerDriver consumerDriver = new ConsumerDriver(configFile, topic, numThread);
        metrics = ConsumerMetrics.getShared();
        metrics.setMinimalist(cmdLine.hasOption("m"));
        metricThread = new Thread(metrics);
        metricThread.setDaemon(true);
        metricThread.start();
        return consumerDriver;
    }

    private static Options getOptions() {
        Options options = new Options();
        options.addOption("c", "config", true, "kafka properties to load for KafkaProducer and KafkaConsumer");
        options.addOption("producer", "producer", false, "test producer performances");
        options.addOption("consumer", "consumer", false, "test consumer performances");
        options.addOption("t", "topic", true, "topic to consumer/produce from/to (default __driver)");
        options.addOption("h", "help", true, "print this help");
        options.addOption("n", "thread", true, "number of thread to use for consuming/producing (default number of core)");
        options.addOption("s", "payload-size", true, "size of the payload to produce (default 4092)");
        options.addOption("d", "duration", true, "maximum duration in seconds of the test (default 20s)");
        options.addOption("m", "minimalist", false, "machine friendly output");
        options.addOption("rf", "replication", true, "replication factor");
        options.addOption("pt", "partition", true, "number of partitions");
        options.addOption("h", "help", false, "display help");
        options.addOption("influx", "influx", true, "InfluxDB output file");
        options.addOption("test", "test", true, "Test name");

        return options;
    }

    private static CommandLine parseOptions(String[] args) throws ParseException {
        CommandLineParser parser = new DefaultParser();
        return parser.parse(getOptions(), args);
    }
}
