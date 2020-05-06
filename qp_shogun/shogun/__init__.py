# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from qiita_client import QiitaCommand
from .shogun import shogun
from .utils import (generate_shogun_dflt_params, get_dbs_list)
from os import environ


__all__ = ['shogun']

# Define the shogun command
default_db_list = get_dbs_list(environ["QC_SHOGUN_DB_DP"])
req_params = {'input': ('artifact', ['per_sample_FASTQ'])}
opt_params = {
    # database
    'Database': ["choice: [%s]" % default_db_list],
    # aligner
    'Aligner tool': ['choice:[' +
                     '"utree", ' +
                     '"burst", ' +
                     '"bowtie2"]', 'bowtie2'],
    # threads
    'Number of threads': ['integer', '5'],
    'Capitalist': ['boolean', 'False'],
    'Percent identity': ['float', '0.95'],
    }
outputs = {
    'Shogun Alignment Profile': 'BIOM',
    'Taxonomic Predictions - phylum': 'BIOM',
    'Taxonomic Predictions - genus': 'BIOM',
    'Taxonomic Predictions - species': 'BIOM',
    }
dflt_param_set = generate_shogun_dflt_params()

shogun_cmd = QiitaCommand(
    'Shogun v1.0.7', "Functional and Taxonomic Predictions", shogun,
    req_params, opt_params, outputs, dflt_param_set)
