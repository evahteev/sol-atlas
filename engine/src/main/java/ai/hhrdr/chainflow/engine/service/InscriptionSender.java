package ai.hhrdr.chainflow.engine.service;

import ai.hhrdr.chainflow.engine.ethereum.InscriptionDataService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.camunda.bpm.engine.impl.history.event.HistoryEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.DisposableBean;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

@Service
public class InscriptionSender implements DisposableBean {

    @Autowired
    private InscriptionDataService inscriptionDataService;

    @Value("${inscription.enabled}")
    private Boolean enabled;

    @Value("${inscription.max_threads}")
    private Integer max_threads;

    private ExecutorService executorService;

    private static final Logger LOG = LoggerFactory.getLogger(InscriptionSender.class);

    @PostConstruct
    public void init() {
        executorService = Executors.newFixedThreadPool(max_threads);
    }

    public void send(HistoryEvent event, String camundaEventType) {
        if (enabled) {
            executorService.submit(() -> {
                try {
                    String jsonData = new ObjectMapper().writeValueAsString(event);
                    inscriptionDataService.sendInscriptionData(jsonData);
                    LOG.debug("Sent asynchronously, eventType = " + camundaEventType + ", msg = " + event);
                } catch (Exception e) {
                    LOG.error("Error sending inscriptions data asynchronously", e);
                }
            });
        } else {
            LOG.info("Event skipped, inscriptions disabled, eventType = " + camundaEventType + ", msg = " + event);
        }
    }

    @Override
    public void destroy() throws Exception {
        if (executorService != null && !executorService.isShutdown()) {
            executorService.shutdown();
            try {
                if (!executorService.awaitTermination(800, TimeUnit.MILLISECONDS)) {
                    executorService.shutdownNow();
                }
            } catch (InterruptedException e) {
                executorService.shutdownNow();
            }
        }
    }
}
