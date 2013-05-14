from distutils.core import setup

setup(
		name='ReferenceFrame',
		version='1.0',
		description='Starry Expanse reference image browser',
		author='Andrew Kennedy, Philip Peterson',
		author_email='andrew@starryexpanse.com, philip@starryexpanse.com',
		url='http://github.com/starryexpanse/Reference-Browser',
		packages=['referenceframe'],
		install_requires=[
			'Flask',
			'sqlalchemy',
		]
)
