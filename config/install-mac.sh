#!/bin/sh

# http://www.serpentcs.com/serpentcs-openerp-installation-guide-on-mac-osx-10-9

# Notizen Postgres:
# 
# postgres=# 
# create role alsu superuser;
# ALTER ROLE alsu with LOGIN ;


# Karinas-iMac:config root# export PATH=/Library/PostgreSQL/9.4/bin/:$PATH
# Karinas-iMac:config root# pip install psycopg2
# Collecting psycopg2
#  Using cached psycopg2-2.6.tar.gz
# Installing collected packages: psycopg2
#  Running setup.py install for psycopg2
# Successfully installed psycopg2-2.6
#
#


# Install PyChart using following commands.
# wget http://download.gna.org/pychart/PyChart-1.39.tar.gz
# tar xvfz PyChart-1.39.tar
# cd PyChart-1.39
# sudo python2.7 setup.py build
# sudo python2.7 setup.py install

# pyyaml


#server
port install py27-decorator
port install py27-pypdf
port install py27-eventlet
port install py27-restkit
port install py27-webdav
port install py27-werkzeug
port install py27-memcache
port install py27-setuptools
port install py27-lxml
port install py27-mako 
port install py27-egenix-mxdatetime
port install py27-dateutil
port install py27-psycopg2
port install py27-pychart
port install py27-pydot
port install py27-psutil
port install py27-tz
port install py27-reportlab
port install py27-yaml
port install py27-vobject
port install py27-setuptools
port install py27-unittest2
port install py27-mock
port install py27-docutils
port install py27-openid
port install py27-requests
port install py27-jinja2
port install py27-vatnumber
port install py27-xlwt
port install py27-geoip
port install py27-vatnumber
port install py27-passlib
port install py27-gevent

#ruby
port install ruby
port install ruby-dev

#aeroolib
port install py27-relatorio
port install py27-genshi
port install py27-cairo
port install py27-pycha

#port install libreoffic-base
#port install libreoffice-calc
#port install libreoffice-draw
#port install libreoffice-impress
#port install libreoffice-writer

#web
port install py27-cherrypy3
port install py27-pybabel
port install py27-formencode
port install py27-simplejson 

#misc
port install py27-ipcalc
port install pdftk

#install pip for further installation
python -m easy_install pip

#install p4j 
python -m pip install py4j

#install pygal depends
port install libffi-dev
port install py27-cairosvg
port install py27-cssselect
python -m pip install tinycss

#install printing depends
port install wkhtmltopdf 
python -m pip install wkhtmltopdf

#install saas depends
gem install sass compass bootstrap-sass
