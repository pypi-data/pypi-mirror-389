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

class SWORD(API):
	
	def __init__(self, log_level=logging.INFO, debug=0, api_key=None):
		API.__init__(self, log_level=logging.INFO, debug=0, api_key=None)
		
	def get_reach_info(self, SWORD_version, SWORD_reach_id):
		""" Get information of SWORD reach in JSON format

		Args:
			SWORD_version (str): SWORD version
			SWORD_reach_id (int) : SWORD reach id			
		Returns:				
			dict: Information of SWORD reach
		
		"""	
		logger.info('Get SWORD reach info (`'+str(SWORD_version)+'`,`'+str(SWORD_reach_id)+'`) ...')
				
		response = self.send_api_request(
			self._api_url+'get-SWORD-reach-info/',
			{			
				'api_key' :  self.api_key,				
				'SWORD_version' : SWORD_version,
				'SWORD_reach_id' : SWORD_reach_id,
			}
		)
		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)
			return json_response['data']
			
		return response	

	def get_nodes_of_reach(self, SWORD_version, SWORD_reach_id):
		""" Get SWORD nodes of SWORD reach

		Args:
			SWORD_version (str): SWORD version
			SWORD_reach_id (int) :SWORD reach id			
		Returns:				
			dict: SWORD nodes
		
		"""					
		
		response = self.send_api_request(
			self._api_url+'get-SWORD-nodes-of-reach/',
			{
				'api_key' :  self.api_key,				
				'reach_id' : SWORD_reach_id,
			}
		)
		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)
			return json_response['data']
			
		return response
		
	def get_nodes_in_AOI(self, SWORD_version, aoi):
		""" Get SWORD nodes in AOI

		Args:
			SWORD_version (str): SWORD version
			aoi (Polygon) : AOI			
		Returns:				
			dict: SWORD nodes
		
		"""			
		if type(aoi) != shapely.geometry.polygon.Polygon:
			logger.error('AOI is not a shapely polygon!')
			return 9
		
		response = self.send_api_request(
			self._api_url+'get-SWORD-nodes-in-AOI/',
			{
				'api_key' :  self.api_key,				
				'aoi' : aoi.wkt,
			}
		)
		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)
			return json_response['data']
			
		return response

	def get_data_in_AOI(self, SWORD_version, aoi):
		""" Get SWORD nodes in AOI

		Args:
			SWORD_version (str): SWORD version
			longitude (double) : Longitude
			latitude (double) : Latitude
		Returns:				
			dict: SWORD reach
		
		"""			
		if type(aoi) != shapely.geometry.polygon.Polygon:
			logger.error('AOI is not a shapely polygon!')
			return 9
		
		response = self.send_api_request(
			self._api_url+'get-SWORD-data-in-AOI/',
			{
				'api_key' :  self.api_key,				
				'aoi' : aoi.wkt,
			}
		)
		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)
			return json_response['data']
			
		return response
		
	def get_nearest_reach(self, SWORD_version, longitude, latitude):
		""" Get nearest SWORD reach

		Args:
			SWORD_version (str): SWORD version
			longitude (double) : Longitude
			latitude (double) : Latitude
		Returns:				
			dict: SWORD reach
		
		"""	
		logger.info('Get nearest SWORD reach (`'+str(longitude)+'`,`'+str(latitude)+'`) ...')
				
		response = self.send_api_request(
			self._api_url+'get-SWORD-nearest-reach/',
			{			
				'api_key' :  self.api_key,				
				'SWORD_version' : SWORD_version,
				'longitude' : longitude,
				'latitude' : latitude,
			}
		)
		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)
			return json_response['data']
			
		return response
		
	def get_nearest_node(self, SWORD_version, longitude, latitude):
		""" Get nearest SWORD node

		Args:
			SWORD_version (str): SWORD version
			longitude (double) : Longitude
			latitude (double) : Latitude
		Returns:				
			dict: SWORD node
		
		"""	
		logger.info('Get nearest SWORD node (`'+str(longitude)+'`,`'+str(latitude)+'`) ...')
				
		response = self.send_api_request(
			self._api_url+'get-SWORD-nearest-node/',
			{			
				'api_key' :  self.api_key,				
				'SWORD_version' : SWORD_version,
				'longitude' : longitude,
				'latitude' : latitude,
			}
		)
		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)
			return json_response['data']
			
		return response						

	def get_nearest_centerline(self, SWORD_version, longitude, latitude):
		""" Get nearest SWORD centerline

		Args:
			SWORD_version (str): SWORD version
			longitude (double) : Longitude
			latitude (double) : Latitude
		Returns:				
			dict: SWORD centerline
		
		"""	
		logger.info('Get nearest SWORD centerline (`'+str(longitude)+'`,`'+str(latitude)+'`) ...')
				
		response = self.send_api_request(
			self._api_url+'get-SWORD-nearest-centerline/',
			{			
				'api_key' :  self.api_key,				
				'SWORD_version' : SWORD_version,
				'longitude' : longitude,
				'latitude' : latitude,
			}
		)
		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)
			return json_response['data']
			
		return response					
								
	def get_AOI_of_centerline(self, SWORD_version, SWORD_reach_id, longitude, latitude, centerline_length, reach_boundary, limit_point_distance):
		""" Get AOI of SWORD centerline

		Args:
			SWORD_version (str): SWORD version
			SWORD_reach_id (int) :SWORD reach id		
		Returns:				
			dict: SWORD nodes
		
		"""					
		
		response = self.send_api_request(
			self._api_url+'get-SWORD-AOI-of-centerline/',
			{
				'api_key' :  self.api_key,				
				'reach_id' : SWORD_reach_id,
				'longitude' : longitude,
				'latitude' : latitude,
				'centerline_length' : centerline_length,
				'reach_boundary' : reach_boundary,
				'limit_point_distance' :limit_point_distance	
			}
		)
		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)
			return json_response['data']
			
		return response
		
	def get_AOI_of_reach(self, SWORD_version, SWORD_reach_id):
		""" Get AOI of SWORD reach

		Args:
			SWORD_version (str): SWORD version
			SWORD_reach_id (int) :SWORD reach id			
		Returns:				
			dict: SWORD nodes
		
		"""					
		
		response = self.send_api_request(
			self._api_url+'get-SWORD-AOI-of-reach/',
			{
				'api_key' :  self.api_key,				
				'reach_id' : SWORD_reach_id,
			}
		)
		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)
			return json_response['data']
			
		return response
		
	def get_river_centerline(self, SWORD_version, upstream_longitude, upstream_latitude, downstream_longitude, downstream_latitude):
		""" Get river centerline

		Args:
			SWORD_version (str): SWORD version
			upstream_longitude (double) : Upstream longitude
			upstream_latitude (double) : Upstream latitude
			downstream_longitude (double) : Downstream longitude
			downstream_latitude (double) : Downstream latitude
		Returns:				
			dict: SWORD centerline
		
		"""	
		logger.info('Get river centerline between (`'+str(upstream_longitude)+'`,`'+str(upstream_latitude)+'`) and (`'+str(downstream_longitude)+'`,`'+str(downstream_latitude)+'`) ...')
				
		response = self.send_api_request(
			self._api_url+'get-SWORD-river-centerline/',
			{			
				'api_key' :  self.api_key,				
				'SWORD_version' : SWORD_version,
				'upstream_longitude' : upstream_longitude,
				'upstream_latitude' : upstream_latitude,
				'downstream_longitude' : downstream_longitude,
				'downstream_latitude' : downstream_latitude,
			}
		)
		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)
			return json_response['data']
			
		return response	
	
	def get_intersections(self, SWORD_version, track):
			
		if type(track) != shapely.geometry.polygon.LineString:
			logger.error('AOI is not a shapely linestring!')
			return 9
		
		response = self.send_api_request(
			self._api_url+'get-SWORD-intersections/',
			{
				'api_key' :  self.api_key,				
				'track' : track.wkt,
			}
		)
		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)
			return json_response['data']
			
		return response		