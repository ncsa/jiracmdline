FROM python:3
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APPDIR=/app

# ENV TZ=America/Chicago
# RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY *.py *.txt *.sh ${APPDIR}/
COPY static/ ${APPDIR}/static/
COPY templates/ ${APPDIR}/templates/
RUN pip install --no-cache-dir -r ${APPDIR}/requirements.txt

# Jira library uses credentials from .netrc
RUN ln -s /home/.netrc /root/.netrc

WORKDIR ${APPDIR}
#ENTRYPOINT [ "gunicorn", "app:app" ]
ENTRYPOINT [ "./entrypoint.sh" ]
