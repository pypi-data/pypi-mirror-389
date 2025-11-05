from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Iterator, Union, List
from string import Template
import os
import numpy as np


@dataclass
class Environment:

    def __init__(self, name: str, **options):
        self.name = name
        self.options = {name.replace("_", " "): value for name, value in options.items()}
        self.content = TikzCode()

    def add(self, content: Union['Environment', str]):
        if isinstance(content, Environment):
            content = content.get_code()
        self.content.add_line(content)

    def get_code(self) -> str:
        return wrap_env(self.name, self.content.get_code(), **self.options)


@dataclass
class View:
    azimuth: int
    elevation: int

    def __str__(self) -> str:
        return f"{{{self.azimuth}}}{{{self.elevation}}}"


class AxisMode(Enum):
    normal = "normal"
    linear = "linear"
    log = "log"


class AxisDir(Enum):
    normal = "normal"
    reverse = "reverse"


class Grid(Enum):
    minor = "minor"
    major = "major"
    both = "both"
    none = "none"


class Axis(Environment):

    def __init__(self,
                 xlabel: str = None,
                 ylabel: str = None,
                 view: View = None,
                 width: str = None,
                 height: str = None,
                 scale_only_axis: bool = False,
                 axis_x_line: str = None,
                 axis_y_line: str = None,
                 axis_z_line: str = None,
                 xmode: AxisMode = None,
                 ymode: AxisMode = None,
                 zmode: AxisMode = None,
                 x_dir: AxisDir = None,
                 y_dir: AxisDir = None,
                 z_dir: AxisDir = None,
                 axis_equal: bool = False,
                 axis_equal_image: bool = False,
                 xmin: float = None, xmax: float = None,
                 ymin: float = None, ymax: float = None,
                 zmin: float = None, zmax: float = None,
                 grid: Grid = None,
                 xminorgrids: bool = None,
                 yminorgrids: bool = None,
                 zminorgrids: bool = None,
                 xmajorgrids: bool = None,
                 ymajorgrids: bool = None,
                 zmajorgrids: bool = None,
                 xtick: str = None,
                 ytick: str = None,
                 ztick: str = None,
                 **extra
                 ):
        arguments = locals()
        arguments.pop("extra")
        arguments.pop("self")
        arguments.pop("__class__")
        arguments = {key.replace("_", " "): value for (key, value) in arguments.items()
                     if value is not None
                     }
        super().__init__("axis", **arguments, **extra)


class TikzPicture(Environment):

    def __init__(self, standalone: bool = True, **options):
        super().__init__("tikzpicture", **options)
        self.standalone = standalone
        self.preamble = TikzCode()

    def add_preamble_line(self, line: str):
        self.preamble.add_line(line)

    def get_code(self) -> str:
        preamble = ""
        if self.standalone:
            preamble += "\\documentclass[tikz]{standalone}\n"
            preamble += self.preamble.get_code()
        else:
            preamble = ""

        content = self.content.get_code()
        content = wrap_env("tikzpicture", content)
        if self.standalone:
            content = wrap_env("document", content)

        return preamble + content

        # -----------------------------------------------------------
        # IO functions
        # -----------------------------------------------------------


class ColorCycler:

    def __init__(self, cmapname: str):
        import matplotlib.pyplot as plt
        self.cmap = plt.get_cmap(cmapname)
        self.pgfdata = PlotData()
        self.__seen_colors = set()
        self.__idx = 0

    def __next__(self) -> str:
        color = self.cmap(self.__idx)
        colorname = name_from_rgb(color)
        if not colorname in self.__seen_colors:
            self.pgfdata.colordefs.append(get_colordef_command(color))
        self.__idx += 1
        return colorname

    def get_definitions(self):
        return self.pgfdata


def load_template_path(path: str) -> Template:
    """Import template with path ``path``.

    Args:
        file (str): filename of template

    Returns:
        Template: Template
    """
    with open(path, "r") as template_file:
        template = template_file.read()
    return Template(template)


def load_template(file: str) -> Template:
    """Import template with filename ``file`` from the ``.template`` directory.

    Args:
        file (str): filename of template

    Returns:
        Template: Template
    """
    template_file = os.path.join(".template", file)
    return load_template_path(template_file)


def write_output(data: str, outdir: str = ".generated_tikz", outfile: str = "plot_rationale_3d.tex") -> str:
    """Write the given data to a file ``outdir/outfile``.
    Will create ``outdir`` if it does not yet exists.

    The full output path is also returned.
    """
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, outfile)

    with open(outpath, "w") as f:
        f.write(data)

    return outpath


# -----------------------------------------------------------
# Tikz generation utilities
# -----------------------------------------------------------

