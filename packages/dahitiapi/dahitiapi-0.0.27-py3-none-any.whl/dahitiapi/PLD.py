import os
import sys
import logging
import json
import requests
import shapely
	
from .API import API

logger = logging.getLogger(__name__)
logging.basicConfig(
	format="%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s",datefmt='%Y-%m-%d %H:%M:%S',
	handlers=[
		logging.StreamHandler(sys.stdout)
	],
	level=logging.INFO
)

class PLD(API):
	
	def __init__(self, log_level=logging.INFO, debug=0, api_key=None):
		API.__init__(self, log_level=logging.INFO, debug=0, api_key=None)
		
	def update_information_of_target(self, PLD_version, dahiti_id):
		
		#~ logger.info(' (`'+str(SWORD_version)+'`,`'+str(SWORD_reach_id)+'`) ...')
				
		response = self.send_api_request(
			self._api_url+'update-PLD-information/',
			{			
				'api_key' :  self.api_key,				
				'PLD_version' : PLD_version,
				'dahiti_id' : dahiti_id,
			}
		)
		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)
			return json_response['data']
			
		return response	

	def get_targets_in_AOI(self, PLD_version, aoi):
		""" Get PLD targets in AOI

		Args:
			PLD_version (str): PLD_version version
			aoi (Polygon) : AOI	
		Returns:				
			list: PLD targets
		
		"""			
		if type(aoi) != shapely.geometry.polygon.Polygon:
			logger.error('AOI is not a shapely polygon!')
			return 9
		
		response = self.send_api_request(
			self._api_url+'PLD/get-targets-in-AOI/',
			{
				'api_key' :  self.api_key,				
				'aoi' : aoi.wkt,
			}
		)
		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)
			return json_response['data']
			
		return response
