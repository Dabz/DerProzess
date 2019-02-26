package io.confluent.dabz.influx;

import org.influxdb.dto.Point;

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
    private final String SERIESNAME = "annotation";

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

    public void writeAnnotation(String value) throws IOException {
        // Format MEASUREMENT,TAGS1=VAL1,... FIELD1=VAL1,... TIME
        String annotation = String.format("%s,test=%s text=\"%s (%s)\",test=\"%s\" %d000000\n", SERIESNAME, this.testName, value, this.testName, this.testName, new Date().getTime());
        Files.write(Paths.get(this.outputPath), annotation.getBytes(), StandardOpenOption.APPEND, StandardOpenOption.CREATE);
    }

}
