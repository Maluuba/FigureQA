#!/usr/bin/python
import itertools
import numpy as np
import random

from sklearn.metrics import auc

from utils import augment_questions

def _calculate_roughness(x, y):

    x = np.array(x)
    y = np.array(y)

    # This calculates the sum of the absolute differences of the left and right slope to each point
    slopes = (y[1:] - y[:-1])/(x[1:] - x[:-1])
    differences = slopes[1:] - slopes[:-1]
    return np.sum(np.abs(differences))


def _is_strictly_greater_than(series_a, series_b):
    return all(np.array(series_a) > np.array(series_b))


def _is_strictly_less_than(series_a, series_b):
    return all(np.array(series_a) < np.array(series_b))


# (label, value)
def _get_min_max_non(tuples): 
    sorted_tuples = sorted(tuples, key=lambda x: x[1])
    min_tup = sorted_tuples[0]
    max_tup = sorted_tuples[-1]

    q_data = {'min': min_tup[0], 'max': max_tup[0]}

    if min_tup[1] != max_tup[1]:
        not_min, not_max = None, None
        indices_to_try = np.random.permutation(range(len(tuples))).tolist()

        for i in range(1, len(indices_to_try)):
            if not_min and not_max:
                break

            if tuples[i][1] < sorted_tuples[-1][1]:
                not_max = tuples[i]

            if tuples[i][1] > sorted_tuples[0][1]:
                not_min = tuples[i]

        if not_min:
            q_data['not_min'] = not_min[0]
        if not_max:
            q_data['not_max'] = not_max[0]

    return q_data


