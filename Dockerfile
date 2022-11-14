FROM python:3-alpine

WORKDIR /backup

RUN pip install arlo
COPY arlo-backup.py /backup/arlo-backup.py

CMD [ "python", "-u", "arlo-backup.py" ]