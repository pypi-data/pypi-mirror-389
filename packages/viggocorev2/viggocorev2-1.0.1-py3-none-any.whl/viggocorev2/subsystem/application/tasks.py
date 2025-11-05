from flask.globals import current_app

from viggocorev2.celery import celery, decide_on_run
from viggocorev2.common import exception
from typing import Optional


@decide_on_run
@celery.task(autoretry_for=(exception.NotFound,),
             default_retry_delay=5,
             retry_kwargs={'max_retries': 3})
def replicate_policies(application_id: Optional[str] = None) -> None:
    api = current_app.api_handler.api()
    application_manager = api.applications()
    return application_manager.replicate_policies(application_id=application_id)
