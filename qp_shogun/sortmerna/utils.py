# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# This file contains functions used by multiple commands
# -----------------------------------------------------------------------------

import gzip
from os.path import join, exists
from functools import partial
from qiita_client import ArtifactInfo


def _gzip_uncompress(input_file):
    if input_file.endswith('.fastq.gz'):
        input_filename_uncompressed = input_file.replace(
            '.fastq.gz', '.fastq')
        # Uncompressing and reading the .gz file
        input = gzip.GzipFile(input_file, 'rb')
        s = input.read()
        input.close()
        # Writing uncompressed data into a file
        output = open(input_filename_uncompressed, 'wb')
        output.write(s)
        output.close()
        # Return the .fastq filename
        return input_filename_uncompressed
    else:
        raise ValueError('File %s has an unexpected name' % input_file)


def _per_sample_ainfo(
        out_dir, samples, suffixes, prg_name,
        files_type_name, fwd_and_rev=False):
    files = []
    missing_files = []
    smd = partial(join, out_dir)
    for rp, _, _, _ in samples:
        for suff in suffixes:
            fname = smd(suff % rp)
            if exists(fname):
                if fname.endswith('R1.fastq'):
                    ftype = 'raw_forward_seqs'
                elif fname.endswith('R2.fastq'):
                    ftype = 'raw_reverse_seqs'
                else:
                    # this should never happen and it's not really possible
                    # to reproduce so no tests!
                    raise ValueError('File %s has an unexpected name' % fname)
                files.append((fname, ftype))
            else:
                missing_files.append(fname)

    if not files:
        # Command did not create any files, which means that no sequence
        # was kept after quality control and filtering for host data
        raise ValueError("No sequences left after %s" % prg_name)

    return [ArtifactInfo(files_type_name, 'per_sample_FASTQ', files)]
