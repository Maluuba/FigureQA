#!/usr/bin/python
from __future__ import division

import argparse
import json
import numpy as np
import os
import shutil

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image


DPI = 80


def add_bboxes_to_plot(bboxes, color):
    if type(bboxes) != type([]):
        bboxes = [bboxes]

    for bbox in bboxes:
        plt.gca().add_patch(Rectangle((bbox['x'], bbox['y']), bbox['w'], bbox['h'],
                            fill=False,
                            edgecolor=color,
                            linewidth=2))


def setup_plot(image):

    # Clear
    plt.cla()
    plt.clf()

    plt.imshow(image)
    plt.tick_params(labelbottom='off', labelleft='off')

    for spine_pos in ['right', 'left', 'top', 'bottom']:
        plt.gca().spines[spine_pos].set_color('none')

    # turn off ticks
    plt.gca().xaxis.set_ticks_position('none')
    plt.gca().yaxis.set_ticks_position('none')
    plt.gca().xaxis.set_ticklabels([])
    plt.gca().yaxis.set_ticklabels([])#
    plt.tight_layout()
    px, py, chan = np.asarray(image).shape
    plt.gcf().set_size_inches(py/DPI, px/DPI)
    plt.gcf().set_dpi(DPI)


def generate_all_images_with_bboxes_for_plot(annotations, image, root_dest_dir, color, load_image=False):
    image_index = annotations['image_index']
    dest_dir = os.path.join(root_dest_dir, str(image_index))

    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)

    os.mkdir(dest_dir)

    if load_image:
        image = Image.open(image)

    # all models
    setup_plot(image)
    bbox_key = None
    for model in annotations['models']:
        if not bbox_key:
            bbox_key = 'bbox' if 'bbox' in model.keys() else 'bboxes'

        add_bboxes_to_plot(model[bbox_key], color)

    plt.savefig(os.path.join(dest_dir, "%d_all_models.png" % image_index))

    # each model separate
    for model in annotations['models']:
        setup_plot(image)
        add_bboxes_to_plot(model[bbox_key], color)
        plt.savefig(os.path.join(dest_dir, "%d_%s_model.png" % (image_index, model['name'])))

    general_annot = annotations['general_figure_info']

    # labels and legend
    setup_plot(image)
    add_bboxes_to_plot(general_annot['title']['bbox'], color)

    if 'legend' in general_annot:
        legend_annot = general_annot['legend']
        add_bboxes_to_plot(legend_annot['bbox'], color)
        add_bboxes_to_plot([item['label']['bbox'] for item in legend_annot['items']], color)
        add_bboxes_to_plot([item['preview']['bbox'] for item in legend_annot['items']], color)

    if 'x_axis' in general_annot:
        x_annot = general_annot['x_axis']
        add_bboxes_to_plot(x_annot['major_labels']['bboxes'], color)
        add_bboxes_to_plot(x_annot['label']['bbox'], color)

    if 'y_axis' in general_annot:
        y_annot = general_annot['y_axis']
        add_bboxes_to_plot(y_annot['major_labels']['bboxes'], color)
        add_bboxes_to_plot(y_annot['label']['bbox'], color)

    plt.savefig(os.path.join(dest_dir, "%d_labels_legend.png" % image_index))

    # ticks and gridlines
    setup_plot(image)
    if 'x_axis' in general_annot:
        x_annot = general_annot['x_axis']
        add_bboxes_to_plot(x_annot['major_ticks']['bboxes'], color)
        add_bboxes_to_plot(x_annot['minor_ticks']['bboxes'], color)

    if 'y_axis' in general_annot:
        y_annot = general_annot['y_axis']
        add_bboxes_to_plot(y_annot['major_ticks']['bboxes'], color)
        add_bboxes_to_plot(y_annot['minor_ticks']['bboxes'], color)

    if 'x_gridlines' in general_annot:
        add_bboxes_to_plot(general_annot['x_gridlines']['bboxes'], color)

    if 'y_gridlines' in general_annot:
        add_bboxes_to_plot(general_annot['y_gridlines']['bboxes'], color)

    # In the case of a pie chart, show the bounds of the whole pie instead
    if annotations['type'] == 'pie':
        add_bboxes_to_plot(general_annot['plot_info']['bbox'], color)

    plt.savefig(os.path.join(dest_dir, "%d_ticks_gridlines.png" % image_index))


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--annotations-json")
    parser.add_argument("-i", "--images", nargs="+")
    parser.add_argument("-s", "--source-dir")
    parser.add_argument("-d", "--dest-dir")
    parser.add_argument("-c", "--color", default="red")
    args = parser.parse_args()

    if not os.path.exists(args.dest_dir):
        os.mkdir(args.dest_dir)

    with open(args.annotations_json, 'r') as f:
        all_annotations = json.load(f)

    if args.images:
        raw_image_paths = args.images
        image_paths = []
        for img in raw_image_paths:
            if not img.endswith(".png"):
                image_paths.append(os.path.join(args.source_dir, "%s.png" % img))
    else:
        image_paths = [os.path.join(args.source_dir, fp) for fp in os.listdir(args.source_dir) if fp.endswith(".png")]

    for image in image_paths:

        image_index = int(os.path.basename(image).replace(".png", ""))
        annotations = all_annotations[image_index]

        if annotations['image_index'] != image_index:
            raise Exception("Image index mismatch!")

        img = Image.open(image)
        generate_all_images_with_bboxes_for_plot(annotations, img, args.dest_dir, args.color, load_image=False)
