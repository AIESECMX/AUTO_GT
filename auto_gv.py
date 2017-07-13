#this mprogram is an miplementation that will look in the opportunitities for GV that were
#open in the last week and will consult the list of active gt eps in GetRepose for GV

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
	
	#getting opps ids
	education = get_opps(expa_token,config.sdgs["education"])
	gender_eq = get_opps(expa_token,config.sdgs["gender_eq"])
	decent_work = get_opps(expa_token,config.sdgs["decent_work"])
	inequalities = get_opps(expa_token,config.sdgs["inequalities"])
	climate = get_opps(expa_token,config.sdgs["climate"])
	partnerships = get_opps(expa_token,config.sdgs["partnerships"])

	opps= {}
	countries = {}

	url = 'https://gis-api.aiesec.org/v2/opportunities/'

	#getting opportunities
	partnerships_op = json.loads(requests.get(url+str(partnerships)+'.json?access_token='+expa_token).text)
	education_op = json.loads(requests.get(url+str(education)+'.json?access_token='+expa_token).text)
	gender_eq_op = json.loads(requests.get(url+str(gender_eq)+'.json?access_token='+expa_token).text)
	decent_work_op = json.loads(requests.get(url+str(decent_work)+'.json?access_token='+expa_token).text)
	inequalities_op = json.loads(requests.get(url+str(inequalities)+'.json?access_token='+expa_token).text)
	climate_op = json.loads(requests.get(url+str(climate)+'.json?access_token='+expa_token).text)

	opps['partnerships_op'] = partnerships_op
	opps['education_op'] =education_op
	opps['gender_eq_op'] = gender_eq_op
	opps['decent_work_op'] =decent_work_op
	opps['inequalities_op'] =inequalities_op
	opps['climate_op'] = climate_op

	#getting opportunities countries
	partnerships_country = json.loads(requests.get('https://gis-api.aiesec.org/v2/committees/'+str(partnerships_op['home_lc']['id'])+'.json?access_token='+expa_token).text)['parent']['name']
	education_country = json.loads(requests.get('https://gis-api.aiesec.org/v2/committees/'+str(education_op['home_lc']['id'])+'.json?access_token='+expa_token).text)['parent']['name']
	gender_eq_country = json.loads(requests.get('https://gis-api.aiesec.org/v2/committees/'+str(gender_eq_op['home_lc']['id'])+'.json?access_token='+expa_token).text)['parent']['name']
	decent_work_country = json.loads(requests.get('https://gis-api.aiesec.org/v2/committees/'+str(decent_work_op['home_lc']['id'])+'.json?access_token='+expa_token).text)['parent']['name']
	inequalities_country = json.loads(requests.get('https://gis-api.aiesec.org/v2/committees/'+str(inequalities_op['home_lc']['id'])+'.json?access_token='+expa_token).text)['parent']['name']
	climate_country = json.loads(requests.get('https://gis-api.aiesec.org/v2/committees/'+str(climate_op['home_lc']['id'])+'.json?access_token='+expa_token).text) ['parent']['name']

	countries['partnerships_country'] = partnerships_country
	countries['education_country'] = education_country
	countries['gender_eq_country'] = gender_eq_country
	countries['decent_work_country'] = decent_work_country
	countries['inequalities_country'] = inequalities_country
	countries['climate_country'] =climate_country


	get_eps_gr_1(opps = opps,countries = countries)
	
#this gets opportunities form te last week form expa using the yop token
def get_opps(aiesec_token, sdg):
	headersx={'access_token': aiesec_token}
	url = "https://gis-api.aiesec.org/v2/opportunities.json"
	yesterday = datetime.date.today()-datetime.timedelta(6)
	params = {
	"access_token" :aiesec_token,
	'filters[programmes][]':[1],#gv
	'filters[sdg_goals][]':[sdg],
	"filters[home_mcs][]":config.gv_countries,
	#"filters[work_fields][]":[724,742],
	"filters[created][to]" : datetime.date.today().strftime('%Y-%m-%d'),
	"sort":"filters[created][to]"
	}
	q = requests.get(url, params=params)
	
	#print q.text
	ops_expa= json.loads(q.text)['data']

	return ops_expa[0]['id']
	


#this method gets eps from get reponse to match them with the opps and then update their profiles
def get_eps_gr_1(opps ,countries ):
	eps = None
	#dates form today and 3 months ago
	day = 3
	while day < 90 :
		#just egtting the eps in days 7*times to reduce requests
		created  = datetime.date.today()-datetime.timedelta(day)
		day += 7
		params = {
		'query[campaignId]' : config.ogv_gr_campaign_id,
		'query[createdOn][from]' : created.strftime('%Y-%m-%d'),
		'query[createdOn][to]' : created.strftime('%Y-%m-%d'),
		'fields' : ''
		}
		query = 'contacts'
		
		contacts  = gr.get_request(query,params = params)
		#print contacts
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
					send_opps(gr_id = ep['contactId'],opps = opps,countries = countries)
					#send the new opportunities to getresponse
			elif not is_applicant(custom_fields['expa_id'],ep['contactId']):
				send_opps(gr_id = ep['contactId'],opps = opps,countries = countries)
		#
		
