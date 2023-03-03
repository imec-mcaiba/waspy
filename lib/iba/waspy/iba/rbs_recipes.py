import logging
import os.path
from datetime import datetime
from pathlib import Path
from shutil import copytree
from typing import List

from scipy.optimize import OptimizeWarning

from waspy.iba.file_handler import FileHandler
from waspy.iba.iba_error import CancelError
from waspy.iba.rbs_plot import plot_energy_yields, plot_graph_group, plot_heat_map
from waspy.iba.rbs_entities import get_positions_as_coordinate, CoordinateRange, Graph, Plot, \
    RbsChanneling, get_positions_as_float, Window, PositionCoordinates, GraphGroup, RbsRandom, \
    AysFitResult, AysJournal, RbsData, ChannelingJournal, RbsJournal, get_rbs_journal, ChannelingMapJournal, \
    RbsChannelingMap, \
    ChannelingMapYield, HeatMap, FitAlgorithmType
from waspy.iba.rbs_setup import RbsSetup
from waspy.iba.rbs_yield_angle_fit import fit_and_smooth


def run_random(recipe: RbsRandom, rbs: RbsSetup) -> RbsJournal:
    start_time = datetime.now()
    rbs.move(recipe.start_position)
    rbs_data = run_rbs_recipe(recipe.coordinate_range, recipe.charge_total, rbs)
    return get_rbs_journal(rbs_data, start_time)


def run_channeling_map(recipe: RbsChannelingMap, rbs: RbsSetup, file_handler: FileHandler,
                       recipe_meta_data) -> ChannelingMapJournal:
    start_time = datetime.now()
    rbs.move(recipe.start_position)

    zeta_angles = get_positions_as_float(recipe.zeta_coordinate_range)
    theta_angles = get_positions_as_float(recipe.theta_coordinate_range)
    rbs_journals = []
    cms_yields = []
    rbs_index = 0

    for zeta in zeta_angles:
        for theta in theta_angles:
            rbs.move(PositionCoordinates(zeta=zeta, theta=theta))
            cms_step_start_time = datetime.now()
            rbs.prepare_acquisition()
            rbs_data = rbs.acquire_data(recipe.charge_total)
            if rbs.cancelled():
                raise CancelError("RBS Recipe was cancelled")
            rbs.finalize_acquisition()
            histogram_data = rbs_data.histograms[recipe.optimize_detector_identifier]
            rbs_journal = get_rbs_journal(rbs_data, cms_step_start_time)
            rbs_journals.append(rbs_journal)
            energy_yield = get_sum(histogram_data, recipe.yield_integration_window)
            cms_yields.append(ChannelingMapYield(zeta=zeta, theta=theta, energy_yield=energy_yield))
            save_channeling_map_journal(file_handler, recipe, rbs_journal, zeta, theta, rbs_index, recipe_meta_data)
            rbs_index += 1
        rbs_index += 1

    end_time = datetime.now()

    return ChannelingMapJournal(start_time=start_time, end_time=end_time, rbs_journals=rbs_journals,
                                cms_yields=cms_yields)


def run_channeling(recipe: RbsChanneling, rbs: RbsSetup, file_handler: FileHandler, recipe_meta_data,
                   ays_report_cb: callable(AysJournal) = None) -> ChannelingJournal:
    rbs.move(recipe.start_position)

    logging.info("[WASPY.IBA.RBS_RECIPES] Start ays")
    ays = run_ays(recipe, rbs, ays_report_cb, file_handler, recipe_meta_data)

    logging.info("[WASPY.IBA.RBS_RECIPES] Start Fixed")
    start_time = datetime.now()
    rbs.prepare_acquisition()
    fixed_data = rbs.acquire_data(recipe.compare_charge_total)
    fixed = get_rbs_journal(fixed_data, start_time)
    save_rbs_journal_with_file_stem(file_handler, recipe.name + "_fixed", recipe, fixed, recipe_meta_data)

    logging.info("[WASPY.IBA.RBS_RECIPES] Start Random")
    rbs.move(PositionCoordinates(theta=-2))
    start_time = datetime.now()
    random_data = run_rbs_recipe(recipe.random_coordinate_range, recipe.compare_charge_total, rbs)
    random = get_rbs_journal(random_data, start_time)
    save_rbs_journal_with_file_stem(file_handler, recipe.name + "_random", recipe, random, recipe_meta_data)

    return ChannelingJournal(random=random, fixed=fixed, ays=ays, title=recipe.name)


