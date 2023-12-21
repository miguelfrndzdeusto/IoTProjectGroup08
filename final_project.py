import os, sys, time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import seaborn as sns
import requests
from threading import Thread

import seeed_dht

import pymongo
from flask import Flask, render_template
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as sp

app = Flask(__name__)
stop_update_thread = False

# Set-Up LED Display
if sys.platform == 'uwp':
    import winrt_smbus as smbus
    bus = smbus.SMBus(1)
else:
    import smbus
    import RPi.GPIO as GPIO
    rev = GPIO.RPI_REVISION
    if rev == 2 or rev == 3:
        bus = smbus.SMBus(1)
    else:
        bus = smbus.SMBus(0)

# this device has two I2C addresses
DISPLAY_RGB_ADDR = 0x62
DISPLAY_TEXT_ADDR = 0x3e

# send command to display
def textCommand(cmd):
    bus.write_byte_data(DISPLAY_TEXT_ADDR,0x80,cmd)

# set display text \n for second line(or auto wrap)
def setText(text):
    textCommand(0x01) # clear display
    time.sleep(.05)
    textCommand(0x08 | 0x04) # display on, no cursor
    textCommand(0x28) # 2 lines
    time.sleep(.05)
    count = 0
    row = 0
    for c in text:
        if c == '\n' or count == 16:
            count = 0
            row += 1
            if row == 2:
                break
            textCommand(0xc0)
            if c == '\n':
                continue
        count += 1
        bus.write_byte_data(DISPLAY_TEXT_ADDR,0x40,ord(c))

def get_current_humi_temp():
    """
    Returns current humidity and temperature...
    """
    sensor = seeed_dht.DHT('11', 12)
    humi, temp = sensor.read()
    return humi, temp

