#!/bin/bash
#source env/bin/activate
echo -e "Initializing MongoDB in port 27017..."
#sudo systemctl start mongod
echo -e "Starting Database..."
python final_project.py launch
#echo -e "Initializing MongoDash in port 3000..."
# https://mongo-dash-docs.vercel.app/docs/getting-started/usage
#mongo_dash --mongo-uri mongodb://localhost --database-name database & python final_project.py stream && sleep 2
echo -e "Initializing Flask in port 5000..."
python final_project.py stream
# When exiting script on Ctrl + C...
trap '' SIGINT;
echo -e "Closing MongoDB Server..."
python final_project.py close
#sudo systemctl stop mongod
