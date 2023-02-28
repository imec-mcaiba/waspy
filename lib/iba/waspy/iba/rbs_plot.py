import copy
import random
from datetime import datetime
from typing import List

import numpy as np
from matplotlib.figure import Figure
from matplotlib import pyplot as plt
from waspy.iba.rbs_entities import RbsData, GraphGroup, AysFitResult, Graph, ChannelingMapYield, HeatMap, \
    FitAlgorithmType
import matplotlib

matplotlib.use('Agg')


def plot_graph_group(graph_group: GraphGroup) -> Figure:
    nr_of_graphs = len(graph_group.graphs)
    fig, axs = plt.subplots(nr_of_graphs)
    fig.suptitle(graph_group.title)

    if nr_of_graphs == 1:
        axs = [axs]

    for (ax, graph) in zip(axs, graph_group.graphs):
        ax.set_title(graph.title)
        for plot in graph.plots:
            ax.plot(plot.points, label=plot.title)
        _configure_ax(ax, graph.x_label, graph.y_label)

    return fig


def plot_heat_map(heat_map: HeatMap) -> Figure:
    x_axis = []
    y_axis = []

    for cms_yield in heat_map.yields:
        if cms_yield.theta not in x_axis:
            x_axis.append(cms_yield.theta)
        if cms_yield.zeta not in y_axis:
            y_axis.append(cms_yield.zeta)

    x_axis.sort()
    y_axis.sort(reverse=True)

    data = np.zeros(shape=(len(y_axis), len(x_axis)), dtype=int)
    for cms_yield in heat_map.yields:
        data[y_axis.index(cms_yield.zeta)][x_axis.index(cms_yield.theta)] = cms_yield.energy_yield


    fig, ax = plt.subplots()
    ax.set_title(f"Channeling Map {heat_map.title}")
    ax.set_xlabel("theta")
    ax.set_ylabel("zeta")
    ax.set_xticks(np.arange(len(x_axis)), labels=x_axis, fontsize=8, rotation=90)
    ax.set_yticks(np.arange(len(y_axis)), labels=y_axis, fontsize=8)
    im = ax.imshow(data)
    fig.colorbar(im)

    return fig


def plot_graph(graph: Graph) -> Figure:
    graph_group = GraphGroup(graphs=[graph])
    return plot_graph_group(graph_group)


def _configure_ax(ax, x_label, y_label):
    ax.grid(which='major')
    ax.grid(which='minor', linestyle=":")
    ax.legend()
    ax.minorticks_on()
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)


def plot_energy_yields(title, fit_result: AysFitResult, fit_algorithm_type=FitAlgorithmType.LOWER_FIT):
    fig, ax = plt.subplots()
    ax.scatter(fit_result.discrete_angles, fit_result.discrete_yields, marker="+", color="red", label="Data Points")
    ax.axhline(np.amin(fit_result.discrete_yields), label="Minimum", linestyle=":")
    if fit_algorithm_type is not FitAlgorithmType.MINIMUM_YIELD:
        smooth_angles = np.arange(fit_result.discrete_angles[1], fit_result.discrete_angles[-1], 0.01)
        smooth_yields = fit_result.fit_func(smooth_angles)
        ax.plot(smooth_angles, smooth_yields, color="green", label="fit")
    ax.axvline(fit_result.minimum, label=f"Minimum Angle={fit_result.minimum}", color="blue", linestyle=":")
    ax.legend(loc=0)
    plt.xlabel("degrees").set_fontsize(15)
    plt.ylabel("yield").set_fontsize(15)
    plt.title(title)
    plt.grid()
    return fig
