#!/usr/bin/python
import click
import json
import numpy as np
import os
import random
import yaml

from tqdm import tqdm

from data_utils import combine_source_and_rendered_data, get_best_inside_legend_position, hex_to_rgb
from questions.categorical import generate_bar_graph_questions, generate_pie_chart_questions
from questions.lines import generate_line_plot_questions
from questions.utils import balance_questions_by_qid, NUM_DISTINCT_QS

from scipy.stats import norm as norm_gen


# Utility functions
def generate_data_by_shape(x_range, y_range, n, x_distn, shape):
    x = []

    if x_distn == "random":
        x = (x_range[1] - x_range[0]) * np.random.random(n) + x_range[0]

    elif x_distn == "linear":
        x = np.linspace(x_range[0], x_range[1], n)

    elif x_distn == "normal":
        mean = (x_range[1] - x_range[0]) * np.random.random(1) + x_range[0]
        points = (x_range[1] - x_range[0]) *  np.random.normal(0, 1/6.0, 3*n) + mean

        final_points = []
        for point in points:
            if point >= x_range[0] and point <= x_range[1]:
                final_points.append(point)
            if len(final_points) == n:
                break
        x = final_points

    x = sorted(x)
    y = []

    max_slope = (y_range[1] - y_range[0]) / float(x_range[1] - x_range[0])

    if shape == "random":
        y = (y_range[1] - y_range[0]) * np.random.random(n) + y_range[0]

    elif shape == "linear":
        # Decide slope direction randomly
        slope_direction = 1 if np.random.random() > 0.5 else -1
        offset = y_range[0] if slope_direction >= 0 else y_range[1]
        y = np.clip(slope_direction*max_slope*np.random.random()*np.array(x[:]) + offset, y_range[0], y_range[1]).tolist()

    elif shape == "linear_with_noise":
        # Decide slope direction randomly
        slope_direction = 1 if np.random.random() > 0.5 else -1
        offset = y_range[0] if slope_direction >= 0 else y_range[1]
        y = np.clip(slope_direction*max_slope*np.random.random()*np.array(x[:]) + offset, y_range[0], y_range[1]).tolist()

        # Add some noise then reclip
        noise_multiplier = 0.05 * (y_range[1] - y_range[0])
        for i in range(len(y)):
            y[i] += noise_multiplier * (2*np.random.random() - 1)

        y = np.clip(y, y_range[0], y_range[1]).tolist()
    
    elif shape == "linear_inc":
        y = np.clip(max_slope*np.random.random()*np.array(x[:]) + y_range[0], y_range[0], y_range[1]).tolist()

    elif shape == "linear_dec":
        y = np.clip(-max_slope*np.random.random()*np.array(x[:]) + y_range[1], y_range[0], y_range[1]).tolist()

    elif shape == "cluster":
        mean = (y_range[1] - y_range[0]) * np.random.random() + y_range[0]

        points = (y_range[1] - y_range[0]) *  np.random.normal(0, 1/6.0, 3*n) + mean
        
        final_points = []
        got_all_points = False

        while True:

            points = (y_range[1] - y_range[0]) *  np.random.normal(0, 1/6.0, n) + mean

            for point in points:

                if point >= y_range[0] and point <= y_range[1]:
                    final_points.append(point)

                if len(final_points) == n:
                    got_all_points = True
                    break

            if got_all_points:
                break

        y = final_points

    elif shape == "quadratic":
        # Use vertex form: y = a(x-h)^2 + k
        h = (x_range[1] - x_range[0])/2 * np.random.random() + x_range[0]
        k = (y_range[1] - y_range[0])/2 * np.random.random() + y_range[0]

        dist_from_mid = np.abs((y_range[1] - y_range[0])/2 + y_range[0])

        # Decide a direction based on k
        if k < (y_range[1] - y_range[0])/2 + y_range[0]:
            a = -1 * dist_from_mid
        else:
            a = 1 * dist_from_mid

        a *= np.random.random()*0.00005
        y = np.clip(np.array([a*(xx-h)**2 + k for xx in x]), y_range[0], y_range[1]).tolist()

    return x, y


