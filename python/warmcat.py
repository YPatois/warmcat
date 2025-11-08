#!/usr/bin/env python3
import os
import sys
import subprocess
import signal
import time
import logging

kTestMode=False

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a file handler
if not kTestMode:
    file_handler = logging.FileHandler('/home/warmcat/var/log/log_file.log')
else:
    file_handler = logging.StreamHandler(sys.stdout)
file_handler.setLevel(logging.INFO)

# Create a formatter and add it to the file handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add the file handler to the logger
logger.addHandler(file_handler)

"""
coretemp-isa-0000
Adapter: ISA adapter
Core 0:       +31.0°C  (high = +105.0°C, crit = +105.0°C)
Core 1:       +31.0°C  (high = +105.0°C, crit = +105.0°C)

acpitz-acpi-0
Adapter: ACPI interface
temp1:        +31.5°C  (crit = +107.0°C)

dell_smm-isa-0000
Adapter: ISA adapter
Processor Fan:    0 RPM  (min =    0 RPM, max = 4900 RPM)
CPU:            +31.0°C
SODIMM:         +37.0°C
Other:          +35.0°C
GPU:            +41.0°C

nouveau-pci-0100
Adapter: PCI adapter
GPU core:    900.00 mV (min =  +0.90 V, max =  +1.17 V)
temp1:        +46.0°C  (high = +95.0°C, hyst =  +3.0°C)
                       (crit = +105.0°C, hyst =  +2.0°C)
                       (emerg = +110.0°C, hyst =  +5.0°C)

BAT0-acpi-0
Adapter: ACPI interface
in0:          11.76 V
curr1:         1.09 A
"""

k_sensor_list_warmcat=[
    [1,'Core 0'        ,100,' (CPU)'  ],
    [1,'Core 1'        ,100,' (CPU)'  ],
    [1,'temp1'         ,100           ],
    [0,'Processor Fan' ,  0           ],
    [1,'CPU'           ,  0           ],
    [1,'SODIMM'        ,  0           ],
    [1,'Other'         ,  0           ],
    [1,'GPU'           ,  0           ],
    [1,'temp1'         , 95,' (GPU)'  ]
]

k_sensor_list_test=[
    ['edge'  ,  90           ],
    ['Tctl'  ,  90           ],
    ['Tccd1' ,  90           ]
]

if (kTestMode):
    logger.info("Running in test mode")
    k_sensor_list=k_sensor_list_test
else:
    k_sensor_list=k_sensor_list_warmcat

class Sensor:
    def __init__(self, s):
        self.is_temperature = True if (s[0] == 1) else False
        self.name = s[1]
        self.max = s[2]
        if (len(s) > 3):
            self.xname = self.name + s[3]
        else:
            self.xname = self.name
        self.current = -1

    def __str__(self):
        return f"{self.xname}: {self.current}°C"

class SensorsData:
    def __init__(self, sensor_list):
        self.parsed_data = []
        for sensor in sensor_list:
            self.parsed_data.append(Sensor(sensor))

    def parse_data(self, data):
        #print(data)
        idx=0
        for line in data.split('\n'):
            if line.strip():
                parts = line.split(':')
                sensor_name = parts[0].strip()
                if (sensor_name == self.parsed_data[idx].name):
                    #print(f"Found {sensor_name}")
                    if (self.parsed_data[idx].is_temperature):
                        value = parts[1].strip().split('°')[0]
                    else:
                        #print (parts[1])
                        value = parts[1].strip().split(' ')[0].strip()
                    self.parsed_data[idx].current = float(value)
                    idx += 1
                    if (idx >= len(self.parsed_data)):
                        break
        if (idx < len(self.parsed_data)):
            print(f"ERROR: {idx} sensors parsed out of {len(self.parsed_data)} expected")
            logger.error(f"ERROR: {idx} sensors parsed out of {len(self.parsed_data)} expected")
            return None
        return self.parsed_data

    def process_sensors(self):
        max=-1
        # Iterate over all sensors
        for sensor in self.parsed_data:
            if not sensor.is_temperature:
                self.fan_speed=sensor.current
                continue
            # Check if the current temperature is greater than the maximum temperature
            if (sensor.max > 0) and (sensor.current > sensor.max):
                # If so, print a warning message
                #print(f"WARNING: {sensor.name} temperature is {sensor.current}°C, which is greater than the maximum temperature of {sensor.max}°C")
                logger.error(f"{sensor.name} temperature is {sensor.current}°C, which is greater than the maximum temperature of {sensor.max}°C")
                os.kill(os.getpid(), signal.SIGINT)
                time.sleep(1)
                sys.exit(1)
            # Check if the current temperature is greater than the maximum temperature
            if (sensor.current > max):
                # If so, update the maximum temperature
                max = sensor.current
        return max

    def __str__(self):
        s=""
        for sensor in self.parsed_data:
            s += str(sensor) + "\n"
        return s

class CatLoad:
    def __init__(self, window_size=1, repeats=5):
        self.window_size = window_size
        self.repeats = repeats
        # Start the virtual framebuffer first
        if ( not kTestMode):
            self.vfb_process = subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1024x768x24', '-ac', '-nolisten', 'tcp'])
            self.shell_process = subprocess.Popen(['glxgears', '-display', ':99'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            self.shell_process = subprocess.Popen(['glxgears'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Suspend load
        self.shell_process.send_signal(signal.SIGTSTP)
    
    def do_load(self,ratio):
        # Ratio 0: only sleep
        # Ratio 1: only run
        slptime=self.window_size*(1-ratio)
        runtime=self.window_size*ratio
        for i in range(self.repeats):
            self.shell_process.send_signal(signal.SIGCONT)
            time.sleep(runtime)
            self.shell_process.send_signal(signal.SIGTSTP)
            time.sleep(slptime)

def compute_ratio(target,maxval,ratio):
    if (maxval > 90):
        return max(0, ratio/2.)
    if (maxval < target):
        return min(1, ratio*(1+abs(maxval/target)/10))
    return max(0, ratio*(1-abs(target/maxval)/10))

def main_loop():
    sensors_data = SensorsData(k_sensor_list)
    cat_load = CatLoad()

    # Suspend and unsuspend the shell process every second
    ratio=0.5
    cnt=0
    while True:
        sensors_data.parse_data(subprocess.check_output(['sensors']).decode('utf-8'))
        maxval = sensors_data.process_sensors()
        #print(sensors_data)
        #print(f"Maximum temperature: {maxval}°C")
        ratio = compute_ratio(75,maxval,ratio)
        #print(f"Load ratio: {ratio}")
        logger.info(f"Tmax: {maxval}°C - Ratio: {ratio:.3f} - Fan: {sensors_data.fan_speed:.0f} RPM")
        cat_load.do_load(ratio)
        cnt += 1
        # An equilibrium can be found at any fan speed (hiher ratio and higher fan speed)
        # To limit divergence, once in a while, we pause, thus slowing fan.
        if cnt > 100:
            time.sleep(100)
            cnt = 0

def main():
    main_loop()

if __name__ == '__main__':
    main()
