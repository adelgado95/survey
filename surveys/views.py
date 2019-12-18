import json
import logging
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from .models import UserChoice, Question, Survey
from .tasks import increment_vote, increment_counter,fill_report_test
from . import celery_native_task_pattern, custom_celery_task_mask
from .utils import get_redis
from .models import MetaDataTask
from datetime import datetime


logger = logging.getLogger(__name__)


class RandomQuestionMixin(object):

    @property
    def current_session_key(self):
        if not self.request.session.session_key:
            self.request.session.save()
        session_key = self.request.session.session_key
        return session_key

    def get_random_question(self):
        return Question.objects.random_get(self.current_session_key)

    def get_current_progress(self):
        questions_count = Question.objects.filter(is_active=True).count()
        user_choices = UserChoice.objects.filter(question__is_active=True)
        user_choices_count = user_choices.filter(**self.session_param()).count()
        return (user_choices_count * 100 // questions_count) if questions_count > 0 else 100

    def session_param(self):
        if self.request.user.is_authenticated:
            query_params = {'user': self.request.user}
        else:
            query_params = {'session_key': self.current_session_key}
        return query_params


class IndexView(RandomQuestionMixin, TemplateView):
    template_name = 'surveys/index.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add extra context
        question = self.get_random_question()
        if question is not None:
            context.update({'questions': [question]})
        context['current_progress'] = self.get_current_progress()
        return context


class UserChoiceCreateView(RandomQuestionMixin, CreateView):
    model = UserChoice
    fields = ['question', 'choice']

    def get_success_url(self):

        return reverse('index')
    def form_invalid(self, form):
        responsedict = {
            'errors': form.errors,
            'status': False
        }
        return HttpResponse(json.dumps(responsedict))

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.user = self.request.user
        else:
            form.instance.session_key = self.current_session_key
        form.save()
        increment_vote.delay(form.instance.choice_id)
        increment_counter.delay(form.instance.choice_id)
        messages.success(self.request, 'Your choice was save successfully.')
        return super().form_valid(form)

def start_again(request):
    request.session.flush()
    messages.success(request, "Let's do it again")
    return redirect('index')


class SurveyListView(LoginRequiredMixin, ListView):
    model = Survey
    paginate_by = 10


class SurveyDetailView(LoginRequiredMixin, DetailView):
    model = Survey


def questions_view(request, slug):
    interval = request.GET.get('interval', 'year')
    labels = []
    data = []
    try:
        obj = Survey.objects.get(slug=slug)
        for question in obj.get_top_questions(interval):
            labels.append(question.slug)
            data.append(question.count)
        responsedict = {
            'data': data,
            'labels': labels
        }
    except Survey.DoesNotExist:
        pass

    responsedict = {
        'data': data,
        'labels': labels
    }
    return HttpResponse(json.dumps(responsedict))

def celery_result_view(request, task_id):
    from app_survey.celery import app
    result = app.AsyncResult(task_id)
    if result.state in ('PENDING', 'FAILURE', 'STARTED'):
        return JsonResponse({'result': result.state}, safe=False)
    if result.state == 'SUCCESS':
        data = {}
        data['result'] = 'SUCCESS'
        data['data'] = result.get()
        return JsonResponse(data,safe=False)


def celery_task_test(request):
    import time
    task = fill_report_test.delay()
    time.sleep(30)
    return HttpResponse(task)

def report_url_test(request):
    task = fill_report_test.delay()
    return render(request, 'surveys/report_from_url.html', {'task_id': task.id})

def task_panel_view(request):
    r_con = get_redis()
    obj = list()
    for key in r_con.scan_iter(celery_native_task_pattern):
        data_task_object = MetaDataTask
        celery_data_task = json.loads(r_con.get(key))
        custom_data_task = json.loads(r_con.get(custom_celery_task_mask.format(celery_data_task['task_id'])))
        #print(custom_data_task)
        # print(r_con.get(key))
        data_task_object.task_id = str(celery_data_task['task_id'])
        # logger.warning(r_con.get(key))
        data_task_object.celery_state = celery_data_task['status']
        data_task_object.task_name = custom_data_task['task_name']
        data_task_object.arguments = custom_data_task['args']
        data_task_object.kwarguments = custom_data_task['kwargs']
        data_task_object.state_datetime = datetime.strptime(custom_data_task['state_datetime'], "%Y-%m-%d %H:%M:%S")
        obj.append((data_task_object.__dict__).copy())

    context = {
            'tasks' :  obj ,
            }
    print("Context")
    for o in obj:
        print(o['task_id'])


    return render(request, 'surveys/task_panel.html', context)
