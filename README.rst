===========
 ASCII Box
===========

Render ASCII boxes and arrows as images.

- Version : 0.1
- License : GPLv3+ (see COPYING for details)
- Author  : Tuomas Jorma Juhani Räsänen <tuomasjjrasanen@tjjr.fi>
- Homepage: <http://tjjr.fi/sw/asciibox/>
- Code    : <http://github.com/tuomasjjrasanen/asciibox/>

Command line usage
==================

Given the following text file, ``doc/examples/fig.txt``::

  +---------------------+ ^
  |      Top layer      | |
  +--------------+------+ |
  |  Middle      |      | |
  |      +-------+ Side | |
  |      | Small |      | |
  +------+--+----+------+ v

  <--------------------->

Then running::

  python asciibox.py -i doc/examples/fig.txt -o fig.png

would render the above diagram as a PNG file, ``fig.png``.

.. image:: doc/examples/fig.png
