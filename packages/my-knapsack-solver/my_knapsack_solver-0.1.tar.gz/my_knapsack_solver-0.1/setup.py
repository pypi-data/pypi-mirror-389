from setuptools import setup, find_packages

setup(
    name='my_knapsack_solver',  # The name of your package [cite: 18]
    version='0.1',  # The starting version [cite: 19]
    packages=find_packages(),  # This finds your package folders automatically [cite: 20]
    
    # You can add other details here if you want
    author='Your Name',
    author_email='your.email@example.com',
    description='A simple 0/1 knapsack problem solver.',

    # These are dependencies your package needs to run [cite: 21]
    # Our knapsack code is pure Python, so it doesn't have any. [cite: 23]
    install_requires=[
    ],

    # This tells Python it's compatible with Python 3
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)