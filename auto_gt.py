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
	it = get_opps(expa_token,programs['IT'])
	#Teaching
	teach = get_opps(expa_token,programs['Teaching'])
	#Engineering
	eng = get_opps(expa_token,programs['Engineering'])
	#Marketing
	mkt = get_opps(expa_token,programs['Marketing'])
	#Business Administration
	ba = get_opps(expa_token,programs['Business Administration'])
	get_eps_gr_1(it_op=it,teaching_op=teach,mkt_op=mkt,eng_op=eng,ba_op=ba)
	
#this gets opportunities form te last week form expa using the yop token
def get_opps(aiesec_token,backgrounds):
	headersx={'access_token': aiesec_token}
	url = "https://gis-api.aiesec.org/v2/opportunities.json"
	yesterday = datetime.date.today()-datetime.timedelta(6)
	params = {
	"access_token" :aiesec_token,
	'filters[programmes][]':[2],
	'filters[backgrounds][][id]':backgrounds,
	"filters[home_mcs][]":[1621,1606 ,1613,1549,1554],
	#"filters[work_fields][]":[724,742],
	"filters[created][to]" : datetime.date.today().strftime('%y-%m-%d'),
	"sort":"filters[created][to]"
	}
	q = requests.get(url, params=params)
	
	ops_expa= json.loads(q.text)['data']
	
	return ops_expa[0]['id']
	


#this method gets eps from get reponse to match them with the opps and then update their profiles
def get_eps_gr_1(it_op,teaching_op,mkt_op,eng_op,ba_op):
	
	eps = None
	#dates form today and 3 months ago
	day = 3
	while day < 90 :
		#just egtting the eps in days 7*times to reduce requests
		created  = datetime.date.today()-datetime.timedelta(day)
		day += 7
		params = {
		'query[campaignId]':'S1vv8',
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
					send_opps(gr_id = ep['contactId'],it  = it_op, teaching = teaching_op, mkt= mkt_op,eng = eng_op,ba = ba_op)
			elif not is_applicant(custom_fields['expa_id'],ep['contactId']):
				send_opps(gr_id = ep['contactId'],it  = it_op, teaching = teaching_op, mkt= mkt_op,eng = eng_op,ba = ba_op)
		#
		
#
def send_opps(gr_id ,it  , teaching , mkt,eng ,ba ):
	#get full ifor for the opps
	url = 'https://gis-api.aiesec.org/v2/opportunities/'
	it_op = json.loads(requests.get(url+str(it)+'.json?access_token='+expa_token).text)
	teach_op = json.loads(requests.get(url+str(teaching)+'.json?access_token='+expa_token).text)
	mkt_op = json.loads(requests.get(url+str(mkt)+'.json?access_token='+expa_token).text)
	eng_op = json.loads(requests.get(url+str(eng)+'.json?access_token='+expa_token).text)
	ba_op = json.loads(requests.get(url+str(ba)+'.json?access_token='+expa_token).text)
	it_country = json.loads(requests.get('https://gis-api.aiesec.org/v2/committees/'+str(it_op['home_lc']['id'])+'.json?access_token='+expa_token).text)['parent']['name']
	teach_country = json.loads(requests.get('https://gis-api.aiesec.org/v2/committees/'+str(teach_op['home_lc']['id'])+'.json?access_token='+expa_token).text)['parent']['name']
	mkt_country = json.loads(requests.get('https://gis-api.aiesec.org/v2/committees/'+str(mkt_op['home_lc']['id'])+'.json?access_token='+expa_token).text)['parent']['name']
	eng_country = json.loads(requests.get('https://gis-api.aiesec.org/v2/committees/'+str(eng_op['home_lc']['id'])+'.json?access_token='+expa_token).text)['parent']['name']
	ba_country = json.loads(requests.get('https://gis-api.aiesec.org/v2/committees/'+str(ba_op['home_lc']['id'])+'.json?access_token='+expa_token).text) ['parent']['name']
	#print eng_op
	params = {
    "customFieldValues": [
        	#http_op_engineering
        	{"customFieldId": 'zDYEj',"value": ['https://opportunities.aiesec.org/opportunity/'+str(eng)]},
        	#http_op_teahcing
        	{"customFieldId": 'zDYEN',"value": ['https://opportunities.aiesec.org/opportunity/'+str(teaching)]},
        	#http_op_ussines
        	{"customFieldId": 'zDYEM',"value": ['https://opportunities.aiesec.org/opportunity/'+str(ba)]},
        	#http_op_mkt
        	{"customFieldId": 'zDYEP',"value": ['https://opportunities.aiesec.org/opportunity/'+str(mkt)]},
        	#http_op_it
        	{"customFieldId": 'zDYEs',"value": ['https://opportunities.aiesec.org/opportunity/'+str(it)]},
        	#titulo eng
        	{"customFieldId": 'zDYE8',"value": [eng_op['title']]},
        	#titulo teach
        	{"customFieldId": 'zDYEI',"value": [teach_op['title']]},
        	#titulo ba
        	{"customFieldId": 'zDYEL',"value": [ba_op['title']]},
        	#titulo mkt
        	{"customFieldId": 'zDYEo',"value": [mkt_op['title']]},
        	#titulo it
        	{"customFieldId": 'zDYEa',"value": [it_op['title']]},
        	#desc eng
        	{"customFieldId": 'zDYEG',"value": [eng_op['description'][:250]]},
        	#description teach
        	{"customFieldId": 'zDYE4',"value": [teach_op['description'][:250]]},
        	#description ba
        	{"customFieldId": 'zDYE2',"value": [ba_op['description'][:250]]},
        	#description mkt
        	{"customFieldId": 'zDYEV',"value": [mkt_op['description'][:250]]},
        	#description it
        	{"customFieldId": 'zDYE0',"value": [it_op['description'][:250]]},
        	#country eng
        	{"customFieldId": 'zDY1L',"value": [eng_country]},
        	#coutry teach
        	{"customFieldId": 'zDY1a',"value": [teach_country]},
        	#country ba
        	{"customFieldId": 'zDY1o',"value": [ba_country]},
        	#country mkt
        	{"customFieldId": 'zDY1I',"value": [mkt_country]},
        	#country it
        	{"customFieldId": 'zDY18',"value": [it_country]}
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