def pick_random_int_range(the_range):
    range_start, range_end = the_range
    start = np.random.random_integers(range_start, range_end - 1)
    end = np.random.random_integers(start + 1, range_end)
    return start, end


def pick_n_classes_from_half_gaussian(start, end):

    # Want range to make up 3 stddevs, so 99.7% or data covered
    float_sample = np.random.normal(start, (end-start) / 3)

    # Flip since symmetric
    if float_sample < start:
        float_sample = -(float_sample - start) + start

    # Clamp
    if float_sample > end:
        float_sample = end

    choice = int(np.floor(float_sample))
    return choice


def sample_from_custom_gaussian(mean, stddev, bound_start, bound_end):

    # Use rejection sampling
    while True:
        y = np.random.normal(mean, stddev)
        g_y = norm_gen.pdf(y, mean, stddev)
        f_y = g_y if (y >= bound_start and y <= bound_end) else 0

        if np.random.random() <= f_y / g_y :
            return y


# Data generation functions
def _generate_scatter_data_continuous(x_range, y_range, x_distns, shapes, n_points_range, n_classes_range, class_distn_mean=0, fix_x_range=False, fix_y_range=False):
    if not fix_x_range:
        x_range = pick_random_int_range(x_range)
    if not fix_y_range:
        y_range = pick_random_int_range(y_range)

    s, e = n_classes_range
    n_classes = np.random.random_integers(s, e)
    s, e = n_points_range
    n_points = np.random.random_integers(s, e)

    point_sets = []
    for i in range(0, n_classes):
        x_distn = np.random.choice(x_distns)
        shape = np.random.choice(shapes)

        x, y = generate_data_by_shape(x_range, y_range, n_points, x_distn, shape)

        if type(x) != type([]):
            x = x.tolist()
        if type(y) != type([]):
            y = y.tolist()

        point_sets.append({ 'class': i, 'x': x, 'y': y })

    return {'type': "scatter_base", 'data': point_sets, 'n_points': n_points, 'n_classes': n_classes}


def _generate_scatter_data_categorical(y_range, n_points_range, x_distns, shapes, n_classes_range, fix_y_range=False):
    if not fix_y_range:
        y_range = pick_random_int_range(y_range)

    s, e = n_classes_range
    n_classes = np.random.random_integers(s, e)
    s, e = n_points_range
    n_points = np.random.random_integers(s, e)
    
    # Pick and randomize the labels, by index
    all_labels = np.random.permutation(n_points).tolist()

    point_sets = []
    for i in range(0, n_classes):
        x_distn = np.random.choice(x_distns)
        shape = np.random.choice(shapes)
        x, y = generate_data_by_shape([0, n_points - 1], y_range, n_points, x_distn, shape)
        
        # Round x to discretize it
        x = np.array(np.around(x), dtype=np.int32)

        # Then de-dupe it
        dedupe_x, dedupe_y = [x[0]], [y[0]]
        last_x = x[0]
        for i in range(1, len(x)):
            try:
                if x[i] == last_x:
                    continue
                last_x = x[i]
                dedupe_x.append(x[i])
                dedupe_y.append(y[i])
            except:
                continue

        x, y = dedupe_x, dedupe_y

        labels = [all_labels[xx] for xx in x]
        if type(y) != type([]):
            y = y.tolist()

        point_sets.append({ 'class': i, 'x': labels, 'y': y })

    return {'type': "scatter_categorical_base", 'data': point_sets, 'n_points': n_points}


def generate_scatter():
    config = data_config['scatter']   
    
    data = _generate_scatter_data_continuous(   config['x_range'],
                                                config['y_range'],
                                                config['x_distn'],
                                                config['shape'],
                                                config['n_points_range'],
                                                config['n_classes_range'],
                                            )
    data['type'] = "scatter"

    # Get colors and labels
    all_color_pairs = []
    with open(os.path.normpath(config['color_sources'][0]), 'r') as f:
        for w in f.readlines():
            name, color = w.split(',')
            all_color_pairs.append((name.strip(), color.strip()))

    for i, color_pair in enumerate(random.sample(all_color_pairs, len(data['data']))):
        name, color = color_pair
        data['data'][i]['label'] = name
        data['data'][i]['color'] = color

    return data


