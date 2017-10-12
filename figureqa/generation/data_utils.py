#!/usr/bin/python
from __future__ import division

import copy
import random


# Used in modified BokehJS
ID_MAP = {
    'title': 'the_title',
    'x_axis': 'the_xaxis',
    'y_axis': 'the_yaxis',
    'x_gridlines': 'the_x_gridlines',
    'y_gridlines': 'the_y_gridlines',
    'legend': 'the_legend',
    'figure_info': '_figure_info'
}


def _map_axis_data(axis_data):
    final_data = {}

    for key in axis_data:
        if key in ['major_ticks', 'major_labels', 'minor_ticks']:
            final_data[key] = { 'bboxes': map(lambda x: x['bbox'], axis_data[key]),
                                'values': map(lambda x: x['value'] if 'value' in x else x['text'], axis_data[key]) }
        elif key in ['rule', 'label']:
            final_data[key] = copy.deepcopy(axis_data[key][0])

    return final_data


def _get_general_figure_data(source_data=None, rendered_data=None):

    if not rendered_data:
        return {}

    data_access_functions = {
        'title':  lambda x: copy.deepcopy(x['title']),
        'x_axis': _map_axis_data,
        'y_axis': _map_axis_data,
        'x_gridlines': lambda x: {'bboxes': map(lambda y: y['bbox'], x['gridlines']), 'values': map(lambda y: y['value'], x['gridlines'])},
        'y_gridlines': lambda x: {'bboxes': map(lambda y: y['bbox'], x['gridlines']), 'values': map(lambda y: y['value'], x['gridlines'])},
        'legend': lambda x: {'bbox': x['bbox'], 'items': copy.deepcopy(x['items'])},
        'figure_info': lambda x: { 'bbox': {'bbox': {'x': 0, 'y': 0, 'w': x['w'], 'h': x['h']}}}
    }

    def get_plot_bbox():

        # Special case for pie charts
        if source_data and 'type' in source_data and source_data['type'] == 'pie':
            xs = []
            ys = []

            for model_data in rendered_data.values():
                if 'slices' not in model_data:
                    continue
                slice_bbox = model_data['slices'][0]['bbox'] 
                xs.append(slice_bbox['x'])
                xs.append(slice_bbox['x'] + slice_bbox['w'])
                ys.append(slice_bbox['y'])
                ys.append(slice_bbox['y'] + slice_bbox['h'])

        else:
            x_axis_bbox = rendered_data[ID_MAP['x_axis']]['rule'][0]['bbox']
            y_axis_bbox = rendered_data[ID_MAP['y_axis']]['rule'][0]['bbox']

            xs = [  x_axis_bbox['x'], x_axis_bbox['x'] + x_axis_bbox['w'],
                    y_axis_bbox['x'], y_axis_bbox['x'] + y_axis_bbox['w'] ]

            ys = [  x_axis_bbox['y'], x_axis_bbox['y'] + x_axis_bbox['h'],
                    y_axis_bbox['y'], y_axis_bbox['y'] + y_axis_bbox['h'] ]

        min_x = min(xs)
        min_y = min(ys)

        return {'x': min_x, 'y': min_y, 'w': max(xs) - min_x, 'h': max(ys) - min_y}

    final_data = {}

    for component, ident in ID_MAP.items():
        if ident in rendered_data:
            final_data[component] = data_access_functions[component](rendered_data[ident])

    final_data['plot_info'] = {'bbox': get_plot_bbox()}

    return final_data


def _get_bar_graph_categorical_data(source_data, rendered_data=None):
    source_bars = source_data['data'][0]
    final_data = { 
        'name': 'bars',
        'x': source_bars['x'],
        'y': source_bars['y'],
        'labels': source_bars['labels'],
        'colors': source_bars['colors']
    }

    if rendered_data:
        rendered_bars = rendered_data['the_bars']['bars']
        final_data['width'] = rendered_bars[0]['width'] if 'width' in rendered_bars[0] else rendered_bars[0]['height']
        final_data['bboxes'] = map(lambda x: x['bbox'], rendered_bars)

    return [final_data]


