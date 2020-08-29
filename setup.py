import setuptools

setuptools.setup(\
    name='actuarydesk',\
    version='0.0.5',\
    author='Arief Anbiya',\
    author_email='anbarief@live.com',\
    description='Tools for actuary to model and analyze simple products or for actuarial students to practice.',\
    url='https://github.com/anbarief/actuarydesk',\
    packages=setuptools.find_packages(),\
    classifiers=["Programming Language :: Python :: 3",\
                 "License :: OSI Approved :: MIT License",\
                 "Operating System :: OS Independent"],\
    python_requires='>=3.6', \
    install_requires=['pandas'])
