FROM ubuntu:artful

USER root

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

RUN apt-get update -y && \
    apt-get install imagemagick -y && \
    apt-get install exiftool -y && \
    apt-get install python3.6 -y && \
    apt-get install curl -y

RUN curl https://bootstrap.pypa.io/get-pip.py | python3.6

WORKDIR /rjpeg

ADD radiometric /rjpeg/radiometric
ADD setup.py /rjpeg/setup.py

RUN pip3 install ./

VOLUME /in
VOLUME /out

ENTRYPOINT ["extract_csv", "--source=/in", "--dest=/out"]
