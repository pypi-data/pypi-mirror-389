from setuptools import setup, find_packages

setup(
    name='ChromifyPro',
    version='1.0.0',
    author='tingkan',
    author_email='tingyu@mail.lhu.edu.tw',
    description='Color conversion library',
    long_description=open('README.md', 'r', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    package_data={
        'ChromifyPro': ["*", "chromify_template.zip"],
    },
    include_package_data=True,
    packages=find_packages(),
    classifiers=[
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    ],
    install_requires=[
    'termcolor>=2.1.0'
    ]
)