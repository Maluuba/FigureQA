#!/usr/bin/python
from __future__ import division

import copy
import logging
import random

NUM_DISTINCT_QS = 15


def augment_questions(qa_pairs, color_map):

    for qa in qa_pairs:

        has_color2 = qa['color2_name'] != "--None--"
        cid_1 = color_map[qa['color1_name']]['id']

        if has_color2:
            cid_2 = color_map[qa['color2_name']]['id']

        qa['color1_id'] = cid_1
        qa['color1_rgb'] = color_map[qa['color1_name']]['rgb']

        qa['color2_id'] = cid_2 if has_color2 else -1
        qa['color2_rgb'] = color_map[qa['color2_name']]['rgb'] if has_color2 else [-1, -1, -1]


def balance_questions_by_qid(all_data):
    refined_data = []
    qid_counts = {}

    for qid in range(0, NUM_DISTINCT_QS):
        qid_counts[qid] = [0, 0]

    # Compile mix by qid
    for data in all_data:
        for qa in data['qa_pairs']:
            qid_counts[qa['question_id']][qa['answer']] += 1

    samples_with_qa_loss = 0
    total_qa_pairs = 0
    total_qa_pairs_lost = 0

    for data in all_data:

        new_qa_pairs = []

        for i, qa in enumerate(data['qa_pairs']):

            # Can't discard everything
            if i == len(data['qa_pairs']) - 1 and len(new_qa_pairs) == 0:
                new_qa_pairs.append(qa)
                continue

            # Next attempt to balance by qid
            diff = qid_counts[qa['question_id']][1] - qid_counts[qa['question_id']][0]

            if diff > 0 and qa['answer'] == 1:
                qid_counts[qa['question_id']][1] -= 1
                continue
            elif diff < 0 and qa['answer'] == 0:
                qid_counts[qa['question_id']][0] -= 1
                continue
            
            # If we made it this far then we keep the question-answer-pair
            new_qa_pairs.append(qa)

        frac = len(new_qa_pairs) / len(data['qa_pairs'])
        total_qa_pairs_lost += len(data['qa_pairs']) - len(new_qa_pairs)
        total_qa_pairs += len(new_qa_pairs)

        if frac < 1.0:
            samples_with_qa_loss += 1

        data['qa_pairs'] = new_qa_pairs

    logging.debug("======== FINAL COUNT IMBALANCES =========")
    logging.debug("QID counts:")
    imbal = 0
    total_diff = 0
    for k in qid_counts.keys():
        if qid_counts[k][0] != qid_counts[k][1]:
            diff = qid_counts[k][1] - qid_counts[k][0]
            imbal += 1
            total_diff += diff
    if imbal == 0:
        logging.debug("No imbalance :D")
    else:
        logging.debug("QID IMBALANCE", imbal, total_diff)

    logging.debug("======== DROP STATS =========")
    logging.debug(" > Total QA loss = {0:.2f}%".format(100*total_qa_pairs_lost/total_qa_pairs))
    logging.debug(" > Average QA loss = {0} per graph".format(total_qa_pairs_lost/len(all_data)))
    logging.debug(" > Samples with QA loss = {0:.2f}%".format(100*samples_with_qa_loss/len(all_data)))

    logging.debug("FINAL NUMBER OF GRAPHS = %d" % len(all_data))
    logging.debug("FINAL NUMBER OF QA PAIRS = %d" % (total_qa_pairs))