def _generate_visuals_common():
    visuals = {}
    visuals['draw_legend'] = True if np.random.random() <= common_config['draw_legend_pr'] else False
    if visuals['draw_legend']:
        visuals['legend_border'] = True if np.random.random() <= common_config['legend_border_pr'] else False

    visuals['figure_height'] = common_config['figure_height_px']

    lo = common_config['figure_width_ratio_range'][0]
    hi = common_config['figure_width_ratio_range'][1]
    ratio = (np.random.random() * (hi - lo)) + lo

    visuals['figure_width'] = int(ratio * visuals['figure_height'])

    visuals['draw_gridlines'] = True if np.random.random() <= common_config['draw_gridlines_pr'] else False

    visuals['legend_label_font_size'] = np.random.choice(common_config['legend_label_font_sizes'])

    return visuals


def _generate_bar_categorical(key):
    config = data_config[key]   
    
    data = _generate_scatter_data_categorical(  config['y_range'],
                                                config['n_points_range'],
                                                config['x_distn'],
                                                config['shape'],
                                                [1, 1],
                                                fix_y_range=True
                                            )

    # Get colors and labels
    all_color_pairs = []
    with open(os.path.normpath(config['color_sources'][0]), 'r') as f:
        for w in f.readlines():
            name, color = w.split(',')
            all_color_pairs.append((name.strip(), color.strip()))

    selected_color_pairs = random.sample(all_color_pairs, len(data['data'][0]['x']))

    assigned_labels = []
    assigned_colors = []
    for label_index in data['data'][0]['x']:
        assigned_labels.append(selected_color_pairs[label_index][0])
        assigned_colors.append(selected_color_pairs[label_index][1])

    # Re-map the labels
    new_point_set = {'class': data['data'][0]['class'], 'x': assigned_labels, 'y': data['data'][0]['y'], 'labels': assigned_labels, 'colors': assigned_colors}
    data['data'] = [new_point_set]
    data['visuals'] = _generate_visuals_common()

    return data


def generate_vbar_categorical():
    bar_data = _generate_bar_categorical("vbar_categorical")
    bar_data['type'] = "vbar_categorical"
    bar_data['qa_pairs'] = generate_bar_graph_questions(combine_source_and_rendered_data(bar_data), color_map=color_map)
    return bar_data


def generate_hbar_categorical():
    bar_data = _generate_bar_categorical("hbar_categorical")
    old_x = bar_data['data'][0]['x']
    bar_data['data'][0]['x'] = bar_data['data'][0]['y']
    bar_data['data'][0]['y'] = old_x
    bar_data['type'] = "hbar_categorical"
    bar_data['qa_pairs'] = generate_bar_graph_questions(combine_source_and_rendered_data(bar_data), color_map=color_map)
    return bar_data


def _generate_visuals_for_line_plot(point_sets):
    visuals = _generate_visuals_common()
    visuals['legend_inside'] = True if np.random.random() <= common_config['legend_inside_pr'] else False

    if visuals['legend_inside']:

        visuals['legend_position'] = get_best_inside_legend_position(point_sets)
        visuals['legend_orientation'] = "vertical"

        if len(point_sets) <= common_config['legend_horizontal_max_classes'] and np.random.random() <= common_config['legend_horizontal_pr']:
            visuals['legend_orientation'] = "horizontal"

    else:

        # Determine legend orientation. If the legend is outside, horizontal legend needs to be below the plot
        if len(point_sets) <= common_config['legend_horizontal_max_classes'] and np.random.random() <= common_config['legend_horizontal_pr']:

            outside_possibilities = [('below', 'bottom_left'), ('below', 'bottom_center'), ('below', 'bottom_right')]
            visuals['legend_orientation'] = "horizontal"

        else:

            outside_possibilities = [('right', 'bottom_right'), ('right', 'center_right'), ('right', 'top_right')]
            visuals['legend_orientation'] = "vertical"

            # Widen the plot a little bit if legend on the right
            min_ratio = common_config['figure_min_width_side_legend']
            max_ratio = common_config['figure_width_ratio_range'][1]

            if max_ratio < min_ratio:
                max_ratio = min_ratio

            if visuals['figure_width'] < min_ratio * visuals['figure_height']:
                visuals['figure_width'] = int((min_ratio + (max_ratio - min_ratio) * (np.random.random())) * visuals['figure_height'])

        legend_layout_position, legend_position = random.sample(outside_possibilities, 1)[0]

        visuals['legend_position'] = legend_position
        visuals['legend_layout_position'] = legend_layout_position

    return visuals


