class NotFoundError(Exception):    
	def __init__(self, message):
		super().__init__(message)

class ArgumentNotFoundError(Exception):    
	def __init__(self, message):
		super().__init__(message)

class DirectoryNotExist(Exception):    
	def __init__(self, message):
		super().__init__(message)

class FileNotExist(Exception):    
	def __init__(self, message):
		super().__init__(message)
		
class InternalServerError(Exception):    
	def __init__(self, message):
		super().__init__(message)

class PermissionDeniedError(Exception):    
	def __init__(self, message):
		super().__init__(message)

class DAHITITargetNotFoundError(Exception):    
	def __init__(self, message):
		super().__init__(message)

class DAHITIDatasetNotFoundError(Exception):    
	def __init__(self, message):
		super().__init__(message)