Shotgun Qiita Plugin
========================

|Build Status| |Coverage Status|

Qiita (canonically pronounced *cheetah*) is an analysis environment for microbiome (and other "comparative -omics") datasets.

This package includes the Shotgun functionality for Qiita. Currently, we have:

- `HUMAnN2 <https://bitbucket.org/biobakery/humann2/wiki/Home>`_

Note that is suggested that you download the full databases once this package is installed by:

.. code:: bash

  $ humann2_databases --download chocophlan full $DIR
  $ humann2_databases --download uniref diamond $DIR


The default pipeline is:

1. Run HUMAnN2 on per sample FASTQ
2. Collate individual results into single OTU tables: gene families, path coverage and path abundance.
3. Renormalize the tables: gene families - CPM, path coverage - relative abundance, path abundance - relative abundance.

Note that HUMAnN2 depends on `metaphlan2 <https://bitbucket.org/biobakery/metaphlan2/get/default.zip>`__ but neither the HUMAnN2 or this plugin automatically install that dependency. Remember that you need to put the `db_v20` folder in the path that the `metaphlan2.py` executable.

.. |Build Status| image:: https://travis-ci.org/qiita-spots/qp-shotgun.svg?branch=master
   :target: https://travis-ci.org/qiita-spots/qp-shotgun
.. |Coverage Status| image:: https://coveralls.io/repos/github/qiita-spots/qp-shotgun/badge.svg?branch=master
   :target: https://coveralls.io/github/qiita-spots/qp-shotgun?branch=master
