# IoTProjectGroup08
Repository for our IoT Project (Group 8).

## Requirements and Installation

Some considerations in terms of the requirements and installation process for this project:
* Make sure to be running `MongoDB` in your host device.
  - If you decide to host your database in a different machine from the one running the dashboard/updates, make sure to modify the `mongod.conf` file accordingly to bind **your** IP address (by default only localhost is bound).
  - If you decide to host the database locally, please uncomment the lines referring to `MongoDB` in the `./launch.sh` script to start/stop the service locally.

In both cases, please do not forget to specify your host (`localhost`/`IP address`) and listening port in the `final_project.py` client configuration :)
 
* For all the necessary python modules, please refer to the `requirements.txt` provided in this repository.
  
## How to Run the Project?

The whole project can be directly executed by running the `./launch.sh` script. 

Optionally, it can be run manually by:
* `python final_project.py launch` to launch and populate the database by fetching the corresponding data.
* `python final_project.py stream` to enter *streaming* mode (i.e. hosting the interactive dashboard, updating the database with real-time data and displaying local sensor information in the Raspberry Pi).
* `python final_project.py close` to (optionally) delete the database entries at the end.
