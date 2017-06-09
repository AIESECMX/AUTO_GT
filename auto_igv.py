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
	'filters[programmes][]':[1] # solo para gv
	}

#SDGS

#SDGs
EDU = "education"
HEALTH = "health"
INEQU = "inequalities"
CLIMATE = "climate"
PARTNER = "partnerships"

sdgs_igv = {
		'health':1103,
		'education':1104,
		'inequalities':1110,
		'climate':1113,
		'partnerships':1117
}

#nurturing para IGV
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
	op_man_1 = op['managers'][0]['full_name']
	op_man__mail_1 = op['managers'][0]['email']
	sdg = 'sdg4'


	if op['sdg_info'] != None:
		if  op['sdg_info']['sdg_target']['goal_id'] == 1104:
			sdg = 'sdg4'
		elif  op['sdg_info']['sdg_target']['goal_id'] == 1105:
			sdg = 'sdg5'
		elif  op['sdg_info']['sdg_target']['goal_id'] == 1108:
			sdg = 'sdg8'
		elif  op['sdg_info']['sdg_target']['goal_id'] == 1110:
			sdg = 'sdg10'
		elif  op['sdg_info']['sdg_target']['goal_id'] == 1113:
			sdg = 'sdg13'
		elif  op['sdg_info']['sdg_target']['goal_id'] == 1117:
			sdg = 'sdg17'

	ep_gr = {
	    "name": ep['full_name'],
	    "email": ep['email'],
	    "dayOfCycle": "0",
	    "campaign": {
	        "campaignId": config.igv_gr_campaign_id
	    },
	    "customFieldValues": [
	        {"customFieldId": 'zU3vv', "value": [ep['id']]},#expa id
	        #todo check custom field for new app in ordedr to let know there are new contacts
	        {"customFieldId": 'zDYTS',"value": ['yes']},#to check if there are new contacts to send
			{"customFieldId": 'zDYz3',"value": [op_man_1]},#manager 1 name
	        {"customFieldId": 'zDYTC',"value": [op_man__mail_1]},#manager 1 mail
	        {"customFieldId": 'zDYKE',"value": [op['title']]},#opp name
	        {"customFieldId": 'zDYdh',"value": [sdg]},#sdg applied
	        {"customFieldId": 'zDYKz',"value": ['https://opportunities.aiesec.org/opportunity/'+str(op['id'])]}#oppp link

	    ],
	    "ipAddress": str(ipAddress)
		}
	
	r = gr.post_requests('/contacts',data=ep_gr)
	print r

	#this means that the Ep was already in GR and we are just sending the contacts of tthe new application 

	if 'message' in r:
		params = {
		'query[campaignId]':config.igv_gr_campaign_id,
		'query[email]':ep['email'],
		'fields':''
		}
		query = 'contacts'
		contacts  = gr.get_request(query,params = params)
		l = json.loads(contacts)
		gr_id = ''
		for ep in l :
			gr_id =  ep['contactId']
		#this means that this is a new aplication for some ep that is already in get reponse and we will send
		#the contacst of their new possible match

		if gr_id != '' :
			#print eng_op
			params = {
		    "customFieldValues": [
			        {"customFieldId": 'zDYTS',"value": ['yes']},#To check if there is new contact to send
					{"customFieldId": 'zDYz3',"value": [op_man_1]},#manager 1 name
			        {"customFieldId": 'zDYTC',"value": [op_man__mail_1]},#manager 1 mail
			        {"customFieldId": 'zDYKE',"value": [op['title']]},#opp name
			        {"customFieldId": 'zDYdh',"value": [sdg]},#sdg applied
	        		{"customFieldId": 'zDYKz',"value": ['https://opportunities.aiesec.org/opportunity/'+str(op['id'])]}#oppp link
		 	   	]
			}
			gr.post_requests('/contacts/'+str(gr_id)+'/custom-fields',data=params)


