#!/bin/bash

# Script dir
scriptDir=$(cd -- "$( dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd )
echo "Current script dir: ${scriptDir}"

echo "Enter dir where services will run:"
read runtimeDir

if [ -z "${runtimeDir}" ]
then
    runtimeDir="$HOME/tmp/final_project"
fi

echo "Running under $runtimeDir and data will be persisted here"

# Create the directory and parent directories including parents
mkdir -p "${runtimeDir}/pgdata"
mkdir -p "${runtimeDir}/mongodata"
mkdir -p "${runtimeDir}/redisdata"
mkdir -p "${runtimeDir}/workbooks"
mkdir -p "${runtimeDir}/input"

# Password should be injected securely as env variables, or using a secrets vault.
# For the purpose of this project, will just ask the user on startup to provide
# a password to be used for all data stores. Simplify
echo -n "Enter Common DB Password:"
read -s password

if [ -z "${password}" ]
then
    password="password" # TODO: only for testing 
fi

# Export as environment variable. Note that these only persist for the current session.
export T12_FINAL_PROJECT_DB_PASS=$password
export T12_RUNTIME_DIR=$runtimeDir

# Run the services and app
docker-compose up