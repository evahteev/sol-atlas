# Base stage for both prod and dev environments
FROM python:3.11.4-slim-bullseye as base
RUN apt-get update && apt-get install -y \
  gcc \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app/src

# Prod stage
FROM base as prod

# Copying requirements of a project
COPY requirements.txt /app/src/

# Installing requirements
RUN pip install --no-cache-dir -r requirements.txt

# Removing gcc after installation to keep the image slim
RUN apt-get purge -y \
  gcc \
  && rm -rf /var/lib/apt/lists/*

# Copying actual application
COPY . /app/src/

CMD ["/usr/local/bin/python", "-m", "warehouse_api"]

# Dev stage
#FROM base as dev
#
## For development, re-install all dependencies including dev dependencies
## Assuming you have also exported dev dependencies in a separate requirements file
#COPY dev-requirements.txt /app/src/
#RUN pip install --no-cache-dir -r dev-requirements.txt
