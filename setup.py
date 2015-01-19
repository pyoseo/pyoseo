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
        'django-activity-stream',
        'django-grappelli',
        'pyxb',
        'redis',
        'celery',
        'lxml',
        'wsgiref',
        'librabbitmq',
        'django-mail-queue',
    ],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'install_celery_service = oseoserver.scripts.installcelery:main',
            'install_proftpd = oseoserver.scripts.installproftpd:main',
            'configure_apache = oseoserver.scripts.configureapache:main',
        ],
    },
)
