# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from itertools import zip_longest
from os.path import basename, join

from qiita_client import ArtifactInfo

from qiita_client.util import system_call, get_sample_names_by_run_prefix


def make_read_pairs_per_sample(forward_seqs, reverse_seqs, map_file):
    """Recovers read pairing information

    Parameters
    ----------
    forward_seqs : list of str
        The list of forward seqs filepaths
    reverse_seqs : list of str
        The list of reverse seqs filepaths
    map_file : str
        The path to the mapping file

    Returns
    -------
    samples: list of tup
        list of 3-tuples with run prefix, sample name, fwd read fp, rev read fp

    Raises
    ------
    ValueError
        If the rev is not an empty list and the same length than fwd seqs
        The prefixes of the run_prefix don't match the file names

    Notes
    -----
    At this stage it is required that if reverse sequences are present that all
    samples have both a forward and a reverse sequence. However, the read
    trimming step can sometimes eliminate all reverse reads, especially in low
    coverage samples with poor overall reverse read quality.
    """

    # sort forward seqs
    forward_seqs.sort()

    # check that rev seqs are same len
    if reverse_seqs:
        if len(forward_seqs) != len(reverse_seqs):
            raise ValueError('Your reverse and forward files are of different '
                             'length. Forward: %s. Reverse: %s.' %
                             (', '.join(forward_seqs),
                              ', '.join(reverse_seqs)))
        reverse_seqs.sort()

    # get run prefixes
    # These are prefixes that should match uniquely to forward reads
    # sn_by_rp is dict of samples keyed by run prefixes
    sn_by_rp = get_sample_names_by_run_prefix(map_file)

    # make pairings
    samples = []
    used_prefixes = set()
    for i, (fwd_fp, rev_fp) in enumerate(zip_longest(forward_seqs,
                                                     reverse_seqs)):
        # fwd_fp is the fwd read filepath
        fwd_fn = basename(fwd_fp)

        # iterate over run prefixes and make sure only one matches
        run_prefix = None
        for rp in sn_by_rp:
            if fwd_fn.startswith(rp) and run_prefix is None:
                run_prefix = rp
            elif fwd_fn.startswith(rp) and run_prefix is not None:
                raise ValueError('Multiple run prefixes match this fwd read: '
                                 '%s' % fwd_fn)

        # make sure that we got one matching run prefix:
        if run_prefix is None:
            raise ValueError('No run prefix matching this fwd read: %s'
                             % fwd_fn)

        if run_prefix in used_prefixes:
            raise ValueError('This run prefix matches multiple fwd reads: '
                             '%s' % run_prefix)

        if rev_fp is None:
            samples.append((run_prefix, sn_by_rp[run_prefix], fwd_fp, None))
        else:
            rev_fn = basename(rev_fp)
            # if we have reverse reads, make sure the matching pair also
            # matches the run prefix:
            if not rev_fn.startswith(run_prefix):
                raise ValueError('Reverse read does not match this run prefix.'
                                 '\nRun prefix: %s\nForward read: %s\n'
                                 'Reverse read: %s\n' %
                                 (run_prefix, fwd_fn, rev_fn))

            samples.append((run_prefix, sn_by_rp[run_prefix], fwd_fp,
                            rev_fp))

        used_prefixes.add(run_prefix)

    return(samples)


def format_kneaddata_params(parameters):

    params = []

    for param in sorted(parameters):
        value = parameters[param]

        if value is True:
            params.append('--%s' % param)
            continue
        elif value is False:
            continue
        elif value:
            params.append('--%s %s' % (param, value))
            continue

    param_string = ' '.join(params)

    return(param_string)


