import requests
import config
import json
import datetime
import urllib
import urllib2
import cookielib
import logging
import socket
from ep import EP
from opp import OP
import sys
sys.path.append("../")
from gis_token_generator import GIS
from get_response import GetResponse
#CONFIG VARS start
#CONFIG VARS start
#names for profiles
IT = 101
ENG = 102
TEACH = 103
MKT = 104
BA = 105
#the get reponbse instace for us to work
gr = GetResponse()
token_genrator = GIS()
ipAddress = getIP()
expa_token = token_genrator.generate_token(config.user_mail,config.user_pass)
yop_token = token_genrator.generate_op_token(config.user_mail,config.user_pass)
yesterday = datetime.date.today()-datetime.timedelta(1)
headers = {'access_token': expa_token,
	'filters[created_at][from]':yesterday.strftime('%Y-%m-%d'),
	'filters[created_at][to]':yesterday.strftime('%Y-%m-%d'),
	'page':1,
	'filters[status]':'open',
	'filters[opportunity_committee]':config.MEXICO, # solo las de mexico 
	'filters[programmes][]':2 # solo para gt
	}

#the backgrounds per profile
backs = open('backgrounds.json','r')
backgrounds = json.loads(backs.read())['data']
#nurturing para ICX
#checar las nuevas apps que haya con correos que no esten repetidos

#when there are multiple pages this method wil 
#recieve the number of page to request and then it will process all the apps
def getApps(page = 1):
	headersx = headers
	headersx['page']=page
	h = {'Accept': 'application/json'}
	r = requests.get("https://gis-api.aiesec.org/v2/applications", params=headersx,data = h)
	#print r.text
	message = json.loads(r.text)
	apps = message['data']
	#here we have tocheck if the ep and the opp are background aligned #TODO
	
	for app in apps:
		
		op = getOP(app['opportunity']['id'])
		
		#getting the ep from expa
		ep = getApplicant(app['opportunity']['id'],app['person']['id'])
		#TODO send ep ep to get response
		sendEPGR(ep)
		ep_background = getEpBackground(ep)
		op_background = getOpBackground(op)
		#todo send background to GR
		sendBackgroundGR(ep,ep_background)
		sendOPsGR(ep,ep_background)
		if  ep_background == op_background:
			print 'ep:'+str(app['person']['id'])+' SIII es compatible con op: '+str(app['opportunity']['id'])
			print 'ep:'+str(ep_background)+' op: '+str(op_background)
			setCompatibleGR(ep,op)

	#cuantas paginas de applicaciones hay que pedir
	#check if there are apps still to process
	extra_pages = message['paging']['total_pages']
	if page < extra_pages:
		getApps(page = page+1)

#this method will send opportunities to GR based on the background of the ep
def sendOPsGR(ep,ep_background):
	#todo
	return None

#this method sets the eo with a compatible flag and with the contacts in GR
def setCompatibleGR(ep,op):
	#TODO send to get response the field 
	return None

#TODO send the EP to GR
def sendEPGR(ep):
	ep_gr = {
	    "name": "Jan Kowalski",
	    "email": "jan.kowalski@wp.pl",
	    "dayOfCycle": "10",
	    "campaign": {
	        "campaignId": "jf7e3jn"
	    },
	    "customFieldValues": [
	        {
	            "customFieldId": "n",
	            "value": [
	                "white"
	            ]
	        }
	    ],
	    "ipAddress": str(ipAddress)
		}	
	return None 

#this method tells if the ep background is in IT, eng, ....
def getEpBackgroundGR(ep):
	if 'backgrounds' in ep['profile']:
		if len(ep['profile']['backgrounds']) == 0:
			return TEACH

	if ep['profile']['backgrounds'][0]['id'] in backgrounds['IT']:
		return IT
	if ep['profile']['backgrounds'][0]['id'] in backgrounds['Engineering']:
		return ENG
	if ep['profile']['backgrounds'][0]['id'] in backgrounds['Marketing']:
		return MKT
	if ep['profile']['backgrounds'][0]['id'] in backgrounds['Business Administration']:
		return BA
	return TEACH 

#this method tells if the ep background is in IT, eng, ....
def getOpBackground(op):
	if 'backgrounds' in op: 
		if len(op['backgrounds']) == 0:
			return TEACH

	if op['backgrounds'][0]['id'] in backgrounds['IT']:
		return IT
	if op['backgrounds'][0]['id'] in backgrounds['Engineering']:
		return ENG
	if op['backgrounds'][0]['id'] in backgrounds['Marketing']:
		return MKT
	if op['backgrounds'][0]['id'] in backgrounds['Business Administration']:
		return BA
	return TEACH

#gets an ep form exa with their id
def getApplicant(op_id,ep_id ):
	#q = requests.get('https://gis-api.aiesec.org/v2/opportunities/'+str(op_id)+'.json?access_token='+expa_token)
	q = requests.get('https://gis-api.aiesec.org/v2/opportunities/'+str(op_id)+'/applicant.json?person_id='+str(ep_id)+'&access_token='+expa_token)
	ep = json.loads(q.text)
	return ep

#gets an op form exa with their id
def getOP(op_id ):	
	#getting the opportunites itself
	op = json.loads(requests.get('https://gis-api.aiesec.org/v2/opportunities/'+str(op_id)+'.json?access_token='+expa_token).text)
	return op

#identificar si el ep ya esta en accepted
#identificar si hacen match con el background de su aplicacion y enviar datos de contacto si si lo hace (a gr)
#revisar el background del perifl y mandarlo a GR
#pedir a nuevas oportunidades de mexico y enviarlas a gr

#to get the IP adress
def getIP():
	return socket.gethostbyname(socket.gethostname())


#the main method
def main():
	#get the new apps of the previous day and check their compatibilty, add new interested to the list and
	#send the contact to those who match background with opps
	getApps()

	#gets the eps from gr that are to be updated today,
	#check if they are in accepted and if so take them out of the flow, else
	#check for their backgrounds, get the 5 most recent opps
	#and put their profiles in GR
	#getEPSGR()



# ejecucion 
if __name__ == "__main__":
	main()