def _preprocess_color(color: tuple) -> tuple:
    if len(color) == 4:
        if color[-1] != 1:
            raise UserWarning("RGBA is not supported. Setting alpha channel to fully opaque.")
        color = color[:-1]
    return color


def format_vector(vector: np.ndarray, separator: str = " ", ints: bool = False) -> str:
    """Format a vector as a string by joining it with the provided separator."""
    if ints:
        formatted = [f"{int(element):d}" for element in vector]
    else:
        formatted = [f"{element:2.9f}" for element in vector]
    return separator.join(formatted)


def format_matrix(matrix: np.ndarray) -> str:
    """Format a matrix for use in an \\addplot command.

    Args:
        matrix (np.ndarray): data

    Returns:
        str: Formatted table
    """
    if np.ndim(matrix) == 0:
        return f"{float(matrix):2.16f}"
    if np.ndim(matrix) == 1:
        return format_vector(matrix)
    elif np.ndim(matrix) == 2:
        return '\n'.join([format_vector(row) for row in matrix])
    else:
        raise ValueError(f"Plotting {np.ndim(matrix)}-dimensional data is not supported.")


def get_plot_command(data: np.ndarray, raw_options: str = "", suffix: str = "",
                     plot3d: bool = True, plotplus: bool = False,
                     label: str = None,
                     inline_label: bool = False,
                     labelopts: str = "") -> str:
    """Return a plot command to plot the given data in pgfplots.
    """
    labelcmd = ""
    if label:
        if inline_label:
            suffix += f"\\node[{labelopts}] {label}"
        else:
            labelcmd = f"\\addlegendentry{{{label}}}"
    tablecmd = "table" if np.ndim(data) >= 1 else ""
    return f"""
\\addplot{'3' if plot3d else ''}{'+' if plotplus else ''}[{raw_options}]
{tablecmd}{{%
{format_matrix(data)}
}}{suffix};
{labelcmd}
"""


def get_errorbar_command_raw(x_data: np.ndarray, y_data: np.ndarray, ymax_data: np.ndarray, ymin_data: np.ndarray,
                             raw_options: str = "", suffix: str = "", plotplus: bool = False,
                             label: str = None,
                             inline_label: bool = False,
                             labelopts: str = "") -> str:
    """Return a plot command with errorbars in pgfplots.
    """
    labelcmd = ""
    if label:
        if inline_label:
            suffix += f"node[{labelopts}] {{{label}}}"
        else:
            labelcmd = f"\\addlegendentry{{{label}}}"

    datarows = [f'{x:2.16f} {y:2.16f} {ym:2.16f} {yp:2.16f}' for x, y, ym, yp in zip(x_data, y_data, y_data - ymin_data, ymax_data - y_data)]
    data_fmt = "\n".join(datarows)
    return f"""
\\addplot{'+' if plotplus else ''}[{raw_options}]
plot[error bars/.cd, y dir=both, y explicit]
table[x=x,y=y, y error plus expr=\\thisrow{{ymax}},y error minus expr=\\thisrow{{ymin}}]
{{%
x y ymin ymax
{data_fmt}
}}{suffix};
{labelcmd}
"""


def get_errorbar_command(xdata: np.ndarray, ydata: np.ndarray, quantile: float,
                         raw_options: str = "", suffix: str = "", plotplus: bool = False,
                         label: str = None,
                         inline_label: bool = False,
                         labelopts: str = "") -> PlotData:
    """High level command to generate an errorbar plot in pgfplots.

    Args:
        xdata (np.ndarray): 1D array for the x-axis
        ydata (np.ndarray): 2D array for the y-axis. Error bars are computed with respect to axis 0.
        quantile (float): quantile level to compute the errorbars from.
        raw_options (str, optional): Defaults to "".
        suffix (str, optional): Defaults to "".
        plotplus (bool, optional): Defaults to False.
        label (str, optional): Label for the legend. Defaults to None.
    """
    upper_quant = np.quantile(ydata, max(quantile, 1 - quantile), axis=0)
    lower_quant = np.quantile(ydata, min(quantile, 1 - quantile), axis=0)
    means = np.mean(ydata, axis=0)

    return PlotData([get_errorbar_command_raw(xdata, means, upper_quant, lower_quant, raw_options, suffix, plotplus, label, inline_label, labelopts)])


def get_boxplot_command(data: np.ndarray, raw_options: str = "", suffix: str = "") -> str:
    """Return a plot command to plot the given data in pgfplots.
    """
    return get_plot_command(data, f"boxplot, {raw_options}", suffix, False, True)


def format_color(color: tuple) -> Iterator[str]:
    """Return an iterator over strings representing the rgb values of the given color.

    Assumes that the given color values are in the range (0,1), and outputs to (0,255),
    as used in tikz.

    Args:
        color (tuple): rgb values in range (0,1).

    Yields:
        Iterator[str]: Iterator over strings representing the color values in (0,255).
    """
    color = _preprocess_color(color)
    for c in color:
        yield str(round(c * 255))


