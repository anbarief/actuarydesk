import setuptools

setuptools.setup(\
    name='actuarydesk',\
    version='0.0.6',\
    author='Arief Anbiya',\
    author_email='anbarief@live.com',\
    description='Tools for actuary to model and analyze simple products or for actuarial students to practice.',\
    url='https://github.com/anbarief/actuarydesk',\
    packages=setuptools.find_packages(),\
    classifiers=["Programming Language :: Python :: 3",\
                 "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",\
                 "Operating System :: OS Independent",\
                 "Topic :: Scientific/Engineering :: Mathematics",\
                 "Intended Audience :: Financial and Insurance Industry"],\
    python_requires='>=3.6', \
    install_requires=['pandas'])
