from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
	long_description = fh.read() 

' read version '
version = None
with open("version.txt", "r", encoding="utf-8") as fh:
    version = fh.read()

setup(
	name='dahitiapi',
	version=version,
	author='Christian Schwatke',
	author_email='christian.schwatke@tum.de', 
	license="MIT",
	license_files=[], 
	packages=find_packages(where="src"),
	package_dir={"": "src"},
	#url='https://gitlab.lrz.de/openadb/python3-dahitiapi',
	description='DAHITI-API',
	long_description=long_description,
	long_description_content_type="text/markdown", 
	include_package_data=True,
	package_data={},
	install_requires=[],
	scripts=[],
	
	# Project URLs (shown on the PyPI page)
	project_urls={
		"DAHITI Homepage": "https://dahiti.dgfi.tum.de/",
		"Documentation": "https://dahiti-api.readthedocs.io/",
		"Source Code": "https://gitlab.lrz.de/openadb/python3-dahitiapi/",
		#"Bug Tracker": "https://gitlab.lrz.de/openadb/python3-dahitiapi/issues/",
		#"Changelog": "https://gitlab.lrz.de/openadb/python3-dahitiapi/latest/changelog/",
	},

	classifiers=[
		"Programming Language :: Python :: 3",
	#	"License :: MIT License",
		"Operating System :: OS Independent",
	],

	python_requires='>=3.8',
)

