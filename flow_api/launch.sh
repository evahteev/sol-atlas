#!/bin/sh

# Apply migrations
alembic upgrade head

# Launch the app
python ./flow_api/__main__.py