def _generate_line(key):
    config = data_config[key]
    data = _generate_scatter_data_continuous(   config['x_range'],
                                                config['y_range'],
                                                config['x_distn'],
                                                config['shape'],
                                                config['n_points_range'],
                                                config['n_classes_range'],
                                                fix_x_range=True
                                            )
    # Get colors and labels
    all_color_pairs = []
    with open(os.path.normpath(config['color_sources'][0]), 'r') as f:
        for w in f.readlines():
            name, color = w.split(',')
            all_color_pairs.append((name.strip(), color.strip()))

    selected_color_pairs = random.sample(all_color_pairs, len(data['data']))

    for i, point_set in enumerate(data['data']):
        point_set['label'] = selected_color_pairs[i][0]
        point_set['color'] = selected_color_pairs[i][1]

    return data


def generate_line():
    line_data = _generate_line("line")
    line_data['type'] = "line"
    line_data['qa_pairs'] = generate_line_plot_questions(combine_source_and_rendered_data(line_data), color_map=color_map)
    visuals = _generate_visuals_for_line_plot(line_data['data'])

    # Add variation for line styles
    solid_only = True if np.random.random() <= data_config['line']['solid_pr'] else False
    if solid_only:
        line_styles = ["solid"] * len(line_data['data'])
    else:
        reference_styles = [ "solid", "dashed", "dotted", "dotdash", "dashdot"]
        permuted_styles = list(np.random.permutation(reference_styles))
        line_styles = permuted_styles[:]

        while len(line_styles) < len(line_data['data']):
            line_styles += permuted_styles

        line_styles = line_styles[:len(line_data['data'])]

    visuals['line_styles'] = line_styles
    line_data['visuals'] = visuals

    return line_data


def generate_dot_line():
    line_data = _generate_line("dot_line")
    line_data['type'] = "dot_line"
    line_data['qa_pairs'] = generate_line_plot_questions(combine_source_and_rendered_data(line_data), color_map=color_map)
    line_data['visuals'] = _generate_visuals_for_line_plot(line_data['data'])

    return line_data


def generate_pie():
    config = data_config['pie']

    s, e = config['n_classes_range']
    n_classes = np.random.random_integers(s, e)

    widths = np.array([np.random.random() + 0.05 for i in range(n_classes)])
    widths_radians = 2 * np.pi * widths / np.sum(widths)
    starts = [0]
    for i in range(0, n_classes - 1):
        starts.append(starts[i] + widths_radians[i])
    ends = starts[1:] + [2*np.pi]

    thetas = [starts[i] + (ends[i] - starts[i])/2 for i in range(len(starts))]
    rad = 0.75
    x = [rad*np.cos(theta) for theta in thetas]
    y = [rad*np.sin(theta) for theta in thetas]

    # Get colors and labels
    all_color_pairs = []
    with open(os.path.normpath(config['color_sources'][0]), 'r') as f:
        for w in f.readlines():
            name, color = w.split(',')
            all_color_pairs.append( (name.strip(), color.strip()) )

    selected_color_pairs = random.sample(all_color_pairs, n_classes)

    pie_data = {
        'type': "pie", 'data': [
            {
                'label_x': x, 'label_y': y, 
                'labels': [cp[0] for cp in selected_color_pairs],
                'colors': [cp[1] for cp in selected_color_pairs],
                'spans': widths_radians.tolist(),
                'starts': starts,
                'ends': ends,
            }
        ]
    }

    # Add visuals and legend placement
    visuals = _generate_visuals_common()

    if visuals['draw_legend']:

        # Decide on legend orientation
        if n_classes <= common_config['legend_horizontal_max_classes'] and np.random.random() <= common_config['legend_horizontal_pr']:
            visuals['legend_orientation'] = "horizontal"
            outside_possibilities = [('below', 'bottom_left'), ('below', 'bottom_center'), ('below', 'bottom_right')]

        else:
            visuals['legend_orientation'] = "vertical"
            outside_possibilities = [('right', 'bottom_right'), ('right', 'center_right'), ('right', 'top_right'),
                                        ('left', 'bottom_left'), ('left', 'center_left'), ('left', 'top_left')]

        legend_layout_position, legend_position = random.sample(outside_possibilities, 1)[0]
        visuals['legend_position'] = legend_position
        visuals['legend_layout_position'] = legend_layout_position            

    pie_data['visuals'] = visuals
    pie_data['qa_pairs'] = generate_pie_chart_questions(combine_source_and_rendered_data(pie_data), color_map=color_map)

    return pie_data