def run_rbs_recipe(coordinate_range: CoordinateRange, charge_total: int, rbs: RbsSetup) -> RbsData:
    logging.info("[WASPY.IBA.RBS_RECIPES] run_rbs_recipe")
    positions = get_positions_as_coordinate(coordinate_range)
    charge_per_step = charge_total / len(positions)
    rbs.prepare_acquisition()
    for position in positions:
        rbs.move(position)
        rbs.acquire_data(charge_per_step)
        if rbs.cancelled():
            raise CancelError("RBS Recipe was cancelled")
    rbs.finalize_acquisition()
    return rbs.get_status(True)


def save_channeling_map_to_disk(file_writer, yields: List[ChannelingMapYield], title):
    heat_map = HeatMap(title=title, yields=yields)
    fig = plot_heat_map(heat_map)
    file_writer.write_matplotlib_fig_to_disk(f'channeling_map_{heat_map.title}.png', fig)


def copy_analysis_to_disk(file_writer):
    file_writer.copy_folder_to_base("../analysis/src/analysis", Path("analysis"))


def save_channeling_graphs_to_disk(file_writer, channeling_result: ChannelingJournal, file_stem):
    graphs = []
    fixed_data = channeling_result.fixed
    random_data = channeling_result.random
    for detector_name in fixed_data.histograms.keys():
        fixed_plot = Plot(title=f'fixed', points=fixed_data.histograms[detector_name])
        random_plot = Plot(title=f'random', points=random_data.histograms[detector_name])
        graph = Graph(title=f'{detector_name}', plots=[fixed_plot, random_plot], x_label="energy level",
                      y_label="yield")
        graphs.append(graph)
    graph_group = GraphGroup(title=f'{file_stem}', graphs=graphs)
    fig = plot_graph_group(graph_group)
    file_writer.write_matplotlib_fig_to_disk(f'{graph_group.title}.png', fig)


def save_rbs_graph_to_disk(file_writer, journal: RbsJournal, file_stem):
    graphs = []
    for [detector, histogram] in journal.histograms.items():
        plot = Plot(title=detector, points=histogram)
        graphs.append(Graph(title="", plots=[plot], x_label="energy level", y_label="yield"))

    graph_group = GraphGroup(graphs=graphs, title=file_stem)
    fig = plot_graph_group(graph_group)
    file_writer.write_matplotlib_fig_to_disk(f'{graph_group.title}.png', fig)


def save_rbs_journal(file_handler: FileHandler, recipe: RbsRandom, journal: RbsJournal, extra):
    save_rbs_journal_with_file_stem(file_handler, recipe.name, recipe, journal, extra)


def save_rbs_journal_with_file_stem(file_writer: FileHandler, file_stem,
                                    recipe: RbsChanneling | RbsRandom | RbsChannelingMap,
                                    journal: RbsJournal, extra):
    for [detector, histogram] in journal.histograms.items():
        title = f'{file_stem}_{detector}.txt'
        header = _serialize_histogram_header(journal, detector, recipe, extra)
        data = format_caen_histogram(histogram)
        file_writer.write_text_to_disk(title, f'{header}\n{data}')
    save_rbs_graph_to_disk(file_writer, journal, file_stem)


def save_channeling_map_journal(file_handler: FileHandler, recipe: RbsChannelingMap, journal: RbsJournal, zeta, theta,
                                rbs_index, recipe_meta_data):
    # file_handler.cd_folder(recipe.name)
    save_rbs_journal_with_file_stem(file_handler,
                                    f'{rbs_index:02}_{recipe.name}_'
                                    f'zeta{zeta}_'
                                    f'theta{theta}',
                                    recipe, journal, recipe_meta_data)
    # file_handler.cd_folder_up()


def save_ays_journal(file_handler: FileHandler, recipe: RbsChanneling, ays_journal: AysJournal, ays_index, extra,
                     fit_algorithm_type=FitAlgorithmType.LOWER_FIT):
    yield_coordinate_range = recipe.yield_coordinate_ranges[ays_index]
    coordinate_ranging = yield_coordinate_range.name
    positions = get_positions_as_float(yield_coordinate_range)
    name = f'{recipe.name}_{ays_index}_{coordinate_ranging}'
    file_handler.cd_folder(name)
    for rbs_index, rbs_journal in enumerate(ays_journal.rbs_journals):
        save_rbs_journal_with_file_stem(file_handler, f'{rbs_index:02}_{name}_{positions[rbs_index]}', recipe,
                                        rbs_journal, extra)
    text = serialize_energy_yields(ays_journal.fit)
    file_handler.write_text_to_disk(f'_{name}_yields.txt', text)

    file_name = f'_{name}'
    if ays_journal.fit.success:
        fig = plot_energy_yields(name, ays_journal.fit, fit_algorithm_type)
        file_handler.write_matplotlib_fig_to_disk(f'{file_name}.png', fig)
    else:
        file_handler.write_text_to_disk(f'{file_name}.txt', "Fitting failed")
        file_handler.cd_folder_up()
        return
    file_handler.cd_folder_up()


