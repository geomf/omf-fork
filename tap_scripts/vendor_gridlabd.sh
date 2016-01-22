#!/bin/bash -x
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
REQUIRED_APT_PACKAGES="fakeroot alien dpkg patch"
GRIDLABD_PACKAGE="gridlabd-3.1.0-1.x86_64.rpm"
THIS_FILE_DIR=$(cd $(dirname $0); pwd)
TARGET_PACKAGE_NAME="${THIS_FILE_DIR}/gridlabd*.deb"

if [ -f $THIS_FILE_DIR/../vendor/gridlabd*.deb ]; then
  echo "Gridlab-d is installed"
else
  cd $THIS_FILE_DIR
  for PKG in $REQUIRED_APT_PACKAGES; do
    dpkg-query -W $PKG || sudo apt-get -y install $PKG
  done


  wget http://sourceforge.net/projects/gridlab-d/files/gridlab-d/Last%20stable%20release/$GRIDLABD_PACKAGE -O $GRIDLABD_PACKAGE
  fakeroot alien --keep-version --to-deb $GRIDLABD_PACKAGE

  #patch gridlabd package to allow running from places other than /usr/bin
  rm -r ${THIS_FILE_DIR}/gridlabd_package || true
  dpkg-deb -x ${TARGET_PACKAGE_NAME} ${THIS_FILE_DIR}/gridlabd_package
  dpkg-deb -e ${TARGET_PACKAGE_NAME} ${THIS_FILE_DIR}/gridlabd_package/DEBIAN

  patch ${THIS_FILE_DIR}/gridlabd_package/usr/bin/gridlabd < ${THIS_FILE_DIR}/gridlabd_run.patch

  dpkg-deb -b ${THIS_FILE_DIR}/gridlabd_package ${TARGET_PACKAGE_NAME}
  rm -r ${THIS_FILE_DIR}/gridlabd_package


  mv gridlab*.deb $THIS_FILE_DIR/../vendor/
fi

echo "Done."