def _get_line_graph_data(source_data, rendered_data=None):
    source_lines = source_data['data']

    final_data = []

    for line in source_lines:
        line_data = {   
            'name': line['label'],
            'x': line['x'],
            'y': line['y'],
            'color': line['color'],
            'label': line['label']
        }

        if rendered_data:
            if 'points' in rendered_data[line['label']]:
                bboxes = [x['bbox'] for x in rendered_data[line['label']]['points']]
            else:
                bboxes = [x['bbox'] for x in rendered_data[line['label']]['segments']]

            line_data['bboxes'] = bboxes

        final_data.append(line_data)

    return final_data


def _get_pie_chart_data(source_data, rendered_data=None):
    source_wedges = source_data['data'][0]
    final_data = []

    if rendered_data and 'the_pie_labels' in rendered_data:
        annotations_map = { text: bbox for text, bbox in zip([x['text'] for x in rendered_data['the_pie_labels']['labels']],
                                                             [x['bbox'] for x in rendered_data['the_pie_labels']['labels']])}
    else:
        annotations_map = {}

    for i, label in enumerate(source_wedges['labels']):
        wedge_data = {
            'name': label,
            'start': source_wedges['starts'][i],
            'end': source_wedges['ends'][i],
            'span': source_wedges['spans'][i],
            'label': label
        }

        if rendered_data:
            wedge_data['bbox'] = rendered_data[label]['slices'][0]['bbox']

            if label in annotations_map:
                wedge_data['annotation'] = {'bbox': annotations_map[label]}

        final_data.append(wedge_data)
    
    return final_data


def combine_source_and_rendered_data(source_data, rendered_data=None):

    model_data_access_functions = {
        'hbar_categorical': _get_bar_graph_categorical_data,
        'vbar_categorical': _get_bar_graph_categorical_data,
        'pie': _get_pie_chart_data,
        'line': _get_line_graph_data,
        'dot_line': _get_line_graph_data
    }

    final_data = {  
        'type': source_data['type'],
        'general_figure_info': _get_general_figure_data(source_data, rendered_data),
        'models': model_data_access_functions[source_data['type']](source_data, rendered_data)
    }

    return final_data


def hex_to_rgb(hexcode):
    hexcode = hexcode.lstrip("#")
    rgb = [int(hexcode[i:i+2], 16) for i in (0, 2, 4)]
    return rgb


def rgb_dist(a, b):
    return np.sqrt(np.sum([(x - y)**2 for x, y in zip(a, b)]))


def get_points_per_quadrant(point_sets):
    # Get the bounds
    all_x, all_y = [], []
    for ps in point_sets:
        all_x += ps['x'][:]
        all_y += ps['y'][:]

    x_mid = ((max(all_x) - min(all_x)) / 2) + min(all_x)
    y_mid = ((max(all_y) - min(all_y)) / 2) + min(all_y)

    counts = {'TR': 0, 'TL': 0, 'BL': 0, 'BR': 0}

    for x, y in zip(all_x, all_y):

        if x > x_mid and y > y_mid:
            counts['TR'] += 1
        elif x <= x_mid and y > y_mid:
            counts['TL'] += 1
        elif x <= x_mid and y <= y_mid:
            counts['BL'] += 1
        else:
            counts['BR'] += 1

    return counts


