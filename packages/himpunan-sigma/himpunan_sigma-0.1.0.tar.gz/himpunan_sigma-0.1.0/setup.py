from setuptools import setup, find_packages

setup(
    name='himpunan_sigma',
    version='0.1.0',         
    author='Mimimi',     
    author_email='swissarchipelago@gmail.com',
    description='Implementasi Himpunan Python untuk Tugas Matematika Diskrit',
    
    packages=find_packages(), 
    
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: Mathematics',
    ],
    python_requires='>=3.6',
)