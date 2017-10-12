#!/usr/bin/python
import click
import json
import os
import signal
import selenium.webdriver as seldriver
import yaml

from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from tqdm import tqdm

from bokeh.io import export_png_and_data
from data_utils import combine_source_and_rendered_data
from figure import *
from show_bounding_boxes import generate_all_images_with_bboxes_for_plot
from questions.categorical import generate_bar_graph_questions, generate_pie_chart_questions
from questions.lines import generate_line_plot_questions


def generate_figures (
        source_data_json,
        destination_directory,
        add_bboxes=False,
        supplied_webdriver=None
    ):

    # Setup dest dirs
    qa_json_dir = os.path.join(destination_directory, "json_qa")
    annotations_json_dir = os.path.join(destination_directory, "json_annotations")
    html_dir = destination_directory
    png_dir = os.path.join(destination_directory, "png")

    dirs = [destination_directory, qa_json_dir, annotations_json_dir, png_dir]

    if add_bboxes:
        bbox_img_dir = os.path.join(destination_directory, "bbox_png")
        dirs.append(bbox_img_dir)

    for dirpath in dirs:
        if not os.path.exists(dirpath):
            os.mkdir(dirpath)

    # Create web driver
    if supplied_webdriver:
        webdriver = supplied_webdriver
    else:
        webdriver = seldriver.PhantomJS()

    # Read in the synthetic data
    with open(source_data_json, 'r') as f:
        source_data_json = json.load(f)

    for fig_id, source in tqdm(iter(enumerate(source_data_json['data'])), total=len(source_data_json['data']), desc="Plotting figures"):

        point_sets = source['data']

        fig = None
        fig_type = source['type']

        if fig_type == 'vbar_categorical':
            fig = VBarGraphCategorical(point_sets[0], source['visuals'])
        elif fig_type == 'hbar_categorical':
            fig = HBarGraphCategorical(point_sets[0], source['visuals'])
        elif fig_type == 'line':
            fig = LinePlot(point_sets, source['visuals'])
        elif fig_type == 'dot_line':
            fig = DotLinePlot(point_sets, source['visuals'])
        elif fig_type == 'pie':
            fig = Pie(point_sets[0], source['visuals'])

        if not fig:
            continue

        html_file = os.path.join(html_dir, "%d_%s.html" % (fig_id, fig_type))
        png_file = os.path.join(png_dir, "%d_%s.png" % (fig_id, fig_type))

        # Export to HTML, PNG, and get rendered data
        rendered_data = export_png_and_data(fig.figure, png_file, html_file, webdriver)

        all_plot_data = combine_source_and_rendered_data(source, rendered_data)

        qa_json_file = os.path.join(qa_json_dir, "%s_%s.json" % (fig_id, fig_type))
        annotations_json_file = os.path.join(annotations_json_dir, "%d_%s_annotations.json" % (fig_id, fig_type))

        for qa in source['qa_pairs']:
            qa['image'] = os.path.basename(png_file)
            qa['annotations'] = os.path.basename(annotations_json_file)

        with open(qa_json_file, 'w') as f:
            json.dump({
                'qa_pairs': source['qa_pairs'], 
                'total_distinct_questions': source_data_json['total_distinct_questions'],
                'total_distinct_colors': source_data_json['total_distinct_colors']
            }, f)

        with open(annotations_json_file, 'w') as f:
            json.dump(all_plot_data, f)

        if add_bboxes:
            all_plot_data['image_index'] = fig_id
            generate_all_images_with_bboxes_for_plot(all_plot_data, png_file, bbox_img_dir, 'red', load_image=True)

        # Cleanup
        os.remove(html_file)

    # Kill the newly created webdriver
    if not supplied_webdriver:
        webdriver.service.process.send_signal(signal.SIGTERM)
        try:
            RemoteWebDriver.quit(webdriver)
        except:
            pass


@click.command()
@click.argument("source_data_json")
@click.argument("destination_directory")
@click.option("--add-bboxes", flag_value=True, 
                help="option to generate figures with bounding box annotations as well")
def main(**kwargs):
    """
    Generates figures from SOURCE_DATA_JSON generated with 'synthetic_data_generation.py' and saves
    them to DESTINATION_DIRECTORY.
    """
    generate_figures(**kwargs)


if __name__ == "__main__":
    main()
