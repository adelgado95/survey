FROM python:3
ENV PYTHONUNBUFFERED 1
ENV APP_PROJ=/srv/survey

COPY . $APP_PROJ
RUN useradd survey && chown survey:survey -R $APP_PROJ
RUN apt-get update

WORKDIR $APP_PROJ
RUN pip install -r requirements/base.txt
COPY ./compose/supervisor/supervisord.conf /etc/supervisord.conf
COPY compose/django/start.sh /start.sh
RUN chmod +x /start.sh && chown survey:survey /start.sh
RUN chmod 777 -R /var/log/



