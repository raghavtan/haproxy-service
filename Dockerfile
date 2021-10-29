FROM python:3.6

WORKDIR /usr

RUN mkdir /usr/app

COPY . /usr/app

WORKDIR /usr
RUN git clone https://c4b84afaee4a53e1fe6fa6186a10c9afa5aa4320:x-oauth-basic@github.com/LimeTray/tl-python-sdk.git

WORKDIR /usr/tl-python-sdk

RUN python setup.py install

WORKDIR /usr/app

RUN mkdir tmp

ADD requirements.txt /usr/app/requirements.txt

RUN pip3 install -r requirements.txt

ENTRYPOINT ["python"]

CMD ["main.py"]

#CMD ["bash"]