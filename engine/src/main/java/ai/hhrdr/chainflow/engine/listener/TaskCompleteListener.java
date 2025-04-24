package ai.hhrdr.chainflow.engine.listener;

import org.camunda.bpm.engine.delegate.DelegateTask;
import org.camunda.bpm.engine.delegate.TaskListener;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

// Delegate for sending a user notification when verification is passed
@Component("TaskCompleteListener")
public class TaskCompleteListener implements TaskListener {

    private static final Logger logger = LoggerFactory.getLogger(UserNotificationListener.class);

    @Override
    public void notify(DelegateTask delegateTask) {
        logger.debug("Completing the task " + delegateTask.getId());
         delegateTask.complete();
    }
}
