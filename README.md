<h1 align=center> layout3mesh </h1>

<div align=justify>
<p> This is a simple tool to convert an integrated circuit layout saved in OASIS / GDSII file format to a mesh 3D image file. The tool doesn't support direct export of the 3D mesh file into the Blender desktop app just yet - but I am working on a solution. This tool was written with the goal of rendering any layout in 3D inside a desktop or web application using WebGL. </p>
</div>

<h2 align=center> Installation </h2>

<h3 align=center> MacOS, Linux, Windows </h3>

```bash
pip install layout3mesh
```

<h2 align=center> Usage - Command Line Interface </h2>

```bash
layout3mesh -i <input_file_path [.gds/.oas]> -o <output_file_path [.gltf]> -t <layerstack_file_path [.ymls]>
```

<h2 align=center> Examples </h2>

<p>
Running the example with the mock layerstack file and layout provided in the <a href="tests/data/">examples</a>, by running the following command:
</p>

```bash
layout3mesh -i ./tests/data/crossed_metal.gds -t ./tests/data/mock_layers.ymls -o ./tests/data/crossed_metal.gltf
```

<p>
can generate the following 3D image:
</p>

<p align=center>


<img src="tests/data/crossed_metal.gif" width=70%/>

</p>
