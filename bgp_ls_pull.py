import httplib2
import json,urllib.request as ur
import requests
import sys
import logging

ODL_IP="192.168.24.129"
ODL_PORT="8181"
ODL_USERNAME="admin"
ODL_PASSWORD="admin"
base_url = "http://198.18.1.80:8181/restconf/operational/network-topology:network-topology"
JSON_FILE_NAME="bgp_ls_topo_data.json"


response= requests.get(base_url,auth=requests.auth.HTTPBasicAuth(ODL_USERNAME,ODL_PASSWORD))
json_data=json.loads(response.text)
with open(JSON_FILE_NAME,'w') as f:
        json.dump(json_data,f,indent=2)


'''
h = httplib2.Http(".cache")
h.add_credentials(ODL_USERNAME, ODL_PASSWORD)
resp,content = h.request(baseUrl,"GET")
topo=json.loads(content.decode('utf-8'))
print (topo)
'''
