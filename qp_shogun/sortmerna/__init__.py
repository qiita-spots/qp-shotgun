from qiita_client import QiitaCommand

from .sortmerna import sortmerna

__all__ = ['sortmerna']

# Defining the Sortmerna command
req_params = {'input': ('artifact', ['per_sample_FASTQ'])}
opt_params = {
    # Threads used
    'Number of threads': ['integer', '5']
    }
outputs = {'Non-ribosomal reads': 'per_sample_FASTQ',
           'Ribosomal reads': 'per_sample_FASTQ'}

sortmerna_cmd = QiitaCommand(
    'Sortmerna v2.1b', "Ribosomal read filtering", sortmerna,
    req_params, opt_params, outputs)
