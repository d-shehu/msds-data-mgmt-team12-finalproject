#!/bin/bash

docker stop final_project_search_app
docker rm final_project_search_app

scriptDir=$(cd -- "$( dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd )
echo "Current script dir: ${scriptDir}"

# This is similar to the code in ./run.sh. But it's copy/pasted here so 
# we can test the app separately from the other services. Please keep
# the passwords in sync.

echo "Enter dir where services will run:"
read runtimeDir

if [ -z "${runtimeDir}" ]
then
    runtimeDir="$HOME/tmp/final_project"
fi

if [ -z "${password}" ]
then
    password="password" # TODO: only for testing 
fi

# Export as environment variable. Note that these only persist for the current session.
export T12_FINAL_PROJECT_DB_PASS=$password

# Run the container in interactive mode (shell) and bind/map the 
# current version of "search_app.py" and "templates" to the
# container's file system. This allows us to quickly test app changes
# in the native environment.
#
# Also maps host to internal HTTP port so we can access the app.
# Keep in mind this has to connect to an existing network.

docker run -it --rm --name=final_project_search_app \
        --entrypoint=/bin/bash \
        --env MONGO_DB_HOSTNAME=t12_final_project_mongodb \
        --env MONGO_DB_USERNAME=t12 \
        --env MONGO_DB_PASSWORD=$T12_FINAL_PROJECT_DB_PASS \
        --env PG_DB_HOSTNAME=t12_final_project_pgdb \
        --env PG_DB_USERNAME=postgres \
        --env PG_DB_PASSWORD=$T12_FINAL_PROJECT_DB_PASS \
        --env REDIS_DB_HOSTNAME=t12_final_project_redisdb \
        --env REDIS_DB_PASSWORD=$T12_FINAL_PROJECT_DB_PASS \
        --volume $runtimeDir/input:/data \
        --volume $scriptDir/templates:/app/templates \
        --volume $scriptDir/static:/app/static \
        --volume $scriptDir/utils:/app/utils \
        --volume $scriptDir/search_app.py:/app/search_app.py \
        --volume $scriptDir/test_app.py:/app/test_app.py \
        --volume $scriptDir/requirements.txt:/app/requirements.txt \
        --network="msds_data_mgmg_final_project_network" \
        --publish 25000:8080 \
	    msds_data_mgmt_t12_final_project/searchapp:latest
