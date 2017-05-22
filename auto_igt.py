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
ipAddress = socket.gethostbyname(socket.gethostname())
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
	#here we have tocheck if the ep and the opp are background aligned
	
	for app in apps:
		
		op = getOP(app['opportunity']['id'])
		
		#getting the ep from expa
		ep = getApplicant(app['opportunity']['id'],app['person']['id'])
		sendEPGR(ep,op)
	#cuantas paginas de applicaciones hay que pedir
	#check if there are apps still to process
	extra_pages = message['paging']['total_pages']
	if page < extra_pages:
		getApps(page = page+1)





#sending eps to gr
def sendEPGR(ep,op):
	ep_background = getEpBackground(ep)
	op_background = getOpBackground(op)
	#business_administration, engineering, information_technology, marketing, teaching
	b = 'business_administration'
	if ep_background == IT:
		b = 'information_technology'
	elif ep_background == MKT:
		b = 'marketing'
	elif ep_background == TEACH:
		b = 'teaching'
	elif ep_background == ENG:
		b = 'engineering'
	elif ep_background == BA:
		b = 'business_administration'

	#compatible
	comp = 'no'
	if  ep_background == op_background:
		comp = 'si'

	ep_gr = {
	    "name": ep['full_name'],
	    "email": ep['email'],
	    "dayOfCycle": "0",
	    "campaign": {
	        "campaignId": config.igt_gr_campaign_id
	    },
	    "customFieldValues": [
	        {
	            "customFieldId": 'zU3vv', #expa id
	            "value": [
	                ep['id']
	            ]
	        },
	        {
	            "customFieldId": 'zDYzj',#background_igt
	            "value": [
	                b
	            ]
	        },
	        {
	            "customFieldId": 'zDYTS',#background_check
	            "value": [
	                comp
	            ]
	        }
	    ],
	    "ipAddress": str(ipAddress)
		}
	gr.post_requests('/contacts',data=ep_gr)

#this method tells if the ep background is in IT, eng, ....
def getEpBackground(ep):
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

#this mathod gets the eps from gr  and gets the newest opps forom expa for a profile
def getEPSGR():
	#todo get the opportunities from EXPA
	ops_it = getOpportunities(IT)
	ops_teach = getOpportunities(TEACH)
	ops_eng = getOpportunities(ENG)
	ops_mkt = getOpportunities(MKT)
	ops_ba = getOpportunities(BA)
	eps = None
	#dates form today and 3 months ago
	day = 0
	while day < 90 :
		#just egtting the eps in days 7*times to reduce requests
		created  = datetime.date.today()
		day += 7
		params = {
		'query[campaignId]':config.igt_gr_campaign_id,
		'query[createdOn][from]':created.strftime('%Y-%m-%d'),
		'query[createdOn][to]':created.strftime('%Y-%m-%d'),
		'fields':''
		}
		query = 'contacts'
		
		contacts  = gr.get_request(query,params = params)

		l = json.loads(contacts)
		non_applicants = []
		for ep in l :
			#print 'imprimiendo usarios de algo '
			#print ep
			custom_fields = {}
			ep_aux =  json.loads(gr.get_request(query+'/'+ep['contactId']))
			for cf in  ep_aux['customFieldValues']:
				custom_fields[cf['name']] = cf['value'][0]
						#check if the ep has a complete profile
			#check oportunitites and if there are actually new opportunities to send, 
			#send to GR and update the flag
			if 'background_igt' in custom_fields:
				if ((custom_fields['background_igt'] == 'business_administration' and ops_ba == None)  or
					(custom_fields['background_igt'] == 'engineering' and ops_eng== None) or
					(custom_fields['background_igt'] == 'information_technology' and ops_it== None) or
					(custom_fields['background_igt'] == 'marketing' and ops_mkt== None) or 
					(custom_fields['background_igt'] == 'teaching' and ops_teach== None) ):
					continue
			if not is_accepted(custom_fields['expa_id'],ep['contactId']):
				print 'se supone que vamos a mandar '
				print ep
				if custom_fields['background_igt'] == 'business_administration'  :
					print 'mandando : ba'
					send_opps(gr_id = ep['contactId'],opps =  ops_ba)
				elif custom_fields['background_igt'] == 'engineering' :
					print 'mandando : eng'
					send_opps(gr_id = ep['contactId'],opps =  ops_eng)
				elif custom_fields['background_igt'] == 'information_technology' :
					print 'mandando : it'
					send_opps(gr_id = ep['contactId'],opps =  ops_it)
				elif custom_fields['background_igt'] == 'marketing' :
					print 'mandando : mkt'
					send_opps(gr_id = ep['contactId'],opps =  ops_mkt)
				elif custom_fields['background_igt'] == 'teaching': 
					print 'mandando : teach'
					send_opps(gr_id = ep['contactId'],opps =  ops_teach)
		#

