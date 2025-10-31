#!/usr/bin/env python3

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

class Sensor:
    def __init__(self, s):
        self.name = s[0]
        self.max = s[1]
        self.current = -1

    def __str__(self):
        return f"{self.name}: {self.current}°C"

class SensorsData:
    sensor_list=[
        ['CPU',0],
        ['SODIMM',0],
        ['Other',0],
        ['GPU',0],
        ['SODIMM',0],
        ['Core 0',100],
        ['Core 1',100],
        ['temp1',99],
        ['temp1',95]
    ]

    def __init__(self):
        self.parsed_data = []
        for sensor in self.sensor_list:
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
    sensors_data = SensorsData()
    sensors_data.parse_data(sensors_example_output)
    print(sensors_data)

if __name__ == "__main__":
    main()
