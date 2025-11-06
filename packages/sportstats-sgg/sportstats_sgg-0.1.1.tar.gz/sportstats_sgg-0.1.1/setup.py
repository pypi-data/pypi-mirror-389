from setuptools import setup, find_packages

setup(
    name='sportstats_sgg',  # El nombre único que tendrá en PyPI
    version='0.1.1',  # La versión inicial. Debe coincidir con __init__.py
    author='Sergio Glez',
    author_email='sergiogg97@gmail.com',
    description='Un paquete de ejemplo para análisis deportivo.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',

    # Encuentra automáticamente el paquete en la carpeta 'sportstats_sgg'
    packages=find_packages(), 

    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)