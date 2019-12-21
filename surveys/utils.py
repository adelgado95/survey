from datetime import datetime
import redis
import json
from django.conf import settings
from . import celery_native_task_pattern, custom_celery_task_mask
from importlib import import_module

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
    str_args = '['+','.join(map(str, arguments)) + ']'
    str_kwargs = json.dumps(kwarguments)
    task_dict['args'] = str_args
    task_dict['kwargs'] = str_kwargs
    print(task_dict)
    return task_dict

def get_task_data_and_counter_state_dict():
    from .models import MetaDataTask
    r_con = get_redis()
    obj = list()
    status_counter = {'SUCCESS':0,'PENDING':0,'FAILURE':0,'RETRY':0, 'TOTAL': 0}
    for key in r_con.scan_iter(celery_native_task_pattern):
        data_task_object = MetaDataTask
        celery_data_task = json.loads(r_con.get(key))
        status_counter[celery_data_task['status']] = status_counter[celery_data_task['status']] + 1
        status_counter['TOTAL'] = status_counter['TOTAL'] + 1
        if r_con.exists(custom_celery_task_mask.format(celery_data_task['task_id'])):
            custom_data_task = json.loads(r_con.get(custom_celery_task_mask.format(celery_data_task['task_id'])))
            #print(custom_data_task)us
            # print(r_con.get(key))
            data_task_object.task_id = str(celery_data_task['task_id'])
            # logger.warning(r_con.get(key))
            data_task_object.celery_state = celery_data_task['status']
            data_task_object.task_name = custom_data_task['task_name']
            data_task_object.arguments = custom_data_task['args']
            data_task_object.kwarguments = custom_data_task['kwargs']
            data_task_object.state_datetime = datetime.strptime(custom_data_task['state_datetime'], "%Y-%m-%d %H:%M:%S")
            obj.append((data_task_object.__dict__).copy())
        else:
            data_task_object.task_id = ''
            # logger.warning(r_con.get(key))
            data_task_object.celery_state = ''
            data_task_object.task_name = ''
            data_task_object.arguments = ''
            data_task_object.kwarguments = ''
            data_task_object.state_datetime = datetime.strptime(str(celery_data_task['date_done']).replace('T',' '), "%Y-%m-%d %H:%M:%S.%f")
    return obj, status_counter

def fullname(o):
  module = o.__class__.__module__
  if module is None or module == str.__class__.__module__:
    return o.__class__.__name__
  else:
    return module + '.' + o.__class__.__name__

def dynamic_import(class_name):
    mods, klass = class_name.rsplit('.',1)
    module_object = import_module(mods)
    target_class = getattr(module_object, klass)
    return target_class
