#!/bin/bash
#
# Open Modeling Framework (OMF) Software for simulating power systems behavior
# Copyright (c) 2015, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
set -eou pipefail
set -x

PYTHON_VERSION=2.7.9
VIRTUALENV_VERSION=13.1.0

INSTALL_DIR=$HOME/.localpython
THIS_FILE_DIR=$(cd $(dirname $0); pwd)

mkdir -p ${INSTALL_DIR}
rm -rf ${INSTALL_DIR}/* -r || true

cd ${THIS_FILE_DIR}

#Python from source
#curl https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz | tar xvz
#cd Python-${PYTHON_VERSION}
#./configure --enable-unicode=ucs4 --prefix=${INSTALL_DIR} && make && make install


#PRE-BAKED python: 
curl https://pivotal-buildpacks.s3.amazonaws.com/python/binaries/cflinuxfs2/python-${PYTHON_VERSION}.tar.gz | tar -C ${INSTALL_DIR} -xvz


cd ${THIS_FILE_DIR}
curl https://pypi.python.org/packages/source/v/virtualenv/virtualenv-${VIRTUALENV_VERSION}.tar.gz | tar xvz
cd virtualenv-${VIRTUALENV_VERSION}
${INSTALL_DIR}/bin/python setup.py install