def generate_line_plot_questions(data, color_map=None):

    qa_pairs = []

    aucs = {}
    roughnesses = {}
    peaks = {}
    valleys = {}
    global_mins = {}
    global_maxes = {}

    for model in data['models']:
        label = model['label']
        aucs[label] = auc(model['x'], model['y'])
        #peaks[label], valleys[label], roughnesses[label] = _calculate_roughness(model['y'])
        roughnesses[label] = _calculate_roughness(model['x'], model['y'])
        sorted_y = sorted(model['y'])
        global_mins[label] = sorted_y[0]
        global_maxes[label] = sorted_y[-1]

    # Generate AUC Qs
    auc_q_data = _get_min_max_non(aucs.items())
    qa_pairs += [{
                    'question_string': "Does %s have the minimum area under the curve?" % auc_q_data['min'], 
                    'question_id': 6, 'color1_name': auc_q_data['min'], 'color2_name': "--None--",
                    'answer': 1
                },
                {
                    'question_string': "Does %s have the maximum area under the curve?" % auc_q_data['max'],
                    'question_id': 7, 'color1_name': auc_q_data['max'], 'color2_name': "--None--",
                    'answer': 1
                }]

    if 'not_min' in auc_q_data:
        qa_pairs.append({   
                            'question_string': "Does %s have the minimum area under the curve?" % auc_q_data['not_min'],
                            'question_id': 6, 'color1_name': auc_q_data['not_min'], 'color2_name': "--None--", 
                            'answer': 0
                        })
    if 'not_max' in auc_q_data:
        qa_pairs.append({
                            'question_string': "Does %s have the maximum area under the curve?" % auc_q_data['not_max'],
                            'question_id': 7, 'color1_name': auc_q_data['not_max'], 'color2_name': "--None--",
                            'answer': 0
                        })

    # Generate smoothness Qs
    roughness_q_data = _get_min_max_non(roughnesses.items())
    qa_pairs += [{
                    'question_string': "Is %s the smoothest?" % roughness_q_data['min'], 'question_id': 8, 
                    'color1_name': roughness_q_data['min'], 'color2_name': "--None--",
                    'answer': 1
                },
                {
                    'question_string': "Is %s the roughest?" % roughness_q_data['max'], 'question_id': 9, 
                    'color1_name': roughness_q_data['max'], 'color2_name': "--None--",
                    'answer': 1
                }]

    if 'not_min' in roughness_q_data:
        qa_pairs.append({
                            'question_string': "Is %s the smoothest?" % roughness_q_data['not_min'], 'question_id': 8,
                            'color1_name': roughness_q_data['not_min'], 'color2_name': "--None--", 
                            'answer': 0
                        })

    if 'not_max' in roughness_q_data:
        qa_pairs.append({
                            'question_string': "Is %s the roughest?" % roughness_q_data['not_max'], 'question_id': 9,
                            'color1_name': roughness_q_data['not_max'], 'color2_name': "--None--",
                            'answer': 0
                        })

    # Generate questions for absolute max and min
    global_min_data = _get_min_max_non(global_mins.items())
    qa_pairs.append({
                        'question_string': "Does %s have the lowest value?" % global_min_data['min'], 'question_id': 10,
                        'color1_name': global_min_data['min'], 'color2_name': "--None--", 
                        'answer': 1
                    })

    if 'not_min' in global_min_data:
        qa_pairs.append({
                            'question_string': "Does %s have the lowest value?" % global_min_data['not_min'], 'question_id': 10,
                            'color1_name': global_min_data['not_min'], 'color2_name': "--None--",
                            'answer': 0
                        })

    global_max_data = _get_min_max_non(global_maxes.items())
    qa_pairs.append({
                        'question_string': "Does %s have the highest value?" % global_max_data['max'], 'question_id': 11,
                        'color1_name': global_max_data['max'], 'color2_name': "--None--",
                        'answer': 1
                    })

    if 'not_max' in global_max_data:
        qa_pairs.append({
                            'question_string': "Does %s have the highest value?" % global_max_data['not_max'], 'question_id': 11,
                            'color1_name': global_max_data['not_max'], 'color2_name': "--None--",
                            'answer': 0
                        })

    # Find some curves that are greater than or less than each other
    # Note that if False, could mean that curve A satisfies the opposite condition or they intersect

    strictness_map = {  'AltB': None, 'AgtB': None, 'AintB': None, 'not_AltB': None, 'not_AgtB': None,
                        'not_AintB': None, 'not_AltB_rev': None, 'not_AgtB_rev': None }

    # To make question generation easier
    all_labels = []
    model_map = {}
    for model in data['models']:
        label = model['label']
        model_map[label] = model
        all_labels.append(label)

    all_perms = [x for x in itertools.combinations(all_labels, 2)]
    all_perms = [(x, y) for x, y in all_perms[:] + [ (b, a) for a, b in all_perms ] if x != y]
    random.shuffle(all_perms)
    all_perms_index = 0

    while not all(map(lambda x: False if x == None else True, strictness_map.values())) \
            and all_perms_index < len(all_perms):
        a, b = all_perms[all_perms_index]

        a_lt_b = _is_strictly_less_than(model_map[a]['y'], model_map[b]['y'])
        a_gt_b = _is_strictly_greater_than(model_map[a]['y'], model_map[b]['y'])

        if a_lt_b and not strictness_map['AltB'] and not strictness_map['not_AintB']:
            strictness_map['AltB'] = (a, b)
            strictness_map['not_AintB'] = (a, b)

        if a_gt_b and not strictness_map['AgtB']:
            strictness_map['AgtB'] = (a, b)

        if not a_lt_b and not a_gt_b and not strictness_map['AintB']:
            strictness_map['AintB'] = (a, b)
            strictness_map['not_AltB'] = (a, b)
            strictness_map['not_AgtB'] = (a, b)

        all_perms_index += 1

    # Generate some questions using this strictness data
    if strictness_map['AltB']:
        qa_pairs.append({
                            'question_string': "Is %s less than %s?" % strictness_map['AltB'], 'question_id': 12,
                            'color1_name': strictness_map['AltB'][0], 'color2_name': strictness_map['AltB'][1],
                            'answer': 1
                        })
    
    if strictness_map['AgtB']:
        qa_pairs.append({
                            'question_string': "Is %s greater than %s?" % strictness_map['AgtB'], 'question_id': 13,
                            'color1_name': strictness_map['AgtB'][0], 'color2_name': strictness_map['AgtB'][1],
                            'answer': 1
                        })
    
    if strictness_map['AintB']:
        qa_pairs.append({
                            'question_string': "Does %s intersect %s?" % strictness_map['AintB'], 'question_id': 14,
                            'color1_name': strictness_map['AintB'][0], 'color2_name': strictness_map['AintB'][1],
                            'answer': 1
                        })
    
    if strictness_map['not_AltB']:
        qa_pairs.append({
                            'question_string': "Is %s less than %s?" % strictness_map['not_AltB'], 'question_id': 12,
                            'color1_name': strictness_map['not_AltB'][0], 'color2_name': strictness_map['not_AltB'][1],
                            'answer': 0
                        })
    
    if strictness_map['not_AgtB']:
        qa_pairs.append({
                            'question_string': "Is %s greater than %s?" % strictness_map['not_AgtB'], 'question_id': 13,
                            'color1_name': strictness_map['not_AgtB'][0], 'color2_name': strictness_map['not_AgtB'][1],
                            'answer': 0
                        })
    
    if strictness_map['not_AintB']:
        qa_pairs.append({
                            'question_string': "Does %s intersect %s?" % strictness_map['not_AintB'], 'question_id': 14,
                            'color1_name': strictness_map['not_AintB'][0], 'color2_name': strictness_map['not_AintB'][1],
                            'answer': 0
                        })

    if color_map:
        augment_questions(qa_pairs, color_map)

    return qa_pairs
