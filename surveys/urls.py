from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView

from .views import (
    IndexView, UserChoiceCreateView,
    SurveyDetailView, SurveyListView,
    start_again, questions_view, celery_result_view,
    celery_task_test, report_url_test
)

urlpatterns = [
    path('', TemplateView.as_view(template_name="surveys/landing.html"), name='landing'),
    path('current', IndexView.as_view(), name='index'),
    path('question/<int:question_id>/choice', UserChoiceCreateView.as_view(), name='user_choice'),
    path('start-again', start_again, name='start_again'),
    path('surveys/<slug:slug>/', SurveyDetailView.as_view(), name='survey_detail'),
    path('surveys/', SurveyListView.as_view(), name='survey_list'),
    path('surveys/<slug:slug>/questions.json', questions_view, name='questions_view'),
    path('celery/<str:task_id>', celery_result_view, name='celery_result_view'),
    path('task_test', celery_task_test),
    path('report_url_test', report_url_test),



]