def generate_kneaddata_commands(forward_seqs, reverse_seqs, map_file,
                                out_dir, parameters):
    """Generates the KneadData commands

    Parameters
    ----------
    forward_seqs : list of str
        The list of forward seqs filepaths
    reverse_seqs : list of str
        The list of reverse seqs filepaths
    map_file : str
        The path to the mapping file
    out_dir : str
        The job output directory
    parameters : dict
        The command's parameters, keyed by parameter name

    Returns
    -------
    cmds: list of str
        The KneadData commands
    samples: list of tup
        list of 3-tuples with run prefix, sample name, fwd read fp, rev read fp

    Raises
    ------
    ValueError
        If the rev is not an empty list and the same length than fwd seqs
        The prefixes of the run_prefix don't match the file names

    Notes
    -----
    Currently this is requiring matched pairs in the make_read_pairs_per_sample
    step but implicitly allowing empty reverse reads in the actual command
    generation. This behavior may allow support of situations with empty
    reverse reads in some samples, for example after trimming and QC.
    """
    # making sure the forward and reverse reads are in the same order

    # we match filenames, samples, and run prefixes
    samples = make_read_pairs_per_sample(forward_seqs, reverse_seqs, map_file)

    cmds = []

    param_string = format_kneaddata_params(parameters)
    prefixes = []
    for run_prefix, sample, f_fp, r_fp in samples:
        prefixes.append(run_prefix)
        if r_fp is None:
            cmds.append('kneaddata --input "%s" --output "%s" '
                        '--output-prefix "%s" %s' %
                        (f_fp, join(out_dir, run_prefix),
                         run_prefix, param_string))
        else:
            cmds.append('kneaddata --input "%s" --input "%s" --output "%s" '
                        '--output-prefix "%s" %s' %
                        (f_fp, r_fp, join(out_dir, run_prefix),
                         run_prefix, param_string))

    return cmds, samples


def _run_commands(qclient, job_id, commands, msg):
    for i, cmd in enumerate(commands):
        qclient.update_job_step(job_id, msg % i)
        std_out, std_err, return_value = system_call(cmd)
        if return_value != 0:
            error_msg = ("Error running KneadData:\nStd out: %s\nStd err: %s"
                         "\n\nCommand run was:\n%s"
                         % (std_out, std_err, cmd))
            return False, error_msg

    return True, ""


def _per_sample_ainfo(out_dir, samples):
    ainfo = []
    for run_prefix, sample, f_fp, r_fp in samples:
        sam_out_dir = join(out_dir, run_prefix)

        if r_fp:
            ainfo.extend([
                ArtifactInfo('clean paired R1', 'per_sample_FASTQ',
                             [(join(sam_out_dir, '%s_paired_1.fastq' %
                               run_prefix), 'per_sample_FASTQ')]),
                ArtifactInfo('clean paired R2', 'per_sample_FASTQ',
                             [(join(sam_out_dir, '%s_paired_2.fastq' %
                               run_prefix), 'per_sample_FASTQ')]),
                ArtifactInfo('clean unpaired R1', 'per_sample_FASTQ',
                             [(join(sam_out_dir, '%s_unmatched_1.fastq' %
                               run_prefix), 'per_sample_FASTQ')]),
                ArtifactInfo('clean unpaired R2', 'per_sample_FASTQ',
                             [(join(sam_out_dir, '%s_unmatched_2.fastq' %
                               run_prefix), 'per_sample_FASTQ')])])
        else:
            ainfo.extend([
                ArtifactInfo('cleaned reads', 'per_sample_FASTQ',
                             [(join(sam_out_dir, '%s.fastq' %
                               run_prefix), 'per_sample_FASTQ')])])

    return ainfo


def kneaddata(qclient, job_id, parameters, out_dir):
    """Run kneaddata with the given parameters

    Parameters
    ----------
    qclient : tgp.qiita_client.QiitaClient
        The Qiita server client
    job_id : str
        The job id
    parameters : dict
        The parameter values to run split libraries
    out_dir : str
        The path to the job's output directory

    Returns
    -------
    bool, list, str
        The results of the job
    """
    # Step 1 get the rest of the information need to run kneaddata
    qclient.update_job_step(job_id, "Step 1 of 3: Collecting information")
    artifact_id = parameters['input']

    # removing input from parameters so it's not part of the final command
    del parameters['input']

    # Get the artifact filepath information
    artifact_info = qclient.get("/qiita_db/artifacts/%s/" % artifact_id)
    fps = artifact_info['files']

    # Get the artifact metadata
    prep_info = qclient.get('/qiita_db/prep_template/%s/'
                            % artifact_info['prep_information'][0])
    qiime_map = prep_info['qiime-map']

    # Step 2 generating command kneaddata
    qclient.update_job_step(job_id, "Step 2 of 5: Generating"
                                    " KneadData command")
    rs = fps['raw_reverse_seqs'] if 'raw_reverse_seqs' in fps else []
    commands, samples = generate_kneaddata_commands(fps['raw_forward_seqs'],
                                                    rs, qiime_map, out_dir,
                                                    parameters)

    # Step 3 execute kneaddata
    msg = "Step 3 of 5: Executing KneadData job (%d/{0})".format(len(commands))
    success, msg = _run_commands(qclient, job_id, commands, msg)
    if not success:
        return False, None, msg

    # Step 4 generating artifacts
    ainfo = _per_sample_ainfo(out_dir, samples)

    return True, ainfo, ""
