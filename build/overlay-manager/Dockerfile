FROM python:3.11.6

WORKDIR /usr/src/app

COPY ./src/overlay-manager/requirements.txt ./

RUN pip install -r requirements.txt

COPY ./src/overlay-manager/l2sm-overlay-manager.py .

CMD ["python3", "l2sm-overlay-manager.py"]
