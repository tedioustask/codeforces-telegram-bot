FROM python:3.10-alpine

RUN mkdir /app
WORKDIR /app

ADD ./tgbot/ /app/

RUN pip install -r /app/requirements.txt

CMD ["python","./bot.py"]