class WeatherStationStats:
    """
    This class provides a wrapper for all the parsed data
    for the available weather stations.
    """
    def __init__(self, id, name):
        self.id = id
        self.station_name = name
        self.air_quality = None
        self.pm2_5, self.pm2_5_min, self.pm2_5_max = None, None, None
        self.pm10, self.pm10_min, self.pm10_max = None, None, None
        self.no2, self.no2_min, self.no2_max = None, None, None
        self.so2, self.so2_min, self.so2_max = None, None, None
        self.temperature, self.temperature_min, self.temperature_max = None, None, None
        self.atm_pressure, self.atm_pressure_min, self.atm_pressure_max = None, None, None
        self.humidity, self.humidity_min, self.humidity_max = None, None, None
        self.wind, self.wind_min, self.wind_max = None, None, None

    def parse_from_html(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        self.air_quality = soup.find(id = "aqiwgtvalue").text
        # PM2.5 Data
        self.pm2_5 = soup.find(id = "cur_pm25").text
        self.pm2_5_min = soup.find(id = "min_pm25").text
        self.pm2_5_max = soup.find(id = "max_pm25").text
        # PM10 Data
        self.pm10 = soup.find(id = "cur_pm10").text
        self.pm10_min = soup.find(id = "min_pm10").text
        self.pm10_max = soup.find(id = "max_pm10").text
        # NO2 Data
        self.no2 = soup.find(id = "cur_no2").text
        self.no2_min = soup.find(id = "min_no2").text
        self.no2_max = soup.find(id = "max_no2").text
        # SO2 Data
        self.so2 = soup.find(id = "cur_so2").text
        self.so2_min = soup.find(id = "min_so2").text
        self.so2_max = soup.find(id = "max_so2").text
        # Temperature Data
        self.temperature = soup.find(id = "cur_t").text
        self.temperature_min = soup.find(id = "min_t").text
        self.temperature_max = soup.find(id = "max_t").text
        # Atm. Pressure Data
        self.atm_pressure = soup.find(id = "cur_p").text
        self.atm_pressure_min = soup.find(id = "min_p").text
        self.atm_pressure_max = soup.find(id = "max_p").text
        # Humidity Data
        self.humidity = soup.find(id = "cur_h").text
        self.humidity_min = soup.find(id = "min_h").text
        self.humidity_max = soup.find(id = "max_h").text
        # Wind Data
        self.wind = soup.find(id = "cur_w").text
        self.wind_min = soup.find(id = "min_w").text
        self.wind_max = soup.find(id = "max_w").text
    
    def __str__(self):
        blank = ""
        table = f"+----------------------+----------------------+----------------------+----------------------+\n"
        table += f"| Attribute            | Current              | Min                  | Max                  |\n"
        table += f"+----------------------+----------------------+----------------------+----------------------+\n"
        table += f"| ID                   | {self.id:<20} | {blank:<20} | {blank:<20} | \n"
        table += f"| Station Name         | {self.station_name:<20} | {blank:<20} | {blank:<20} | \n"
        table += f"| Air Quality          | {self.air_quality:<20} | {blank:<20} | {blank:<20} | \n"
        table += f"| PM2.5                | {self.pm2_5:<20} | {self.pm2_5_min:<20} | {self.pm2_5_max:<20} |\n"
        table += f"| PM10                 | {self.pm10:<20} | {self.pm10_min:<20} | {self.pm10_max:<20} |\n"
        table += f"| NO2                  | {self.no2:<20} | {self.no2_min:<20} | {self.no2_max:<20} |\n"
        table += f"| SO2                  | {self.so2:<20} | {self.so2_min:<20} | {self.so2_max:<20} |\n"
        table += f"| Temperature          | {self.temperature:<20} | {self.temperature_min:<20} | {self.temperature_max:<20} |\n"
        table += f"| Atmospheric Pressure | {self.atm_pressure:<20} | {self.atm_pressure_min:<20} | {self.atm_pressure_max:<20} |\n"
        table += f"| Humidity             | {self.humidity:<20} | {self.humidity_min:<20} | {self.humidity_max:<20} |\n"
        table += f"| Wind                 | {self.wind:<20} | {self.wind_min:<20} | {self.wind_max:<20} |\n"
        table += f"+----------------------+----------------------+----------------------+----------------------+\n"
        return table

def fetch_data():
    # Fetch data from weather stations
    stations_data = []
    for id, name in zip(station_ids, station_names):
        station_url = f"https://aqicn.org/city/spain/pais-vasco/bilbao/{id}/es/"
        station_report = WeatherStationStats(id, name)
        content = requests.get(station_url).text
        station_report.parse_from_html(content)
        stations_data.append(station_report)
    return stations_data

def update_sensors():
    # Update LED info from local sensors
    setText("Updating...")
    time.sleep(2)
    # Display Current Temp and Humidity from local sensor
    humi, temp = get_current_humi_temp()
    setText(f"Temp: {temp} \nHumidity: {humi}")

def update_database():
    while True:
        update_sensors()
        # Fetch data from weather stations
        stations_data = fetch_data()
        station_dicts = [station.__dict__ for station in stations_data]

        # Get list of station ids in the db
        list_mongo_ids = {}
        for document in collection.find({}):
            list_mongo_ids[document["id"]] = document["_id"]
        
        # Update Database data...
        bulk_operations = [pymongo.ReplaceOne({"_id": list_mongo_ids[station_dict["id"]]}, station_dict, upsert = True) for station_dict in station_dicts]
        collection.bulk_write(bulk_operations)
        if stop_update_thread:
            break
        
        time.sleep(60)  # Wait for one minute before the next update
        print("Updating Database Entries...")

def fetch_data_from_db():
    # Fetch data from the database
    stations_data = []
    for id in station_ids:
        document = collection.find_one({"id": id})
        if document:
            station_data = WeatherStationStats(id, document["station_name"])
            for key, value in document.items():
                setattr(station_data, key, value)
            stations_data.append(station_data)
    return stations_data

def generate_charts(data):
    
    charts = []

    for station in data:
        df = pd.DataFrame({
            'Attribute': ['Current', 'Min', 'Max'],
            'PM2.5': [station.pm2_5, station.pm2_5_min, station.pm2_5_max],
            'PM10': [station.pm10, station.pm10_min, station.pm10_max],
            'NO2': [station.no2, station.no2_min, station.no2_max],
            'SO2': [station.so2, station.so2_min, station.so2_max],
            'Temperature': [station.temperature, station.temperature_min, station.temperature_max],
            'Atm. Pressure': [station.atm_pressure, station.atm_pressure_min, station.atm_pressure_max],
            'Humidity': [station.humidity, station.humidity_min, station.humidity_max],
            'Wind': [station.wind, station.wind_min, station.wind_max],
        })

        # Bar plot for each variable
        fig = px.bar(
            df.melt(id_vars='Attribute'),
            x='Attribute',
            y='value',
            color='Attribute',
            facet_col='variable',
            labels={'value': f'{station.station_name}'},
            title=f'Metrics for {station.station_name}',
        )

        # Gauge plots
        gauge_figs = []
        variables = ['pm2_5', 'pm10', 'no2', 'temperature', 'humidity', 'atm_pressure']

        for variable in variables:
            gauge_fig = go.Figure()

            # Customize the layout of the gauge plot
            gauge_fig.update_layout(
                paper_bgcolor = "lavender", 
                font = {'color': "darkblue", 'family': "Arial"}
            )

            curr_value = float(getattr(station, variable)) 
            min_value = float(getattr(station, variable + "_min")) 
            max_value = float(getattr(station, variable + "_max")) 

            # Add gauge trace for the variable
            gauge_fig.add_trace(go.Indicator(
                mode="gauge+number",
                value = curr_value,
                title={'text': variable, 'font': {'size': 24}},
                gauge={'bar': {'color': "darkblue"},
                    'axis': {
                        'range': [min_value, max_value], 
                        'tickwidth': 1, 'tickcolor' : 'darkblue'}},
                domain={'x': [0, 1], 'y': [0, 1]}
            ))

            gauge_figs.append(gauge_fig)

        charts.append((fig, *gauge_figs, station))

    return charts

@app.route('/')
def dashboard():
    stations_data = fetch_data_from_db()
    charts = generate_charts(stations_data)

    charts_dashboard = [item[0:] for item in charts]

    return render_template('dashboard.html', charts = charts_dashboard)

if __name__ == "__main__":

    try:
        op_mode = sys.argv[1]
        if op_mode not in ["launch", "stream", "close"]: raise IndexError
    except IndexError as e:
        print("Please provide one of the following operation modes: launch/stream/close")
        sys.exit(1)

    # Create a MongoDB client and connect to the database
    host, port = os.environ.get('MONGO_HOST'), 27017
    client = pymongo.MongoClient(host, port)
    db = client.weather_stations_db
    collection = db.weather_stations
    station_ids = ["mazarredo", "m--diaz-haro", "europa"]
    station_names = ["Mazarredo", "Mª Díaz de Haro", "Europa"]

    if op_mode == "launch":
        # Fetch data from weather stations
        stations_data = fetch_data()
        
        # Insert data into database
        station_dicts = [station.__dict__ for station in stations_data]
        collection.insert_many(station_dicts)

        setText("Welcome...")
        print("Finished Launching the Database...")
    
    elif op_mode == "stream":
        try:                
            # Run database updates in a different thread...
            update_thread = Thread(target = update_database)
            update_thread.start()

            # Run the Flask app
            try:
                app.run(debug = True, use_reloader = False, host = '0.0.0.0')
                
            finally:
                print("\nFlask App Stopped...")
                stop_update_thread = True
                update_thread.join(timeout = 2)
                raise KeyboardInterrupt        
        except KeyboardInterrupt:
            print("Terminating Streaming mode...")
        
    elif op_mode == "close":
        setText("Goodbye...")
        time.sleep(2)
        textCommand(0x01) # Clear LED display
        print("Droping Weather Station Database...")
        client.drop_database("weather_stations_db")
        client.close()
    
    sys.exit(0)
