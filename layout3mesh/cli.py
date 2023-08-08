#!/usr/bin/env python3

"""layout3mesh command line tool.

Usage:
   layout3mesh -i INPUT_FILE -t LAYER_FILE [-c TOP_CELL_NAME] [-o OUT_FILE] [--verbose] [--blender]
   layout3mesh -h | --help
   layout3mesh --version

Options:
    -h --help                   Show this help message and exit.
    --version                   Show version information.
    --verbose                   Enable verbose debug output.
    --blender                   Use Blender to render glTF.
    -i --input INPUT_FILE       Input [.gds] | [.oas] layout file.
    -t LAYER_FILE               Layerstack [.lys.yml] file.
    -c --top-cell TOP_CELL_NAME Top cell name. If not specified, the largest area cell is used.
    -o --output OUT_FILE        Output [.svg] file.
Description:
    layout3mesh is a tool to convert GDS or OAS layout files to SVG. 
    Optional direct rendering to Inkscape is supported.
"""


from layout3mesh.layout3mesh import load_layerstack, load_layout, render_to_mesh

import platform
import sys
import tempfile
import subprocess

try:
    from loguru import logger
except ImportError as e:
    print("Error: loguru not found.", e)
    print("Please install loguru with: pip install loguru")
    exit(1)

try:
    from docopt import docopt
except ImportError as e:
    print("Error: docopt not found.", e)
    print("Please install docopt with: pip install docopt")
    exit(1)

# get inkscape binary path
BLENDER_BIN = ""
try:
    if platform.system() == "Windows":
        BLENDER_BIN = (
            subprocess.check_output(["where", "blender"]).decode("utf-8").strip()
        )
    elif platform.system() == "Darwin":
        BLENDER_BIN = (
            subprocess.check_output(["which", "blender"]).decode("utf-8").strip()
        )
    elif platform.system() == "Linux":
        BLENDER_BIN = (
            subprocess.check_output(["command", "-v", "blender"])
            .decode("utf-8")
            .strip()
        )
    else:
        print("Error: Unsupported platform.")
        exit(1)
except subprocess.CalledProcessError as e:
    print("Error: Could not find inkscape binary.", e)
    exit(1)


def main():
    # Configure the logger to write to a file
    logger.add(
        "layout3mesh.log", rotation="1 week"
    )  # Change the log file name and rotation settings as needed
    args = docopt(__doc__, version="layout3mesh 0.1.5")
    verbose = args["--verbose"]
    render_to_blender = args["--blender"] and (BLENDER_BIN != "")
    render_to_outfile = args["--output"]
    in_file = args["--input"]
    layerstack_file = args["-t"]
    out_file = args["--output"]
    try:
        assert render_to_outfile or render_to_blender, "No output specified."
    except AssertionError as e:
        sys.exit("Failed: No output specified.")

    try:
        # import layout
        layerstack = load_layerstack(layerstack_file)
        # import layerstack to generate svg layer info
        layout = load_layout(in_file)
    except Exception as e:
        if verbose:
            logger.error("Could not load layout or layerstack: ")
            logger.exception(e)
        sys.exit("Failed: Could not load input files.")

    topcell_name = args["--top-cell"]
    if render_to_outfile:
        try:
            render_to_mesh(layout, layerstack, topcell=topcell_name, out=out_file)
        except Exception as e:
            if verbose:
                logger.error(f"Could not render to 3D Object: {e}")
            sys.exit("Failed: Could not render to output file.")
        if verbose:
            logger.success("Rendered to 3D Object: ", out_file)
    if render_to_blender:
        cmd = [BLENDER_BIN]
        with tempfile.NamedTemporaryFile(suffix=".blend") as f:
            try:
                render_to_mesh(layout, layerstack, topcell=topcell_name, out=f.name)
            except Exception as e:
                if verbose:
                    logger.error("Could not render to temporary file: ")
                    logger.exception(e)
                sys.exit("Failed: Could not render to Blender.")
            try:
                cmd.append(f.name)
                subprocess.run(cmd)
            except subprocess.CalledProcessError as e:
                if verbose:
                    logger.error("Subprocess system call failed: ")
                    logger.exception(e)
                sys.exit("Failed: Could not render to Blender.")
            if verbose:
                cmds = " ".join(cmd)
                logger.success(f"Blender run: {cmds}")

    logger.success("Done.")


if __name__ == "__main__":
    main()
