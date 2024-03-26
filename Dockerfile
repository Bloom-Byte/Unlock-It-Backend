FROM python:3.10.12
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y gettext

RUN pip install --upgrade pip

RUN adduser --disabled-password user

ENV PATH="/home/user/.local/bin:${PATH}"

USER user

WORKDIR /django

COPY --chown=user:user requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY --chown=user:user . .

CMD ["gunicorn", "UnlockIt.wsgi", "--bind", "0.0.0.0:8000", "--workers", "4"]