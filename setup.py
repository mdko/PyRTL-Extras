from setuptools import setup, find_packages

setup(
    name = 'pyrtl_extras',
    version = '0.0.0',
    packages =  find_packages(),
    description = 'My Extra Library of PyRTL Fun',
    author =  'Michael Christensen',
    author_email =  'mchristensen@cs.ucsb.edu',
    #url =  '',
    #download_url = '',
    install_requires =  ['six'],
    tests_require =  ['tox','nose'],
    extras_require =  {},
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
        'Topic :: System :: Hardware'
        ]
)
