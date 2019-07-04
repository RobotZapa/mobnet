import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()
setuptools.setup(
     name='mobnet',
     version='1.0',
     scripts=['name_server.py', 'server.py'],
     author="Michael Elliott",
     author_email="robotzapa@gmail.com",
     description="A Dead Simple Python Subscriber/Publisher Network",
     long_description=long_description,
   long_description_content_type="text/markdown",
     url="https://github.com/robotzapa/mobnet",
     packages=setuptools.find_packages(),
     classifiers=[
         "Programming Language :: Python :: 3.6",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
     ],
 )