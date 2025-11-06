from setuptools import setup, find_packages
import os 

this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()
    
setup(
    name='himpunan_sigma',
    version='0.2.1',         
    author='Mimimi',     
    author_email='swissarchipelago@gmail.com',
    description='Implementasi Himpunan Python untuk Tugas Matematika Diskrit',
    long_description=long_description,
    long_description_content_type='text/markdown',
    
    packages=find_packages(), 
    
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: Mathematics',
    ],
    python_requires='>=3.6',
)