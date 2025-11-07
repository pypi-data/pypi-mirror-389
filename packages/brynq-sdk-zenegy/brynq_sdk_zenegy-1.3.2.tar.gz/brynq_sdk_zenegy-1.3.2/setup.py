from setuptools import setup, find_namespace_packages

setup(
    name='brynq_sdk_zenegy',
    version='1.3.2',
    description='Zenegy wrapper from BrynQ',
    long_description='Zenegy wrapper from BrynQ',
    author='BrynQ',
    author_email='support@brynq.com',
    packages=find_namespace_packages(include=['brynq_sdk*']),
    license='BrynQ License',
    install_requires=[
        'brynq-sdk-brynq>=3'
    ],
    zip_safe=False,
)
