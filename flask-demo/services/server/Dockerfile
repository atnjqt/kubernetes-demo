# base image
FROM python:3.9.4-slim

# install netcat
RUN apt-get update && \
    apt-get -y install netcat && \
    apt-get clean

# set working directory
WORKDIR /usr/src/app

# add and install requirements
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

# add entrypoint.sh
#COPY ./entrypoint.sh /usr/src/app/entrypoint.sh
#RUN chmod +x /usr/src/app/entrypoint.sh

# add app
COPY . /usr/src/app
RUN chmod +x /usr/src/app/app.py

CMD ["python3","app.py","--host=0.0.0.0"]