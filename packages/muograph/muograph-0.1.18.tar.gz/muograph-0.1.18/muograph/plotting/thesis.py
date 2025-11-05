import matplotlib.pyplot as plt
from typing import Tuple, Dict, Union

# Number of bins for histograms
n_bins: int = 50

textwidth_inch = 4.724409  # inches
textwidth_cm = 12.0  # cm

half_textwidth_inch = textwidth_inch / 2
half_textwidth_cm = textwidth_cm / 2

# Transparency
alpha_points = .6


# Figure size
def get_figsize_from_textwidth(
    textwidth: float = 4.724409,
    scale: float = 1.0,
    aspect_ratio: float = 6 / 8,
) -> Tuple[float, float]:

    width = textwidth * scale
    height = width * aspect_ratio
    return (width, height)


figsize = get_figsize_from_textwidth(textwidth_cm, scale=1, aspect_ratio=6 / 8)
half_figsize = get_figsize_from_textwidth(textwidth_cm, scale=.5, aspect_ratio=6 / 8)
third_figsize = get_figsize_from_textwidth(textwidth_cm, scale=.35, aspect_ratio=6 / 8)

fontsize: int = 12
labelsize: int = 12
titlesize: int = 22


fontweigh: str = "normal"
font: Dict[str, Union[str, int]] = {"weight": "normal", "size": fontsize, "family": "sans-serif"}

# Set matplotlib theme
def configure_plot_theme() -> None:
    import scienceplots  # type: ignore
    import matplotlib
    # Reset default params
    matplotlib.rcParams.update(matplotlib.rcParamsDefault)
    # matplotlib.use("pgf")
    matplotlib.rcParams.update(
        {
            # "pgf.texsystem": "pdflatex",
            "font.family": "serif",
            "text.usetex": True,
            "pgf.rcfonts": False,
            "font.size": font["size"],
            "axes.labelsize": font["size"],
            "axes.titlesize": font["size"],
            "xtick.labelsize": font["size"],
            "ytick.labelsize": font["size"],
        }
    )
    plt.style.use(["science", "grid"])