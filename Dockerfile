FROM python:3.12-slim

COPY . /app
WORKDIR /app
#RUN apt-get update \
#  && apt-get install -y python3-pip python3-dev \
#  && cd /usr/local/bin \
#  && ln -s /usr/bin/python3 python \
#  && pip3 install --upgrade pip
EXPOSE 5000
RUN pip install --upgrade pip
RUN pip install -r requirements.txt


ENV FLASK_APP=app.py

CMD flask run -h 0.0.0.0 -p 5000