#this method sends the opps to GR for the specific user
def send_opps(gr_id,opps):

	#print eng_op
	params = {
    "customFieldValues": [
        	#http_op_igt_1
        	{"customFieldId": 'zDYTs',"value": ['https://opportunities.aiesec.org/opportunity/'+str(opps[0]['id'])]},
        	#http_op_igt_2
        	{"customFieldId": 'zDYT8',"value": ['https://opportunities.aiesec.org/opportunity/'+str(opps[1]['id'])]},
        	#titulo_igt_1
        	{"customFieldId": 'zDYTa',"value": [opps[0]['title']]},
        	#titulo_igt_2
        	{"customFieldId": 'zDYTG',"value": [opps[1]['title']]},
        	#descripcion_igt_1
        	{"customFieldId": 'zDYT0',"value": [opps[0]['description'][:250]]},
        	#descripcion_igt_2
        	{"customFieldId": 'zDYTq',"value": [opps[1]['description'][:250]]},
        	#opp_ciudad_1
        	{"customFieldId": 'zDYTv',"value": [opps[0]['country']]}
        	#opp_ciudad_2
        	{"customFieldId": 'zDYTi',"value": [opps[1]['teach_country']]},
        	#notify there are new apps
        	{"customFieldId": 'zDYRL',"value": 'yes'}
 	   	]
	}
	test = gr.post_requests('/contacts/'+str(gr_id)+'/custom-fields',data=params)

#this method get opps based on the background 
def getOpportunities(background):
	#map one opp per porgram 
	backgrounds = open('backgrounds.json','r')
	programs = json.loads(backgrounds.read())['data']
	backs = []
	if background == IT:
		backs  = programs['IT']
	elif background == MKT:
		backs = programs['Marketing']
	elif background == ENG:
		backs = programs['Engineering']
	elif background == BA:
		backs = programs['Business Administration']
	else:
		backs = programs['Teaching']

	#this gets opportunities form te last week form expa using the yop token
	url = "https://gis-api.aiesec.org/v2/opportunities.json"
	yesterday = datetime.date.today()-datetime.timedelta(14)
	params = {
	"access_token" :expa_token,
	'filters[programmes][]':[2],
	'filters[backgrounds][][id]':backs,
	'filters[status]':'open',
	"filters[home_mcs][]":[1589],
	"filters[created][from]" : yesterday.strftime('%Y-%m-%d'),
	"sort":"created_at"
	}
	q = requests.get(url, params=params)
	#print q.status_code
	ops_expa= json.loads(q.text)['data']
	
	if len(ops_expa) < 2:
		return None
	else:
		a = json.loads(requests.get('https://gis-api.aiesec.org/v2/opportunities/'+str(ops_expa[0]['id'])+'.json?access_token='+expa_token).text)
		a_c = json.loads(requests.get('https://gis-api.aiesec.org/v2/committees/'+str(a['home_lc']['id'])+'.json?access_token='+expa_token).text)['parent']['name']
		a['country'] = a_c
		ops = [a]

		return ops

#check if an ep is already accepted		
def is_accepted(expa_id,gr_id):
#this method check if the ep is already applying to something in expa dn inf it is it marks it as accepted in getresponse
	url = 'https://gis-api.aiesec.org/v2/people/'+str(expa_id)+'.json?access_token='+expa_token
	q = requests.get(url)
	#print q.text
	ep = json.loads(q.text)

	if ep['status'] == 'accepted' or ep['status'] == 'completed' or ep['status'] == 'realized': 
		#set profile complete as true
		params = {
	    "customFieldValues": [
	        	
	        	{"customFieldId": 'zDYTc',"value": ['yes']}
	 	   	]
		}
		test = gr.post_requests('/contacts/'+str(gr_id)+'/custom-fields',data=params)
		

		return True
	return False


#the main method
def main():
	#get the new apps of the previous day and check their compatibilty, add new interested to the list and
	#send the contact to those who match background with opps
	#getApps()
	#print  gr.get_request('custom-fields')
	#gets the eps from gr that are to be updated today,
	#check if they are in accepted and if so take them out of the flow, else
	#check for their backgrounds, get the 5 most recent opps
	#and put their profiles in GR
	getEPSGR()
	#getOpportunities(IT)



# ejecucion 
if __name__ == "__main__":
	main()