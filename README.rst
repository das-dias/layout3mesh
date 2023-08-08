.. raw:: html

   <h1 align="center">

layout3mesh

.. raw:: html

   </h1>

.. container::

   .. raw:: html

      <p>

   This is a simple tool to convert an integrated circuit layout saved
   in OASIS / GDSII file format to a mesh 3D image file. The tool
   supports direct export of the 3D mesh file into the Blender desktop
   app. This tool was written with the goal of rendering any layout in
   3D inside a desktop or web application using WebGL.

   .. raw:: html

      </p>

.. raw:: html

   <h2 align="center">

Installation

.. raw:: html

   </h2>

.. raw:: html

   <h3 align="center">

MacOS, Linux, Windows

.. raw:: html

   </h3>

.. code:: bash

   pip install layout3mesh

.. raw:: html

   <h2 align="center">

Usage - Command Line Interface

.. raw:: html

   </h2>

.. code:: bash

   layout3mesh -i <input_file_path [.gds/.oas]> -o <output_file_path [.gltf]> -t <layerstack_file_path [.ymls]>

.. raw:: html

   <h2 align="center">

Examples

.. raw:: html

   </h2>

.. raw:: html

   <p>

Running the example with the mock layerstack file and layout provided in
the examples, by running the following command:

.. raw:: html

   </p>

.. code:: bash

   layout3mesh -i ./tests/data/crossed_metal.gds -t ./tests/data/mock_layers.ymls -o ./tests/data/crossed_metal.gltf

.. raw:: html

   <p>

can generate the following 3D image:

.. raw:: html

   </p>

.. raw:: html

   <p align="center">

.. raw:: html

   </p>
