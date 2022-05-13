#Test reading the last influxdb record
import datetime
#For influx load
from influxdb import InfluxDBClient
# influx configuration - edit these
ifuser = "grafana"
ifpass = "JonWb2mnf"
ifdb   = "home"
ifhost = "127.0.0.1"
ifport = 8086
measurement_name = "PWRgate"
timenow=datetime.datetime.utcnow()

ifclient = InfluxDBClient(ifhost,ifport,ifuser,ifpass,ifdb)
#ifclient.write_points(body)

#Retrieve the last cumulative charge from influx database
query_result = ifclient.query ('SELECT ("Cum Battery Current") from "home"."autogen"."PWRgate" ORDER BY DESC LIMIT 1')
query_lines = query_result.get_points()
print ("Reading query")
for query_line in query_lines:
	print ("Time: %s, Cum Current %i" % (query_line['time'],query_line['Cum Battery Current']))
	CumCurrent = query_line['Cum Battery Current']
	print ("CumCurrent=" + str(query_line['Cum Battery Current']))
