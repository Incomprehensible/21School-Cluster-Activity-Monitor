from enum import IntEnum
from intra import IntraAPIClient
import json
from intra import ic
import pprint
import pandas as pd


# 89 ALP
# 90 CAP
# 91 SAL
# 92 MED

# class C_status(IntEnum):
# 	EMP = 88
# 	ALP = 89
# 	CAP = 90
# 	SAL = 91
# 	MED = 92

def coalition_by_name_intra(login):
	payload = {
	   "filter[login]":[login]
	}
	response = ic.get("users", params = payload)
	coalition_id = 0
	if response.status_code == 200: # Make sure response status is OK
		data = response.json()
	if (len(data) > 0):
		id = data[0]["id"]
		response = ic.get("users/" + str(id) + "/coalitions")
		if response.status_code == 200: # Make sure response status is OK
			data = response.json()
		if (len(data) > 0):
			for i in range(len(data)):
				if (data[i]["id"] in [89 ,90, 91, 92]):
					coalition_id = data[i]["id"]
					coalition_name = data[i]["name"]
	return coalition_id

def coalition_by_name(login):

	df = pd.read_csv("logins.csv", names=["login","coalition"])
	if (len(df[df["login"]==login]) != 0):
		result = df[df["login"]==login]
		return(int(result["coalition"]))
	else:
		result = coalition_by_name_intra(login)
		size = df["login"].size
		df.loc[size] = [login, result]
		df.to_csv('logins.csv', header = False)
		return (result)

