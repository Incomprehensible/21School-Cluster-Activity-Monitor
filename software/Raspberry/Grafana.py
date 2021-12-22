import requests
import json
from credentials import HOST, API_KEY
from rpi_DB import Status
from coalition_utils import coalition_by_name
from pprintpp import pprint

# mi-g6.msk.21-school.ru: empty
# ox-o4.msk.21-school.ru: empty
# at-k8.msk.21-school.ru: empty
# ga-o4.msk.21-school.ru: empty

class Grafana:
    def __init__(self, db):
        self.db = db
        self.headers = {'Authorization': 'Bearer %s' % (API_KEY,)}
        self.clusters = {'oa' : 'oasis', 'il' : 'illusion', 'mi' : 'mirage', 'at' : 'atlantis', 'am' : 'atrium'}
    
    def get_metrics_c_mode(self):
        data_url ='/api/datasources/proxy/1/api/v1/query?query=iMacUser_status{instance=~\".*\"}'
        r = requests.get('%s%s' % (HOST, data_url,), headers=self.headers)
        print("rrrrrrr:", r)
        data = r.json()
        print('getting metrics')
        for each in data['data']['result']:
            data = each['metric']['instance']
            mac = data.split(".")[0]
            cluster = mac.split("-")[0]
            mac = mac.split("-")[1]
            login = each['metric']['login']
            cluster = self.clusters.get(cluster)
            if cluster == None:
                continue
            if login == 'empty':
                status = 88
            else:
                status = coalition_by_name(login)
            if (status != 88):
                print (status)
            status = status - 83
            self.db.change_mac_status(cluster, mac, int(status))
        ### switch off leds for macs that are phisically turned off but untracked by prometheus
        self.db.change_mac_status("oasis", "g1", 5)
        self.db.change_mac_status("mirage", "e1", 5)
        self.db.change_mac_status("atlantis", "l2", 5)

    def get_metrics(self):
        data_url ='/api/datasources/proxy/1/api/v1/query?query=iMacUser_status{instance=~\".*\"}'
        r = requests.get('%s%s' % (HOST, data_url,), headers=self.headers)
        data = r.json()
        data2 = data
        print('getting metrics')
        for each in data['data']['result']:
            data = each['metric']['instance']
            mac = data.split(".")[0]
            cluster = mac.split("-")[0]
            mac = mac.split("-")[1]
            if (cluster == "oa" and mac == "g1"):
                pprint(data, width=1)
            login = each['metric']['login']
            if (login == "lajudy" or login == "rmander"):
                pprint(each)
            cluster = self.clusters.get(cluster)
            if cluster == None:
                continue
            #status = Status.USED
            if login == 'empty':
                status = Status.FREE
            self.db.change_mac_status(cluster, mac, int(status))
        self.get_exams()

    def get_exams(self):
        data_url ='/api/datasources/proxy/1/api/v1/query?query=iMacExam_status{instance=~\".*\"}'
        r = requests.get('%s%s' % (HOST, data_url,), headers=self.headers)
        data = r.json()
        print('getting exams')
        for each in data['data']['result']:
            if each['value'][1] == '0':
                continue
            data = each['metric']['instance']
            mac = data.split(".")[0]
            cluster = mac.split("-")[0]
            mac = mac.split("-")[1]
            cluster = self.clusters.get(cluster)
            if cluster == None:
                continue
            status = Status.EXAM
            self.db.change_mac_status(cluster, mac, int(status))


