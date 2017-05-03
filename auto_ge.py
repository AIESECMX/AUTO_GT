#this mprogram is an miplementation that will look in the opportunitities for GT that were
#open in the last week and will consult the list of active gt eps in GetRepose for GT

import requests
import config
import json
import datetime
import urllib
import urllib2
import cookielib
import logging
from ep import EP
from opp import OP
import sys
sys.path.append("../")
from gis_token_generator import GIS
from get_response import GetResponse
#CONFIG VARS start
#CONFIG VARS start

#the get reponbse instace for us to work
gr = GetResponse()
token_genrator = GIS()
expa_token = token_genrator.generate_token(config.user_mail,config.user_pass)
yop_token = token_genrator.generate_op_token(config.user_mail,config.user_pass)
#print 
#CONFIG VARS end
#CONFIG VARS end


#this method gets the opps of gt oppened in the last week and sends them to GR for the 
#apropiate profiles
## this is supposed to be run once a week to then notify Get reposnse 
def notify_new_opps(expa_token):

	
	#map one opp per porgram 
	backgrounds = open('backgrounds.json','r')
	programs = json.loads(backgrounds.read())['data']
	#IT
	
	#get_opps(expa_token,[224])
	peru = get_opps(expa_token,config.PERU)
	#Teaching
	colombia = get_opps(expa_token,config.COLOMBIA)
	#Engineering
	argentina = get_opps(expa_token,config.ARGENTINA)
	#Marketing
	costarica = get_opps(expa_token,config.COSTARICA)
	#Business Administration
	brasil = get_opps(expa_token,config.Brasil)
	get_eps_gr_1(peru_op=peru,colombia_op=colombia,argentina_op=argentina,costarica_op=costarica,brasil_op=brasil)
	
#this gets opportunities form te last week form expa using the yop token
def get_opps(aiesec_token,country = config.PERU):
	headersx={'access_token': aiesec_token}
	url = "https://gis-api.aiesec.org/v2/opportunities.json"
	yesterday = datetime.date.today()-datetime.timedelta(6)
	params = {
	"access_token" :aiesec_token,
	'filters[programmes][]':[5],#GE
	"filters[home_mcs][]":[country],
	"per_page":2,
	#"filters[work_fields][]":[724,742],
	"filters[created][to]" : datetime.date.today().strftime('%y-%m-%d'),
	"sort":"filters[created][to]"
	}
	q = requests.get(url, params=params)
	
	ops_expa= json.loads(q.text)['data']
	return ops_expa[0]['id']
	


#this method gets eps from get reponse to match them with the opps and then update their profiles
def get_eps_gr_1(peru_op,colombia_op,argentina_op,costarica_op,brasil_op):
	eps = None
	#dates form today and 3 months ago
	day = 3
	while day < 90 :
		#just egtting the eps in days 7*times to reduce requests
		created  = datetime.date.today()-datetime.timedelta(day)
		day += 7
		params = {
		'query[campaignId]':config.oge_gr_campaign_id,
		'query[createdOn][from]':created.strftime('%y-%m-%d'),
		'query[createdOn][to]':created.strftime('%y-%m-%d'),
		'fields':''
		}
		query = 'contacts'
		
		contacts  = gr.get_request(query,params = params)
		l = json.loads(contacts)
		non_applicants = []
		for ep in l :
			#print 'imprimiendo usarios de algo '
			#print ep
			ep_aux =  json.loads(gr.get_request(query+'/'+ep['contactId']))
			custom_fields = {}
			for cf in  ep_aux['customFieldValues']:
				custom_fields[cf['name']] = cf['value'][0]
						#check if the ep has a complete profile
			if 'perfil_completo' in custom_fields:
				if custom_fields['perfil_completo'] != 'yes':
					continue
			if not is_profile_complete(custom_fields['expa_id'],ep['contactId']):
				continue	
			#check if the ep is an apllicant in gr and check if the ep is applicant in expa
			if 'aplicante' in custom_fields:
				if custom_fields['aplicante'] != 'yes' :
					#send the new opportunities to getresponse
					send_opps(gr_id = ep['contactId'],peru=peru_op,colombia=colombia_op,argentina=argentina_op,costarica=costarica_op,brasil=brasil_op)
			elif not is_applicant(custom_fields['expa_id'],ep['contactId']):
				send_opps(gr_id = ep['contactId'],peru=peru_op,colombia=colombia_op,argentina=argentina_op,costarica=costarica_op,brasil=brasil_op)
				
		#
		
