#!/usr/bin/python
import click
import json
import logging
import os
import re
import shutil

from tqdm import tqdm


def combine_figure_data(
        destination_directory,
        source_directories,
        stop_index=-1
    ):

    if not os.path.exists(destination_directory):
        os.mkdir(destination_directory)

    dest_png_dir = os.path.join(destination_directory, "png")

    if not os.path.exists(dest_png_dir):
        os.mkdir(dest_png_dir)

    image_index = 0
    all_annotations = []
    all_qas = []
    total_distinct_questions, total_distinct_colors = None, None

    for src_dir in source_directories:
        png_subdir = os.path.join(src_dir, "png")
        qa_subdir = os.path.join(src_dir, "json_qa")
        annotations_subdir = os.path.join(src_dir, "json_annotations")

        image_files = os.listdir(png_subdir)

        for image in tqdm(iter(image_files), total=len(image_files), desc="Processing %s" % src_dir):

            image_name = os.path.basename(image).replace(".png", "")

            orig_image_index = int(re.match(r'^[0-9]+', image_name).group(0))

            if stop_index >= 0 and orig_image_index >= stop_index:
                break

            # Copy image to new location
            shutil.copy(os.path.join(png_subdir, image), os.path.join(dest_png_dir, "%d.png" % image_index))

            # Read annotations and append
            with open(os.path.join(annotations_subdir, "%s_annotations.json" % image_name), 'r') as f:
                annotations = json.load(f)
                annotations['image_index'] = image_index
                all_annotations.append(annotations)

            # Read QA pairs and append
            with open(os.path.join(qa_subdir, "%s.json" % image_name), 'r') as f:
                qa_data = json.load(f)
                qas = qa_data['qa_pairs']

            if not total_distinct_questions and len(qas) > 0:
                total_distinct_questions = qa_data['total_distinct_questions']
                total_distinct_colors = qa_data['total_distinct_colors']

            for qa in qas:
                del qa['image']
                del qa['annotations']
                qa['image_index'] = image_index
                all_qas.append(qa)

            image_index += 1

    logging.info("Dumping qa_pairs json...")
    with open(os.path.join(destination_directory, "qa_pairs.json"), 'w') as f:
        json.dump({
            'qa_pairs': all_qas,
            'total_distinct_questions': total_distinct_questions,
            'total_distinct_colors': total_distinct_colors
        }, f)

    logging.info("Dumping annotations json...")
    with open(os.path.join(destination_directory, "annotations.json"), 'w') as f:
        json.dump(all_annotations, f)

    logging.info("Done combining data.")


@click.command()
@click.argument("destination_directory")
@click.argument("source_directories", nargs=-1, required=True)
@click.option("-x", "--stop-index", default=-1, type=int,
                help="which image index to stop at in each directory of SOURCE_DIRECTORIES")
def main(**kwargs):
    """
    Combines all the figures, questions & answers, and annotations across all SOURCE_DIRECTORIES, each generated
    from a run of 'figure_generation.py', and saves the result to DESTINATION_DIRECTORY.
    """
    logging.basicConfig(level=logging.INFO)
    combine_figure_data(**kwargs)


if __name__ == "__main__":
    main()