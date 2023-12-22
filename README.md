# IoTProjectGroup08
Repository for our IoT Project (Group 8). Please find below all the required information for the installation process.

## Requirements and Installation

Some considerations in terms of the requirements and installation process for this project:
* Make sure to be running `MongoDB` in your host device.
  - If you decide to host your database in a different machine from the one running the dashboard/updates, make sure to modify the `mongod.conf` file accordingly to bind **your** IP address (by default only localhost is bound).
  - If you decide to host the database locally, please uncomment the lines referring to `MongoDB` in the `./launch.sh` script to start/stop the service locally.
  - For the sake of simplicity, we recommend running MongoDB within a docker container:
```
# For pulling the latest MongoDB image
docker pull mongo:latest
# For running the container
docker run -d -p 27017:27017 --name=mongo mongo
# For starting the container
docker start mongo
# For stoping the container
docker stop mongo
```

In both cases, please do not forget to specify your host (`localhost`/`IP address`) and listening port in the `final_project.py` client configuration :)

* For all the necessary python modules, please refer to the `requirements.txt` provided in this repository.

* In terms of the local sensors/actuators deployed, do not forget to plug the LED display and the temperature/humidity sensors to the board.

* If you wish to access the dashboard from outside the hosting device, we provide below a comprehensive guide on how to do so using the `ufw` linux firewall:
```
# Install ufw
sudo apt install ufw
# Enable ufw
sudo ufw enable
# Allow ssh connections (optional in this case, but great for debugging)
sudo ufw allow ssh
# Open port 5000 to access Flask dashboard :)
sudo ufw allow 5000
# In order to see the IP address of your host device:
hostname -I
# Disable ufw firewall
sudo ufw disable
```
  
## How to Run the Project?

The whole project can be directly executed by running the `./launch.sh` script. To do so, please provide as an argument the address of your `mongodb` host (i.e. `./launch.sh <mongo-host-ip>`).

Optionally, it can be run manually by:
* `python final_project.py launch` to launch and populate the database by fetching the corresponding data.
* `python final_project.py stream` to enter *streaming* mode (i.e. hosting the interactive dashboard, updating the database with real-time data and displaying local sensor information in the Raspberry Pi).
* `python final_project.py close` to (optionally) delete the database entries at the end.
