
Installation
============

This guide will walk you through the installation process and hopefully avoid any issues.



Repository download 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
I would recommend creating a code directory first.

.. code-block:: bash

	mkdir source_code
	cd source_code


You can download the github repository to this directory with.

.. code-block:: bash

	git clone https://github.com/gefdz/AstroDART

Move to the cloned directory.

.. code-block:: bash

	cd AstroDART


Environment 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
I strongly recommend you create a dedicated environment to avoid conflicts with dependencies with other python packages. There is a yml file inside the AstroDART directory, you can use it to create the environment as follows, activate the environment. The whole process may take some minutes.

.. code-block:: bash

	conda env create --name astrodart --file=AstroDART.yml
	conda activate astrodart

AstroDART package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Version 0.1 of the package can be installed to this environment from PyPI using.

.. code-block:: bash

	pip install AstroDART

Checking installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
You can check 2 things to verify the installation.

1) check list of all packages.

.. code-block:: bash

	pip list > packages.txt

2) run python in a terminal and import the package.

.. code-block:: bash

	python

.. code-block:: python

	import AstroDART as asd


Issues with installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you encounter any issues don't hesitate to contact me and I will try to solve it: gareb.fernandez@gmail.com

