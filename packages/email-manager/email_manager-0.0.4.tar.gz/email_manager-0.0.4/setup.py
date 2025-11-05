from setuptools import setup

VERSION = '0.0.4' 
DESCRIPTION = 'Email manager'
LONG_DESCRIPTION = 'Email manager'

# Configurando
setup(
        name="email-manager", 
        version=VERSION,
        author="Carlos Pacheco",
        license='MIT',
        author_email="carlos.pacheco@kemok.io",
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        url='https://github.com/Kemok-Repos/email-manager',
        packages=['email_manager']
)