#
def send_opps(gr_id,opps ,countries ):
	#get full ifor for the opps
	

	partnerships_op = opps['partnerships_op'] 
	education_op=opps['education_op'] 
	gender_eq_op=opps['gender_eq_op'] 
	decent_work_op = opps['decent_work_op'] 
	inequalities_op = opps['inequalities_op'] 
	climate_op = opps['climate_op'] 

	partnerships_country = countries['partnerships_country'] 
	education_country = countries['education_country'] 
	gender_eq_country = countries['gender_eq_country'] 
	decent_work_country = countries['decent_work_country'] 
	inequalities_country = countries['inequalities_country'] 
	climate_country = countries['climate_country'] 

	#print inequalities_op
	params = {
    "customFieldValues": [
    		#http_op_partnership
        	{"customFieldId": 'zDYzA',"value": ['https://opportunities.aiesec.org/opportunity/'+str(partnerships_op['id'])]},
        	#http_op_inequalitiesineering
        	{"customFieldId": 'zDYzc',"value": ['https://opportunities.aiesec.org/opportunity/'+str(inequalities_op['id'])]},
        	#http_op_teahcing
        	{"customFieldId": 'zDYzC',"value": ['https://opportunities.aiesec.org/opportunity/'+str(gender_eq_op['id'])]},
        	#http_op_ussines
        	{"customFieldId": 'zDYzx',"value": ['https://opportunities.aiesec.org/opportunity/'+str(climate_op['id'])]},
        	#http_op_decent_work
        	{"customFieldId": 'zDYzS',"value": ['https://opportunities.aiesec.org/opportunity/'+str(decent_work_op['id'])]},
        	#http_op_education
        	{"customFieldId": 'zDYEs',"value": ['https://opportunities.aiesec.org/opportunity/'+str(education_op['id'])]},
        	#titulo partnerships
        	{"customFieldId": 'zDYz7',"value": [partnerships_op['title']]},
        	#titulo inequalities
        	{"customFieldId": 'zDYzE',"value": [inequalities_op['title']]},
        	#titulo gender_eq
        	{"customFieldId": 'zDYzr',"value": [gender_eq_op['title']]},
        	#titulo climate
        	{"customFieldId": 'zDYz1',"value": [climate_op['title']]},
        	#titulo decent_work
        	{"customFieldId": 'zDYzh',"value": [decent_work_op['title']]},
        	#titulo education
        	{"customFieldId": 'zDYzK',"value": [education_op['title']]},
        	#desc partnerships
        	{"customFieldId": 'zDYzn',"value": [partnerships_op['description'][:250]]},
        	#desc inequalities
        	{"customFieldId": 'zDYzR',"value": [inequalities_op['description'][:250]]},
        	#description gender_eq
        	{"customFieldId": 'zDYzT',"value": [gender_eq_op['description'][:250]]},
        	#description climate
        	{"customFieldId": 'zDYzd',"value": [climate_op['description'][:250]]},
        	#description decent_work
        	{"customFieldId": 'zDYzp',"value": [decent_work_op['description'][:250]]},
        	#description education
        	{"customFieldId": 'zDYzz',"value": [education_op['description'][:250]]},
        	#country partnerships
        	{"customFieldId": 'zDYzb',"value": [partnerships_country]},
        	#country inequalities
        	{"customFieldId": 'zDYzy',"value": [inequalities_country]},
        	#coutry gender_eq
        	{"customFieldId": 'zDYz5',"value": [gender_eq_country]},
        	#country climate
        	{"customFieldId": 'zDYzf',"value": [climate_country]},
        	#country decent_work
        	{"customFieldId": 'zDYzw',"value": [decent_work_country]},
        	#country education
        	{"customFieldId": 'zDYzJ',"value": [education_country]}
 	   	]
	}
	test = gr.post_requests('/contacts/'+str(gr_id)+'/custom-fields',data=params)
	#print 'aqui se hicieron las madre estas de las practicas par auna usarios'	
	#print params
	#print test.text

#this method check if the profile is complete in expa and if its then it notifyies get response
def is_profile_complete(expa_id,gr_id,):
	print 'checando perfil completo de :'+str(expa_id)
	url = 'https://gis-api.aiesec.org/v2/people/'+str(expa_id)+'.json?access_token='+expa_token
	q = requests.get(url)
	#print q.status_code
	ep = json.loads(q.text)
	if 'missing_profile_fields' in ep:
		if len(ep['missing_profile_fields']) == 0:
			#set profile complete as true
			params = {
		    "customFieldValues": [

		        	
		        	{"customFieldId": 'zDY1V',"value": ['yes']}
		 	   	]
			}
			test  = gr.post_requests('/contacts/'+str(gr_id)+'/custom-fields',data=params)
			print 'perfil completo'
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
		print 'ya es palicante'
		
		return True
	return False


#	the main method	
def main():
	#this methos starts the full excecution of autogt
	notify_new_opps(yop_token)
	#get_opps(yop_token,1104)
	#print  gr.get_request('custom-fields')
	


#
if __name__ == "__main__":
	main()