def generate_source_data (
        data_config_yaml,
        output_file_json,
        common_config_yaml=os.path.join("config", "common_source_data.yaml"),
        seed=1,
        colors=os.path.join("resources", "x11_colors_refined.txt"),
        keep_all_questions=False,
        vbar=0,
        hbar=0,
        pie=0,
        line=0,
        dot_line=0
    ):

    PLOT_KEY_PAIRS = [("vbar", "vbar_categorical"), ("hbar", "hbar_categorical"), ("pie", None), ("line", None), ("dot_line", None)]

    if all([locals()[arg_name] == 0 for arg_name, actual_name in PLOT_KEY_PAIRS]) \
            or any([locals()[arg_name] < 0 for arg_name, actual_name in PLOT_KEY_PAIRS]):
        raise Exception("Invalid number of figures! Need at least one plot type specified!")

    global data_config
    global common_config

    with open(data_config_yaml, 'r') as f:
        data_config = yaml.load(f)

    with open(common_config_yaml, 'r') as f:
        common_config = yaml.load(f)

    # Set the seed
    np.random.seed(seed)
    random.seed(seed)

    # Read the colors and create a map
    global color_map
    color_map = {}
    color_count = 0

    with open(os.path.normpath(colors), 'r') as f:
        for w in f.readlines():
            name, color = w.split(',')
            color = color.strip()
            color_map[name] = {'id': color_count, 'hex': color, 'rgb': hex_to_rgb(color)}
            color_count += 1

    generated_data = []

    for args_key, config_key in PLOT_KEY_PAIRS:

        figure_ids = range(0, locals()[args_key])

        if len(figure_ids) == 0:
            continue

        for i in tqdm(iter(figure_ids), total=len(figure_ids), desc="Generating data for {:10}".format(args_key)):
            if not config_key:
                config_key = args_key

            if config_key in data_config:
                generated_data.append(globals()['generate_' + config_key]())

    # Balance by question ID
    if not keep_all_questions:
        balance_questions_by_qid(generated_data)

    with open(output_file_json, 'w') as f:
        json.dump({
            'data': generated_data, 
            'total_distinct_questions': NUM_DISTINCT_QS,
            'total_distinct_colors': len(color_map)
        }, f)


@click.command()
@click.argument("data_config_yaml")
@click.argument("output_file_json")
@click.option("-c", "--common-config-yaml", default=os.path.join("config", "common_source_data.yaml"),
                help="YAML file with common plotting and style attributes")
@click.option("--seed", default=1, type=int,
                help="seed for PRNGs")
@click.option("--colors", default=os.path.join("resources", "x11_colors_refined.txt"),
                help="file with all color names and hexcodes")
@click.option("--keep-all-questions", flag_value=True,
                help="if specified, all possible questions will be generated without any filtering")
@click.option("--vbar", default=0, type=int,
                help="number of vertical bar graphs")
@click.option("--hbar", default=0, type=int,
                help="number of horizontal bar graphs")
@click.option("--pie", default=0, type=int,
                help="number of pie charts")
@click.option("--line", default=0, type=int,
                help="number of line plots")
@click.option("--dot-line", default=0, type=int,
                help="number of dotted line plots")
def main (**kwargs):
    """
    Generates source data and questions for figures using the plotting parameters and colors
    defined in DATA_CONFIG_YAML and saves the data to OUTPUT_FILE_JSON.
    """
    generate_source_data(**kwargs)


if __name__ == "__main__":
    main()
