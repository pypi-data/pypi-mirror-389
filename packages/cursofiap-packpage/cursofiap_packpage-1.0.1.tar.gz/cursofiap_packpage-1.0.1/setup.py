from setuptools import setup, find_packages
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
setup(
    name='cursofiap-packpage',
    version='1.0.1',
    packages=find_packages(),
    description='Descricao da sua lib cursofiap',
    author='dridev',
    author_email='adrielroquedev@gmail.com',
    url='https://github.com/tadrianonet/cursofiap',  
    license='MIT',  
    long_description=long_description,
    long_description_content_type='text/markdown'
)
