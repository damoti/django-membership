from setuptools import setup
setup(
    name='django-membership',
    version='0.0.1',
    url='https://github.com/damoti/django-membership',
    license='BSD',
    description='Django membership system.',
    author='Lex Berezhny',
    author_email='lex@damoti.com',
    keywords='django,user,membership,account,subscription',
    install_requires=[
        "django>=4.2",
        "django-ninja>=0.21.0",
        "channels>=4.0.0",
        "pyjwt>=2.6.0",
        "crispy-bootstrap5>=0.7",
    ],
    extras_require={
        "development": [
            "daphne",
            "selenium",
            "webdriver-manager",
        ],
    },
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
