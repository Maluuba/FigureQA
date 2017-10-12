# FigureQA

Code to generate the FigureQA dataset, see https://datasets.maluuba.com/FigureQA.

## Data Generation

Data generation consists of 3 parts:

1. Generate the source numerical data, styles, and question-answer pairs for the figures.
1. Generate the figure images and bounding box annotatations.
1. Aggregrate the figure images, questions & answers, annotations, and source data.

### Code Map

All data generation source code lives in the `figureqa/generation` subpackage:

- `questions` subpackage contains code to generate questions

    - `categorical.py` for questions for bar graphs and pie charts.
    - `lines.py` for line plots.
    - `utils.py` for balancing and question encoding augmentation.

- `source_data_generation.py` to generate source data, questions, and answers.

- `figure_generation.py` to generate figure images and bounding boxes.

- `json_combiner.py` aggregates the generated data into the documented format. Allows for generating a data split in multiple batches.

- `data_utils.py` has misc. utilities for reconciling data formats, placing legends, etc.

- `figure.py` defines the figure objects in Bokeh.

- `generate_dataset.py` generates a whole dataset end-to-end.

- `show_bounding_boxes.py` generates images with bounding boxes visualized.

Each runnable module (script) can have its command line arguments displayed with `--help`.

There are some additional files used for data generation in these directories:

- `config` contains `.yaml` files that configure visual apsects, source data parameters, color splits, and dataset generation.

- `resources` contains the colors and other misc. resources for data generation.

And `docs` contains additional documentation on annotations, question format, and file formats.

### Prerequisites

1. Install the FigureQA fork of Bokeh from https://www.github.com/Maluuba/bokeh.
1. `pip install -r requirements.txt`.
1. Make sure you have enough space. The whole dataset unzipped is > 6GB, plus you need room for intermediate data.

### Generate a whole dataset

#### Using a single script

This is done with the end-to-end script `generate_dataset.py`. It does the source data synthesis, figure generation, and aggregation.

This script must be run from the root directory, `FigureQA`.

The config for the actual dataset is in `config/figureqa_generation_config.yaml`.
A sample config is provided in `config/sample_figureqa_generation_config.yaml`.

Note that this does not generate the test sets.

#### With individual scripts

1. `cd FigureQA`
1. `python figureqa/generation/source_data_generation.py CONFIG_FILE.yaml SOURCE_DATA.json --<figure_type> <N_figures> ...`
1. `python figureqa/generation/figure_generation.py SOURCE_DATA.json RAW_GENERATED_DIR`
1. `python figureqa/generation/json_combiner.py FINAL_AGGREGATE_DIR RAW_GENERATED_DIR1 RAW_GENERATED_DIR2 ...`
