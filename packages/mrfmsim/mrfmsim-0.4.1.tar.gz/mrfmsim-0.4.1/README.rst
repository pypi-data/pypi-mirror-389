MrfmSim
=======

|GitHub version| |Unit tests| |DOI|

*mrfmsim* is a Python framework for simulating magnetic resonance force microscopy (MRFM)
experiments. The package is based on the
`mmodel <https://marohn-group.github.io/mmodel-docs/>`_ framework, which provides
modular modeling capabilities for the experiments. 

This *mrfmsim* package contains tools to simulate signals in a Magnetic Resonance Force 
Microscope (MRFM) [#Sidles1995jan]_ [#Kuehn2008feb]_ [#Poggio2010aug]_ experiment.
The code in the package simulates signal from **electron spins**, 
particularly the **nitroxide spin radical** "TEMPO" to **selected nuclear 
spins (1H, 19F, and 71Ga)**.

The package host variety of MRFM experiments with the tip-on-cantilever setup.
It can simulate signals from both **Curie-law spin magnetization** and **spin 
fluctuations** (in the small polarization limit); and can simulate **force 
experiments** and **force-gradient experiments** (in the 
small-cantilever-amplitude limit and without the small amplitude approximation 
--- in the large amplitude limit). It can simulate signal with the cantilever 
and field-aligned in both the **hangdown** [#Mamin2003nov]_ and **SPAM** [#Marohn1998dec]_
[#Garner2004jun]_ experimental geometries.


Quickstart
----------

Installation
^^^^^^^^^^^^^

*Graphviz* installation
***********************

To view the graph, Graphviz needs to be installed:
`Graphviz Installation <https://graphviz.org/download/>`_
For Windows installation, please choose "add Graphviz to the
system PATH for all users/current users" during the setup.

For macOS systems, sometimes `brew install` results
in an unexpected installation path, it is recommended to install
with conda::

    conda install -c conda-forge pygraphviz


*mrfmsim* installation
***********************

To install the package, run::

    pip install .


Tests
^^^^^

To run the tests locally::

    python -m pytest

To test in different environments::

    tox


Contributing
^^^^^^^^^^^^

We welcome contributions! Please see our `Contributing Guide <docs/contribute.rst>`_ for details on how to follow our development guidelines and submit pull requests.

.. rubric:: References

.. [#Sidles1995jan] Sidles, J. A.; Garbini, J. J.; Bruland, K. J.; Rugar, D.; 
    Züger, O.; Hoen, S. & Yannoni, C. S. "Magnetic Resonance Force Microscopy",
    *Rev. Mod. Phys.*, **1995**, *67*, 249 - 265
    [`10.1103/RevModPhys.67.249\
    <http://doi.org/10.1103/RevModPhys.67.249>`__].

.. [#Kuehn2008feb] Kuehn, S.; Hickman, S. A. & Marohn, J. A. "Advances in 
    Mechanical Detection of Magnetic Resonance", *J. Chem. Phys.*, **2008**, 
    *128*, 052208 
    [`10.1063/1.2834737 <http://dx.doi.org/10.1063/1.2834737>`__].
    **OPEN ACCESS**.

.. [#Poggio2010aug] Poggio, M. & Degen, C. L. "Force-Detected Nuclear Magnetic
    Resonance: Recent Advances and Future Challenges", 
    *Nanotechnology*, **2010**, *21*, 342001 
    [`10.1088/0957-4484/21/34/342001\
    <http://doi.org/10.1088/0957-4484/21/34/342001>`__].

.. [#Mamin2003nov] Mamin, H. J.; Budakian, R.; Chui, B. W. & Rugar, D.
     "Detection and Manipulation of Statistical Polarization in Small 
     Spin Ensembles", *Phys. Rev. Lett.*, **2003**, *91*, 207604 
     [`10.1103/PhysRevLett.91.207604\
     <http://doi.org/10.1103/PhysRevLett.91.207604>`__].

.. [#Marohn1998dec] Marohn, J. A.; Fainchtein, R. & Smith, D. D. 
    "An Optimal Magnetic Tip Configuration for Magnetic-Resonance Force 
    Microscopy of Microscale Buried Features", *Appl. Phys. Lett.*, **1998**,
    *73*, 3778 - 3780 
    [`10.1063/1.122892 <http://dx.doi.org/10.1063/1.122892>`__].
    SPAM stands for Springiness Preservation by Aligning Magnetization.

.. [#Garner2004jun] Garner, S. R.; Kuehn, S.; Dawlaty, J. M.; Jenkins, N. E. 
    & Marohn, J. A. "Force-Gradient Detected Nuclear Magnetic Resonance", 
    *Appl. Phys. Lett.*, **2004**, *84*, 5091 - 5093 
    [`10.1063/1.1762700 <http://dx.doi.org/10.1063/1.1762700>`__]. 



.. |GitHub version| image:: https://badge.fury.io/gh/Marohn-Group%2Fmrfmsim.svg
   :target: https://github.com/Marohn-Group/mrfmsim

.. .. |PyPI version shields.io| image:: https://img.shields.io/pypi/v/mrfmsim.svg
..    :target: https://pypi.python.org/pypi/mrfmsim/

.. .. |PyPI pyversions| image:: https://img.shields.io/pypi/pyversions/mrfmsim.svg

.. |Unit tests| image:: https://github.com/Marohn-Group/mrfmsim/actions/workflows/tox.yml/badge.svg
    :target: https://github.com/Marohn-Group/mrfmsim/actions

.. .. |Docs| image:: https://img.shields.io/badge/Documentation--brightgreen.svg
..     :target: https://github.com/Marohn-Group/mrfmsim-docs/

.. |DOI| image:: https://zenodo.org/badge/534295792.svg
   :target: https://zenodo.org/badge/latestdoi/534295792
