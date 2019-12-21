import logging
import json
from celery import shared_task, Task, task
from django.db.models import F
from django.conf import settings
from . import custom_celery_task_mask
from .utils import get_redis, get_dict_from_task_data, fullname
from datetime import datetime

logger = logging.getLogger(__name__)

class FallbackTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        print('{0!r} failed: {1!r}'.format(task_id, exc))
        print("self name")
        print(self)
        print("exc")
        print(exc)
        print("einfo")
        print(einfo)
        task_key = custom_celery_task_mask.format(task_id)
        task_dict = get_dict_from_task_data(task_id, fullname(self), args,
                                kwargs, 'FAILED', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        r_con = get_redis()
        r_con.set(task_key, json.dumps(task_dict))
        # r_con = get_redis()
        # task_dict = {'class':self.__dict__['__qualname__']}
        # # r_con.hset(task_key,'class',self.__dict__['__qualname__'])
        # if len(args) > 0:
        #     str_args = ','.join(map(str, args))
        #     # print(str_args)
        #     task_dict['args'] ='['+str_args+']'
        # else:
        #     r_con.hset(task_key,'args','')
        #     task_dict['args']=''
        # if len(kwargs) > 0:
        #     # r_con.hset(task_key,'kwargs',json.dumps(kwargs))
        #     task_dict['kwargs'] ='['+json.dumps(kwars)+']'
        # else:
        #     # r_con.hset(task_key,'kwargs','')
        #     task_dict['kwargs'] ='['+str_args+']'
        # # r_con.hset(task_key,'state_datetime',datetime.now().strftime("%m-%d-%Y %H:%M:%S"))
        # task_dict['state_datetime'] = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
        # # r_con.hset(task_key,'state','FAILED')
        # task_dict['state'] = 'FAILED'
        # r_con.set(task_key,json.dumps(task_dict))

    def on_success(self, retval, task_id, args, kwargs):
        print('{0!r} success:'.format(task_id))
        print(self.__dict__)
        print(self.__dict__['__trace__'].__dict__)
        print("Priting retval")
        print(retval)
        task_key = custom_celery_task_mask.format(task_id)
        task_dict = get_dict_from_task_data(task_id, fullname(self), args,
                                kwargs, 'SUCCESS', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        r_con = get_redis()
        r_con.set(task_key, json.dumps(task_dict))
        # task_key = custom_celery_task_mask.format(task_id)
        # print (task_key)
        # r_con = get_redis()
        # r_con.hset(task_key,'class',self.__dict__['__qualname__'])
        # if len(args) > 0:
        #     str_args = ','.join(map(str, args))
        #     print(str_args)
        #     r_con.hset(task_key,'args','['+str_args+']')
        # else:
        #     r_con.hset(task_key,'args','')
        # if len(kwargs) > 0:
        #     r_con.hset(task_key,'kwargs',json.dumps(kwargs))
        # else:
        #     r_con.hset(task_key,'kwargs','')

        # r_con.hset(task_key,'state_datetime',datetime.now().strftime("%m-%d-%Y %H:%M:%S"))
        # r_con.hset(task_key,'state','SUCCESS')


@shared_task
def increment_vote(choice_id):
    from .models import Choice
    logger.info("increment {0}".format(choice_id))
    Choice.active_objects.filter(pk=choice_id).update(votes=F('votes')+1)
    logger.info("done")


@shared_task
def increment_counter(choice_id):
    from .utils import get_redis
    logger.info("increment {0}".format(choice_id))
    rconn = get_redis()
    rconn.incr("Choice%s" % choice_id)
    logger.info("done")

@task(base=FallbackTask)
def fill_report_test():
    import time, json
    from .models import Survey
    from django.core.serializers import serialize
    time.sleep(20)
    surveys = Survey.objects.all()
    data = json.loads(serialize('json', surveys))
    return data

@task(base=FallbackTask)
def fill_report_test_with_params(survey_id, *args, **kwargs):
    import time, json
    from .models import Survey
    from django.core.serializers import serialize
    time.sleep(5)
    surveys = Survey.objects.all()[:10]
    data = json.loads(serialize('json', surveys))
    return data