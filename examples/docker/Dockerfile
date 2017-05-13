FROM python:3.5
MAINTAINER Channel Cat <channelcat@gmail.com>

ADD . /code
RUN pip3 install git+https://github.com/channelcat/sanic

EXPOSE 8000

WORKDIR /code

CMD ["python", "simple_server.py"]