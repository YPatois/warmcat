#!/usr/bin/env python3
import sys
import os
import datetime
import rrdtool

sensors_example_output="""
dell_smm-isa-0000
Adapter: ISA adapter
Processor Fan: 2522 RPM  (min =    0 RPM, max = 4000 RPM)
CPU:            +42.0°C  
SODIMM:         +44.0°C  
Other:          +44.0°C  
GPU:            +53.0°C  
SODIMM:         +40.0°C  

coretemp-isa-0000
Adapter: ISA adapter
Core 0:       +37.0°C  (high = +100.0°C, crit = +100.0°C)
Core 1:       +42.0°C  (high = +100.0°C, crit = +100.0°C)

acpitz-acpi-0
Adapter: ACPI interface
temp1:        +42.5°C  (crit = +99.0°C)

nouveau-pci-0100
Adapter: PCI adapter
GPU core:      1.15 V  (min =  +1.00 V, max =  +1.20 V)
temp1:        +63.0°C  (high = +95.0°C, hyst =  +3.0°C)
                       (crit = +105.0°C, hyst =  +5.0°C)
                       (emerg = +125.0°C, hyst =  +5.0°C)
"""

k_sensor_list=[
    ['CPU'   ,  0           ],
    ['SODIMM',  0,'_1'      ],
    ['Other' ,  0           ],
    ['GPU'   ,  0           ],
    ['SODIMM',  0,'_2'      ],
    ['Core 0',100,' (CPU)'  ],
    ['Core 1',100,' (CPU)'  ],
    ['temp1' , 99,' (ACPI)' ],
    ['temp1' , 95,' (GPU)'  ],
]

import rrdtool

import rrdtool
import datetime
import os

class SensorRRD:
    def __init__(self, rrd_dir, sensor_list, fill_missing=True):
        self.rrd_dir = rrd_dir
        self.sensor_list = sensor_list
        self.timestamp_log = []
        self.last_event_timestamp_file = os.path.join(self.rrd_dir, 'last_event_timestamp.txt')
        self.rrd_file = os.path.join(self.rrd_dir, 'warmcat.rrd')

        # Check if the RRD file already exists
        if not rrdtool.info(self.rrd_file):
            # Create the RRD file if it doesn't exist
            self.create_rrd()

        # Read the last event timestamp from the file
        if os.path.isfile(self.last_event_timestamp_file):
            with open(self.last_event_timestamp_file, 'r') as file:
                last_event_timestamp_str = file.read().strip()
                self.last_event_timestamp = datetime.datetime.strptime(last_event_timestamp_str, '%Y-%m-%d %H:%M:%S')
                if fill_missing:
                    self.fill_missing_entries()
        else:
            self.last_event_timestamp = datetime.datetime.min

    def create_rrd(self):
        ds_definition = 'DS:temperature:GAUGE:10:U:U'
        rra_definitions = [
            'RRA:AVERAGE:0.5:1:24:0',  # Define the first RRA (Average, 5-minute interval, 24 hours)
            'RRA:AVERAGE:0.5:1:288:0',  # Define the second RRA (Average, 5-minute interval, 7 days)
            'RRA:AVERAGE:0.5:1:17520:0',  # Define the third RRA (Average, 5-minute interval, 30 days)
        ]

        # Create the RRD file
        rrdtool.create(self.rrd_file,
                       '--step', '10',  # Data resolution in seconds
                       ds_definition,
                       *rra_definitions)

    def fill_missing_entries(self):
        now = datetime.datetime.now()
        # Calculate the start and end timestamps for the missing entries
        start_timestamp = self.last_event_timestamp
        end_timestamp = now

        # Calculate the number of missing entries
        num_missing_entries = int((end_timestamp - start_timestamp).total_seconds() // 10)

        # Update the RRD file with zeroes for the missing entries
        rrdtool.update(self.rrd_file, 'N:' + ','.join(['0'] * len(self.sensor_list)),
                       '--start', str(start_timestamp),
                       '--end', str(end_timestamp))

        # Update the last event timestamp in the file
        with open(self.last_event_timestamp_file, 'w') as file:
            file.write(str(datetime.datetime.now()))

        # Print the number of missing entries filled
        print(f"Filled {num_missing_entries} missing entries with zeroes")


    def update_rrd(self, data):
        # Update the RRD with new data
        rrdtool.update(self.rrd_file,
                       'N:' + ','.join(f'{sensor_name}:{value}' for sensor_name, value in data.items()))
        self.timestamp_log.append(datetime.datetime.now())

        # Update the last event timestamp in the file
        with open(self.last_event_timestamp_file, 'w') as file:
            file.write(str(datetime.datetime.now()))

    def get_graph(self):
        # Retrieve data from the RRD and generate a graph
        data = rrdtool.graph(self.rrd_file,
                            '--width', '1600',
                            '--height', '400',
                            '--start', '-1d',
                            '--end', 'now',
                            '--title', 'Sensor Data',
                            '--vertical-label', 'Values',
                            '--slope-mode',
                            '--lower-limit', '0',
                            '--upper-limit', '100',
                            '--color', '#FF0000',
                            '--font TITLE:Arial:12:bold',
                            '--font AXIS:Arial:10:normal',
                            '--font LEGEND:Arial:10:normal',
                            *(
                                f'DEF:{sensor_name}={self.rrd_file}:{sensor_name}:AVERAGE'
                                for sensor_name in self.sensor_list
                            ),
                            *(
                                f'LINE1:{sensor_name}#FF0000:{sensor_name}'
                                for sensor_name in self.sensor_list
                            ),
                            )

        # Print the retrieved data
        print(data)

        # Check for missing entries
        current_time = datetime.datetime.now()
        time_difference = current_time - self.last_event_timestamp
        missing_entries = int(time_difference.total_seconds() // 10)

        # Print the number of missing entries
        print(f"Missing entries: {missing_entries}")



class SensorsData:
    def __init__(self, data):
        self.data = data

    def get_sensor_data(self, sensor_name):
        # Retrieve the data for a specific sensor
        return self.data.get(sensor_name, None)


class Sensor:
    def __init__(self, s):
        self.name = s[0]
        self.max = s[1]
        if (len(s) > 2):
            self.xname = self.name + s[2]
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
        idx=0
        for line in data.split('\n'):
            if line.strip():
                parts = line.split(':')
                sensor_name = parts[0].strip()
                if (sensor_name == self.parsed_data[idx].name):
                    #print(f"Found {sensor_name}")
                    value = parts[1].strip().split('°')[0]
                    self.parsed_data[idx].current = float(value)
                    idx += 1
                    if (idx >= len(self.parsed_data)):
                        break
        if (idx < len(self.parsed_data)):
            print(f"ERROR: {idx} sensors parsed out of {len(self.parsed_data)} expected")
        return self.parsed_data

    def __str__(self):
        s=""
        for sensor in self.parsed_data:
            s += str(sensor) + "\n"
        return s

def main():
    sensors_data = SensorsData(k_sensor_list)
    sensors_data.parse_data(sensors_example_output)
    print(sensors_data)

if __name__ == "__main__":
    main()
