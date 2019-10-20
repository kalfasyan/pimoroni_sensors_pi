#!/usr/bin/env python

import pandas as pd
import os
import time
from pms5003 import PMS5003, ReadTimeoutError
from enviroplus import gas
try:
    # Transitional fix for breaking change in LTR559
    from ltr559 import LTR559
    ltr559 = LTR559()
except ImportError:
    import ltr559
from bme280 import BME280
try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus

# Get the temperature of the CPU for compensation
def get_cpu_temperature():
    with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
        temp = f.read()
        temp = int(temp) / 1000.0
    return temp
from datetime import datetime

cpu_temps = [get_cpu_temperature()] * 5

# PMs
pms5003 = PMS5003()
bus = SMBus(1)
bme280 = BME280(i2c_dev=bus)
time.sleep(1.0)
data = {}
data['cpu_factor'] = 0.95

try:
    while True:
        now = datetime.now() 
        data['datetime'] = now.strftime("%d/%m/%Y %H:%M:%S")
        data['temperature'] = bme280.get_temperature()
        cpu_temp = get_cpu_temperature()
        # Smooth out with some averaging to decrease jitter
        cpu_temps = cpu_temps[1:] + [cpu_temp]
        data['avg_cpu_temp'] = sum(cpu_temps) / float(len(cpu_temps))
        raw_temp = data['temperature']
        data['comp_temp'] = raw_temp - ((data['avg_cpu_temp'] - data['temperature']) / data['cpu_factor'])
        data['pressure'] = bme280.get_pressure()
        data['humidity'] = bme280.get_humidity()        
        data['gas_nh3'] = gas.read_nh3()
        data['gas_oxidising'] = gas.read_oxidising()
        data['gas_reducing'] = gas.read_reducing()
        data['lux'] = ltr559.get_lux()
        data['prox'] = ltr559.get_proximity()            
        try:
            pms = pms5003.read()
            data['pms1_0'] = pms.data[0]
            data['pms2_5'] = pms.data[1]
            data['pms10'] = pms.data[2]
            data['pms1_0_atmenv'] = pms.data[3]
            data['pms2_5_atmenv'] = pms.data[4]
            data['pms10_atmenv'] = pms.data[5]
            data['pms_03_in_01'] = pms.data[6]
            data['pms_05_in_01'] = pms.data[7]
            data['pms_1_in_01'] = pms.data[8]
            data['pms_2_5_in_01'] = pms.data[9]
            data['pms_5_in_01'] = pms.data[10]
            data['pms_10_in_01'] = pms.data[11]
        except ReadTimeoutError:
            pms = PMS5003()#pms5003 = PMS5003()
        time.sleep(2.0)
        
        df =pd.DataFrame.from_dict(data, orient='index').T
        
        datafile = '/home/pi/Desktop/sensor_data.csv'
        if os.path.isfile(datafile):
            df.to_csv('sensor_data.csv', mode='a', header=False) 
        else:
            df.to_csv('sensor_data.csv', mode='a', header=True) 
except KeyboardInterrupt:
    pass
