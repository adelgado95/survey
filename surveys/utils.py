import datetime
import redis
import json
from django.conf import settings


SURVEY_DAYS = 15
survey_end_date = lambda: datetime.date.today() + datetime.timedelta(days=SURVEY_DAYS)

def get_last_survey():
    from surveys.models import Survey
    survey = Survey.objects.all().order_by("-id")[0]
    return survey


def get_redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB):
    return redis.Redis(
        host=host,
        port=port,
        db=db,
    )

def get_dict_from_task_data(task_id,task_name,arguments,kwarguments,state,state_datetime):
    task_dict = {'task_id':task_id, 'task_name':task_name,'state': state, 'state_datetime': state_datetime}
    str_args = ','.join(map(str, arguments))
    str_kwargs = json.dumps(kwarguments)
    task_dict['args'] = str_args
    task_dict['kwargs'] = str_kwargs
    print(task_dict)
    return task_dict


