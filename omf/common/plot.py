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

import logging

logger = logging.getLogger(__name__)

class Plot:
    @staticmethod
    def save_fig(plt, path):
        """
        Save matplotlib Figure to specific path with license text
        :param plt: matplotlib pyplot context
        :param path: path to save file
        :return:
        """
        plt.figtext(0.01, 0.02, 'Plot created by matplotlib. The license for matplotlib can be found here: http://matplotlib.org/users/license.html.', va='top', size='x-small')
        logger.debug("Saving matplotlib's figure to %s", path)
        plt.savefig(path)