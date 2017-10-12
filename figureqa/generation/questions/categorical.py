#!/usr/bin/python
import numpy as np
import random

from collections import Counter

from utils import augment_questions


def _get_cat_noncat_bars(bars_data):
    """ Returns (cat, non-cat) """
    if type(bars_data['x'][0]) == type("") or type(bars_data['x'][0]) == type(u""):
        return 'x', 'y'
    else:
        return 'y', 'x'


def _generate(original_data, cat, noncat, color_map=None):
    """
    Generate two questions (yes/no) of each type
    """
    qa_pairs = []
    data = zip(original_data[cat], original_data[noncat])

    sorted_categories = sorted(data, key=lambda b: b[1])

    # Get min and max
    min_category = sorted_categories[0]
    max_category = sorted_categories[-1]

    qa_pairs += [{
                    'question_string': "Is %s the minimum?" % min_category[0], 'question_id': 0,
                    'color1_name': min_category[0], 'color2_name': "--None--",
                    'answer': 1
                },
                {
                    'question_string': "Is %s the maximum?" % max_category[0], 'question_id': 1,
                    'color1_name': max_category[0], 'color2_name': "--None--",
                    'answer': 1
                }]

    # If the min and max aren't equal, then we can get greater/less than +ve answers
    if min_category[1] != max_category[1]:

        not_min_category, not_max_category, greater, less = None, None, None, None
        indices_to_try = np.random.permutation(range(len(data))).tolist()

        for i in range(1, len(indices_to_try)):
            if not_min_category and not_max_category and greater and less:
                break

            if data[i][1] < sorted_categories[-1][1]:
                not_max_category = data[i][0]

            if data[i][1] > sorted_categories[0][1]:
                not_min_category = data[i][0]

            if data[i - 1][1] < data[i][1]:
                less = data[i - 1][0]
                greater = data[i][0]

            elif data[i - 1][1] > data[i][1]:
                less = data[i][0]
                greater = data[i - 1][0]

        if not_min_category:
            qa_pairs.append({
                                'question_string': "Is %s the minimum?" % not_min_category, 'question_id': 0,
                                'color1_name': not_min_category, 'color2_name': "--None--",
                                'answer': 0
                            })

        if not_max_category:
            qa_pairs.append({
                                'question_string': "Is %s the maximum?" % not_max_category, 'question_id': 1,
                                'color1_name': not_max_category, 'color2_name': "--None--",
                                'answer': 0
                            })
        
        if less and greater:
            qa_pairs += [{
                            'question_string': "Is %s greater than %s?" % (greater, less), 'question_id': 3,
                            'color1_name': greater, 'color2_name': less,
                            'answer': 1
                        },
                        {
                            'question_string': "Is %s less than %s?" % (less, greater), 'question_id': 2,
                            'color1_name': less, 'color2_name': greater,
                            'answer': 1},
                        {
                            'question_string': "Is %s greater than %s?" % (less, greater), 'question_id': 3,
                            'color1_name': less, 'color2_name': greater,
                            'answer': 0},
                        {
                            'question_string': "Is %s less than %s?" % (greater, less), 'question_id': 2,
                            'color1_name': greater, 'color2_name': less,
                            'answer': 0
                        }]

    else:
        qa_pairs += [{
                        'question_string': "Is %s greater than %s?" % (min_category, max_category), 'question_id': 3,
                        'color1_name': min_category, 'color2_name': max_category,
                        'answer': 0
                    },
                    {
                        'question_string': "Is %s less than %s?" % (max_category, min_category), 'question_id': 2,
                        'color1_name': max_category, 'color2_name': min_category,
                        'answer': 0
                    }]

    # Get median
    if len(sorted_categories) % 2 == 1:
        median_low_index = len(sorted_categories) / 2
        median_high_index = median_low_index
    else:
        median_high_index = len(sorted_categories) / 2
        median_low_index = median_high_index - 1

    median_low = sorted_categories[median_low_index][0]
    median_high = sorted_categories[median_high_index][0]

    not_median_low = sorted_categories[random.choice(range(median_low_index) \
                        + range(median_low_index + 1, len(sorted_categories) ))][0]
    not_median_high = sorted_categories[random.choice(range(median_high_index) \
                        + range(median_high_index + 1, len(sorted_categories) ))][0]

    qa_pairs += [{
                    'question_string': "Is %s the high median?" % median_high, 'question_id': 5,
                    'color1_name': median_high, 'color2_name': "--None--",
                    'answer': 1
                },
                {
                    'question_string': "Is %s the low median?" % median_low, 'question_id': 4,
                    'color1_name': median_low, 'color2_name': "--None--",
                    'answer': 1
                },
                {
                    'question_string': "Is %s the high median?" % not_median_high, 'question_id': 5,
                    'color1_name': not_median_high, 'color2_name': "--None--",
                    'answer': 0
                },
                {
                    'question_string': "Is %s the low median?" % not_median_low, 'question_id': 4,
                    'color1_name': not_median_low, 'color2_name': "--None--",
                    'answer': 0
                }]

    if color_map:
        augment_questions(qa_pairs, color_map)

    return qa_pairs


def generate_bar_graph_questions(data, color_map=None):
    data = data['models'][0]
    cat, noncat = _get_cat_noncat_bars(data)
    return _generate(data, cat, noncat, color_map)


def generate_pie_chart_questions(data, color_map=None):
    new_data = { 'labels': [], 'spans': []}

    for model in data['models']:
        new_data['labels'].append(model['label'])
        new_data['spans'].append(model['span'])

    return _generate(new_data, 'labels', 'spans', color_map)