def serialize_energy_yields(fit_data: AysFitResult) -> str:
    text = ""
    for [angle, energy_yield] in zip(fit_data.discrete_angles, fit_data.discrete_yields):
        text += f'{angle}, {energy_yield}\n'
    return text


def run_ays(recipe: RbsChanneling, rbs: RbsSetup, ays_report_callback: callable(AysJournal), file_handler,
            recipe_meta_data) -> List[AysJournal]:
    """ays: angular yield scan"""
    start_time = datetime.now()
    result = []
    logging.info(f"[WASPY.IBA.RBS_RECIPES] YIELD COORD RANGES {recipe.yield_coordinate_ranges}")
    for ays_index, coordinate_range in enumerate(recipe.yield_coordinate_ranges):
        rbs_journals = []
        yields = []
        angles = get_positions_as_float(coordinate_range)
        for angle in angles:
            single = CoordinateRange.init_single(coordinate_range.name, angle)
            ays_step_start_time = datetime.now()
            rbs_data = run_rbs_recipe(single, recipe.yield_charge_total, rbs)
            rbs_journal = get_rbs_journal(rbs_data, ays_step_start_time)
            rbs_journals.append(rbs_journal)
            yields.append(get_sum(rbs_journal.histograms[recipe.yield_optimize_detector_identifier],
                                  recipe.yield_integration_window))
        fit_result = find_minimum(angles, yields, recipe.fit_algorithm_type)
        if fit_result.success:
            logging.info(f"[WASPY.IBA.RBS_RECIPES] Minimum found at {coordinate_range.name}={fit_result.minimum}")
            rbs.move(convert_float_to_coordinate(coordinate_range.name, fit_result.minimum))
        ays_journal = AysJournal(start_time=start_time, end_time=datetime.now(), rbs_journals=rbs_journals,
                                 fit=fit_result)
        result.append(ays_journal)
        if ays_report_callback:
            ays_report_callback(result[-1])
        save_ays_journal(file_handler, recipe, ays_journal, ays_index, recipe_meta_data, recipe.fit_algorithm_type)

    return result


def find_minimum(angles, yields, fit_algorithm_type=FitAlgorithmType.LOWER_FIT) -> AysFitResult:
    try:
        fit_func, min_angle = fit_and_smooth(angles, yields, fit_algorithm_type)
        return AysFitResult(success=True, minimum=min_angle, discrete_angles=angles,
                            discrete_yields=yields, fit_func=fit_func)
    except (RuntimeError, OptimizeWarning, ValueError) as e:
        logging.error(e)
        return AysFitResult(success=False, discrete_angles=angles, discrete_yields=yields)


def get_sum(data: List[int], window: Window) -> int:
    return sum(data[window.start:window.end])


def convert_float_to_coordinate(coordinate_name: str, position: float) -> PositionCoordinates:
    return PositionCoordinates.parse_obj({coordinate_name: position})


def format_caen_histogram(data: List[int]) -> str:
    index = 0
    data_string = ""
    for energy_level in data:
        data_string += f'{index}, {energy_level}\n'
        index += 1
    return data_string


def _serialize_histogram_header(journal: RbsJournal, detector_name, recipe: RbsRandom | RbsChanneling, extra):
    now = datetime.utcnow().strftime("%Y.%m.%d__%H:%M__%S.%f")[:-3]
    header = f""" % Comments
 % Title                 := {recipe.name + "_" + detector_name}
 % Section := <raw_data>
 *
 * Filename no extension := {recipe.name}
 * DATE/Time             := {now}
 * MEASURING TIME[sec]   := {journal.measuring_time_sec}
 * ndpts                 := {1024}
 *
 * ANAL.IONS(Z)          := 4.002600
 * ANAL.IONS(symb)       := He+
 * Charge[nC]            := {journal.accumulated_charge}
 *
 * Sample ID             := {recipe.sample}
 * Sample X              := {journal.x}
 * Sample Y              := {journal.y}
 * Sample Zeta           := {journal.zeta}
 * Sample Theta          := {journal.theta}
 * Sample Phi            := {journal.phi}
 * Sample Det            := {journal.det}
 *
 * Detector name         := {detector_name}
 * Detector ZETA         := 0.0
 * Detector Omega[mSr]   := 0.42
 * Detector offset[keV]  := 33.14020
 * Detector gain[keV/ch] := 1.972060
 * Detector FWHM[keV]    := 18.0
"""
    if extra:
        header += extra

    header += f""" % Section :=  </raw_data>
 % End comments"""
    return header
