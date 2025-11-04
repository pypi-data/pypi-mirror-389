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

class InSitu(API):
	
	def __init__(self, log_level=logging.INFO, debug=0, api_key=None):
		API.__init__(self, log_level=logging.INFO, debug=0, api_key=None)

	def download(self, insitu_id):
		""" Download time series

		Args:
			insitu_id (int) : In-Situ id
		Returns:				
			dict: target info
		
		"""	
		logger.info('Download time series of target (`'+str(insitu_id)+'`) ...')
				
		response = self.send_api_request(
			self._api_url+'insitu/download/',
			{			
				'api_key' :  self.api_key,								
				'insitu_id' : insitu_id,				
			}
		)
		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)			
			return json_response['data']
			
		return response
		
	def get_nearest_target(self, longitude, latitude):
		""" Get nearest target

		Args:
			longitude (double) : Longitude
			latitude (double) : Latitude
		Returns:				
			dict: target
		
		"""	
		logger.info('Get nearest target (`'+str(longitude)+'`,`'+str(latitude)+'`) ...')
				
		response = self.send_api_request(
			self._api_url+'insitu/get-nearest-target/',
			{			
				'api_key' :  self.api_key,								
				'longitude' : longitude,
				'latitude' : latitude,
			}
		)
		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)
			return json_response['data']
			
		return response
	
	def get_target_info(self, insitu_id):
		""" Get target info

		Args:
			insitu_id (int) : In-Situ id
		Returns:				
			dict: target info
		
		"""	
		logger.info('Get nearest target (`'+str(insitu_id)+'`) ...')
				
		response = self.send_api_request(
			self._api_url+'insitu/get-target-info/',
			{			
				'api_key' :  self.api_key,								
				'insitu_id' : insitu_id,				
			}
		)
		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)
			return json_response['data']
			
		return response
		

	#~ import project.APIv3.view_insitu_download
	#~ urlpatterns.append(re_path(r'^insitu/download/$', project.APIv3.view_insitu_download.request))

	#~ import project.APIv3.view_insitu_delete_data
	#~ urlpatterns.append(re_path(r'^insitu/delete-data/$', project.APIv3.view_insitu_delete_data.request))

	#~ import project.APIv3.view_insitu_update_time_series
	#~ urlpatterns.append(re_path(r'^insitu/update-time-series/$', project.APIv3.view_insitu_update_time_series.request))

	#~ import project.APIv3.view_insitu_list_collection
	#~ urlpatterns.append(re_path(r'^insitu/list-collection/$', project.APIv3.view_insitu_list_collection.request))

	#~ import project.APIv3.view_insitu_copy_data
	#~ urlpatterns.append(re_path(r'^insitu/copy-data/$', project.APIv3.view_insitu_copy_data.request))

	#~ import project.APIv3.view_insitu_create_target
	#~ urlpatterns.append(re_path(r'^insitu/create-target/$', project.APIv3.view_insitu_create_target.request))

	#~ import project.APIv3.view_insitu_update_target_info
	#~ urlpatterns.append(re_path(r'^insitu/update-target-info/$', project.APIv3.view_insitu_update_target_info.request))

	#~ import project.APIv3.view_insitu_add_data
	#~ urlpatterns.append(re_path(r'^insitu/add-data/$', project.APIv3.view_insitu_add_data.request))

	#~ import project.APIv3.view_insitu_search
	#~ urlpatterns.append(re_path(r'^insitu/search/$', project.APIv3.view_insitu_search.request))

	#~ import project.APIv3.view_insitu_delete_target
	#~ urlpatterns.append(re_path(r'^insitu/delete-target/$', project.APIv3.view_insitu_delete_target.request))
