package tee.notifier;

import com.amazonaws.services.s3.event.S3EventNotification;

public class Application {

    public String handleRequest(S3EventNotification request) {
        return "OK";
    }

}
