#!/usr/bin/python
from __future__ import division

import copy

from bokeh.io import export_png_and_data    # Custom function
from bokeh.models import ColumnDataSource, LabelSet, Legend
from bokeh.models.glyphs import Line
from bokeh.models.markers import Asterisk, Circle, Cross, Diamond, Square, Triangle, X
from bokeh.plotting import figure


MARKERS = [Asterisk, Circle, Cross, Diamond, Square, Triangle, X]


# Used in modified BokehJS
TITLE_ID = "the_title"
TITLE_LABEL = "title"
X_AXIS_ID = "the_xaxis"
Y_AXIS_ID = "the_yaxis"
X_AXIS_LABEL = "xaxis_label"
Y_AXIS_LABEL = "yaxis_label"
X_GRID_ID = "the_x_gridlines"
Y_GRID_ID = "the_y_gridlines"


def get_grid_plot_data(title="title", xlabel="xaxis_label", ylabel="yaxis_label"):
    data = {
        TITLE_ID: {'type': "title", 'text': title},
        X_AXIS_ID: {'type': "xaxis", 'label': xlabel},
        Y_AXIS_ID: {'type': "yaxis", 'label': ylabel},
        X_GRID_ID: {'type': "x_gridline"},
        Y_GRID_ID: {'type': "y_gridline"}
    }

    return data



class HBarGraphCategorical (object):

    def __init__(self, data, visuals={}):

        # Set up the plot
        p = figure(plot_width=visuals['figure_width'], plot_height=visuals['figure_height'], title=TITLE_LABEL, toolbar_location=None, y_range=data['y'])
        p.hbar(y=data['y'], height=0.5, left=0, right=data['x'], fill_color=data['colors'], line_color=None, name="the_bars")
        
        # Set identifiers for the figure elements
        p.xaxis.name = X_AXIS_ID
        p.xaxis.axis_label = X_AXIS_LABEL
        p.yaxis.name = Y_AXIS_ID
        p.yaxis.axis_label = Y_AXIS_LABEL
        p.title.name = TITLE_ID

        if visuals['draw_gridlines']:
            if p.grid[0].dimension == 0:
                p.grid[0].name = X_GRID_ID
                p.grid[1].name = Y_GRID_ID
            else:
                p.grid[0].name = Y_GRID_ID
                p.grid[1].name = X_GRID_ID
        else:
            p.grid[0].visible = False
            p.grid[1].visible = False

        self.figure = p


class VBarGraphCategorical (object):

    def __init__(self, data, visuals={}):

        # Set up the plot
        p = figure(plot_width=visuals['figure_width'], plot_height=visuals['figure_height'], title=TITLE_LABEL, toolbar_location=None, x_range=data['x'])
        p.vbar(x=data['x'], width=0.5, bottom=0, top=data['y'], fill_color=data['colors'], line_color=None, name="the_bars")
        
        # Set identifiers for the figure elements
        p.xaxis.name = X_AXIS_ID
        p.xaxis.axis_label = X_AXIS_LABEL
        p.xaxis.major_label_orientation = "vertical"
        p.yaxis.name = Y_AXIS_ID
        p.yaxis.axis_label = Y_AXIS_LABEL
        p.title.name = TITLE_ID

        if visuals['draw_gridlines']:
            if p.grid[0].dimension == 0:
                p.grid[0].name = X_GRID_ID
                p.grid[1].name = Y_GRID_ID
            else:
                p.grid[0].name = Y_GRID_ID
                p.grid[1].name = X_GRID_ID
        else:
            p.grid[0].visible = False
            p.grid[1].visible = False

        self.figure = p


class LinePlot (object):

    def __init__(self, data, visuals={}):

        p = figure(plot_width=visuals['figure_width'], plot_height=visuals['figure_height'], title=TITLE_LABEL, toolbar_location=None)

        # Create the column data source and glyphs scatter data
        legend_items = []
        for i, point_set in enumerate(data):
            col_data = ColumnDataSource({ 'x': point_set['x'], 'y': point_set['y'], 's': [10]*len(point_set['x'])})
            glyph = Line(x='x', y='y', line_width=2, line_color=point_set['color'], name=point_set['label'],
                            line_dash=visuals['line_styles'][i])
            renderer = p.add_glyph(col_data, glyph)
            renderer.name = glyph.name
            legend_items.append((renderer.name, [renderer]))

        if 'draw_legend' in visuals and visuals['draw_legend']:

            alpha = 1.0 if visuals['legend_border'] else 0.0
            border_color = "black" if visuals['legend_border'] else None

            legend = Legend(items=legend_items, location=visuals['legend_position'], name="the_legend", margin=0,
                            background_fill_alpha=alpha, border_line_color=border_color, border_line_alpha=1.0,
                            label_text_font_size=visuals['legend_label_font_size'],
                            orientation=visuals['legend_orientation'])

            if visuals['legend_inside']:
                p.add_layout(legend)
            else:
                p.add_layout(legend, visuals['legend_layout_position'])

        # Set identifiers for the figure elements
        p.xaxis.name = X_AXIS_ID
        p.xaxis.axis_label = X_AXIS_LABEL
        p.yaxis.name = Y_AXIS_ID
        p.yaxis.axis_label = Y_AXIS_LABEL
        p.title.name = TITLE_ID

        if visuals['draw_gridlines']:
            if p.grid[0].dimension == 0:
                p.grid[0].name = X_GRID_ID
                p.grid[1].name = Y_GRID_ID
            else:
                p.grid[0].name = Y_GRID_ID
                p.grid[1].name = X_GRID_ID
        else:
            p.grid[0].visible = False
            p.grid[1].visible = False

        self.figure = p


