#!/usr/bin/env python
import datetime
import psutil
import time as t
from influxdb import InfluxDBClient

# influx configuration - edit these
ifuser = "grafana"
ifpass = "JonWb2mnf"
ifdb   = "powermonitor"
ifhost = "192.168.50.37"
ifport = 8086
measurement_name = "system"

# take a timestamp for this measurement
time = datetime.datetime.utcnow()

# collect some stats from psutil
disk = psutil.disk_usage('/')
mem = psutil.virtual_memory()
#load = psutil.getloadavg()
cpu_percents = psutil.cpu_percent(percpu=True)
cpu_percent = psutil.cpu_percent(percpu=False)
#print ("CPU_time = ")
#print (cpu_percent)

mem = psutil.virtual_memory()
#print ("xirtual_memory=")
#print (mem[2])

net = psutil.net_io_counters()
#print ("IO_bytes_sent=")
#print (net[0]/1000000)
#print ("IO_bytes_rcvd=")
#print (net[1]/1000000)

disk_io = psutil.disk_io_counters()
#print ("disk_read_bytes=")
#print (disk_io[2]/1000000)

#print ("disk_write_bytes=")
#print (disk_io[3]/1000000)

boot_time = psutil.boot_time()
#print ("Boot time = ")
#print (boot_time)

epoch_time = int(t.time())
#print ("Epoch time=")
#print (epoch_time)

#print ("up_hours=")
#print (epoch_time - boot_time)/3600

#CPU temp
tFile = open('/sys/class/thermal/thermal_zone0/temp')
temp = (float(tFile.read())/ 1000 * 9 / 5)  + 32
tFile.close()

# format the data as a single measurement for influx
body = [
    {
        "measurement": measurement_name,
        "time": time,
        "fields": {
#           "load_1": load[0],
#           "load_5": load[1],
#           "load_15": load[2],
            "disk_percent": disk.percent,
            "disk_free": disk.free,
            "disk_used": disk.used,
            "mem_percent": mem.percent,
            "mem_free": mem.free,
            "mem_used": mem.used,
	    "cpu_pct": cpu_percent,
	    "virtual_memory": mem[2],
	    "io_sent_mbytes": net[0]/1000000,
	    "io_rcvd_mbytes": net[1]/1000000,
	    "disk_read_mbytes": disk_io[2]/1000000,
	    "disk_write_mbytes": disk_io[3]/1000000,
	    "up_hours": (epoch_time - boot_time) / 3600,
	    "cpu_temp_f": temp
        }
    }
]

# connect to influx
ifclient = InfluxDBClient(ifhost,ifport,ifuser,ifpass,ifdb)

# write the measurement
ifclient.write_points(body)

#print ("Influx record written")