#gets an ep form exa with their id
def getApplicant(op_id,ep_id ):
	#q = requests.get('https://gis-api.aiesec.org/v2/opportunities/'+str(op_id)+'.json?access_token='+expa_token)
	ep = json.loads(requests.get('https://gis-api.aiesec.org/v2/opportunities/'+str(op_id)+'/applicant.json?person_id='+str(ep_id)+'&access_token='+expa_token).text)
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



	#Getting the opportunities by SGD form expa
	ops_edu = getOpportunities(EDU)
	ops_health = getOpportunities(HEALTH)
	ops_ineq = getOpportunities(INEQU)
	ops_climate = getOpportunities(CLIMATE)
	ops_part = getOpportunities(PARTNER)
	eps = None
	#dates form today and 2 months ago
	day = 3
	while day < 60 :
		#just egtting the eps in days 7*times to reduce requests
		created = datetime.date.today()-datetime.timedelta(day)
		day += 7
		params = {
		'query[campaignId]':config.igv_gr_campaign_id,
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
						
			#check oportunitites and if there are actually new opportunities to send, 
			#send to GR and update the flag
			if 'sdg_check' in custom_fields:
				if ((custom_fields['sdg_check'] == 'sdg4' and ops_edu == None)  or
					(custom_fields['sdg_check'] == 'sdg3' and ops_health== None) or
					(custom_fields['sdg_check'] == 'sdg10' and ops_ineq== None) or
					(custom_fields['sdg_check'] == 'sdg17' and ops_part== None) or 
					(custom_fields['sdg_check'] == 'sdg13' and ops_climate== None) ):
					continue
			if not is_accepted(custom_fields['expa_id'],ep['contactId']):
				if custom_fields['sdg_check'] == 'sdg4' :
					send_opps(gr_id = ep['contactId'],opps =  ops_edu)
				elif custom_fields['sdg_check'] == 'sdg3' :
					send_opps(gr_id = ep['contactId'],opps =  ops_health)
				elif custom_fields['sdg_check'] == 'sdg10' :
					send_opps(gr_id = ep['contactId'],opps =  ops_ineq)
				elif custom_fields['sdg_check'] == 'sdg17': 
					send_opps(gr_id = ep['contactId'],opps =  ops_part)
				elif custom_fields['sdg_check'] == 'sdg13': 
					send_opps(gr_id = ep['contactId'],opps =  ops_climate)
		#

#this method sends the opps to GR for the specific user
def send_opps(gr_id,opps):
	#print eng_op
	params = {
    "customFieldValues": [
        	#http_op_igv_1
        	{"customFieldId": 'zDYp7',"value": ['https://opportunities.aiesec.org/opportunity/'+str(opps[0]['id'])]},
        	#http_op_igv_2
        	{"customFieldId": 'zDYpz',"value": ['https://opportunities.aiesec.org/opportunity/'+str(opps[1]['id'])]},
        	#titulo_igv_1
        	{"customFieldId": 'zDYpd',"value": [opps[0]['title']]},
        	#titulo_igv_2
        	{"customFieldId": 'zDYpn',"value": [opps[1]['title']]},
        	#descripcion_igv_1
        	{"customFieldId": 'zDYpw',"value": [opps[0]['description'][:250]]},
        	#descripcion_igv_2
        	{"customFieldId": 'zDYpy',"value": [opps[1]['description'][:250]]},
        	#opp_ciudad_1
        	{"customFieldId": 'zDYTv',"value": [opps[0]['location']]},
        	#opp_ciudad_2
        	{"customFieldId": 'zDYTi',"value": [opps[1]['location']]},
        	#notify there are new apps
        	{"customFieldId": 'zDYRL',"value": 'yes'}
 	   	]
	}
	test = gr.post_requests('/contacts/'+str(gr_id)+'/custom-fields',data=params)

#this method get opps based on the background 
def getOpportunities(sdg):

	#this gets opportunities form te last week form expa using the yop token
	url = "https://gis-api.aiesec.org/v2/opportunities.json"
	yesterday = datetime.date.today()-datetime.timedelta(14)
	params = {
	"access_token" :expa_token,
	'filters[programmes][]':[1],#igv
	#todo change this for sdgs
	'filters[sdg_goals][]':[config.sdgs[sdg]],
	'filters[status]':'open',
	'filters[home_mcs][]':[1589],
	'filters[created][from]' : yesterday.strftime('%Y-%m-%d'),
	'sort':'created_at'
	}
	q = requests.get(url, params=params)
	#print q.status_code
	ops_expa= json.loads(q.text)['data']
	
	if len(ops_expa) < 2:
		print 'no ops'
		return None
	else:
		a_r = requests.get('https://gis-api.aiesec.org/v2/opportunities/'+str(ops_expa[0]['id'])+'.json?access_token='+expa_token).text
		a = json.loads(a_r)
		b_r = requests.get('https://gis-api.aiesec.org/v2/opportunities/'+str(ops_expa[1]['id'])+'.json?access_token='+expa_token).text
		b = json.loads(b_r)
		return [a,b]
		

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



###IGT
###IGT




#the main method
def main():
	#get the new apps of the previous day and check their compatibilty, add new interested to the list and
	#send the contact to those who match background with opps
	getApps()
	#print  gr.get_request('custom-fields')
	#testduplicados()
	#gets the eps from gr that are to be updated today,
	#check if they are in accepted and if so take them out of the flow, else
	#check for their backgrounds, get the 5 most recent opps
	#and put their profiles in GR
	getEPSGR()
	




# ejecucion 
if __name__ == "__main__":
	main()