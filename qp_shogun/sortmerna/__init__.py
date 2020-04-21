# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from qiita_client import QiitaCommand

from .sortmerna import sortmerna

__all__ = ['sortmerna']

# Defining the Sortmerna command
req_params = {'input': ('artifact', ['per_sample_FASTQ'])}
opt_params = {
    'Output blast format': ['interger', '1']
    'Number of alignments': ['integer', '1']
    'Number of threads': ['integer', '5']
    }
outputs = {'Non-ribosomal reads': 'per_sample_FASTQ',
           'Ribosomal reads': 'per_sample_FASTQ'}

sortmerna_cmd = QiitaCommand(
    'Sortmerna v2.1b', "Ribosomal read filtering", sortmerna,
    req_params, opt_params, outputs)
