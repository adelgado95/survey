import logging

logger = logging.getLogger(__name__)

class SurveyRouter(object):
    def route_for_task(self, task, args=None, kwargs=None):
        logger.warning(task)
        if task == "surveys.tasks.increment_counter" or task == "surveys.tasks.fill_report_test":
            return {
                "queue": "stats"
            }
        elif task.startswith("surveys.tasks."):
            return {"queue": "surveys"}
