from setuptools import setup, find_packages

setup(
    name='txtcleanen',
    version='1.0.0',
    author='Md. Ismiel Hossen Abir',
    author_email='ismielabir1971@gmail.com',
    description='A lightweight Python package to clean English text by removing HTML tags, URLs, emojis, digits, and punctuation.',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Text Processing :: Filters',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)