package io.confluent.dabz.metrics;

public abstract class Metrics implements Runnable {
    private Boolean shouldStart = false;
    private Boolean running = true;
    private Boolean minimalist = false;

    public Boolean getShouldStart() {
        return shouldStart;
    }

    public void setShouldStart(Boolean shouldStart) {
        this.shouldStart = shouldStart;
    }

    public void setRunning(boolean running) {
        this.running = running;
    }

    public Boolean getRunning() {
        return running;
    }

    public Boolean getMinimalist() {
        return minimalist;
    }

    public void setMinimalist(Boolean minimalist) {
        this.minimalist = minimalist;
    }

    public void waitUntilReady() {
        while (! shouldStart) {
            try {
                Thread.sleep(50);
            } catch (InterruptedException e) {
            }
        }
    }
}
