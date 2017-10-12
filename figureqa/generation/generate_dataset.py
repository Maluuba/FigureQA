#!/usr/bin/python
import click
import copy
import logging
import os
import selenium.webdriver as seldriver
import yaml

from figure_generation import generate_figures
from json_combiner import combine_figure_data
from source_data_generation import generate_source_data


@click.command()
@click.argument("generation_yaml")
@click.option("--share-webdriver/--new-webdriver", default=True,
                help="whether or not to share a webdriver between all calls to 'generate_figures'")
def main(generation_yaml, share_webdriver):
    """
    Produces a dataset from the config described in GENERATION_YAML.
    """
    logging.basicConfig(level=logging.INFO)

    with open(generation_yaml, 'r') as f:
        config = yaml.load(f)

    # Create a single webdriver for serial generation
    webdriver = seldriver.PhantomJS() if share_webdriver else None

    working_dir = os.path.normpath(config['working_directory']) if 'working_directory' in config else "working_generation"
    dest_dir = os.path.normpath(config['destination_directory']) if 'destination_directory' in config else "final_generation"

    if not os.path.exists(working_dir):
        os.mkdir(working_dir)

    if not os.path.exists(dest_dir):
        os.mkdir(dest_dir)

    for split in config['splits']:

        working_sub_dir = os.path.join(working_dir, split['name'])
        if not os.path.exists(working_sub_dir):
            os.mkdir(working_sub_dir)

        partition_figure_data_dirs = []

        for partition in split['partitions']:
            partition_dir = os.path.join(working_sub_dir, partition['name'])

            if not os.path.exists(partition_dir):
                os.mkdir(partition_dir)

            source_data_args = copy.deepcopy(partition)
            del source_data_args['name']

            source_data_args['output_file_json'] = os.path.join(partition_dir, "source_data.json")

            # Add missing arguments if they aren't present
            for arg in ['common_config_yaml', 'colors', 'keep_all_questions']:
                if arg not in partition and arg in config:
                    source_data_args[arg] = config[arg]

            logging.info("Generating source data for %s/%s" % (split['name'], partition['name']))
            generate_source_data(**source_data_args)

            generated_figures_dir = os.path.join(partition_dir, "figure_data")
            if not os.path.exists(generated_figures_dir):
                os.mkdir(generated_figures_dir)

            partition_figure_data_dirs.append(generated_figures_dir)

            logging.info("Generating figures for %s/%s" % (split['name'], partition['name']))
            generate_figures(source_data_args['output_file_json'], generated_figures_dir, supplied_webdriver=webdriver)

        logging.info("Combining data for %s" % split['name'])

        combined_data_dir = os.path.join(dest_dir, split['name'])
        if not os.path.exists(combined_data_dir):
            os.mkdir(combined_data_dir)

        combine_figure_data(combined_data_dir, partition_figure_data_dirs)

    # Kill the shared webdriver
    if share_webdriver:
        import signal
        from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver

        webdriver.service.process.send_signal(signal.SIGTERM)

        try:
            RemoteWebDriver.quit(webdriver)
        except:
            pass


if __name__ == "__main__":
    main()
