import requests
import json
#this is a get reponse wrapper in python for basic functions

class GetResponse(object):



	#gets ready everything you need to make REST calls to GR
	def __init__(self, url ='https://api3.getresponse360.com/v3',gr_id='api-key edd91283845856ad6863a3ee76a421c9',gr_api_domain = 'aiesec.getresponse360.com'):
		super(GetResponse, self).__init__()
		self.url =url
		self.headers = {'X-Auth-Token':gr_id,'X-Domain':gr_api_domain}


	#gets a url commando and returns the response as a string
	def get_request(self, url, params = None):
		q = requests.get(self.url+'/'+url, headers=self.headers,params= params)
		return q.content

	#thi makes a post request to GR, it gets as parameters the url for the action and the data as a json object
	def post_requests(self,url,data= None):
		headers_aux = self.headers
		headers_aux['Content-Type'] = 'application/json'
		q = requests.post(self.url+url, headers=headers_aux,data=json.dumps(data))
		

