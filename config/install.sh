#!/bin/sh

#server
apt-get -y install python-decorator
apt-get -y install python-pypdf
apt-get -y install python-eventlet
apt-get -y install python-restkit
apt-get -y install python-webdav
apt-get -y install python-werkzeug
apt-get -y install python-memcache
apt-get -y install python-setuptools
apt-get -y install python-lxml
apt-get -y install python-mako 
apt-get -y install python-egenix-mxdatetime
apt-get -y install python-dateutil
apt-get -y install python-psycopg2
apt-get -y install python-pychart
apt-get -y install python-pydot
apt-get -y install python-psutil
apt-get -y install python-tz
apt-get -y install python-reportlab
apt-get -y install python-yaml
apt-get -y install python-vobject
apt-get -y install python-setuptools
apt-get -y install python-unittest2
apt-get -y install python-mock
apt-get -y install python-docutils
apt-get -y install python-openid
apt-get -y install python-requests
apt-get -y install python-jinja2
apt-get -y install python-vatnumber
apt-get -y install python-xlwt
apt-get -y install python-geoip
apt-get -y install python-vatnumber
apt-get -y install python-passlib
apt-get -y install python-gevent
apt-get -y install python-pyicu

#ruby
apt-get -y install ruby
apt-get -y install ruby-dev

#aeroolib
apt-get -y install python-relatorio
apt-get -y install python-genshi
apt-get -y install python-cairo
apt-get -y install python-pycha

#apt-get -y install libreoffic-base
#apt-get -y install libreoffice-calc
#apt-get -y install libreoffice-draw
#apt-get -y install libreoffice-impress
#apt-get -y install libreoffice-writer

#web
apt-get -y install python-cherrypy3
apt-get -y install python-pybabel
apt-get -y install python-formencode
apt-get -y install python-simplejson 

#misc
apt-get -y install python-ipcalc
apt-get -y install pdftk
apt-get -y install python-couchdb

#install pip for further installation
python -m easy_install pip

#install p4j 
python -m pip install py4j

#install pygal depends
apt-get -y install libffi-dev
apt-get -y install python-cairosvg
apt-get -y install python-cssselect
python -m pip install tinycss

#install printing depends
#apt-get -y install wkhtmltopdf
python -m pip install wkhtmltopdf

#install saas depends
gem install sass compass bootstrap-sass