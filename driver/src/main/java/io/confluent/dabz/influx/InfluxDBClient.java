package io.confluent.dabz.influx;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.util.Date;

public class InfluxDBClient {
    private static InfluxDBClient shared = new InfluxDBClient();
    private String outputPath;
    private String testName;

    private final String DBNAME = "telegraf";
    private final String ANNOTATIONSERIESNAME = "annotation";
    private final String POINTSERIESNAME = "drivers";

    public static InfluxDBClient getShared() {
        return shared;
    }

    private InfluxDBClient() {
    }

    public void configure(String outputPath, String testName) {
        this.outputPath = outputPath;
        this.testName = testName;
    }

    public Boolean isOnline() {
        return this.outputPath != null;
    }

    public synchronized void writeAnnotation(String value) throws IOException {
        // Format MEASUREMENT,TAGS1=VAL1,... FIELD1=VAL1,... TIME
        String annotation = String.format("%s,test=%s text=\"%s (%s)\",test=\"%s\" %d000000\n", ANNOTATIONSERIESNAME, this.testName, value, this.testName, this.testName, new Date().getTime());
        Files.write(Paths.get(this.outputPath), annotation.getBytes(), StandardOpenOption.APPEND, StandardOpenOption.CREATE);
    }

    public synchronized void writePoint(long numberOfMessage, long sizeOfMessage, long latency) throws IOException {
        // Format MEASUREMENT,TAGS1=VAL1,... FIELD1=VAL1,... TIME
        String annotation = String.format("%s,test=%s numberOfMessage=%d,sizeOfMessage=%d,latency=%d %d000000\n",
                POINTSERIESNAME, this.testName, numberOfMessage, sizeOfMessage, latency, new Date().getTime());
        Files.write(Paths.get(this.outputPath), annotation.getBytes(), StandardOpenOption.APPEND, StandardOpenOption.CREATE);
    }

}