#
def send_opps(gr_id , peru , colombia , argentina , costarica , brasil):
	#get full ifor for the opps
	url = 'https://gis-api.aiesec.org/v2/opportunities/'
	peru_op = json.loads(requests.get(url+str(peru)+'.json?access_token='+expa_token).text)
	colombia_op = json.loads(requests.get(url+str(colombia)+'.json?access_token='+expa_token).text)
	argentina_op = json.loads(requests.get(url+str(argentina)+'.json?access_token='+expa_token).text)
	costarica_op = json.loads(requests.get(url+str(costarica)+'.json?access_token='+expa_token).text)
	brasil_op = json.loads(requests.get(url+str(brasil)+'.json?access_token='+expa_token).text)
	#print costarica_op
	params = {
    "customFieldValues": [
        	#http_op_costaricaineering
        	{"customFieldId": 'zDY7G',"value": ['https://opportunities.aiesec.org/opportunity/'+str(costarica)]},
        	#http_op_teahcing
        	{"customFieldId": 'zDY7L',"value": ['https://opportunities.aiesec.org/opportunity/'+str(colombia)]},
        	#http_op_ussines
        	{"customFieldId": 'zDY7o',"value": ['https://opportunities.aiesec.org/opportunity/'+str(brasil)]},
        	#http_op_argentina
        	{"customFieldId": 'zDY74',"value": ['https://opportunities.aiesec.org/opportunity/'+str(argentina)]},
        	#http_op_it
        	{"customFieldId": 'zDY72',"value": ['https://opportunities.aiesec.org/opportunity/'+str(peru)]},
        	#titulo costarica
        	{"customFieldId": 'zDY7q',"value": [costarica_op['title']]},
        	#titulo colombia
        	{"customFieldId": 'zDY7V',"value": [colombia_op['title']]},
        	#titulo brasil
        	{"customFieldId": 'zDY70',"value": [brasil_op['title']]},
        	#titulo argentina
        	{"customFieldId": 'zDY7X',"value": [argentina_op['title']]},
        	#titulo peru
        	{"customFieldId": 'zDY7m',"value": [peru_op['title']]},
        	#desc costarica
        	{"customFieldId": 'zDY7v',"value": [costarica_op['description'][:250]]},
        	#description colombia
        	{"customFieldId": 'zDY7B',"value": [colombia_op['description'][:250]]},
        	#description brasil
        	{"customFieldId": 'zDY7k',"value": [brasil_op['description'][:250]]},
        	#description argentina
        	{"customFieldId": 'zDY7i',"value": [argentina_op['description'][:250]]},
        	#description it
        	{"customFieldId": 'zDY73',"value": [peru_op['description'][:250]]}
 	   	]
	}
	#print params
	test = gr.post_requests('/contacts/'+str(gr_id)+'/custom-fields',data=params)
	#print 'aqui se hicieron las madre estas de las practicas par auna usarios'	
	#print params
	#print test.text

#this method check if the profile is complete in expa and if its then it notifyies get response
def is_profile_complete(expa_id,gr_id,):
	print 'checando perfil completo de :'+str(expa_id)
	url = 'https://gis-api.aiesec.org/v2/people/'+str(expa_id)+'.json?access_token='+expa_token
	q = requests.get(url)
	ep = json.loads(q.text)

	if len(ep['missing_profile_fields']) == 0:
		#set profile complete as true
		params = {
	    "customFieldValues": [

	        	
	        	{"customFieldId": 'zDY1V',"value": ['yes']}
	 	   	]
		}
		test  = gr.post_requests('/contacts/'+str(gr_id)+'/custom-fields',data=params)
		print 'lo del perfil completo'
		print 'yes'
		return True
	print 'no'
	return False
		
#this method check if the ep is already applying to something in expa dn inf it is it marks it as applicant in getresponse
def is_applicant(expa_id,gr_id):
	url = 'https://gis-api.aiesec.org/v2/people/'+str(expa_id)+'.json?access_token='+expa_token
	q = requests.get(url)
	ep = json.loads(q.text)

	if ep['status'] != 'open': 
		#set profile complete as true
		params = {
	    "customFieldValues": [
	        	#country it
	        	{"customFieldId": 'zDYEt',"value": ['yes']}
	 	   	]
		}
		test = gr.post_requests('/contacts/'+str(gr_id)+'/custom-fields',data=params)
		print 'lo de si ya es palicante'
		

		return True
	return False


#	the main method	
def main():
	#this methos starts the full excecution of autogt
	notify_new_opps(yop_token)
	#print  gr.get_request('custom-fields')
	


#
if __name__ == "__main__":
	main()