def get_best_inside_legend_position_quadrant(point_sets, first_only=True):
    """
    First only means we only look at the quadrants with the same lowest counts
    Else we also look at the 2 lowest counts. It allows us to expand the range of candidates
    """

    def get_quad_combos(quads):
        quads = list(set(quads))
        combos = []
        for q1 in quads:
            for q2 in quads:
                if q1[0] == q2[0] or q1[0] == q2[1] or q1[1] == q2[0] or q1[1] == q2[1]:
                    combos.append((q1, q2))
                    combos.append((q2, q1)) # Repeat to get equal weighting for single and double-quadrant combos
        return combos

    legend_pos = {
        ('TR', 'TR'): "top_right",

        ('TL', 'TR'): "top_center",
        ('TR', 'TL'): "top_center",

        ('TL', 'TL'): "top_left",

        ('TL', 'BL'): "center_left",
        ('BL', 'TL'): "center_left",

        ('BL', 'BL'): "bottom_left",

        ('BL', 'BR'): "bottom_center",
        ('BR', 'BL'): "bottom_center",

        ('BR', 'BR'): "bottom_right",

        ('TR', 'BR'): "center_right",
        ('BR', 'TR'): "center_right"
    }

    points_per_quad = get_points_per_quadrant(point_sets)
    sorted_points_per_quad = sorted([(k, points_per_quad[k]) for k in points_per_quad.keys()], key=lambda c: c[1])

    best_positions = []

    # Walk to include any that may be relevant
    cand_quads = [sorted_points_per_quad[0][0]]
    last_c = sorted_points_per_quad[0][1]
    allow_more = True

    for q, c in sorted_points_per_quad[1:]:
        if c == last_c:
            cand_quads.append(q)
        elif first_only:
            break
        elif allow_more:
            cand_quads.append(q)
            last_c = c
            allow_more = False

    # Compute all possible adjacent quad combos and choose one at random
    quad_combos = get_quad_combos(cand_quads)
    best_pos = random.sample(quad_combos, 1)[0]

    return legend_pos[best_pos]


def get_points_per_section(point_sets):
    # Get the bounds
    all_x, all_y = [], []
    for ps in point_sets:
        all_x += ps['x'][:]
        all_y += ps['y'][:]

    x_int = (max(all_x) - min(all_x)) / 3
    x_mid_left = min(all_x) + x_int
    x_mid_right = min(all_x) + 2*x_int

    y_int = (max(all_y) - min(all_y)) / 3
    y_mid_left = min(all_y) + y_int
    y_mid_right = min(all_y) + 2*y_int

    counts = {
        'top_left': 0,
        'top_center': 0,
        'top_right': 0,
        'center_left': 0,
        'center': 0,
        'center_right': 0,
        'bottom_left': 0,
        'bottom_center': 0,
        'bottom_right': 0
    }

    # REMEMBER THESE ARE CARTESIAN, NOT CANVAS COORDS! Lower Y -> lower on plot
    for x, y in zip(all_x, all_y):

        if x <= x_mid_left:
            if y <= y_mid_left:
                counts['bottom_left'] += 1
            elif y > y_mid_left and y <= y_mid_right:
                counts['center_left'] += 1
            else:
                counts['top_left'] += 1

        elif x > x_mid_left and x <= x_mid_right:
            if y <= y_mid_left:
                counts['bottom_center'] += 1
            elif y > y_mid_left and y <= y_mid_right:
                counts['center'] += 1
            else:
                counts['top_center'] += 1

        else:
            if y <= y_mid_left:
                counts['bottom_right'] += 1
            elif y > y_mid_left and y <= y_mid_right:
                counts['center_right'] += 1
            else:
                counts['top_right'] += 1

    return counts


def get_best_inside_legend_position(point_sets):

    points_per_section = get_points_per_section(point_sets)
    sorted_points_per_section = sorted([(k, points_per_section[k]) for k in points_per_section.keys()], key=lambda c: c[1])

    # Walk to include any that may be relevant
    cand_sections = [sorted_points_per_section[0][0]] 
    last_c = sorted_points_per_section[0][1]

    for q, c in sorted_points_per_section[1:]:
        if c == last_c:
            cand_sections.append(q)
        else:
            break

    # Compute all possible adjacent quad combos and choose one at random
    best_pos = random.sample(cand_sections, 1)[0]

    return best_pos
