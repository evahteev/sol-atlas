#!/bin/bash

# Variables
POSTGRES_USER="postgres"
POSTGRES_PORT="5433"
POSTGRES_HOST="localhost"
POSTGRES_PASSWORD="SuperSecretPassword"
DB_NAMES=("engine" "flow_api" "warehouse_api")

# Provision Databases
for DB_NAME in "${DB_NAMES[@]}"; do
  echo "Creating database '$DB_NAME'..."
  PGPASSWORD=$POSTGRES_PASSWORD psql -U $POSTGRES_USER -h $POSTGRES_HOST -p $POSTGRES_PORT -c "CREATE DATABASE $DB_NAME;"

  if [ $? -eq 0 ]; then
    echo "Database '$DB_NAME' created successfully."
  else
    echo "Failed to create database '$DB_NAME'."
  fi
done

echo "All databases provisioned."
