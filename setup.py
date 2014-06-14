from setuptools import setup, find_packages

execfile('pyoseo/version.py')

setup(
    name='pyoseo',
    version=__version__,
    description='An OGC OSEO web server based on django and pyxb',
    long_description='',
    author='Ricardo Silva',
    author_email='ricardo.garcia.silva@gmail.com',
    url='',
    classifiers=[''],
    platforms=[''],
    license='',
    #packages=find_packages(),
    package_dir={'': 'pyoseo',},
    packages=find_packages('pyoseo'),
    install_requires=[
        'django',
        'pyxb',
        'celery',
        'lxml',
        'wsgiref',
        'giosystemcore',
        'librabbitmq',
    ],
    include_package_data=True,
)
