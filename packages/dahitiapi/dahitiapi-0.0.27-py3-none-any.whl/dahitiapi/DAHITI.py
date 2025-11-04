import os
import sys
import re
import netrc
import logging
import requests
import json
import pprint
import traceback

from .API import API

logger = logging.getLogger(__name__)
logging.basicConfig(
		format="%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s",datefmt='%Y-%m-%d %H:%M:%S',
		handlers=[
			logging.StreamHandler(sys.stdout)
		],
		level=logging.INFO
	)
		
class DAHITI(API):
	"""Client for DAHITI-API.

	Handles authentication and data retrieval.
	"""

	def __init__(self, log_level=logging.INFO, debug=0, api_key=None):
		API.__init__(self, log_level=logging.INFO, debug=0, api_key=None)
			
	def get_quality_assessment(self, dahiti_id, dataset, software, parameters=None):
		
		logger.info('Get quality assessment of DAHITI target with id '+str(dahiti_id)+' ...')
		
		response = self.send_api_request(
			self._api_url+'get-quality-assessment/',
			{			
				'api_key' :  self.api_key,
				'dahiti_id' : dahiti_id,
				'dataset' : dataset,
				'software' : software,
				'parameters' : parameters
			}
		)
				
		return response
	
	def download_water_level_ascii(self, dahiti_id, **kwargs):
		"""Download water levels from satellite altimetry for a DAHITI target in ASCII format

		Args:
			dahiti_id (int): DAHITI Id
			**kwargs : Optional keyword arguments:			
		Returns:				
			str: Water level time series for a DAHITI target in ASCII format
		
		"""
		kwargs['format'] = "ascii"
		return self.__download_water_level(dahiti_id, **kwargs)
	
	def download_water_level_ascii_to_file(self, dahiti_id, path, **kwargs):	
		"""Download water levels from satellite altimetry for a DAHITI target in ASCII format

		Args:
			dahiti_id (int): DAHITI Id
			path (str): Output path
			**kwargs : Optional keyword arguments:			
		Returns:				
			str: Water level time series for a DAHITI target in ASCII format
		
		"""					
		kwargs['format'] = "ascii"
		kwargs['path'] = path		
		return self.__download_water_level(dahiti_id, **kwargs)
		
	def download_water_level_json(self, dahiti_id, **kwargs):
		"""Download water levels from satellite altimetry for a DAHITI target in JSON format

		Args:
			dahiti_id (int): DAHITI Id
			**kwargs : Optional keyword arguments:			
		Returns:				
			dict: Water level time series for a DAHITI target in JSON format
		
		"""	
		kwargs['format'] = "json"
		return self.__download_water_level(dahiti_id, **kwargs)
	
	def download_water_level_json_to_file(self, dahiti_id, path, **kwargs):
		"""Download water levels from satellite altimetry for a DAHITI target in JSON format

		Args:
			dahiti_id (int): DAHITI Id
			path (str): Output path
			**kwargs : Optional keyword arguments:			
		Returns:				
			dict: Water level time series for a DAHITI target in JSON format
		
		"""			
		kwargs['format'] = "json"
		kwargs['path'] = path		
		return self.__download_water_level(dahiti_id, **kwargs)

	def download_water_level_csv(self, dahiti_id, **kwargs):
		"""Download water levels from satellite altimetry for a DAHITI target in CSV format

		Args:
			dahiti_id (int): DAHITI Id
			**kwargs : Optional keyword arguments:			
		Returns:				
			str: Water level time series for a DAHITI target in ASCII format
		
		"""		
		kwargs['format'] = "csv"
		return self.__download_water_level(dahiti_id, **kwargs)
	
	def download_water_level_csv_to_file(self, dahiti_id, path, **kwargs):	
		"""Download water levels from satellite altimetry for a DAHITI target in CSV format

		Args:
			dahiti_id (int): DAHITI Id
			path (str): Output path
			**kwargs : Optional keyword arguments:			
		Returns:				
			str: Water level time series for a DAHITI target in CSV format
		
		"""				
		kwargs['format'] = "csv"
		kwargs['path'] = path		
		return self.__download_water_level(dahiti_id, **kwargs)

	def download_water_level_netcdf(self, dahiti_id, path, **kwargs):	
		"""Download water levels from satellite altimetry for a DAHITI target in NetCDF format

		Args:
			dahiti_id (int): DAHITI Id
			path (str): Output path
			**kwargs : Optional keyword arguments:			
		Returns:				
			Response: Status code of API-request
		
		"""			
		kwargs['format'] = "netcdf"
		kwargs['path'] = path		
		return self.__download_water_level(dahiti_id, **kwargs)
						
	def __download_water_level(self, dahiti_id, **kwargs):
				
		format = None
		if 'format' in kwargs:
			format = kwargs['format']
			
		software = None
		if 'software' in kwargs:
			software = kwargs['software']

		path = None
		if 'path' in kwargs:
			path = kwargs['path']
		
		parameters = None
		if 'parameters' in kwargs:
			parameters = kwargs['format']
				
		if format in ['netcdf'] and path == None:
			raise ArgumentNotFoundError('Format `netcdf` requires `path` for saving!')
		
		logger.info('Download water levels DAHITI target with id '+str(dahiti_id)+' ...')
		
		response = self.send_api_request(
			self._api_url+'download-water-level/',
			{			
				'api_key' :  self.api_key,
				'dahiti_id' : dahiti_id,
				'format' : format,
				'software' : software,
				'parameters' : parameters,
			}
		)
		if type(response) == requests.models.Response:
			try:						
				if format == 'ascii':
					ascii_response = str(response.text)
					if path != None:
						if not os.path.isdir(os.path.dirname(path)):
							raise DirectoryNotExist('Directory `'+str(os.path.dirname(path))+'` does not exist!')		
						logger.info('Writing data to '+path+' ...')
						with open(path, 'w') as f:
							f.write(ascii_response)
						if not os.path.isfile(path):
							raise FileNotExist('`'+str(path)+'` could not be written!')
					return ascii_response
				elif format == 'json':
					json_response = json.loads(response.text)							
					if path != None:
						if not os.path.isdir(os.path.dirname(path)):
							raise DirectoryNotExist('Directory `'+str(os.path.dirname(path))+'` does not exist!')		
						logger.info('Writing data to '+path+' ...')
						with open(path, 'w') as f:
							json.dump(json_response, f)
						if not os.path.isfile(path):
							raise FileNotExist('`'+str(path)+'` could not be written!')
					return json_response
				elif format == 'csv':
					csv_response = str(response.text)
					if path != None:
						if not os.path.isdir(os.path.dirname(path)):
							raise DirectoryNotExist('Directory `'+str(os.path.dirname(path))+'` does not exist!')		
						logger.info('Writing data to '+path+' ...')
						with open(path, 'w') as f:
							f.write(csv_response)
						if not os.path.isfile(path):
							raise FileNotExist('`'+str(path)+'` could not be written!')
					return csv_response
				elif format == 'netcdf':
					if not os.path.isdir(os.path.dirname(path)):
						raise DirectoryNotExist('Directory `'+str(os.path.dirname(path))+'` does not exist!')		
					logger.info('Writing data to '+path+' ...')					
					with open(path, 'wb') as f:
						for chunk in response.iter_content(chunk_size=1024): 
							if chunk:
								f.write(chunk)
					if not os.path.isfile(path):
						raise FileNotExist('`'+str(path)+'` could not be written!')
			except:
				traceback.print_exc()

		return response

	def download_water_level_hypsometry_ascii(self, dahiti_id, **kwargs):
		"""Download water levels from hypsometry derived from satellite altimetry and optical imagery for a DAHITI target in ASCII format

		Args:
			dahiti_id (int): DAHITI Id
			**kwargs : Optional keyword arguments:			
		Returns:				
			str: Water level time series from hypsometry for a DAHITI target in ASCII format
		
		"""
		kwargs['format'] = "ascii"
		return self.__download_water_level_hypsometry(dahiti_id, **kwargs)
	
	def download_water_level_hypsometry_ascii_to_file(self, dahiti_id, path, **kwargs):
		"""Download water levels from hypsometry derived from satellite altimetry and optical imagery for a DAHITI target in ASCII format

		Args:
			dahiti_id (int): DAHITI Id
			path: Output path
			**kwargs : Optional keyword arguments:			
		Returns:				
			str: Water level time series from hypsometry for a DAHITI target in ASCII format
		
		"""		
		kwargs['format'] = "ascii"
		kwargs['path'] = path		
		return self.__download_water_level_hypsometry(dahiti_id, **kwargs)
		
	def download_water_level_hypsometry_json(self, dahiti_id, **kwargs):
		"""Download water levels from hypsometry derived from satellite altimetry and optical imagery for a DAHITI target in ASCII format

		Args:
			dahiti_id (int): DAHITI Id
			**kwargs : Optional keyword arguments:			
		Returns:				
			dict: Water level time series from hypsometry for a DAHITI target in JSON format
		
		"""	
		kwargs['format'] = "json"
		return self.__download_water_level_hypsometry(dahiti_id, **kwargs)
	
	def download_water_level_hypsometry_json_to_file(self, dahiti_id, path, **kwargs):
		"""Download water levels from hypsometry derived from satellite altimetry and optical imagery for a DAHITI target in ASCII format

		Args:
			dahiti_id (int): DAHITI Id
			path: Output path
			**kwargs : Optional keyword arguments:			
		Returns:				
			dict: Water level time series from hypsometry for a DAHITI target in JSON format
		
		"""			
		kwargs['format'] = "json"
		kwargs['path'] = path		
		return self.__download_water_level_hypsometry(dahiti_id, **kwargs)

	def download_water_level_hypsometry_csv(self, dahiti_id, **kwargs):
		"""Download water levels from hypsometry derived from satellite altimetry and optical imagery for a DAHITI target in CSV format

		Args:
			dahiti_id (int): DAHITI Id			
			**kwargs : Optional keyword arguments:			
		Returns:				
			str: Water level time series from hypsometry for a DAHITI target in CSV format
		
		"""	
		kwargs['format'] = "csv"
		return self.__download_water_level_hypsometry(dahiti_id, **kwargs)
	
	def download_water_level_hypsometry_csv_to_file(self, dahiti_id, path, **kwargs):
		"""Download water levels from hypsometry derived from satellite altimetry and optical imagery for a DAHITI target in CSV format

		Args:
			dahiti_id (int): DAHITI Id
			path: Output path
			**kwargs : Optional keyword arguments:			
		Returns:				
			str: Water level time series from hypsometry for a DAHITI target in CSV format
		
		"""				
		kwargs['format'] = "csv"
		kwargs['path'] = path		
		return self.__download_water_level_hypsometry(dahiti_id, **kwargs)

	def download_water_level_hypsometry_netcdf(self, dahiti_id, path, **kwargs):
		"""Download water levels from hypsometry derived from satellite altimetry and optical imagery for a DAHITI target in NetCDF format

		Args:
			dahiti_id (int): DAHITI Id
			path: Output path
			**kwargs : Optional keyword arguments:			
		Returns:				
			Response: Status code of API-request
		
		"""			
		kwargs['format'] = "netcdf"
		kwargs['path'] = path		
		return self.__download_water_level_hypsometry(dahiti_id, **kwargs)
				
	def __download_water_level_hypsometry(self, dahiti_id, **kwargs):
				
		format = None
		if 'format' in kwargs:
			format = kwargs['format']
			
		software = None
		if 'software' in kwargs:
			software = kwargs['software']

		path = None
		if 'path' in kwargs:
			path = kwargs['path']
		
		parameters = None
		if 'parameters' in kwargs:
			parameters = kwargs['format']
				
		if format in ['netcdf'] and path == None:
			raise ArgumentNotFoundError('Format `netcdf` requires `path` for saving!')
		
		logger.info('Download water levels from hypsometry of DAHITI target with id '+str(dahiti_id)+' ...')
		
		response = self.send_api_request(
			self._api_url+'download-water-level-hypsometry/',
			{			
				'api_key' :  self.api_key,
				'dahiti_id' : dahiti_id,
				'format' : format,
				'software' : software,
				'parameters' : parameters,
			}
		)
		if type(response) == requests.models.Response:
			try:						
				if format == 'ascii':
					ascii_response = str(response.text)
					if path != None:
						if not os.path.isdir(os.path.dirname(path)):
							raise DirectoryNotExist('Directory `'+str(os.path.dirname(path))+'` does not exist!')		
						logger.info('Writing data to '+path+' ...')
						with open(path, 'w') as f:
							f.write(ascii_response)
						if not os.path.isfile(path):
							raise FileNotExist('`'+str(path)+'` could not be written!')
					return ascii_response
				elif format == 'json':
					json_response = json.loads(response.text)							
					if path != None:
						if not os.path.isdir(os.path.dirname(path)):
							raise DirectoryNotExist('Directory `'+str(os.path.dirname(path))+'` does not exist!')		
						logger.info('Writing data to '+path+' ...')
						with open(path, 'w') as f:
							json.dump(json_response, f)
						if not os.path.isfile(path):
							raise FileNotExist('`'+str(path)+'` could not be written!')
					return json_response
				elif format == 'csv':
					csv_response = str(response.text)
					if path != None:
						if not os.path.isdir(os.path.dirname(path)):
							raise DirectoryNotExist('Directory `'+str(os.path.dirname(path))+'` does not exist!')		
						logger.info('Writing data to '+path+' ...')
						with open(path, 'w') as f:
							f.write(csv_response)
						if not os.path.isfile(path):
							raise FileNotExist('`'+str(path)+'` could not be written!')
					return csv_response
				elif format == 'netcdf':
					if not os.path.isdir(os.path.dirname(path)):
						raise DirectoryNotExist('Directory `'+str(os.path.dirname(path))+'` does not exist!')		
					logger.info('Writing data to '+path+' ...')					
					with open(path, 'wb') as f:
						for chunk in response.iter_content(chunk_size=1024): 
							if chunk:
								f.write(chunk)
					if not os.path.isfile(path):
						raise FileNotExist('`'+str(path)+'` could not be written!')
			except:
				traceback.print_exc()
			
		return response
	
	def download_surface_area_ascii(self, dahiti_id, **kwargs):
		"""Download surface area time series derived from satellite altimetry for a DAHITI target in ASCII format

		Args:
			dahiti_id (int): DAHITI Id
			**kwargs : Optional keyword arguments:			
		Returns:				
			str: Surface area time series for a DAHITI target in ASCII format
		
		"""	
		kwargs['format'] = "ascii"
		return self.__download_surface_area(dahiti_id, **kwargs)
	
	def download_surface_area_ascii_to_file(self, dahiti_id, path, **kwargs):
		"""Download surface area time series derived from satellite altimetry for a DAHITI target in ASCII format

		Args:
			dahiti_id (int): DAHITI Id
			path: Output path
			**kwargs : Optional keyword arguments:			
		Returns:				
			str: Surface area time series for a DAHITI target in ASCII format
		
		"""			
		kwargs['format'] = "ascii"
		kwargs['path'] = path		
		return self.__download_surface_area(dahiti_id, **kwargs)
		
	def download_surface_area_json(self, dahiti_id, **kwargs):
		"""Download surface area time series derived from satellite altimetry for a DAHITI target in JSON format

		Args:
			dahiti_id (int): DAHITI Id
			**kwargs : Optional keyword arguments:			
		Returns:				
			dict: Surface area time series for a DAHITI target in JSON format
		
		"""	
		kwargs['format'] = "json"
		return self.__download_surface_area(dahiti_id, **kwargs)
	
	def download_surface_area_json_to_file(self, dahiti_id, path, **kwargs):
		"""Download surface area time series derived from satellite altimetry for a DAHITI target in JSON format

		Args:
			dahiti_id (int): DAHITI Id
			path: Output path
			**kwargs : Optional keyword arguments:			
		Returns:				
			dict: Surface area time series for a DAHITI target in JSON format
		
		"""				
		kwargs['format'] = "json"
		kwargs['path'] = path		
		return self.__download_surface_area(dahiti_id, **kwargs)

	def download_surface_area_csv(self, dahiti_id, **kwargs):
		"""Download surface area time series derived from satellite altimetry for a DAHITI target in CSV format

		Args:
			dahiti_id (int): DAHITI Id
			**kwargs : Optional keyword arguments:			
		Returns:				
			str: Surface area time series for a DAHITI target in CSV format
		
		"""	
		kwargs['format'] = "csv"
		return self.__download_surface_area(dahiti_id, **kwargs)
	
	def download_surface_area_csv_to_file(self, dahiti_id, path, **kwargs):	
		"""Download surface area time series derived from satellite altimetry for a DAHITI target in CSV format

		Args:
			dahiti_id (int): DAHITI Id
			path: Output path
			**kwargs : Optional keyword arguments:			
		Returns:				
			str: Surface area time series for a DAHITI target in CSV format
		
		"""				
		kwargs['format'] = "csv"
		kwargs['path'] = path		
		return self.__download_surface_area(dahiti_id, **kwargs)

	def download_surface_area_netcdf(self, dahiti_id, path, **kwargs):
		"""Download surface area time series derived from satellite altimetry for a DAHITI target in NetCDF format

		Args:
			dahiti_id (int): DAHITI Id
			path: Output path
			**kwargs : Optional keyword arguments:			
		Returns:				
			Response: Status code of API-request
		
		"""			
		kwargs['format'] = "netcdf"
		kwargs['path'] = path		
		return self.__download_surface_area(dahiti_id, **kwargs)
			
	def __download_surface_area(self, dahiti_id, **kwargs):
		
		format = None
		if 'format' in kwargs:
			format = kwargs['format']
			
		software = None
		if 'software' in kwargs:
			software = kwargs['software']

		path = None
		if 'path' in kwargs:
			path = kwargs['path']
		
		parameters = None
		if 'parameters' in kwargs:
			parameters = kwargs['format']
					
		if format in ['netcdf'] and path == None:
			raise ArgumentNotFoundError('Format `netcdf` requires `path` for saving!')
		
		logger.info('Download surface area DAHITI target with id '+str(dahiti_id)+' ...')
				
		response = self.send_api_request(
			self._api_url+'download-surface-area/',
			{			
				'api_key' :  self.api_key,
				'dahiti_id' : dahiti_id,
				'format' : format,
				'software' : software,
				'parameters' : parameters,
			}
		)		
		if type(response) == requests.models.Response:
			try:						
				if format == 'ascii':
					ascii_response = str(response.text)
					if path != None:
						if not os.path.isdir(os.path.dirname(path)):
							raise DirectoryNotExist('Directory `'+str(os.path.dirname(path))+'` does not exist!')		
						logger.info('Writing data to '+path+' ...')
						with open(path, 'w') as f:
							f.write(ascii_response)
						if not os.path.isfile(path):
							raise FileNotExist('`'+str(path)+'` could not be written!')
					return ascii_response
				elif format == 'json':
					json_response = json.loads(response.text)							
					if path != None:
						if not os.path.isdir(os.path.dirname(path)):
							raise DirectoryNotExist('Directory `'+str(os.path.dirname(path))+'` does not exist!')		
						logger.info('Writing data to '+path+' ...')
						with open(path, 'w') as f:
							json.dump(json_response, f)
						if not os.path.isfile(path):
							raise FileNotExist('`'+str(path)+'` could not be written!')
					return json_response
				elif format == 'csv':
					csv_response = str(response.text)
					if path != None:
						if not os.path.isdir(os.path.dirname(path)):
							raise DirectoryNotExist('Directory `'+str(os.path.dirname(path))+'` does not exist!')		
						logger.info('Writing data to '+path+' ...')
						with open(path, 'w') as f:
							f.write(csv_response)
						if not os.path.isfile(path):
							raise FileNotExist('`'+str(path)+'` could not be written!')
					return csv_response
				elif format == 'netcdf':
					if not os.path.isdir(os.path.dirname(path)):
						raise DirectoryNotExist('Directory `'+str(os.path.dirname(path))+'` does not exist!')		
					logger.info('Writing data to '+path+' ...')					
					with open(path, 'wb') as f:
						for chunk in response.iter_content(chunk_size=1024): 
							if chunk:
								f.write(chunk)
					if not os.path.isfile(path):
						raise FileNotExist('`'+str(path)+'` could not be written!')
			except:
				traceback.print_exc()
				
		return response

	def download_volume_variation_ascii(self, dahiti_id, **kwargs):
		"""Download volume variations from satellite altimetry and opical imagery for a DAHITI target in ASCII format

		Args:
			dahiti_id (int): DAHITI Id
			**kwargs : Optional keyword arguments:			
		Returns:				
			str: Time series of volume variations of DAHITI target in ASCII format
		
		"""
		kwargs['format'] = "ascii"
		return self.__download_volume_variation(dahiti_id, **kwargs)
	
	def download_volume_variation_ascii_to_file(self, dahiti_id, path, **kwargs):
		"""Download volume variations from satellite altimetry and opical imagery for a DAHITI target in ASCII format

		Args:
			dahiti_id (int): DAHITI Id
			path (str): Output path
			**kwargs : Optional keyword arguments:			
		Returns:				
			str: Time series of volume variations of DAHITI target in ASCII format
		
		"""		
		kwargs['format'] = "ascii"
		kwargs['path'] = path		
		return self.__download_volume_variation(dahiti_id, **kwargs)
		
	def download_volume_variation_json(self, dahiti_id, **kwargs):
		"""Download volume variations from satellite altimetry and opical imagery for a DAHITI target in JSON format

		Args:
			dahiti_id (int): DAHITI Id
			**kwargs : Optional keyword arguments:			
		Returns:				
			dict: Time series of volume variations of DAHITI target in JSON format
		
		"""	
		kwargs['format'] = "json"
		return self.__download_volume_variation(dahiti_id, **kwargs)
	
	def download_volume_variation_json_to_file(self, dahiti_id, path, **kwargs):
		"""Download volume variations from satellite altimetry and opical imagery for a DAHITI target in JSON format

		Args:
			dahiti_id (int): DAHITI Id
			path (str): Output path
			**kwargs : Optional keyword arguments:			
		Returns:				
			dict: Time series of volume variations of DAHITI target in JSON format
		
		"""				
		kwargs['format'] = "json"
		kwargs['path'] = path		
		return self.__download_volume_variation(dahiti_id, **kwargs)

	def download_volume_variation_csv(self, dahiti_id, **kwargs):
		"""Download volume variations from satellite altimetry and opical imagery for a DAHITI target in CSV format

		Args:
			dahiti_id (int): DAHITI Id
			**kwargs : Optional keyword arguments:			
		Returns:				
			str: Time series of volume variations of DAHITI target in CSV format
		
		"""	
		kwargs['format'] = "csv"
		return self.__download_volume_variation(dahiti_id, **kwargs)
	
	def download_volume_variation_csv_to_file(self, dahiti_id, path, **kwargs):
		"""Download volume variations from satellite altimetry and opical imagery for a DAHITI target in CSV format

		Args:
			dahiti_id (int): DAHITI Id
			path (str): Output path
			**kwargs : Optional keyword arguments:			
		Returns:				
			str: Time series of volume variations of DAHITI target in CSV format
		
		"""				
		kwargs['format'] = "csv"
		kwargs['path'] = path		
		return self.__download_volume_variation(dahiti_id, **kwargs)

	def download_volume_variation_netcdf(self, dahiti_id, path, **kwargs):
		"""Download volume variations from satellite altimetry and opical imagery for a DAHITI target in NetCDF format

		Args:
			dahiti_id (int): DAHITI Id
			path (str): Output path
			**kwargs : Optional keyword arguments:			
		Returns:				
			Response: Status code of API-request
		
		"""				
		kwargs['format'] = "netcdf"
		kwargs['path'] = path		
		return self.__download_volume_variation(dahiti_id, **kwargs)
		
	def __download_volume_variation(self, dahiti_id, **kwargs):
	
		format = None
		if 'format' in kwargs:
			format = kwargs['format']
			
		software = None
		if 'software' in kwargs:
			software = kwargs['software']

		path = None
		if 'path' in kwargs:
			path = kwargs['path']
		
		parameters = None
		if 'parameters' in kwargs:
			parameters = kwargs['format']
				
		if format in ['netcdf'] and path == None:
			raise ArgumentNotFoundError('Format `netcdf` requires `path` for saving!')
		
		logger.info('Download volume variation of  DAHITI target with id '+str(dahiti_id)+' ...')
		
		response = self.send_api_request(
			self._api_url+'download-volume-variation/',
			{			
				'api_key' :  self.api_key,
				'dahiti_id' : dahiti_id,
				'format' : format,
				'software' : software,
				'parameters' : parameters,
			}
		)		
		if type(response) == requests.models.Response:
			try:						
				if format == 'ascii':
					ascii_response = str(response.text)
					if path != None:
						if not os.path.isdir(os.path.dirname(path)):
							raise DirectoryNotExist('Directory `'+str(os.path.dirname(path))+'` does not exist!')		
						logger.info('Writing data to '+path+' ...')
						with open(path, 'w') as f:
							f.write(ascii_response)
						if not os.path.isfile(path):
							raise FileNotExist('`'+str(path)+'` could not be written!')
					return ascii_response
				elif format == 'json':
					json_response = json.loads(response.text)							
					if path != None:
						if not os.path.isdir(os.path.dirname(path)):
							raise DirectoryNotExist('Directory `'+str(os.path.dirname(path))+'` does not exist!')		
						logger.info('Writing data to '+path+' ...')
						with open(path, 'w') as f:
							json.dump(json_response, f)
						if not os.path.isfile(path):
							raise FileNotExist('`'+str(path)+'` could not be written!')
					return json_response
				elif format == 'csv':
					csv_response = str(response.text)
					if path != None:
						if not os.path.isdir(os.path.dirname(path)):
							raise DirectoryNotExist('Directory `'+str(os.path.dirname(path))+'` does not exist!')		
						logger.info('Writing data to '+path+' ...')
						with open(path, 'w') as f:
							f.write(csv_response)
						if not os.path.isfile(path):
							raise FileNotExist('`'+str(path)+'` could not be written!')
					return csv_response
				elif format == 'netcdf':
					if not os.path.isdir(os.path.dirname(path)):
						raise DirectoryNotExist('Directory `'+str(os.path.dirname(path))+'` does not exist!')		
					logger.info('Writing data to '+path+' ...')					
					with open(path, 'wb') as f:
						for chunk in response.iter_content(chunk_size=1024): 
							if chunk:
								f.write(chunk)
					if not os.path.isfile(path):
						raise FileNotExist('`'+str(path)+'` could not be written!')
			except:
				traceback.print_exc()
				
				
		return response
	
	def download_water_occurrence_mask(self, dahiti_id,  path, **kwargs):
		"""Download water occurrence mask derived from optical imagery for a DAHITI target as GeoTiff

		Args:
			dahiti_id (int): DAHITI Id
			path (str): Output path of GeoTiff
			**kwargs : Optional keyword arguments:			
		Returns:				
			Response: Status code of API-request
		
		"""			
		software = None
		if 'software' in kwargs:
			software = kwargs['software']
			
		logger.info('Download water occurrence mask of DAHITI target with id '+str(dahiti_id)+' ...')
		
		response = self.send_api_request(
			self._api_url+'download-water-occurrence-mask/',
			{			
				'api_key' :  self.api_key,
				'dahiti_id' : dahiti_id,
				'software' : software
			}
		)
		
		if type(response) == requests.models.Response:		
			if not os.path.isdir(os.path.dirname(path)):
				raise DirectoryNotExist('Directory `'+str(os.path.dirname(path))+'` does not exist!')		
			logger.info('Writing data to '+path+' ...')					
			with open(path, 'wb') as f:
				for chunk in response.iter_content(chunk_size=1024): 
					if chunk:
						f.write(chunk)
			if not os.path.isfile(path):
				raise FileNotExist('`'+str(path)+'` could not be written!')
		return response
	
	def download_hypsometry(self, dahiti_id,  **kwargs):
		"""Download hypsometry from satellite altimetry and optical imagery for a DAHITI target

		Args:
			dahiti_id (int): DAHITI Id
			**kwargs : Optional keyword arguments:			
		Returns:				
			dict : Paramaters of hypsometry model
		
		"""	
		software = None
		if 'software' in kwargs:
			software = kwargs['software']

		path = None
		if 'path' in kwargs:
			path = kwargs['path']
			
		logger.info('Download hypsometry of DAHITI target with id '+str(dahiti_id)+' ...')
		
		response = self.send_api_request(
			self._api_url+'download-hypsometry/',
			{			
				'api_key' :  self.api_key,
				'dahiti_id' : dahiti_id,
				'software' : software
			}
		)
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)			
			return json_response
		return response
	
	def download_bathymetry(self, dahiti_id, path,  **kwargs):
		"""Download bathymetry derived from satellite altimetry and optical imagery for a DAHITI target as GeoTiff

		Args:
			dahiti_id (int): DAHITI Id
			path (str): Output path of GeoTiff
			**kwargs : Optional keyword arguments:			
		Returns:				
			Response: Status code of API-request
		
		"""	
		software = None
		if 'software' in kwargs:
			software = kwargs['software']

		logger.info('Download bathymetry of DAHITI target with id '+str(dahiti_id)+' ...')
		
		response = self.send_api_request(
			self._api_url+'download-bathymetry/',
			{			
				'api_key' :  self.api_key,
				'dahiti_id' : dahiti_id,
				'software' : software
			}
		)
		
		if type(response) == requests.models.Response:		
			if not os.path.isdir(os.path.dirname(path)):
				raise DirectoryNotExist('Directory `'+str(os.path.dirname(path))+'` does not exist!')		
			logger.info('Writing data to '+path+' ...')					
			with open(path, 'wb') as f:
				for chunk in response.iter_content(chunk_size=1024): 
					if chunk:
						f.write(chunk)
			if not os.path.isfile(path):
				raise FileNotExist('`'+str(path)+'` could not be written!')
		return response
	
	def download_land_water_mask(self, dahiti_id, path,  **kwargs):
		"""Download archive of land water masks from optical imagery for a DAHITI target as GeoTiff (compressed as tar.gz archive)

		Args:
			dahiti_id (int): DAHITI Id
			path (str): Output path of tar.gz archive
			**kwargs : Optional keyword arguments:			
		Returns:				
			Response: Status code of API-request
		
		"""	
		software = None
		if 'software' in kwargs:
			software = kwargs['software']

		logger.info('Download land water mask of DAHITI target with id '+str(dahiti_id)+' ...')
		
		response = self.send_api_request(
			self._api_url+'download-land-water-mask/',
			{			
				'api_key' :  self.api_key,
				'dahiti_id' : dahiti_id,
				'software' : software
			}
		)
		
		if type(response) == requests.models.Response:		
			if not os.path.isdir(os.path.dirname(path)):
				raise DirectoryNotExist('Directory `'+str(os.path.dirname(path))+'` does not exist!')		
			logger.info('Writing data to '+path+' ...')					
			with open(path, 'wb') as f:
				for chunk in response.iter_content(chunk_size=1024): 
					if chunk:
						f.write(chunk)
			if not os.path.isfile(path):
				raise FileNotExist('`'+str(path)+'` could not be written!')
		return response


	def download_water_surface_slope_ascii(self, dahiti_id, **kwargs):
		"""Download time serie of water surface slopes from satellite altimetry for a DAHITI target in ASCII format

		Args:
			dahiti_id (int): DAHITI Id
			**kwargs : Optional keyword arguments:			
		Returns:				
			str: time series of water surface slopes  for a DAHITI target in ASCII format
		
		"""
		kwargs['format'] = "ascii"
		return self.__download_water_surface_slope(dahiti_id, **kwargs)
	
	def download_water_surface_slope_ascii_to_file(self, dahiti_id, path, **kwargs):				
		"""Download time serie of water surface slopes from satellite altimetry for a DAHITI target in ASCII format

		Args:
			dahiti_id (int): DAHITI Id
			path (str) : Output path
			**kwargs : Optional keyword arguments:			
		Returns:				
			str: time series of water surface slopes  for a DAHITI target in ASCII format
		
		"""
		kwargs['format'] = "ascii"
		kwargs['path'] = path		
		return self.__download_water_surface_slope(dahiti_id, **kwargs)
		
	def download_water_surface_slope_json(self, dahiti_id, **kwargs):
		"""Download time serie of water surface slopes from satellite altimetry for a DAHITI target in JSON format

		Args:
			dahiti_id (int): DAHITI Id
			**kwargs : Optional keyword arguments:			
		Returns:				
			dict: time series of water surface slopes  for a DAHITI target in JSON format
		
		"""	
		kwargs['format'] = "json"
		return self.__download_water_surface_slope(dahiti_id, **kwargs)
	
	def download_water_surface_slope_json_to_file(self, dahiti_id, path, **kwargs):	
		"""Download time serie of water surface slopes from satellite altimetry for a DAHITI target in JSON format

		Args:
			dahiti_id (int): DAHITI Id
			path (str) : Output path
			**kwargs : Optional keyword arguments:			
		Returns:				
			dict: time series of water surface slopes  for a DAHITI target in JSON format
		
		"""		
		kwargs['format'] = "json"
		kwargs['path'] = path		
		return self.__download_water_surface_slope(dahiti_id, **kwargs)

	def download_water_surface_slope_csv(self, dahiti_id, **kwargs):
		"""Download time serie of water surface slopes from satellite altimetry for a DAHITI target in ASCII format

		Args:
			dahiti_id (int): DAHITI Id
			**kwargs : Optional keyword arguments:			
		Returns:				
			str: time series of water surface slopes  for a DAHITI target in ASCII format
		
		"""
		kwargs['format'] = "csv"
		return self.__download_water_surface_slope(dahiti_id, **kwargs)
	
	def download_water_surface_slope_csv_to_file(self, dahiti_id, path, **kwargs):
		"""Download time serie of water surface slopes from satellite altimetry for a DAHITI target in CSV format

		Args:
			dahiti_id (int): DAHITI Id
			path (str) : Output path
			**kwargs : Optional keyword arguments:			
		Returns:				
			str: time series of water surface slopes for a DAHITI target in CSV format
		
		"""		
		kwargs['format'] = "csv"
		kwargs['path'] = path		
		return self.__download_water_surface_slope(dahiti_id, **kwargs)

	def download_water_surface_slope_netcdf(self, dahiti_id, path, **kwargs):
		"""Download time serie of water surface slopes from satellite altimetry for a DAHITI target in NetCDF format

		Args:
			dahiti_id (int): DAHITI Id
			path (str) : Output path
			**kwargs : Optional keyword arguments:			
		Returns:				
			Response: Status code of API-request		
		"""				
		kwargs['format'] = "netcdf"
		kwargs['path'] = path		
		return self.__download_water_surface_slope(dahiti_id, **kwargs)
		
	def __download_water_surface_slope(self, dahiti_id, **kwargs):
	
		format = None
		if 'format' in kwargs:
			format = kwargs['format']
			
		software = None
		if 'software' in kwargs:
			software = kwargs['software']

		path = None
		if 'path' in kwargs:
			path = kwargs['path']
		
		parameters = None
		if 'parameters' in kwargs:
			parameters = kwargs['format']
				
		if format in ['netcdf'] and path == None:
			raise ArgumentNotFoundError('Format `netcdf` requires `path` for saving!')
		
		logger.info('Download water surface slope of DAHITI target with id '+str(dahiti_id)+' ...')
		
		response = self.send_api_request(
			self._api_url+'download-water-surface-slope/',
			{			
				'api_key' :  self.api_key,
				'dahiti_id' : dahiti_id,
				'format' : format,
				'software' : software,
				'parameters' : parameters,
			}
		)		
		if type(response) == requests.models.Response:
			try:						
				if format == 'ascii':
					ascii_response = str(response.text)
					if path != None:
						if not os.path.isdir(os.path.dirname(path)):
							raise DirectoryNotExist('Directory `'+str(os.path.dirname(path))+'` does not exist!')		
						logger.info('Writing data to '+path+' ...')
						with open(path, 'w') as f:
							f.write(ascii_response)
						if not os.path.isfile(path):
							raise FileNotExist('`'+str(path)+'` could not be written!')
					return ascii_response
				elif format == 'json':
					json_response = json.loads(response.text)							
					if path != None:
						if not os.path.isdir(os.path.dirname(path)):
							raise DirectoryNotExist('Directory `'+str(os.path.dirname(path))+'` does not exist!')		
						logger.info('Writing data to '+path+' ...')
						with open(path, 'w') as f:
							json.dump(json_response, f)
						if not os.path.isfile(path):
							raise FileNotExist('`'+str(path)+'` could not be written!')
					return json_response
				elif format == 'csv':
					csv_response = str(response.text)
					if path != None:
						if not os.path.isdir(os.path.dirname(path)):
							raise DirectoryNotExist('Directory `'+str(os.path.dirname(path))+'` does not exist!')		
						logger.info('Writing data to '+path+' ...')
						with open(path, 'w') as f:
							f.write(csv_response)
						if not os.path.isfile(path):
							raise FileNotExist('`'+str(path)+'` could not be written!')
					return csv_response
				elif format == 'netcdf':
					if not os.path.isdir(os.path.dirname(path)):
						raise DirectoryNotExist('Directory `'+str(os.path.dirname(path))+'` does not exist!')		
					logger.info('Writing data to '+path+' ...')					
					with open(path, 'wb') as f:
						for chunk in response.iter_content(chunk_size=1024): 
							if chunk:
								f.write(chunk)
					if not os.path.isfile(path):
						raise FileNotExist('`'+str(path)+'` could not be written!')
			except:
				traceback.print_exc()
				
				
		return response

	def download_discharge_ascii(self, dahiti_id, **kwargs):
		"""Download time series of river discharge from satellite altimetry and optical imagery for a DAHITI target in ASCII format

		Args:
			dahiti_id (int): DAHITI Id
			**kwargs : Optional keyword arguments:			
		Returns:				
			str: Discharge time series for a DAHITI target in ASCII format
		
		"""
		kwargs['format'] = "ascii"
		return self.__download_discharge(dahiti_id, **kwargs)
	
	def download_discharge_ascii_to_file(self, dahiti_id, path, **kwargs):				
		"""Download time series of river discharge from satellite altimetry and optical imagery for a DAHITI target in ASCII format

		Args:
			dahiti_id (int): DAHITI Id
			path (str) : Output path
			**kwargs : Optional keyword arguments:			
		Returns:				
			str: Discharge time series for a DAHITI target in ASCII format
		
		"""
		kwargs['format'] = "ascii"
		kwargs['path'] = path		
		return self.__download_discharge(dahiti_id, **kwargs)
		
	def download_discharge_json(self, dahiti_id, **kwargs):
		"""Download time series of river discharge from satellite altimetry and optical imagery for a DAHITI target in JSON format

		Args:
			dahiti_id (int): DAHITI Id
			**kwargs : Optional keyword arguments:			
		Returns:				
			dict: Discharge time series for a DAHITI target in JSON format
		
		"""
		kwargs['format'] = "json"
		return self.__download_discharge(dahiti_id, **kwargs)
	
	def download_discharge_json_to_file(self, dahiti_id, path, **kwargs):
		"""Download time series of river discharge from satellite altimetry and optical imagery for a DAHITI target in JSON format

		Args:
			dahiti_id (int): DAHITI Id
			path (str) : Output path
			**kwargs : Optional keyword arguments:			
		Returns:				
			str: Discharge time series for a DAHITI target in JSON format
		
		"""		
		kwargs['format'] = "json"
		kwargs['path'] = path		
		return self.__download_discharge(dahiti_id, **kwargs)

	def download_discharge_csv(self, dahiti_id, **kwargs):
		"""Download time series of river discharge from satellite altimetry and optical imagery for a DAHITI target in CSV format

		Args:
			dahiti_id (int): DAHITI Id			
			**kwargs : Optional keyword arguments:			
		Returns:				
			str: Discharge time series for a DAHITI target in CSV format
		
		"""
		kwargs['format'] = "csv"
		return self.__download_discharge(dahiti_id, **kwargs)
	
	def download_discharge_csv_to_file(self, dahiti_id, path, **kwargs):				
		"""Download time series of river discharge from satellite altimetry and optical imagery for a DAHITI target in CSV format

		Args:
			dahiti_id (int): DAHITI Id
			path (str) : Output path
			**kwargs : Optional keyword arguments:			
		Returns:				
			str: Discharge time series for a DAHITI target in CSV format
		
		"""
		kwargs['format'] = "csv"
		kwargs['path'] = path		
		return self.__download_discharge(dahiti_id, **kwargs)

	def download_discharge_netcdf(self, dahiti_id, path, **kwargs):
		"""Download time series of river discharge from satellite altimetry and optical imagery for a DAHITI target in NetCDF format

		Args:
			dahiti_id (int): DAHITI Id
			path (str) : Output path
			**kwargs : Optional keyword arguments:			
		Returns:				
			Response: Status code of API-request
		
		"""		
		kwargs['format'] = "netcdf"
		kwargs['path'] = path		
		return self.__download_discharge(dahiti_id, **kwargs)
		
	def __download_discharge(self, dahiti_id, **kwargs):
				
		format = None
		if 'format' in kwargs:
			format = kwargs['format']
			
		software = None
		if 'software' in kwargs:
			software = kwargs['software']

		path = None
		if 'path' in kwargs:
			path = kwargs['path']
		
		parameters = None
		if 'parameters' in kwargs:
			parameters = kwargs['format']
				
		if format in ['netcdf'] and path == None:
			raise ArgumentNotFoundError('Format `netcdf` requires `path` for saving!')
		
		logger.info('Download river discharge of DAHITI target with id '+str(dahiti_id)+' ...')
		
		response = self.send_api_request(
			self._api_url+'download-discharge/',
			{			
				'api_key' :  self.api_key,
				'dahiti_id' : dahiti_id,
				'format' : format,
				'software' : software,
				'parameters' : parameters,
			}
		)
		if type(response) == requests.models.Response:			
			try:						
				if format == 'ascii':
					ascii_response = str(response.text)
					if path != None:
						if not os.path.isdir(os.path.dirname(path)):
							raise DirectoryNotExist('Directory `'+str(os.path.dirname(path))+'` does not exist!')		
						logger.info('Writing data to '+path+' ...')
						with open(path, 'w') as f:
							f.write(ascii_response)
						if not os.path.isfile(path):
							raise FileNotExist('`'+str(path)+'` could not be written!')
					return ascii_response
				elif format == 'json':
					json_response = json.loads(response.text)							
					if path != None:
						if not os.path.isdir(os.path.dirname(path)):
							raise DirectoryNotExist('Directory `'+str(os.path.dirname(path))+'` does not exist!')		
						logger.info('Writing data to '+path+' ...')
						with open(path, 'w') as f:
							json.dump(json_response, f)
						if not os.path.isfile(path):
							raise FileNotExist('`'+str(path)+'` could not be written!')
					return json_response
				elif format == 'csv':
					csv_response = str(response.text)
					if path != None:
						if not os.path.isdir(os.path.dirname(path)):
							raise DirectoryNotExist('Directory `'+str(os.path.dirname(path))+'` does not exist!')		
						logger.info('Writing data to '+path+' ...')
						with open(path, 'w') as f:
							f.write(csv_response)
						if not os.path.isfile(path):
							raise FileNotExist('`'+str(path)+'` could not be written!')
					return csv_response
				elif format == 'netcdf':
					if not os.path.isdir(os.path.dirname(path)):
						raise DirectoryNotExist('Directory `'+str(os.path.dirname(path))+'` does not exist!')		
					logger.info('Writing data to '+path+' ...')					
					with open(path, 'wb') as f:
						for chunk in response.iter_content(chunk_size=1024): 
							if chunk:
								f.write(chunk)
					if not os.path.isfile(path):
						raise FileNotExist('`'+str(path)+'` could not be written!')
			except:
				traceback.print_exc()
				
		return response

		
	def get_target_info(self, dahiti_id, software=None, path=None):
		
		logger.info('Get target info DAHITI target with id '+str(dahiti_id)+' ...')
				
		response = self.send_api_request(
			self._api_url+'get-target-info/',
			{			
				'api_key' :  self.api_key,
				'dahiti_id' : dahiti_id,
			}
		)		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)	
			return json_response
			
		return response
	
	def list_targets(self, args):
		
		logger.info('List targets ...')
		
		args['api_key'] = self.api_key
		
		response = self.send_api_request(
			self._api_url+'list-targets/',
			args
		)	
				
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)
			logger.info(str(len(json_response['data']))+' target(s) found!')
			return json_response['data']
			
		return response
	
	def create_target(self, args):
		
		logger.info('Create new DAHITI target ...')
		
		args['api_key'] = self.api_key
		
		response = self.send_api_request(
			self._api_url+'create-target/',
			args
		)
		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)
			return json_response['dahiti_id']
			
		return response
	
	def update_AOI_from_JRC(self, dahiti_id, args):
		
		logger.info('Update AOI from JRC ...')
		
		args['api_key'] = self.api_key
		args['dahiti_id'] = dahiti_id		
		
		response = self.send_api_request(
			self._api_url+'update-AOI-from-JRC/',
			args
		)
		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)
			return json_response['data']
			
		return response
		
	def is_location_in_AOI(self, args):
		
		logger.info('Is location in AOI ...')
		
		args['api_key'] = self.api_key
		
		response = self.send_api_request(
			self._api_url+'is-location-in-AOI/',
			args
		)
		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)
			return json_response['data']
			
		return response
	
	def get_targets_in_AOI(self, args):
		
		logger.info('Get DAHITI targets in AOI ...')
		
		args['api_key'] = self.api_key
		
		response = self.send_api_request(
			self._api_url+'get-targets-in-AOI/',
			args
		)
		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)
			return json_response['data']
			
		return response
	
	def update_PLD_information(self, dahiti_id):
		
		logger.info('Update PLD information ...')
		
		args = {}
		args['api_key'] = self.api_key
		args['dahiti_id'] = dahiti_id		
		
		response = self.send_api_request(
			self._api_url+'update-PLD-information/',
			args
		)
		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)
			return json_response['data']
			
		return response
	
	def get_spreadsheet(self, args):
		
		logger.info('Get Spreadsheet ...')
		
		args['api_key'] = self.api_key
		
		response = self.send_api_request(
			self._api_url+'get-spreadsheet/',
			args
		)
		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)
			return json_response['data']
			
		return response
	
	def get_country(self, tld):
		
		logger.info('Get Country ...')
		
		args = {}
		args['api_key'] = self.api_key
		args['tld'] = tld
		
		response = self.send_api_request(
			self._api_url+'get-country/',
			args
		)
		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)
			return json_response['data']
			
		return response
		
	def get_targets_by_reach_id(self, reach_id):
		
		logger.info('Get DAHITI targets by reach_id `'+reach_id+'` ...')
		
		args = {}
		args['api_key'] = self.api_key
		args['reach_id'] = reach_id
		
		response = self.send_api_request(
			self._api_url+'get-targets-by-reach-id/',
			args
		)
		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)
			return json_response['data']
			
		return response
	
	def get_targets_in_AOI(self, aoi):
		
		logger.info('Get DAHITI targets in polygon ...')
		
		import shapely
		if type(aoi) != shapely.geometry.polygon.Polygon:
			logger.error('AOI is not a shapely polygon!')
			return 9
		
		response = self.send_api_request(
			self._api_url+'get-targets-in-AOI/',
			{
				'api_key' :  self.api_key,				
				'aoi' : aoi.wkt,
			}
		)
		
		if type(response) == requests.models.Response:			
			json_response = json.loads(response.text)
			return json_response['data']
			
		return response
		
	def get_nearest_target(self, longitude, latitude):
		
		logger.info('Get nearest DAHITI target to location (`'+str(longitude)+'`,`'+str(latitude)+'`) ...')
		
		args = {}
		args['api_key'] = self.api_key
		args['longitude'] = longitude
		args['latitude'] = latitude
		
		response = self.send_api_request(
			self._api_url+'get-nearest-target/',
			args
		)
		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)
			return json_response['data']
			
		return response
	
	
	
	def create_target(self, longitude, latitude, target_type, target_name):

		logger.info('Create new DAHITI targets')
				
		response = self.send_api_request(
			self._api_url+'create-target/',
			{			
				'api_key' :  self.api_key,				
				'longitude' : longitude,
				'latitude' : latitude,
				'type' : target_type,
				'target_name' : target_name,
			}
		)
		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)
			return json_response['dahiti_id']
			
		return response
	
	def update_AOI_from_SWORD(self, dahiti_id, SWORD_version, centerline_length, reach_boundary, limit_point_distance):

		logger.info('Update AOI of DAHITI targets from SWORD')
				
		response = self.send_api_request(
			self._api_url+'update-AOI-from-SWORD/',
			{			
				'api_key' :  self.api_key,				
				'dahiti_id' : dahiti_id,
				'SWORD_version' : SWORD_version,
				'centerline_length' : centerline_length,
				'reach_boundary' : reach_boundary,
				'limit_point_distance' : limit_point_distance,
			}
		)
		
		if type(response) == requests.models.Response:
			json_response = json.loads(response.text)			
			return json_response
			
		return response		