FROM ubuntu:trusty

USER root

RUN apt-get update -y && \
    apt-get install imagemagick -y && \
    apt-get install exiftool -y

CMD echo "foo"