class DotLinePlot (object):

    def __init__(self, data, visuals={}):

        p = figure(plot_width=visuals['figure_width'], plot_height=visuals['figure_height'], title=TITLE_LABEL, toolbar_location=None)

        # Create the column data source and glyphs scatter data
        legend_items = []
        for i, point_set in enumerate(data):
            col_data = ColumnDataSource({ 'x': point_set['x'], 'y': point_set['y'], 's': [10]*len(point_set['x'])})
            glyph = Circle(x='x', y='y', size='s', fill_color=point_set['color'], line_color=None, name=point_set['label'])
            renderer = p.add_glyph(col_data, glyph)
            renderer.name = glyph.name
            legend_items.append((renderer.name, [renderer]))

        if 'draw_legend' in visuals and visuals['draw_legend']:

            alpha = 1.0 if visuals['legend_border'] else 0.0
            border_color = "black" if visuals['legend_border'] else None

            legend = Legend(items=legend_items, location=visuals['legend_position'], name="the_legend", margin=0,
                            background_fill_alpha=alpha, border_line_color=border_color,
                            label_text_font_size=visuals['legend_label_font_size'],
                            orientation=visuals['legend_orientation'])

            if visuals['legend_inside']:
                p.add_layout(legend)
            else:
                p.add_layout(legend, visuals['legend_layout_position'])

        # Set identifiers for the figure elements
        p.xaxis.name = X_AXIS_ID
        p.xaxis.axis_label = X_AXIS_LABEL
        p.yaxis.name = Y_AXIS_ID
        p.yaxis.axis_label = Y_AXIS_LABEL
        p.title.name = TITLE_ID

        if visuals['draw_gridlines']:
            if p.grid[0].dimension == 0:
                p.grid[0].name = X_GRID_ID
                p.grid[1].name = Y_GRID_ID
            else:
                p.grid[0].name = Y_GRID_ID
                p.grid[1].name = X_GRID_ID
        else:
            p.grid[0].visible = False
            p.grid[1].visible = False

        self.figure = p


class Pie (object):

    def __init__(self, data, visuals={}):

        label_data = { 'labels': data['labels'], 'x': data['label_x'], 'y': data['label_y'] }
        wedge_data = { 'starts': data['starts'], 'ends': data['ends'], 'colors': data['colors'], 'spans': data['spans'], 'labels': data['labels'] }

        # Keep width <= 1.5 times height
        width = visuals['figure_width']
        clamp_ratio = 1.33
        if width > clamp_ratio * visuals['figure_height']:
            width = int(clamp_ratio * visuals['figure_height'])

        # Adjust based on aspect ratio
        aspect = visuals['figure_width'] / visuals['figure_height']

        # Need to adjust the figure ranges if we put the legend below. Can't modify because of Bokeh class IDs
        diff = 0
        if 'draw_legend' in visuals and visuals['draw_legend'] and visuals['legend_layout_position'] == "below":
            diff = 0.25 * len(data['colors']) #  'magic constant'
            width = visuals['figure_height'] # Clamp the width

        default_rad = 1.0

        x_range = (-default_rad*aspect - diff, default_rad*aspect + diff)
        y_range = (-default_rad - diff, default_rad + diff)

        p = figure(plot_width=width, plot_height=visuals['figure_height'], x_range=x_range, y_range=y_range, title=" " + TITLE_LABEL, toolbar_location=None)
        
        glyphs = []
        for i in range(len(data['colors'])):
            glyphs.append(p.wedge(x=0, y=0, radius=1, start_angle=data['starts'][i], end_angle=data['ends'][i], color=data['colors'][i], name=data['labels'][i]))

        if 'draw_legend' in visuals and visuals['draw_legend']:
            alpha = 1.0 if visuals['legend_border'] else 0.0
            border_color = "black" if visuals['legend_border'] else None

            legend = Legend(items=[(data['labels'][i], [glyph]) for i, glyph in enumerate(glyphs)], name="the_legend", margin=0,
                            location=visuals['legend_position'],
                            background_fill_alpha=alpha, border_line_color=border_color,
                            label_text_font_size=visuals['legend_label_font_size'],
                            orientation=visuals['legend_orientation'])
            
            p.add_layout(legend, visuals['legend_layout_position'])

        else:
            pie_label_data = ColumnDataSource(label_data)
            labels = LabelSet(x='x', y='y', text='labels', level='glyph', source=pie_label_data, render_mode='canvas', text_color='black', name="the_pie_labels")
            p.add_layout(labels)

        p.title.name = TITLE_ID
        p.xaxis.visible = False
        p.yaxis.visible = False
        p.grid[0].visible = False
        p.grid[1].visible = False

        # Best we can do to get rid of the border around the plot. outline_line_(width|color|alpha) don't work
        p.outline_line_color = "white" 

        self.figure = p
        