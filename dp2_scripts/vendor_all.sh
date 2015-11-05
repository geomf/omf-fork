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

if [[ -f ]]; then
#uninstall python
    rm -rf ${INSTALL_DIR}/* -r || true
#uninstall wheels
    rm ${THIS_FILE_DIR}/../vendor/*.whl || true
#uninstall deb packages
    rm ${THIS_FILE_DIR}/../vendor/*.deb || true
fi

echo "Get python 2.7.9 and prepare Virtual Env"
./get_python.sh

echo "Get python requirements and creates wheels"
./vendor_python_dependencies.sh

echo "Get gridLab-D as .RPM and convert it to .DEB"
./vendor_gridlabd.sh

echo "Get packages from outside repositories"
./vendor_other_packages.sh


echo "Install python requirements locally"
sudo pip install -r ../requirements.txt
sudo pip install decorator      #TODO: determine, why it is not required in container, but required locally?


echo "Install .DEB packages"
sudo dpkg -i ../vendor/libmdbodbc1_0.7~rc1-4_amd64.deb
sudo dpkg -i ../vendor/gridlabd_3.1.0-1_amd64.deb

