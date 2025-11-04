import os
import sys
import json
import logging
import netrc
import requests

from .Exceptions import *

logger = logging.getLogger(__name__)
logging.basicConfig(
		format="%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s",datefmt='%Y-%m-%d %H:%M:%S',
		handlers=[
			logging.StreamHandler(sys.stdout)
		],
		level=logging.INFO
	)

class API:
	
	_api_url = "https://dahiti.dgfi.tum.de/api/v3/"
	
	def __init__(self, log_level=logging.INFO, debug=0, api_key=None):
		
		' set log level '
		logger.setLevel(log_level)
		
		if debug == 1:
			self._api_url = "https://dahiti.dgfi.tum.de:8002/api/v3/"
			logger.warning("Debug-API enabled ("+str(self._api_url)+")!")
		
		if api_key == None:
			' read credential from ~/.netrc '		
			n = netrc.netrc()
			credentials = n.authenticators('dahiti.dgfi.tum.de')
			if credentials == None:
				logger.error('No credentials found in ~/.netrc')
				sys.exit(0)			
			self.api_key = credentials[2]
			logger.info('API-Key (~/.netrc): '+str(self.api_key))
		else:
			self.api_key = api_key
			logger.info('API-Key: '+str(self.api_key))

		' authenicate user '		
		response = self.send_api_request(
			self._api_url+'auth/',
			{			
				'api_key' :  self.api_key
			}
		)		
		if response.status_code == 200:
			logger.info('Authentication successful!')
			
	def send_api_request(self, url, args):
		
		response = requests.post(url, json=args)				
		if response.status_code == 400:	
			json_response = json.loads(response.text)			
			logger.error('400 - DAHITI-API url not found!')
			raise ArgumentNotFoundError(json_response['message'])
		elif response.status_code == 403:	
			json_response = json.loads(response.text)
			logger.error('403 - Permission denied!')
			raise PermissionDeniedError(json_response['message'])	
		elif response.status_code == 404:			
			json_response = json.loads(response.text)
			logger.error('404 - Unknown API request URL!')
			raise NotFoundError(json_response['message'])
		elif response.status_code == 470:			
			json_response = json.loads(response.text)
			logger.error('470 - DAHITI target not found!')
			raise NotFoundError(json_response['message'])
		elif response.status_code == 471:			
			json_response = json.loads(response.text)
			logger.error('471 - DAHITI dataset not found!')
			raise NotFoundError(json_response['message'])
		elif response.status_code == 500:
			json_response = json.loads(response.text)
			logger.error('500 - Internal Server Error')			
			raise InternalServerError(json_response['message'])	
					
		return response