def name_from_rgb(color: tuple) -> str:
    """Generate a name for the given rgb color.

    Args:
        color (tuple): rgb values in the (0,1)-range.

    Returns:
        str: name for the color.
    """
    return 'color' + ''.join(format_color(color))


def get_colordef_command(color: tuple) -> str:
    """Generate a command to define the given color.

    Args:
        color (tuple): rgb values in the (0,1)-range.

    Returns:
        str: definecolor-command
    """
    color = _preprocess_color(color)
    rgbcomma = ", ".join(format_color(color))
    return f"\definecolor{{{name_from_rgb(color)}}}{{RGB}}{{{rgbcomma}}}"


def get_plot_command_vector(base: np.ndarray, direction: np.ndarray, *,
                            options="", color: tuple = None, suffix: str = "") -> PlotData:
    """Generate a pgfplots command for a vector (drawn as an arrow).
    """
    start = base
    end = direction + start
    if color is not None:
        colorname = name_from_rgb(color)
        newcolor = get_colordef_command(color)
    else:
        newcolor = ""
        colorname = ""
    return PlotData(
        f"\draw[{','.join(['->, >=stealth', options, colorname])}] (axis cs: {format_vector(start, separator=', ')}) -- (axis cs: {format_vector(end, separator=', ')}) {suffix};",
        newcolor
    )


STANDALONE_SUBSTITUTIONS = dict(
    documentclass=r"\documentclass[tikz, dvipsnames]{standalone}",
    begindocument=r"\begin{document}",
    enddocument=r"\end{document}"
)
REGULAR_SUBSTITUTIONS = dict(
    documentclass="",
    begindocument="",
    enddocument=""
)


def generate_and_build(generator: Callable[[str, bool], PlotData], template_file: str, outfile: str, *,
                       copy_dst_dir: str = ""):
    """Fill the given ``template_file`` with data and write the resulting tikz-file to ``outfile``.
    If ``copy_dst_dir`` is the empty string, then a standalone document is generated which is compiled.
    Otherwise, the tex file is copied to ``copy_dst_dir``, where it can be included in another document.

    Args:
        generator (Callable[[str, bool], PlotData]): Given a path to a template file and a boolean specifying whether the plot is standalone, generate a ``PlotData`` object which contains all the plots to be generated.
        template_file (str): Path to the template file.
        outfile (str): Path to the output ``.tex`` file.
        copy_dst_dir (str, optional): Path to a directory to copy the result to. If empty, then no copying is done. Defaults to "".
    """
    import subprocess

    template = load_template(template_file)

    standalone = copy_dst_dir == ""
    if standalone:
        substitutions = STANDALONE_SUBSTITUTIONS
        preamble_data = [r"\usepackage{pgfplots}", r"\pgfplotsset{compat=1.8}", r"\usetikzlibrary{arrows,arrows.meta,3d}"]
    else:
        substitutions = REGULAR_SUBSTITUTIONS
        preamble_data = [r"\usetikzlibrary{arrows,arrows.meta,3d}"]

    plots = PlotData(preamble=preamble_data)

    plots.extend(generator(template_file, standalone))

    generated_substitutions = plots.get_substitution_dict()
    substitutions.update(generated_substitutions)
    output = template.safe_substitute(substitutions)

    # Write to file
    outfile = write_output(output, outfile=outfile)

    if standalone:
        # Build the latex file
        subprocess.call(["latexmk", "-interaction=nonstopmode", "-quiet", "-shell-escape", "-file-line-error", "-cd", "-pdf", outfile])
        print(f"Generated tikz code in \n{os.path.abspath(outfile)}")
    else:
        print(f"Generated tikz code in \n{os.path.abspath(outfile)}")
        # Copy to provided directory
        import shutil
        print(f"Copying to {os.path.join(copy_dst_dir, os.path.split(outfile)[-1])}")
        shutil.copy(os.path.abspath(outfile), copy_dst_dir)


def get_axis_settings(**kwargs) -> PlotData:
    options = []
    for key, value in kwargs.items():
        options.append(get_axis_option(key, value))
    return PlotData(extraaxisoptions=options)


def get_axis_option(key: str, value: str = None) -> str:
    if value is None:
        return f"{key},"
    return f"{key}={value},"

# -----------------------------------------------------------
# CLI
# -----------------------------------------------------------


def parse_cli():
    """Parse common cli arguments"""
    import argparse
    parser = argparse.ArgumentParser("Generate tikz code for cdc2023 paper.")
    parser.add_argument("--outdir", "-o", type=str, default="")
    args = parser.parse_args()
    args.standalone = len(args.outdir) == 0
    return args
