FROM python:3

ENV TZ=America/Chicago
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /srv
COPY ./*.py ./*.txt ./*.sh /srv
RUN python -m pip install -r /srv/requirements.txt
RUN ln -s /home/.netrc /root/.netrc

CMD ["bash"]
