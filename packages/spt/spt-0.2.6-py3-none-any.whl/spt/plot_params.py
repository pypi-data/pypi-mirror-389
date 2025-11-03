from matplotlib import rcParams

"""sci_plot_params: SCI 绘图参数
所有字体加粗
增加线、轴的线宽 3.0 有加粗效果
增加主、次刻度线长度与宽度
不显示图例边框
"""
sci_plot_params = {
    "font.weight": "bold",
    "axes.labelweight": "bold",
    "axes.titleweight": "bold",
    "axes.linewidth": 3.0,
    "lines.linewidth": 3.0,
    "xtick.major.width": 3.0,
    "ytick.major.width": 3.0,
    "xtick.minor.width": 3.0,
    "ytick.minor.width": 3.0,
    "xtick.major.size": 6.0,
    "ytick.major.size": 6.0,
    "xtick.minor.size": 3.5,
    "ytick.minor.size": 3.5,
    "legend.frameon": False,
}

"""roman_plot_params: 字体 Times New Roman"""
roman_plot_params = {"font.serif": "Times New Roman"}


def set_plot_params(
    roman_params: bool = False,
    sci_params: bool = False,
    font_family: str = "serif",
    font_weight: str = "normal",
    axes_labelweight: str = "normal",
    axes_titleweight: str = "normal",
    font_size: int = 22,
    legend_fontsize: int = 18,
    mathtext_fontset: int = "stix",
    mathtext_default: str = "regular",
    xtick_direction: str = "in",
    ytick_direction: str = "in",
    axes_linewidth: float = 2.0,
    lines_linewidth: float = 2.0,
    lines_markersize: float = 10,
    xtick_major_width: float = 2.0,
    ytick_major_width: float = 2.0,
    xtick_minor_width: float = 1.5,
    ytick_minor_width: float = 1.5,
    xtick_major_size: float = 3.5,
    ytick_major_size: float = 3.5,
    xtick_minor_size: float = 2.0,
    ytick_minor_size: float = 2.0,
    xtick_minor_visible: bool = False,
    ytick_minor_visible: bool = False,
    xtick_major_pad: int = 7,
    ytick_major_pad: int = 7,
    xtick_top: bool = False,
    ytick_right: bool = False,
    axes_labelpad: int = 10,
    axes_titlepad: int = 10,
    savefig_dpi: int = 1000,
    figure_dpi: int = 1000,
    savefig_bbox: str = "tight",
    legend_columnspacing: float = 0.5,
    legend_labelspacing: float = 0.3,
    legend_handletextpad: float = 0.2,
    legend_frameon: bool = True,
    axes3d_grid: bool = True,
    axes_grid: bool = False,
    image_aspect: str = "equal",
    **kwargs
) -> dict:
    """
    设置 Matplotlib 绘图参数

    Args:
        roman_params (bool, optional): 是否使用 Times New Roman 字体. Defaults: False.
        sci_params (bool, optional): 是否使用 SCI 绘图参数. Defaults: False.
        font_family (str, optional): 字体类型. Defaults: "serif".
        font_weight (str, optional): 字体加粗类型. Defaults: "normal".
        axes_labelweight (str, optional): 坐标轴标签加粗类型. Defaults: "normal".
        axes_titleweight (str, optional): 图表标题加粗类型. Defaults: "normal".
        font_size (int, optional): 字体大小. Defaults: 22.
        legend_fontsize (int, optional): 图例字体大小. Defaults: 18.
        mathtext_fontset (str, optional): 数学公式字体类型. Defaults: "stix".
        mathtext_default (str, optional): 数学公式字体族类型. Defaults: "regular".
        xtick_direction (str, optional): x 轴主刻度线方向. Defaults: "in".
        ytick_direction (str, optional): y 轴主刻度线方向. Defaults: "in".
        axes_linewidth (float, optional): 坐标轴线宽度. Defaults: 2.0.
        lines_linewidth (float, optional): 线条宽度. Defaults: 2.0.
        lines_markersize (int, optional): marker 大小. Defaults: 10.
        xtick_major_width (float, optional): x 轴主刻度线宽度. Defaults: 2.0.
        ytick_major_width (float, optional): y 轴主刻度线宽度. Defaults: 2.0.
        xtick_minor_width (float, optional): x 轴次刻度线宽度. Defaults: 1.5.
        ytick_minor_width (float, optional): y 轴次刻度线宽度. Defaults: 1.5.
        xtick_major_size (float, optional): x 轴主刻度线长度. Defaults: 3.5.
        ytick_major_size (float, optional): y 轴主刻度线长度. Defaults: 3.5.
        xtick_minor_size (float, optional): x 轴次刻度线长度. Defaults: 2.0.
        ytick_minor_size (float, optional): y 轴次刻度线长度. Defaults: 2.0.
        xtick_minor_visible (bool, optional): 是否添加 x 轴次刻度线. Defaults: False.
        ytick_minor_visible (bool, optional): 是否添加 y 轴次刻度线. Defaults: False.
        xtick_major_pad (int, optional): x 轴主刻度线标签与刻度线的距离. Defaults: 7.
        ytick_major_pad (int, optional): y 轴主刻度线标签与刻度线的距离. Defaults: 7.
        xtick_top (bool, optional): 是否在 x 轴顶部添加刻度线. Defaults: False.
        ytick_right (bool, optional): 是否在 y 轴顶部添加刻度线. Defaults: False.
        axes_labelpad (int, optional): 坐标轴标签与坐标轴的距离. Defaults: 10.
        axes_titlepad (int, optional): 标题与坐标轴的距离. Defaults: 10.
        savefig_dpi (int, optional): 图片保存时的分辨率. Defaults: 1000.
        figure_dpi (int, optional): 图片显示时的分辨率. Defaults: 1000.
        savefig_bbox (str, optional): 图片保存时的裁剪方式, "tight" 表示裁剪掉图片周围的空白部分. Defaults: "tight".
        legend_columnspacing (float, optional): 图例之间的列间距. Defaults: 0.5.
        legend_labelspacing (float, optional): 图例之间的行间距. Defaults: 0.3.
        legend_handletextpad (float, optional): 图例符号与文本标签间的间距. Defaults: 0.2.
        legend_frameon (bool, optional): 图例是否显示边框. Defaults: True.
        axes3d_grid (bool, optional): 3D 图是否显示网格线. Defaults: True.
        axes_grid (bool, optional): 2D 图是否显示网格线. Defaults: False.
        image_aspect (str, optional): 图片显示时的长宽比. Defaults: "equal".

    Returns:
        Dict: Matplotlib rcParams dict

    -------

    其他可以补充的 rcParams
    "axes.edgecolor": "color", 设置坐标轴边框的颜色.
    "axes.facecolor": "color", 设置坐标轴背景颜色.
    "xtick.labelsize": size, 设置 x 轴刻度标签的字体大小.
    "ytick.labelsize": size, 设置 y 轴刻度标签的字体大小.
    "text.usetex": bool, 设置是否使用 TeX 解析字符串中的 LaTeX 标记.
    "axes.prop_cycle": cycle, 设置默认颜色循环.

    """

    rcParams_dict = {
        "font.family": font_family,
        "font.weight": font_weight,
        "axes.labelweight": axes_labelweight,
        "axes.titleweight": axes_titleweight,
        "font.size": font_size,
        "legend.fontsize": legend_fontsize,
        "mathtext.fontset": mathtext_fontset,
        "mathtext.default": mathtext_default,
        "xtick.direction": xtick_direction,
        "ytick.direction": ytick_direction,
        "axes.linewidth": axes_linewidth,
        "lines.linewidth": lines_linewidth,
        "lines.markersize": lines_markersize,
        "xtick.major.width": xtick_major_width,
        "ytick.major.width": ytick_major_width,
        "xtick.minor.width": xtick_minor_width,
        "ytick.minor.width": ytick_minor_width,
        "xtick.major.size": xtick_major_size,
        "ytick.major.size": ytick_major_size,
        "xtick.minor.size": xtick_minor_size,
        "ytick.minor.size": ytick_minor_size,
        "xtick.minor.visible": xtick_minor_visible,
        "ytick.minor.visible": ytick_minor_visible,
        "xtick.major.pad": xtick_major_pad,
        "ytick.major.pad": ytick_major_pad,
        "xtick.top": xtick_top,
        "ytick.right": ytick_right,
        "axes.labelpad": axes_labelpad,
        "axes.titlepad": axes_titlepad,
        "savefig.dpi": savefig_dpi,
        "figure.dpi": figure_dpi,
        "savefig.bbox": savefig_bbox,
        "legend.columnspacing": legend_columnspacing,
        "legend.labelspacing": legend_labelspacing,
        "legend.handletextpad": legend_handletextpad,
        "legend.frameon": legend_frameon,
        "axes3d.grid": axes3d_grid,
        "axes.grid": axes_grid,
        "image.aspect": image_aspect,
    }

    rcParams_dict.update(kwargs)

    if roman_params:
        rcParams_dict.update(roman_plot_params)

    if sci_params:
        rcParams_dict.update(sci_plot_params)

    rcParams.update(rcParams_dict)

    return rcParams_dict
