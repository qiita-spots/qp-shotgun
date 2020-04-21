# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------


from os.path import join
from os import environ
from qp_shogun.sortmerna.utils import (make_read_pairs_per_sample,
                                       _run_commands, _per_sample_ainfo)


DIR = environ["QC_SORTMERNA_DB_DP"]

RNA_REF_DB = (
    '{0}rRNA_databases/silva-arc-23s-id98.fasta,'
    '{0}index/silva-arc-23s-id98.idx'
).format(DIR)

# rRNA databases used in screening
# For testing used only one db and index
# rRNA databases used in screening
# RNA_REF_DB = (
#   '{0}rRNA_databases/silva-bac-16s-id90.fasta,'
#   '{0}index/silva-bac-16s-id90.idx:'
#   '{0}rRNA_databases/silva-bac-23s-id98.fasta,'
#    '{0}index/silva-bac-23s-id98.idx:'
#    '{0}rRNA_databases/silva-arc-16s-id95.fasta,'
#    '{0}index/silva-arc-16s-id95.idx:'
#    '{0}rRNA_databases/silva-arc-23s-id98.fasta,'
#    '{0}index/silva-arc-23s-id98.idx:'
#    '{0}rRNA_databases/silva-euk-18s-id95.fasta,'
#    '{0}index/silva-euk-18s-id95.idx:'
#    '{0}rRNA_databases/silva-euk-28s-id98.fasta,'
#    '{0}index/silva-euk-28s-id98.idx:'
#    '{0}rRNA_databases/rfam-5s-database-id98.fasta,'
#    '{0}index/rfam-5s-database-id98.idx:'
#    '{0}rRNA_databases/rfam-5.8s-database-id98.fasta,'
#    '{0}index/rfam-5.8s-database-id98.idx'
# ).format(DIR)

SORTMERNA_PARAMS = {
    'a': 'Number of threads',
    'blast': 'Output blast format',
    'num_alignments': 'Number of alignments'}


def generate_sortmerna_commands(forward_seqs, reverse_seqs, map_file,
                                out_dir, parameters):
    """Generates the Sortmerna commands
    
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
        The Sortmerna commands
    samples: list of tup
        list of 4-tuples with run prefix, sample name, fwd read fp, rev read fp

    Notes
    -----
    Currently this is requiring matched pairs in the make_read_pairs_per_sample
    step but implicitly allowing empty reverse reads in the actual command
    generation. This behavior may allow support of situations with empty
    reverse reads in some samples, for example after trimming and QC.
    """
    # matching filenames, samples, and run prefixes
    samples = make_read_pairs_per_sample(forward_seqs, reverse_seqs, map_file)

    cmds = []
    param_string = _format_params(parameters, SORTMERNA_PARAMS)

    # Sortmerna 2.1 does not support processing of
    # compressed files but they said the newest release might
    # but that version first has to be tested before use and currently
    # does not have MAC OS supported release

    threads = parameters['Number of threads']

    for run_prefix, sample, f_fp, r_fp in samples:
        cmds.append('sortmerna --ref %s --reads %s '
                    '--aligned %s --other %s '
                    '--fastx --blast 1 --num_alignments 1 -a %s' % (
                        RNA_REF_DB, f_fp,
                        join(out_dir, '%s.ribosomal.R1' % run_prefix),
                        join(out_dir, '%s.nonribosomal.R1' % run_prefix),
                        threads))
    
        if r_fp is not None:
            cmds.append('sortmerna --ref %s --reads %s '
                        '--aligned %s --other %s '
                        '--fastx --blast 1 --num_alignments 1 -a %s' % (
                            RNA_REF_DB, r_fp,
                            join(out_dir, '%s.ribosomal.R2' % run_prefix),
                            join(out_dir, '%s.nonribosomal.R2' % run_prefix),
                            threads))
    return cmds, samples
    # In this version I have not added a summary file or sam file


def sortmerna(qclient, job_id, parameters, out_dir):
    """Run Sortmerna with the given parameters

    Parameters
    ----------
    qclient : tgp.qiita_client.QiitaClient
        The Qiita server client
    job_id : str
        The job id
    parameters : dict
        The parameter values
    out_dir : str
        The path to the job's output directory

    Returns
    -------
    bool, list, str
        The results of the job
    """
    # Step 1 get the rest of the information need to run Sortmerna
    qclient.update_job_step(job_id, "Step 1 of 4: Collecting information")
    artifact_id = parameters['input']
    del parameters['input']

    # Get the artifact filepath information
    artifact_info = qclient.get("/qiita_db/artifacts/%s/" % artifact_id)
    fps = artifact_info['files']

    # Get the artifact metadata
    prep_info = qclient.get('/qiita_db/prep_template/%s/'
                            % artifact_info['prep_information'][0])
    qiime_map = prep_info['qiime-map']

    # Step 2 generating command for Sortmerna
    qclient.update_job_step(job_id, "Step 2 of 4: Generating"
                                    " SortMeRNA commands")
    rs = fps['raw_reverse_seqs'] if 'raw_reverse_seqs' in fps else []
    commands, samples = generate_sortmerna_commands(fps['raw_forward_seqs'],
                                                    rs, qiime_map, out_dir,
                                                    parameters)

    # Step 3 executing Sortmerna
    len_cmd = len(commands)
    msg = "Step 3 of 4: Executing ribosomal filtering (%d/{0})".format(len_cmd)
    success, msg = _run_commands(qclient, job_id,
                                 commands, msg, 'QC_Sortmerna')
    if not success:
        return False, None, msg

    ainfo = []

    # Generates 2 artifacts: one for the ribosomal
    # reads and other for the non-ribosomal reads
    # Step 4 generating artifacts for Nonribosomal reads

    msg = ("Step 4 of 5: Generating artifacts "
           "for Nonribosomal reads (%d/{0})").format(len_cmd)
    suffixes = ['%s.nonribosomal.R1.fastq', '%s.nonribosomal.R2.fastq']
    prg_name = 'Sortmerna'
    file_type_name = 'Non-ribosomal reads'
    ainfo.append(_per_sample_ainfo(
        out_dir, samples, suffixes, prg_name, file_type_name, bool(rs)))
    # Step 5 generating artifacts for Ribosomal reads
    msg = ("Step 5 of 5: Generating artifacts "
           "for Ribosomal reads (%d/{0})").format(len_cmd)

    suffixes = ['%s.ribosomal.R1.fastq', '%s.ribosomal.R2.fastq']
    prg_name = 'Sortmerna'
    file_type_name = 'Ribosomal reads'
    ainfo.append(_per_sample_ainfo(
        out_dir, samples, suffixes, prg_name, file_type_name, bool(rs)))

    return True, ainfo, ""
