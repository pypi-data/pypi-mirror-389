'''
Copyright (c) 2022 Masayuki TAKAHASHI

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), 
to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, 
and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import re
import tempfile
import psutil
import math
import copy
import warnings
import numpy as np
from tqdm import tqdm
import pandas as pd
import itertools as it
from scipy.special import comb
from functools import partial
from multiprocessing import Pool, get_context
from multiprocessing.shared_memory import SharedMemory, ShareableList
from shrslib.basicfunc import init_worker, nucleotide_sequence, make_wobble, calculate_Tm_value, complementary_sequence
from shrslib.scores import array_diff, calculate_score, calculate_flexibility, arr_length_in_arr, fragment_size_distance
try:
    import cupy as cp
    mempool = cp.get_default_memory_pool()
except:
    pass
Pandas_later_210 = pd.__version__ >= '2.1.0'

def search_position(Combination = [], evaluating_sequence = "", input_sequence = "", allowance = 0, interval_distance = 0, Position_list = np.array([]), Match_rate = 0.8, Maximum_annealing_site_number = 10, circularDNAtemplate = False, IgnoreLowQualityRegion = True):
    '''
    Search an annealing site position .

    Parameters
    ----------
    Combination: list
    evaluating_sequence: str ot nucleotide_sequence
    input_sequence: str ot nucleotide_sequence
        Evaluating sequence is the sequence for which you want to identify the annealing site position in a input sequence.

    Returns
    -------
    Start_position: dict
        The annealing site position between an evaluated sequence and a input sequence.
        The absolute value of a position number indicates the onset point of the annealing site of a input sequence.
        e.g., If the "evaluating_sequence" is "ATGC" and the "input_sequence" is following sequence, {"ATGC": [10, −35]} will be obtained.\n
            Template : ttggaatgagATGCtgtgaacagtcgtatatacgcGCATcgagattacgctattcgcgcggcg\n

    '''
    if Combination != []:
        evaluating_sequence = Combination[0]
        Position_list = np.array(Combination[1])
    if circularDNAtemplate:
        input_sequence = str(input_sequence) + str(input_sequence)[0:int(len(evaluating_sequence) - 1):]
    if IgnoreLowQualityRegion:
        IGNORE = math.ceil(np.max([(len(str(evaluating_sequence)) - allowance) / 2, 2]))
        IGNORE = r"".join(["N" for n in range(IGNORE)]) + r'+'
        IGNORE = re.findall(IGNORE, input_sequence)
        IGNORE.sort(reverse = True)
        for igr in IGNORE:
            input_sequence = re.sub(igr, igr.replace("N", "X"), input_sequence)
    if Position_list.size == 0:
        encode_table = {"a":'1', "t":'8', "g":'2', "c":'4', "b":'e', "d":'b', "h":'d', "k":'a', "m":'5', "r":'3', "s":'6', "v":'7', "w":'9', "y":'c', "n":'f', "x":'0'}
        encode_table = str.maketrans(encode_table)
        if len(input_sequence) > len(evaluating_sequence):
            translate_sequence = np.array([list('{:04b}'.format(int(n,16))) for n in list(input_sequence.lower().translate(encode_table)) if re.sub(r'[0-9a-f]', '', n) == ''], dtype = int)
        else:
            print("\nInput data error in search homologous position.\n")
            sys.exit()
        translate_sequence_matrix = np.empty(((len(translate_sequence) - len(evaluating_sequence) + 1), 0), np.uint8)
        for i in range(len(evaluating_sequence) - 1):
            translate_sequence_matrix = np.concatenate([translate_sequence_matrix.astype(np.uint8), translate_sequence[i:(i - len(evaluating_sequence) + 1):].astype(np.uint8)], axis = 1)
        translate_sequence_matrix = np.concatenate([translate_sequence_matrix, translate_sequence[(len(evaluating_sequence) - 1)::]], axis = 1).astype(np.uint8)
        translate_evaluating_sequence = np.array([list('{:04b}'.format(int(n,16))) for n in list(evaluating_sequence.lower().translate(encode_table))], dtype = int)
        if "cupy" in sys.modules:
            try:
                translate_sequence_matrix_GPU = cp.asarray((translate_sequence_matrix.T).astype(np.uint8))
                translate_evaluating_sequence_GPU = cp.asarray((translate_evaluating_sequence.flatten()).astype(np.uint8))
                score_list_preparation_GPU = cp.zeros(shape = (translate_sequence_matrix_GPU.shape[1], ), dtype = cp.uint8)
                cp.dot(translate_evaluating_sequence_GPU, translate_sequence_matrix_GPU, out = score_list_preparation_GPU)
                score_list_preparation = cp.asnumpy(score_list_preparation_GPU)
                cp.dot(translate_evaluating_sequence_GPU, cp.flipud(translate_sequence_matrix_GPU), out = score_list_preparation_GPU)
                complementary_score_list_preparation = cp.asnumpy(score_list_preparation_GPU)
                del score_list_preparation_GPU, translate_sequence_matrix_GPU, translate_evaluating_sequence_GPU
                mempool.free_all_blocks()
            except:
                if 'translate_sequence_matrix_GPU' in locals(): del translate_sequence_matrix_GPU
                if 'translate_evaluating_sequence_GPU' in locals(): del translate_evaluating_sequence_GPU
                if 'score_list_preparation_GPU' in locals(): del score_list_preparation_GPU
                mempool.free_all_blocks()
                translate_sequence_matrix_CPU = (translate_sequence_matrix.T).astype(np.uint8)
                translate_evaluating_sequence_CPU = (translate_evaluating_sequence.flatten()).astype(np.uint8)
                score_list_preparation = np.dot(translate_evaluating_sequence_CPU, translate_sequence_matrix_CPU).astype(np.uint8)
                complementary_score_list_preparation = np.dot(translate_evaluating_sequence_CPU, np.flipud(translate_sequence_matrix_CPU)).astype(np.uint8)
        else:
            translate_sequence_matrix_CPU = (translate_sequence_matrix.T).astype(np.uint8)
            translate_evaluating_sequence_CPU = (translate_evaluating_sequence.flatten()).astype(np.uint8)
            score_list_preparation = np.dot(translate_evaluating_sequence_CPU, translate_sequence_matrix_CPU).astype(np.uint8)
            complementary_score_list_preparation = np.dot(translate_evaluating_sequence_CPU, np.flipud(translate_sequence_matrix_CPU)).astype(np.uint8)
        IDX = np.where(score_list_preparation.astype(np.float32) >= (len(evaluating_sequence) - allowance))[0]
        score_list = score_list_preparation.astype(np.float32) / len(evaluating_sequence)
        score_list[IDX] = [calculate_score(evaluating_sequence, input_sequence[id:(id + len(evaluating_sequence)):]) for id in IDX]
        score_list_criteria = list(np.where(np.array(score_list) >= ((len(evaluating_sequence) - allowance)/len(evaluating_sequence)))[0])
        IDX = np.where(complementary_score_list_preparation.astype(np.float32) >= (len(evaluating_sequence) - allowance))[0]
        complementary_score_list = complementary_score_list_preparation.astype(np.float32) / len(evaluating_sequence)
        complementary_score_list[IDX] = [calculate_score(evaluating_sequence, complementary_sequence(input_sequence[id:(id + len(evaluating_sequence)):])) for id in IDX]
        score_list = np.maximum(score_list, complementary_score_list)
    else:
        if type(input_sequence) is str:
            split_sequences = np.array([input_sequence[i:(i + len(evaluating_sequence)):] for i in Position_list.tolist()])
        else:
            split_sequences = np.array([str(input_sequence)[i:(i + len(evaluating_sequence)):] for i in Position_list.tolist()])
        score_list = [calculate_score(evaluating_sequence, split_sequence) for split_sequence in split_sequences]
        score_list_criteria = np.array(Position_list)[np.where(np.array(score_list) >= ((len(evaluating_sequence) - allowance)/len(evaluating_sequence)))[0]]
        complementary_score_list = [calculate_score(evaluating_sequence, complementary_sequence(split_sequence)) for split_sequence in split_sequences]
        score_list = np.maximum(score_list, complementary_score_list)
    Start_positions = dict()
    Mismatch_Counter = 0
    Total_Counter = 0
    Maximum_position_list_size = 12
    Maximum_combination_size = 30000
    if Position_list.size == 0:
        Position_list = list(np.where(np.array(score_list) >= ((len(evaluating_sequence) - allowance)/len(evaluating_sequence)))[0])
        score_list_criteria = np.array([set(score_list_criteria) >= set([Position]) for Position in Position_list])
        Complementary_criteria = list(np.where(np.array(complementary_score_list) >= ((len(evaluating_sequence) - allowance)/len(evaluating_sequence)))[0])
        Complementary_criteria = np.array([set(Complementary_criteria) >= set([Position]) for Position in Position_list])
        Position_list = np.array(Position_list)
        if len(Position_list) != 0:
            Palindrome_sequence_list = {}
            Palindrome_position = Position_list[score_list_criteria & Complementary_criteria]
            [Palindrome_sequence_list.update({input_sequence[Ppos:(Ppos + len(evaluating_sequence)):]: Palindrome_sequence_list[input_sequence[Ppos:(Ppos + len(evaluating_sequence)):]] + [Ppos]}) if (input_sequence[Ppos:(Ppos + len(evaluating_sequence)):] in Palindrome_sequence_list.keys()) else Palindrome_sequence_list.update({input_sequence[Ppos:(Ppos + len(evaluating_sequence)):]: [Ppos]}) for Ppos in Palindrome_position]
        else:
            Palindrome_sequence_list = {}
        if np.any(Complementary_criteria):
            Position_list[Complementary_criteria] = Position_list[Complementary_criteria] * (-1)
        if len(Position_list) != 0:
            score_list = np.array(score_list)[np.abs(Position_list)]
            split_sequences = np.array([input_sequence[Position:(Position + len(evaluating_sequence)):] if Position >= 0 else complementary_sequence(input_sequence[np.abs(Position):(np.abs(Position) + len(evaluating_sequence)):]) for Position in Position_list])
            duplicate_index = [split_sequences == seq for seq in sorted(list(set(split_sequences)))]
            Grouping_position_list = [list(Position_list[didx]) for didx in duplicate_index]
            Grouping_split_sequences = [list(set(split_sequences[didx])) for didx in duplicate_index]
            if len(Grouping_position_list) > Maximum_position_list_size:
                Position_combinations = [tuple(sorted(list(it.chain.from_iterable(Grouping_position_list)), key = abs))]
            else:
                Group_combination_numbers = [[np.array(Grouping_combination_number) for Grouping_combination_number in list(it.combinations(range(len(Grouping_position_list)), i))] for i in range(1, len(Grouping_position_list) + 1)]
                Position_combinations = list(it.chain.from_iterable([[tuple(sorted(it.chain.from_iterable(np.array(Grouping_position_list, dtype = object)[Gcn].tolist()), key = abs)) for Gcn in Group_combination_number] for Group_combination_number in Group_combination_numbers]))
                Split_sequences_combinations = list(it.chain.from_iterable([[tuple(it.chain.from_iterable(np.array(Grouping_split_sequences, dtype = object)[Gcn].tolist())) for Gcn in Group_combination_number] for Group_combination_number in Group_combination_numbers]))
                Combination_in_allowance = [len(re.sub('[ATGC]', '', make_wobble(*Split_sequences_combination)[0])) <= np.max([(allowance / 0.75), np.max([len(re.sub('[ATGC]', '', seq)) for seq in Split_sequences_combination])]) for Split_sequences_combination in Split_sequences_combinations]
                Position_combinations = [Position_combinations[i] for i in range(len(Position_combinations)) if Combination_in_allowance[i]]
                if len(Position_combinations) > Maximum_combination_size:
                    Position_combinations = [tuple(sorted(list(it.chain.from_iterable(Grouping_position_list)), key = abs))]
            Criteria = np.array([[np.count_nonzero(np.array(posc) == pos) > 0 for pos in Position_list] for posc in Position_combinations])
            score_list = [np.array(score_list)[cr] for cr in Criteria]
            del split_sequences
            for i in range(len(Position_combinations)):
                for in_allowance in range(allowance + 1):
                    Position_index = np.array(Position_combinations[i])[np.where(np.array(score_list[i]) >= ((len(evaluating_sequence) - in_allowance)/len(evaluating_sequence)))[0].tolist()]
                    if np.any([np.all([np.all(np.diff(np.sort(np.abs(Position_index))) >= interval_distance), len(Position_index) <= Maximum_annealing_site_number]), (len(Position_index) == 1)]):
                        extract_input_sequences = [input_sequence[Position:(Position + len(evaluating_sequence)):] if Position >= 0 else complementary_sequence(input_sequence[np.abs(Position):(np.abs(Position) + len(evaluating_sequence)):]) for Position in Position_index]
                        extract_input_sequences = [nucleotide_sequence(extract_input_sequence).Decompress() if len(re.sub('[ATGC]', '', extract_input_sequence)) > 0 else [extract_input_sequence] for extract_input_sequence in extract_input_sequences]
                        extract_input_sequence_score = [np.argmax([nucleotide_sequence(decompressed_seq).calculate_score(evaluating_sequence) for decompressed_seq in extract_input_sequence]) for extract_input_sequence in extract_input_sequences]
                        extract_input_sequences = [str(np.array(extract_input_sequences[i])[extract_input_sequence_score[i]]) for i in range(len(extract_input_sequences))]
                        seq = make_wobble(*([evaluating_sequence] + extract_input_sequences))
                        Position_index = Position_list[np.array([calculate_score(seq[0], input_sequence[Position:(Position + len(evaluating_sequence)):]) == 1 if Position >= 0 else calculate_score(seq[0], complementary_sequence(input_sequence[np.abs(Position):(np.abs(Position) + len(evaluating_sequence)):])) == 1 for Position in Position_list])].astype(object)
                        Start_position = {seq[0]:Position_index} if np.all([(calculate_flexibility(seq[0]) <= (calculate_flexibility(evaluating_sequence) + (in_allowance/len(evaluating_sequence)))), (calculate_flexibility(seq[0]) < 1.0), len(Position_index) > 0]) else None
                        Start_positions.update({list(Start_position.keys())[0]:np.array(sorted(list(set(Start_positions[list(Start_position.keys())[0]].tolist() + Start_position[list(Start_position.keys())[0]].tolist())), key = abs), dtype = object)} if (set(Start_position.keys()) <= set(Start_positions.keys())) else Start_position) if Start_position is not None else Start_positions.update()
                        Mismatch_Counter = Mismatch_Counter if np.any([np.all([np.all(np.diff(np.sort(np.abs(Position_index))) >= interval_distance), len(Position_index) <= Maximum_annealing_site_number]), (len(Position_index) == 1)]) else Mismatch_Counter + 1
                    else:
                        Mismatch_Counter += 1
                    Total_Counter += 1
        else:
            pass
    else:
        Complementary_criteria = np.array(Position_list)[np.where(np.array(complementary_score_list) >= ((len(evaluating_sequence) - allowance)/len(evaluating_sequence)))[0]]
        Complementary_criteria = np.array([set(Complementary_criteria) >= set([Position]) for Position in Position_list])
        Position_list = np.array(Position_list)
        score_list_criteria = np.array([set(score_list_criteria) >= set([Position]) for Position in Position_list])
        Palindrome_sequence_list = {}
        Palindrome_position = Position_list[score_list_criteria & Complementary_criteria]
        [Palindrome_sequence_list.update({input_sequence[Ppos:(Ppos + len(evaluating_sequence)):]: Palindrome_sequence_list[input_sequence[Ppos:(Ppos + len(evaluating_sequence)):]] + [Ppos]}) if (input_sequence[Ppos:(Ppos + len(evaluating_sequence)):] in Palindrome_sequence_list.keys()) else Palindrome_sequence_list.update({input_sequence[Ppos:(Ppos + len(evaluating_sequence)):]: [Ppos]}) for Ppos in Palindrome_position]
        if np.any(Complementary_criteria):
            Position_list[Complementary_criteria] = Position_list[Complementary_criteria] * (-1)
        split_sequences = np.array([split_sequences[i] if Position_list[i] >= 0 else complementary_sequence(split_sequences[i]) for i in range(len(split_sequences))])
        duplicate_index = [split_sequences == seq for seq in sorted(list(set(split_sequences)))]
        Grouping_position_list = [list(Position_list[didx]) for didx in duplicate_index]
        Grouping_split_sequences = [list(set(split_sequences[didx])) for didx in duplicate_index]
        if len(Grouping_position_list) > Maximum_position_list_size:
            Position_combinations = [tuple(sorted(list(it.chain.from_iterable(Grouping_position_list)), key = abs))]
        else:
            Group_combination_numbers = [[np.array(Grouping_combination_number) for Grouping_combination_number in list(it.combinations(range(len(Grouping_position_list)), i))] for i in range(1, len(Grouping_position_list) + 1)]
            Position_combinations = list(it.chain.from_iterable([[tuple(sorted(it.chain.from_iterable(np.array(Grouping_position_list, dtype = object)[Gcn].tolist()), key = abs)) for Gcn in Group_combination_number] for Group_combination_number in Group_combination_numbers]))
            Split_sequences_combinations = list(it.chain.from_iterable([[tuple(it.chain.from_iterable(np.array(Grouping_split_sequences, dtype = object)[Gcn].tolist())) for Gcn in Group_combination_number] for Group_combination_number in Group_combination_numbers]))
            Combination_in_allowance = [len(re.sub('[ATGC]', '', make_wobble(*Split_sequences_combination)[0])) <= np.max([(allowance / 0.75), np.max([len(re.sub('[ATGC]', '', seq)) for seq in Split_sequences_combination])]) for Split_sequences_combination in Split_sequences_combinations]
            Position_combinations = [Position_combinations[i] for i in range(len(Position_combinations)) if Combination_in_allowance[i]]
            if len(Position_combinations) > Maximum_combination_size:
                Position_combinations = [tuple(sorted(list(it.chain.from_iterable(Grouping_position_list)), key = abs))]
        Criteria = np.array([[np.count_nonzero(np.array(posc) == pos) > 0 for pos in Position_list] for posc in Position_combinations])
        for i in range(len(Position_combinations)):
            for in_allowance in range(allowance + 1):
                Position_index = np.array(Position_combinations[i])[np.where(np.array(score_list)[Criteria[i]] >= ((len(evaluating_sequence) - in_allowance)/len(evaluating_sequence)))[0].tolist()]
                if np.any([np.all([np.all(np.diff(np.sort(np.abs(Position_index))) >= interval_distance), len(Position_index) <= Maximum_annealing_site_number]), (len(Position_index) == 1)]):
                    extract_split_sequences = split_sequences[Criteria[i]][np.where(np.array(score_list)[Criteria[i]] >= ((len(evaluating_sequence) - in_allowance)/len(evaluating_sequence)))[0].tolist()]
                    extract_split_sequences = [nucleotide_sequence(extract_split_sequence).Decompress() if len(re.sub('[ATGC]', '', extract_split_sequence)) > 0 else [extract_split_sequence] for extract_split_sequence in extract_split_sequences]
                    extract_split_sequence_score = [np.argmax([nucleotide_sequence(decompressed_seq).calculate_score(evaluating_sequence) for decompressed_seq in extract_split_sequence]) for extract_split_sequence in extract_split_sequences]
                    extract_split_sequences = [str(np.array(extract_split_sequences[i])[extract_split_sequence_score[i]]) for i in range(len(extract_split_sequences))]
                    seq = make_wobble(*([evaluating_sequence] + extract_split_sequences))
                    Position_index = Position_list[np.array([calculate_score(seq[0], split_sequences[i]) == 1 for i in range(len(Position_list))])].astype(object)
                    Start_position = {seq[0]:Position_index} if np.all([(calculate_flexibility(seq[0]) <= (calculate_flexibility(evaluating_sequence) + (in_allowance/len(evaluating_sequence)))), (calculate_flexibility(seq[0]) < 1.0), (len(Position_index) > 0)]) else None
                    Start_positions.update({list(Start_position.keys())[0]:np.array(sorted(list(set(Start_positions[list(Start_position.keys())[0]].tolist() + Start_position[list(Start_position.keys())[0]].tolist())), key = abs), dtype = object)} if (set(Start_position.keys()) <= set(Start_positions.keys())) else Start_position) if Start_position is not None else Start_positions.update()
                    Mismatch_Counter = Mismatch_Counter if np.any([np.all([np.all(np.diff(np.sort(np.abs(Position_index))) >= interval_distance), len(Position_index) <= Maximum_annealing_site_number]), (len(Position_index) == 1)]) else Mismatch_Counter + 1
                else:
                    Mismatch_Counter += 1
                Total_Counter += 1
    Mismatch_rate = Mismatch_Counter / Total_Counter if ((allowance > 0) & (Total_Counter > 0)) else 0
    if len(Palindrome_sequence_list) != 0:
        Start_positions = {Key: Position.tolist() + [pp * (-1) if set(Position) >= set([pp]) else pp for palseq, Ppos in Palindrome_sequence_list.items() if ((calculate_score(Key, palseq) == 1.0) & (calculate_score(Key, complementary_sequence(palseq)) == 1.0)) for pp in Ppos] for Key, Position in Start_positions.items()}
        Start_positions = {Key: np.array(sorted(sorted(list(set(Position))), key = abs), dtype = object) for Key, Position in Start_positions.items()}
    Start_positions = {Key:Position for Key, Position in Start_positions.items() if np.all(np.diff(np.sort(np.abs(Position))) >= interval_distance)}
    if (len(Start_positions) != 0) & ((1 - Mismatch_rate) >= Match_rate):
        return Start_positions
    else:
        return None

def make_primer_set_and_amplicon_size(i, df, cut_off_lower, cut_off_upper, separation_key = []):
    """
    Function for making primer set by parallel process. (private)
    
    """
    shared_Melted_df_Start_positions_set = df
    if shared_Melted_df_Start_positions_set.iloc[i]['Position'] >= 0:
        Extracted_data_plus = shared_Melted_df_Start_positions_set.iloc[i+1:]
        Extracted_data_plus = Extracted_data_plus[Extracted_data_plus['Position'] >= 0]
        Extracted_data_plus = Extracted_data_plus[((Extracted_data_plus['Position'].add(Extracted_data_plus['Sequence'].map(lambda x:len(x)), axis = 0) - shared_Melted_df_Start_positions_set.iloc[i]['Position']) > cut_off_lower) & ((Extracted_data_plus['Position'].add(Extracted_data_plus['Sequence'].map(lambda x:len(x)), axis = 0) - shared_Melted_df_Start_positions_set.iloc[i]['Position']) < cut_off_upper)]
        Criterion_plus = [array_diff(shared_Melted_df_Start_positions_set.iloc[i, 2:], Extracted_data_plus.iloc[n, 2:].add(len(Extracted_data_plus['Sequence'].iloc[n]), axis = 0), lower = cut_off_lower, upper = cut_off_upper, logical = True, separation_key = separation_key) for n in range(len(Extracted_data_plus.iloc[:, 2:]))]
        Extracted_data_plus = Extracted_data_plus[Criterion_plus]
    else:
        Extracted_data_minus = shared_Melted_df_Start_positions_set.iloc[i+1:]
        Extracted_data_minus = Extracted_data_minus[Extracted_data_minus['Position'] < 0]
        Extracted_data_minus = Extracted_data_minus[((shared_Melted_df_Start_positions_set.iloc[i]['Position'] - Extracted_data_minus['Position'].sub(Extracted_data_minus['Sequence'].map(lambda x:len(x)), axis = 0)) > cut_off_lower) & ((shared_Melted_df_Start_positions_set.iloc[i]['Position'] - Extracted_data_minus['Position'].sub(Extracted_data_minus['Sequence'].map(lambda x:len(x)), axis = 0)) < cut_off_upper)]
        Criterion_minus = [array_diff(Extracted_data_minus.iloc[n, 2:].sub(len(Extracted_data_minus['Sequence'].iloc[n]), axis = 0), shared_Melted_df_Start_positions_set.iloc[i, 2:], lower = cut_off_lower, upper = cut_off_upper, logical = True, separation_key = separation_key) for n in range(len(Extracted_data_minus.iloc[:, 2:]))]
        Extracted_data_minus = Extracted_data_minus[Criterion_minus]
    Result = []
    if 'Extracted_data_plus' in locals():
        if len(Extracted_data_plus) != 0:
            Primer_sets = list(it.product([shared_Melted_df_Start_positions_set.iloc[i]['Sequence']], Extracted_data_plus['Sequence']))
            Fragment_size = [array_diff(shared_Melted_df_Start_positions_set.iloc[i, 2:].map(lambda x:[p - len(shared_Melted_df_Start_positions_set["Sequence"].iloc[i]) if p < 0 else p for p in x] if np.any(pd.notna(x)) else np.nan), Extracted_data_plus.iloc[n, 2:].map(lambda x:[p + len(Extracted_data_plus["Sequence"].iloc[n]) if p > 0 else p for p in x] if np.any(pd.notna(x)) else np.nan), lower = cut_off_lower, upper = cut_off_upper, logical = False, separation_key = separation_key) for n in range(len(Extracted_data_plus.iloc[:, 2:]))]
            Fragment_size = [[list(f) for f in fs] for fs in Fragment_size]
            Criterion1 = [fragment_size_distance(fs, sum = True, method = 'average') != 0 for fs in Fragment_size]
            Criterion2_1 = [(np.all(np.array(arr_length_in_arr(shared_Melted_df_Start_positions_set.iloc[i, 2:])) == 1) & np.all(np.array(arr_length_in_arr(Extracted_data_plus.iloc[n, 2:])) == 1)) for n in range(Extracted_data_plus.shape[0])]
            Criterion2_2 = [fragment_size_distance(fs, sum = False, method = 'average') == 0 for fs in Fragment_size]
            Criterion2 = np.logical_not([np.all(cr) for cr in zip(Criterion2_1, Criterion2_2)])
            Criteria = [np.all(cr) for cr in zip(Criterion1, Criterion2)]
            Primer_sets = [tuple([Primer_sets[n][0], complementary_sequence(Primer_sets[n][1])]) for n in range(len(Primer_sets)) if Criteria[n]]
            Fragment_size = [Fragment_size[n] for n in range(len(Fragment_size)) if Criteria[n]]
            Result += list(zip(Primer_sets, Fragment_size))
    if 'Extracted_data_minus' in locals():
        if len(Extracted_data_minus) != 0:
            Primer_sets = list(it.product([shared_Melted_df_Start_positions_set.iloc[i]['Sequence']], Extracted_data_minus['Sequence']))
            Fragment_size = [array_diff(Extracted_data_minus.iloc[n, 2:].map(lambda x:[p - len(Extracted_data_minus["Sequence"].iloc[n]) if p < 0 else p for p in x] if np.any(pd.notna(x)) else np.nan), shared_Melted_df_Start_positions_set.iloc[i, 2:].map(lambda x:[p + len(shared_Melted_df_Start_positions_set["Sequence"].iloc[i]) if p > 0 else p for p in x] if np.any(pd.notna(x)) else np.nan), lower = cut_off_lower, upper = cut_off_upper, logical = False, separation_key = separation_key) for n in range(len(Extracted_data_minus.iloc[:, 2:]))]
            Fragment_size = [[list(f) for f in fs] for fs in Fragment_size]
            Criterion1 = [fragment_size_distance(fs, sum = True, method = 'average') != 0 for fs in Fragment_size]
            Criterion2_1 = [(np.all(np.array(arr_length_in_arr(shared_Melted_df_Start_positions_set.iloc[i, 2:])) == 1) & np.all(np.array(arr_length_in_arr(Extracted_data_minus.iloc[n, 2:])) == 1)) for n in range(Extracted_data_minus.shape[0])]
            Criterion2_2 = [fragment_size_distance(fs, sum = False, method = 'average') == 0 for fs in Fragment_size]
            Criterion2 = np.logical_not([np.all(cr) for cr in zip(Criterion2_1, Criterion2_2)])
            Criteria = [np.all(cr) for cr in zip(Criterion1, Criterion2)]
            Primer_sets = [tuple([complementary_sequence(Primer_sets[n][0]), Primer_sets[n][1]]) for n in range(len(Primer_sets)) if Criteria[n]]
            Fragment_size = [Fragment_size[n] for n in range(len(Fragment_size)) if Criteria[n]]
            Result += list(zip(Primer_sets, Fragment_size))
    if len(Result) != 0:
        return Result
    else:
        return None

def homology_calculation(Chunk_Start_position, parameter):
    """
    Function for calculating homology by parallel process. (private)
    
    """
    homology_calculation_chunks = parameter['homology_calculation_chunks']
    share_informations = parameter['share_informations']
    probe_size = parameter['probe_size']
    allowance = parameter['allowance']
    Mode = parameter['Mode']
    GPU = parameter['GPU']
    Allowance_adjustment = parameter['Allowance_adjustment']
    input_sequences_length = parameter['input_sequences_length']
    interval_distance = parameter['interval_distance']
    Maximum_annealing_site_number = parameter['Maximum_annealing_site_number']
    Annealing_site_number_threshold = parameter['Annealing_site_number_threshold']
    update_factor = parameter['update_factor']
    Interval_factor = parameter['Interval_factor']
    if (Mode == "Exclude") & GPU:
        existing_shm1 = SharedMemory(name = share_informations[0][0])
        translate_exclude_sequence_matrix = np.ndarray(shape = share_informations[0][1], dtype = share_informations[0][2], buffer = existing_shm1.buf)
        existing_shm2 = SharedMemory(name = share_informations[1][0])
        template_translate_sequences_matrix = np.ndarray(shape = share_informations[1][1], dtype = share_informations[1][2], buffer = existing_shm2.buf)
        extract_template_translate_sequences_matrix = template_translate_sequences_matrix[Chunk_Start_position:(Chunk_Start_position + homology_calculation_chunks)].astype(np.uint8)
        if len(extract_template_translate_sequences_matrix.shape) == 1:
            extract_template_translate_sequences_matrix = extract_template_translate_sequences_matrix.reshape(1, -1).astype(np.uint8)
        Extract_template_sequences_number = extract_template_translate_sequences_matrix.shape[0]
        try:
            translate_exclude_sequence_matrix_GPU = cp.asarray(translate_exclude_sequence_matrix).astype(cp.uint8)
            translate_sequences_matrix_chunk_GPU = cp.asarray(extract_template_translate_sequences_matrix).astype(cp.uint8)
            translate_exclude_sequence_mismatch_matrix_GPU = cp.dot(translate_sequences_matrix_chunk_GPU, translate_exclude_sequence_matrix_GPU)
            translate_exclude_sequence_mismatch_matrix = cp.asnumpy(translate_exclude_sequence_mismatch_matrix_GPU)
            del translate_exclude_sequence_mismatch_matrix_GPU
            mempool.free_all_blocks()
            translate_complementary_exclude_sequence_mismatch_matrix_GPU = cp.dot(translate_sequences_matrix_chunk_GPU, cp.flipud(translate_exclude_sequence_matrix_GPU))
            translate_complementary_exclude_sequence_mismatch_matrix = cp.asnumpy(translate_complementary_exclude_sequence_mismatch_matrix_GPU)
            translate_exclude_sequence_mismatch_matrix = np.maximum(translate_exclude_sequence_mismatch_matrix, translate_complementary_exclude_sequence_mismatch_matrix)
            del translate_exclude_sequence_matrix_GPU, translate_sequences_matrix_chunk_GPU, translate_complementary_exclude_sequence_mismatch_matrix_GPU, translate_complementary_exclude_sequence_mismatch_matrix
            mempool.free_all_blocks()
        except:
            if 'translate_exclude_sequence_matrix_GPU' in locals(): del translate_exclude_sequence_matrix_GPU
            if 'translate_sequences_matrix_chunk_GPU' in locals(): del translate_sequences_matrix_chunk_GPU
            if 'translate_exclude_sequence_mismatch_matrix_GPU' in locals(): del translate_exclude_sequence_mismatch_matrix_GPU
            if 'translate_complementary_exclude_sequence_mismatch_matrix_GPU' in locals(): del translate_complementary_exclude_sequence_mismatch_matrix_GPU
            mempool.free_all_blocks()
            translate_exclude_sequence_mismatch_matrix = np.dot(extract_template_translate_sequences_matrix, translate_exclude_sequence_matrix)
            translate_complementary_exclude_sequence_mismatch_matrix = np.dot(extract_template_translate_sequences_matrix, np.flipud(translate_exclude_sequence_matrix))
            translate_exclude_sequence_mismatch_matrix = np.maximum(translate_exclude_sequence_mismatch_matrix, translate_complementary_exclude_sequence_mismatch_matrix)
            del translate_complementary_exclude_sequence_mismatch_matrix
        Criterion = list((np.count_nonzero(translate_exclude_sequence_mismatch_matrix.astype(np.int32) >= (probe_size - allowance), axis = 1) == 0))
        del translate_exclude_sequence_matrix, template_translate_sequences_matrix
        existing_shm1.close(); existing_shm2.close()
        pbar_information = [(Extract_template_sequences_number / homology_calculation_chunks) * update_factor / Interval_factor, "", int(0)]
        del extract_template_translate_sequences_matrix
        return [pbar_information, Criterion, [], []]
    elif (Mode == "Exclude") & np.logical_not(GPU):
        existing_shm1 = SharedMemory(name = share_informations[0][0])
        translate_exclude_sequence_matrix = np.ndarray(shape = share_informations[0][1], dtype = share_informations[0][2], buffer = existing_shm1.buf)
        existing_shm2 = SharedMemory(name = share_informations[1][0])
        template_translate_sequences_matrix = np.ndarray(shape = share_informations[1][1], dtype = share_informations[1][2], buffer = existing_shm2.buf)
        extract_template_translate_sequences_matrix = template_translate_sequences_matrix[Chunk_Start_position:(Chunk_Start_position + homology_calculation_chunks)].astype(np.uint8)
        if len(extract_template_translate_sequences_matrix.shape) == 1:
            extract_template_translate_sequences_matrix = extract_template_translate_sequences_matrix.reshape(1, -1).astype(np.uint8)
        Extract_template_sequences_number = extract_template_translate_sequences_matrix.shape[0]
        translate_exclude_sequence_mismatch_matrix = np.dot(extract_template_translate_sequences_matrix, translate_exclude_sequence_matrix)
        translate_complementary_exclude_sequence_mismatch_matrix = np.dot(extract_template_translate_sequences_matrix, np.flipud(translate_exclude_sequence_matrix))
        translate_exclude_sequence_mismatch_matrix = np.maximum(translate_exclude_sequence_mismatch_matrix, translate_complementary_exclude_sequence_mismatch_matrix)
        del translate_complementary_exclude_sequence_mismatch_matrix
        Criterion = list((np.count_nonzero(translate_exclude_sequence_mismatch_matrix.astype(np.int32) >= (probe_size - allowance), axis = 1) == 0))
        del translate_exclude_sequence_mismatch_matrix, translate_exclude_sequence_matrix, template_translate_sequences_matrix
        existing_shm1.close(); existing_shm2.close()
        pbar_information = [(Extract_template_sequences_number / homology_calculation_chunks) * update_factor / Interval_factor, "", int(0)]
        del extract_template_translate_sequences_matrix
        return [pbar_information, Criterion, [], []]
    elif (Mode == "Explore") & GPU:
        existing_shm1 = SharedMemory(name = share_informations[0][0])
        translate_sequence_matrix = np.ndarray(shape = share_informations[0][1], dtype = share_informations[0][2], buffer = existing_shm1.buf)
        existing_shm2 = SharedMemory(name = share_informations[1][0])
        template_translate_sequences_matrix = np.ndarray(shape = share_informations[1][1], dtype = share_informations[1][2], buffer = existing_shm2.buf)
        existing_shm3 = SharedMemory(name = share_informations[2][0])
        Sequence = np.ndarray(shape = share_informations[2][1], dtype = share_informations[2][2], buffer = existing_shm3.buf)
        existing_shm4 = SharedMemory(name = share_informations[3][0])
        Cumulative_valid_index = np.ndarray(shape = share_informations[3][1], dtype = share_informations[3][2], buffer = existing_shm4.buf) 
        Allowance_list = ShareableList(name = share_informations[4][0])
        extract_template_translate_sequences_matrix = template_translate_sequences_matrix[Chunk_Start_position:(Chunk_Start_position + homology_calculation_chunks)].astype(np.uint8)
        if len(extract_template_translate_sequences_matrix.shape) == 1:
            extract_template_translate_sequences_matrix = extract_template_translate_sequences_matrix.reshape(1, -1).astype(np.uint8)
        Extract_template_sequences_number = extract_template_translate_sequences_matrix.shape[0]
        if Allowance_adjustment:
            alw = copy.deepcopy(Allowance_list[0])
        else:
            alw = np.min(np.abs(Allowance_list))
        Previous_result = [set([]) for i in range(len(extract_template_translate_sequences_matrix))]
        while True:
            try:
                PU = "GPU"
                translate_sequence_matrix_GPU = cp.asarray(translate_sequence_matrix).astype(cp.uint8)
                translate_sequences_matrix_chunk_GPU = cp.asarray(extract_template_translate_sequences_matrix).astype(cp.uint8)
                shape = (translate_sequences_matrix_chunk_GPU.shape[0], translate_sequence_matrix_GPU.shape[1], )
                translate_sequence_mismatch_matrix_GPU = cp.zeros(shape = shape, dtype=cp.uint8)
                cp.dot(translate_sequences_matrix_chunk_GPU, translate_sequence_matrix_GPU, out = translate_sequence_mismatch_matrix_GPU)
                translate_sequence_mismatch_matrix = cp.asnumpy(translate_sequence_mismatch_matrix_GPU)
                cp.dot(translate_sequences_matrix_chunk_GPU, cp.flipud(translate_sequence_matrix_GPU), out = translate_sequence_mismatch_matrix_GPU)
                translate_complementary_sequence_mismatch_matrix = cp.asnumpy(translate_sequence_mismatch_matrix_GPU)
                translate_sequence_mismatch_matrix = np.maximum(translate_sequence_mismatch_matrix, translate_complementary_sequence_mismatch_matrix)
                del translate_sequences_matrix_chunk_GPU, translate_sequence_matrix_GPU, translate_complementary_sequence_mismatch_matrix, translate_sequence_mismatch_matrix_GPU
                mempool.free_all_blocks()
            except:
                if 'translate_sequence_matrix_GPU' in locals(): del translate_sequence_matrix_GPU
                if 'translate_sequences_matrix_chunk_GPU' in locals(): del translate_sequences_matrix_chunk_GPU
                if 'translate_sequence_mismatch_matrix_GPU' in locals(): del translate_sequence_mismatch_matrix_GPU
                mempool.free_all_blocks()
                PU = "Switch to CPU"
                translate_sequence_matrix_CPU = translate_sequence_matrix
                translate_sequences_matrix_chunk_CPU = extract_template_translate_sequences_matrix
                translate_sequence_mismatch_matrix = np.zeros(shape = (translate_sequences_matrix_chunk_CPU.shape[0], translate_sequence_matrix_CPU.shape[1]), dtype = np.uint8)
                np.dot(translate_sequences_matrix_chunk_CPU, translate_sequence_matrix_CPU, out = translate_sequence_mismatch_matrix)
                translate_complementary_sequence_mismatch_matrix = np.zeros(shape = (translate_sequences_matrix_chunk_CPU.shape[0], translate_sequence_matrix_CPU.shape[1]), dtype = np.uint8)
                np.dot(translate_sequences_matrix_chunk_CPU, np.flipud(translate_sequence_matrix_CPU), out = translate_complementary_sequence_mismatch_matrix)
                translate_sequence_mismatch_matrix = np.maximum(translate_sequence_mismatch_matrix, translate_complementary_sequence_mismatch_matrix)
                del translate_sequence_matrix_CPU, translate_sequences_matrix_chunk_CPU, translate_complementary_sequence_mismatch_matrix
            preliminary_matrix = np.nonzero(translate_sequence_mismatch_matrix.astype(np.int32) >= (probe_size - (alw / 0.75)))
            Valid_index = np.count_nonzero(translate_sequence_mismatch_matrix.astype(np.int32) >= (probe_size - alw), axis = 1).astype(np.int32)
            Extend_valid_index = np.count_nonzero(translate_sequence_mismatch_matrix.astype(np.int32) >= (probe_size - (alw / 0.75)), axis = 1).astype(np.int32)
            Criterion_current_loop = list(((Valid_index > 0) & (Valid_index < input_sequences_length / np.max([interval_distance, 1]))) | ((Valid_index == 0) & (Extend_valid_index <= Maximum_annealing_site_number * 3) & (Extend_valid_index > 0)))
            Annealing_site_number = round(np.sum(np.sort(Valid_index)[0:np.max([19, math.floor(len(Valid_index) * 0.95)])]) / len(np.sort(Valid_index)[0:np.max([19, math.floor(len(Valid_index) * 0.95)])]), 1)
            position_list_current_loop = [list(preliminary_matrix[1][preliminary_matrix[0] == i]) if (np.any(preliminary_matrix[0] == i) & Criterion_current_loop[i]) else None for i in range(translate_sequence_mismatch_matrix.shape[0])]
            if np.logical_not(Allowance_adjustment):
                if "Exclusion_required_sequences" not in locals():
                    Exclusion_required_sequences = [[] for n in range(translate_sequence_mismatch_matrix.shape[0])]
                if ((Annealing_site_number >= 0) & (Annealing_site_number <= np.min([Maximum_annealing_site_number, Annealing_site_number_threshold]))) | (alw == 0):
                    Cumulative_valid_index[Chunk_Start_position:(Chunk_Start_position + homology_calculation_chunks)] = Valid_index
                    Average_annealing_site_number = round(np.sum(Cumulative_valid_index[0:(Chunk_Start_position + homology_calculation_chunks)]) / len(Cumulative_valid_index[0:(Chunk_Start_position + homology_calculation_chunks)]), 1)
                    Allowance_list[Chunk_Start_position // homology_calculation_chunks + 1] = alw
                    break
                else:
                    alw -= 1
            else:
                if "Exclusion_required_sequences" not in locals():
                    Exclusion_required_sequences = [[] for n in range(translate_sequence_mismatch_matrix.shape[0])]
                if ((Annealing_site_number >= 0) & (Annealing_site_number <= np.min([Maximum_annealing_site_number, Annealing_site_number_threshold]))) | (alw == 0):
                    Exclusion_required_sequences_current_loop = [list(Previous_result[i] - set([str(Sequence[0])[position:(position + probe_size):] for position in position_list_current_loop[i]])) if position_list_current_loop[i] is not None else [] for i in range(len(position_list_current_loop))]
                    [li.extend(add) for li, add in zip(Exclusion_required_sequences, Exclusion_required_sequences_current_loop)]
                    Cumulative_valid_index[Chunk_Start_position:(Chunk_Start_position + homology_calculation_chunks)] = Valid_index
                    Average_annealing_site_number = round(np.sum(Cumulative_valid_index[0:(Chunk_Start_position + homology_calculation_chunks)]) / len(Cumulative_valid_index[0:(Chunk_Start_position + homology_calculation_chunks)]), 1)
                    Allowance_list[Chunk_Start_position // homology_calculation_chunks + 1] = alw
                    break
                else:
                    Exclusion_required_sequences_current_loop = [list(Previous_result[i] - set([str(Sequence[0])[position:(position + probe_size):] for position in position_list_current_loop[i]])) if position_list_current_loop[i] is not None else [] for i in range(len(position_list_current_loop))]
                    [li.extend(add) for li, add in zip(Exclusion_required_sequences, Exclusion_required_sequences_current_loop)]
                    Exclusion_required_sequences = [list(set(li)) for li in Exclusion_required_sequences]
                    Previous_result = [set([str(Sequence[0])[position:(position + probe_size):] for position in position_list_current_loop[i]]) if position_list_current_loop[i] is not None else set([]) for i in range(len(position_list_current_loop))]
                    alw -= 1
        Optimized_allowance_value = round(np.mean([a for a in Allowance_list if a >= 0]) / probe_size, 2)
        pbar_information = [(Extract_template_sequences_number / homology_calculation_chunks) * update_factor / Interval_factor, PU, Optimized_allowance_value, Average_annealing_site_number]
        Allowance_list.shm.close()
        del translate_sequence_matrix, template_translate_sequences_matrix, Sequence, Cumulative_valid_index, Allowance_list
        existing_shm1.close(); existing_shm2.close(); existing_shm3.close(); existing_shm4.close()
        return [pbar_information, Criterion_current_loop, position_list_current_loop, Exclusion_required_sequences]
    elif (Mode == "Explore") & np.logical_not(GPU):
        existing_shm1 = SharedMemory(name = share_informations[0][0])
        translate_sequence_matrix = np.ndarray(shape = share_informations[0][1], dtype = share_informations[0][2], buffer = existing_shm1.buf)
        existing_shm2 = SharedMemory(name = share_informations[1][0])
        template_translate_sequences_matrix = np.ndarray(shape = share_informations[1][1], dtype = share_informations[1][2], buffer = existing_shm2.buf)
        existing_shm3 = SharedMemory(name = share_informations[2][0])
        Sequence = np.ndarray(shape = share_informations[2][1], dtype = share_informations[2][2], buffer = existing_shm3.buf)
        existing_shm4 = SharedMemory(name = share_informations[3][0])
        Cumulative_valid_index = np.ndarray(shape = share_informations[3][1], dtype = share_informations[3][2], buffer = existing_shm4.buf)
        Allowance_list = ShareableList(name = share_informations[4][0])
        extract_template_translate_sequences_matrix = template_translate_sequences_matrix[Chunk_Start_position:(Chunk_Start_position + homology_calculation_chunks)].astype(np.uint8)
        if len(extract_template_translate_sequences_matrix.shape) == 1:
            extract_template_translate_sequences_matrix = extract_template_translate_sequences_matrix.reshape(1, -1).astype(np.uint8)
        Extract_template_sequences_number = extract_template_translate_sequences_matrix.shape[0]
        if Allowance_adjustment:
            alw = copy.deepcopy(Allowance_list[0])
        else:
            alw = np.min(np.abs(Allowance_list))
        Previous_result = [set([]) for i in range(len(extract_template_translate_sequences_matrix))]
        PU = "CPU"
        while True:
            translate_sequence_mismatch_matrix = np.zeros(shape = (extract_template_translate_sequences_matrix.shape[0], translate_sequence_matrix.shape[1]), dtype = np.uint8)
            np.dot(extract_template_translate_sequences_matrix, translate_sequence_matrix, out = translate_sequence_mismatch_matrix)
            translate_complementary_sequence_mismatch_matrix = np.zeros(shape = (extract_template_translate_sequences_matrix.shape[0], translate_sequence_matrix.shape[1]), dtype = np.uint8)
            np.dot(extract_template_translate_sequences_matrix, np.flipud(translate_sequence_matrix), out = translate_complementary_sequence_mismatch_matrix)
            translate_sequence_mismatch_matrix = np.maximum(translate_sequence_mismatch_matrix, translate_complementary_sequence_mismatch_matrix)
            preliminary_matrix = np.nonzero(translate_sequence_mismatch_matrix.astype(np.int32) >= (probe_size - (alw / 0.75))) 
            Valid_index = np.count_nonzero(translate_sequence_mismatch_matrix.astype(np.int32) >= (probe_size - alw), axis = 1).astype(np.int32)
            Extend_valid_index = np.count_nonzero(translate_sequence_mismatch_matrix.astype(np.int32) >= (probe_size - (alw / 0.75)), axis = 1).astype(np.int32)
            Criterion_current_loop = list(((Valid_index > 0) & (Valid_index < input_sequences_length / np.max([interval_distance, 1]))) | ((Valid_index == 0) & (Extend_valid_index <= Maximum_annealing_site_number * 3) & (Extend_valid_index > 0)))
            Annealing_site_number = round(np.sum(np.sort(Valid_index)[0:np.max([19, math.floor(len(Valid_index) * 0.95)])]) / len(np.sort(Valid_index)[0:np.max([19, math.floor(len(Valid_index) * 0.95)])]), 1)
            position_list_current_loop = [list(preliminary_matrix[1][preliminary_matrix[0] == i]) if (np.any(preliminary_matrix[0] == i) & Criterion_current_loop[i]) else None for i in range(translate_sequence_mismatch_matrix.shape[0])]
            if np.logical_not(Allowance_adjustment):
                if "Exclusion_required_sequences" not in locals():
                    Exclusion_required_sequences = [[] for n in range(translate_sequence_mismatch_matrix.shape[0])]
                if ((Annealing_site_number >= 0) & (Annealing_site_number <= np.min([Maximum_annealing_site_number, Annealing_site_number_threshold]))) | (alw == 0):
                    Cumulative_valid_index[Chunk_Start_position:(Chunk_Start_position + homology_calculation_chunks)] = Valid_index
                    Average_annealing_site_number = round(np.sum(Cumulative_valid_index[0:(Chunk_Start_position + homology_calculation_chunks)]) / len(Cumulative_valid_index[0:(Chunk_Start_position + homology_calculation_chunks)]), 1)
                    Allowance_list[Chunk_Start_position // homology_calculation_chunks + 1] = alw
                    break
                else:
                    alw -= 1
            else:
                if "Exclusion_required_sequences" not in locals():
                    Exclusion_required_sequences = [[] for n in range(translate_sequence_mismatch_matrix.shape[0])]
                if ((Annealing_site_number >= 0) & (Annealing_site_number <= np.min([Maximum_annealing_site_number, Annealing_site_number_threshold]))) | (alw == 0):
                    Exclusion_required_sequences_current_loop = [list(Previous_result[i] - set([str(Sequence[0])[position:(position + probe_size):] for position in position_list_current_loop[i]])) if position_list_current_loop[i] is not None else [] for i in range(len(position_list_current_loop))]
                    [li.extend(add) for li, add in zip(Exclusion_required_sequences, Exclusion_required_sequences_current_loop)]
                    Cumulative_valid_index[Chunk_Start_position:(Chunk_Start_position + homology_calculation_chunks)] = Valid_index
                    Average_annealing_site_number = round(np.sum(Cumulative_valid_index[0:(Chunk_Start_position + homology_calculation_chunks)]) / len(Cumulative_valid_index[0:(Chunk_Start_position + homology_calculation_chunks)]), 1)
                    Allowance_list[Chunk_Start_position // homology_calculation_chunks + 1] = alw
                    break
                else:
                    Exclusion_required_sequences_current_loop = [list(Previous_result[i] - set([str(Sequence[0])[position:(position + probe_size):] for position in position_list_current_loop[i]])) if position_list_current_loop[i] is not None else [] for i in range(len(position_list_current_loop))]
                    [li.extend(add) for li, add in zip(Exclusion_required_sequences, Exclusion_required_sequences_current_loop)]
                    Exclusion_required_sequences = [list(set(li)) for li in Exclusion_required_sequences]
                    Previous_result = [set([str(Sequence[0])[position:(position + probe_size):] for position in position_list_current_loop[i]]) if position_list_current_loop[i] is not None else set([]) for i in range(len(position_list_current_loop))]
                    alw -= 1
        Optimized_allowance_value = round(np.mean([a for a in Allowance_list if a >= 0]) / probe_size, 2)
        pbar_information = [(Extract_template_sequences_number / homology_calculation_chunks) * update_factor / Interval_factor, PU, Optimized_allowance_value, Average_annealing_site_number]
        Allowance_list.shm.close()
        del translate_sequence_matrix, template_translate_sequences_matrix, Sequence, Cumulative_valid_index, Allowance_list, extract_template_translate_sequences_matrix, translate_complementary_sequence_mismatch_matrix
        existing_shm1.close(); existing_shm2.close(); existing_shm3.close(); existing_shm4.close()
        return [pbar_information, Criterion_current_loop, position_list_current_loop, Exclusion_required_sequences]
    elif (Mode == "Check") & GPU:
        existing_shm1 = SharedMemory(name = share_informations[0][0])
        translate_check_sequence_matrix = np.ndarray(shape = share_informations[0][1], dtype = share_informations[0][2], buffer = existing_shm1.buf)
        existing_shm2 = SharedMemory(name = share_informations[1][0])
        template_translate_sequences_matrix = np.ndarray(shape = share_informations[1][1], dtype = share_informations[1][2], buffer = existing_shm2.buf)
        extract_template_translate_sequences_matrix = template_translate_sequences_matrix[Chunk_Start_position:(Chunk_Start_position + homology_calculation_chunks)].astype(np.uint8)
        if len(extract_template_translate_sequences_matrix.shape) == 1:
            extract_template_translate_sequences_matrix = extract_template_translate_sequences_matrix.reshape(1, -1).astype(np.uint8)
        Extract_template_sequences_number = extract_template_translate_sequences_matrix.shape[0]
        try:
            translate_check_sequence_matrix_GPU = cp.asarray(translate_check_sequence_matrix).astype(cp.uint8)
            translate_sequences_matrix_chunk_GPU = cp.asarray(extract_template_translate_sequences_matrix).astype(cp.uint8)
            translate_check_sequence_mismatch_matrix_GPU = cp.dot(translate_sequences_matrix_chunk_GPU, translate_check_sequence_matrix_GPU)
            translate_check_sequence_mismatch_matrix = cp.asnumpy(translate_check_sequence_mismatch_matrix_GPU)
            del translate_check_sequence_mismatch_matrix_GPU
            mempool.free_all_blocks()
            translate_complementary_check_sequence_mismatch_matrix_GPU = cp.dot(translate_sequences_matrix_chunk_GPU, cp.flipud(translate_check_sequence_matrix_GPU))
            translate_complementary_check_sequence_mismatch_matrix = cp.asnumpy(translate_complementary_check_sequence_mismatch_matrix_GPU)
            translate_check_sequence_mismatch_matrix = np.maximum(translate_check_sequence_mismatch_matrix, translate_complementary_check_sequence_mismatch_matrix)
            del translate_check_sequence_matrix_GPU, translate_sequences_matrix_chunk_GPU, translate_complementary_check_sequence_mismatch_matrix_GPU
            mempool.free_all_blocks()
        except:
            if 'translate_check_sequence_matrix_GPU' in locals(): del translate_check_sequence_matrix_GPU
            if 'translate_sequences_matrix_chunk_GPU' in locals(): del translate_sequences_matrix_chunk_GPU
            if 'translate_check_sequence_mismatch_matrix_GPU' in locals(): del translate_check_sequence_mismatch_matrix_GPU
            if 'translate_complementary_check_sequence_mismatch_matrix_GPU' in locals(): del translate_complementary_check_sequence_mismatch_matrix_GPU
            mempool.free_all_blocks()
            translate_check_sequence_mismatch_matrix = np.dot(extract_template_translate_sequences_matrix, translate_check_sequence_matrix)
            translate_complementary_check_sequence_mismatch_matrix = np.dot(extract_template_translate_sequences_matrix, np.flipud(translate_check_sequence_matrix))
            translate_check_sequence_mismatch_matrix = np.maximum(translate_check_sequence_mismatch_matrix, translate_complementary_check_sequence_mismatch_matrix)
        preliminary_matrix = np.nonzero(translate_check_sequence_mismatch_matrix.astype(np.int32) >= (probe_size - allowance))
        preliminary_complementary_matrix = np.nonzero(translate_complementary_check_sequence_mismatch_matrix.astype(np.int32) >= (probe_size - allowance))
        Position_matrix = [list(preliminary_matrix[1][preliminary_matrix[0] == i]) if np.any(preliminary_matrix[0] == i) else [] for i in range(translate_check_sequence_mismatch_matrix.shape[0])]
        Complementary_index = [list(preliminary_complementary_matrix[1][preliminary_complementary_matrix[0] == i]) if np.any(preliminary_complementary_matrix[0] == i) else [] for i in range(translate_complementary_check_sequence_mismatch_matrix.shape[0])]
        Position_matrix = [[pos * (-1) if pos in Complementary_index[i] else pos for pos in Position_matrix[i]] for i in range(len(Position_matrix))]
        del translate_check_sequence_matrix, template_translate_sequences_matrix, translate_complementary_check_sequence_mismatch_matrix
        existing_shm1.close(); existing_shm2.close()
        pbar_information = [(Extract_template_sequences_number / homology_calculation_chunks) * update_factor / Interval_factor, "", int(0)]
        del extract_template_translate_sequences_matrix
        return [pbar_information, Position_matrix, [], []]
    elif (Mode == "Check") & np.logical_not(GPU):
        existing_shm1 = SharedMemory(name = share_informations[0][0])
        translate_check_sequence_matrix = np.ndarray(shape = share_informations[0][1], dtype = share_informations[0][2], buffer = existing_shm1.buf)
        existing_shm2 = SharedMemory(name = share_informations[1][0])
        template_translate_sequences_matrix = np.ndarray(shape = share_informations[1][1], dtype = share_informations[1][2], buffer = existing_shm2.buf)
        extract_template_translate_sequences_matrix = template_translate_sequences_matrix[Chunk_Start_position:(Chunk_Start_position + homology_calculation_chunks)].astype(np.uint8)
        if len(extract_template_translate_sequences_matrix.shape) == 1:
            extract_template_translate_sequences_matrix = extract_template_translate_sequences_matrix.reshape(1, -1).astype(np.uint8)
        Extract_template_sequences_number = extract_template_translate_sequences_matrix.shape[0]
        translate_check_sequence_mismatch_matrix = np.dot(extract_template_translate_sequences_matrix, translate_check_sequence_matrix)
        translate_complementary_check_sequence_mismatch_matrix = np.dot(extract_template_translate_sequences_matrix, np.flipud(translate_check_sequence_matrix))
        translate_check_sequence_mismatch_matrix = np.maximum(translate_check_sequence_mismatch_matrix, translate_complementary_check_sequence_mismatch_matrix)
        preliminary_matrix = np.nonzero(translate_check_sequence_mismatch_matrix.astype(np.int32) >= (probe_size - allowance))
        preliminary_complementary_matrix = np.nonzero(translate_complementary_check_sequence_mismatch_matrix.astype(np.int32) >= (probe_size - allowance))
        Position_matrix = [list(preliminary_matrix[1][preliminary_matrix[0] == i]) if np.any(preliminary_matrix[0] == i) else [] for i in range(translate_check_sequence_mismatch_matrix.shape[0])]
        Complementary_index = [list(preliminary_complementary_matrix[1][preliminary_complementary_matrix[0] == i]) if np.any(preliminary_complementary_matrix[0] == i) else [] for i in range(translate_complementary_check_sequence_mismatch_matrix.shape[0])]
        Position_matrix = [[pos * (-1) if pos in Complementary_index[i] else pos for pos in Position_matrix[i]] for i in range(len(Position_matrix))]
        del translate_check_sequence_mismatch_matrix, translate_check_sequence_matrix, template_translate_sequences_matrix, translate_complementary_check_sequence_mismatch_matrix
        existing_shm1.close(); existing_shm2.close()
        pbar_information = [(Extract_template_sequences_number / homology_calculation_chunks) * update_factor / Interval_factor, "", int(0)]
        del extract_template_translate_sequences_matrix
        return [pbar_information, Position_matrix, [], []]

def Extracted_Sequences_and_fragment(Combination_input_list, allowance, probe_size):
    """
    Optimize candidate sequences. (private)
    
    """
    input_list = Combination_input_list[0]
    Exclusion_required_sequences = Combination_input_list[1]
    Combination_number = np.prod([len(i) for i in input_list], dtype = np.float64)
    if Combination_number * len(input_list) > 1000000:
        IDX = [[np.argmax([calculate_score(seq, reference) * (1 - calculate_flexibility(seq)) for seq in i.keys()]) for i in input_list] for reference in input_list[-1]]
        Seq_combs = [[list(ip.keys())[id] for ip, id in zip(input_list, ID)] for ID in IDX]
    else:
        Sequence_combinations_list = (tuple(i.keys()) for i in input_list)
        Seq_combs = (Seq_comb for Seq_comb in iter(it.chain.from_iterable([tuple(it.product(*Sequence_combinations_list))])) if (calculate_flexibility(make_wobble(*Seq_comb)[0]) <= allowance / probe_size))
        Seq_combs = [Seq_comb for Seq_comb in Seq_combs if np.logical_not(np.any([set(seqDict.keys()).issubset(set(Seq_comb)) if len(seqDict) > 1 else False for seqDict in input_list]))]
    if len(Seq_combs) == 0:
        return {}
    Frag_combs = [[seqDict[seq] for seqDict, seq in zip(input_list, Seq_comb)] for Seq_comb in Seq_combs]
    Seq_combs = (make_wobble(*Seq_comb)[0] for Seq_comb in Seq_combs)
    if len(Exclusion_required_sequences) > 0:
        Result = {seq: frag for seq, frag in zip(Seq_combs, Frag_combs) if ((calculate_flexibility(seq) <= allowance / probe_size) & (np.sum([calculate_score(seq, Exrseq) == 1 for Exrseq in Exclusion_required_sequences]) == 0))}
    else:
        Result = {seq: frag for seq, frag in zip(Seq_combs, Frag_combs) if (calculate_flexibility(seq) <= allowance / probe_size)}
    return Result

def identify_microorganisms(input, probe_size, size_range, allowance_rate, cut_off_lower, cut_off_upper, interval_distance, Match_rate, CPU = int(1), homology_calculation_chunks = 100, Maximum_annealing_site_number = 10, Window_size = 50, Exclude_sequences_list = {}, Search_mode = "moderate", Search_interval = float(0.5), Exclude_mode = 'fast', withinMemory = True, Allowance_adjustment = True, progress_bar = None):
    """
    Function for generating primer set and fragment size table. (private)
    
    """
    warnings.simplefilter('ignore')
    sequences = []
    name = []
    Start_positions = dict()
    initial_index = 0
    if type(input) is dict:
        for key in input:
            name.append(key); sequences.append(input[key])
    elif (type(input) is list) | (type(input) is tuple):
        sequences = input; name = ["".join(["Sequence", str(i)]) for i in range(1, len(input) + 1)]
    elif (type(input) is str):
        sequences = [input]; name = ["Sequence"]
    elif (type(input) is nucleotide_sequence):
        sequences = [str(input)]; name = ["Sequence"]
    else:
        print("\nInput file should be 'dictionary {name:seq}', 'list [seqs]', 'tuple (seqs,)' or 'str (seq)' including Nucleotide sequence(s)\n")
        sys.exit()
    if len(Exclude_sequences_list) != 0:
        Exclude_name = []
        Exclude_sequences = []
        if type(Exclude_sequences_list) is dict:
            for key in Exclude_sequences_list:
                Exclude_name.append(key); Exclude_sequences.append(Exclude_sequences_list[key])
        elif (type(Exclude_sequences_list) is list) | (type(Exclude_sequences_list) is tuple):
            Exclude_sequences = Exclude_sequences_list; Exclude_name = ["".join(["Sequence", str(i)]) for i in range(1, len(Exclude_sequences_list) + 1)]
        elif (type(Exclude_sequences_list) is str):
            Exclude_sequences = [Exclude_sequences_list]; Exclude_name = ["Sequence"]
        elif (type(Exclude_sequences_list) is nucleotide_sequence):
            Exclude_sequences = [str(Exclude_sequences_list)]; Exclude_name = ["Sequence"]
        exclude_sequences_number = len(Exclude_sequences)
        exclude_sequences_length = [len(seq) for seq in Exclude_sequences]
    encode_table = {"a":'1', "t":'8', "g":'2', "c":'4', "b":'e', "d":'b', "h":'d', "k":'a', "m":'5', "r":'3', "s":'6', "v":'7', "w":'9', "y":'c', "n":'f', "x":'0'}
    encode_table = str.maketrans(encode_table)
    input_sequences_number = len(sequences)
    input_sequences_length = [len(seq) for seq in sequences]
    separation_key = []
    for sequence in sequences:
        sep_pos = []
        pos = 0
        while (len(sep_pos) == 0) | (sequence.lower().find("x", pos + 1) != -1):
            pos = sequence.lower().find("x", pos + 1)
            sep_pos.append(pos)
        sep_pos = sep_pos + [sp * (-1) for sp in sep_pos if sp != -1]
        sep_pos.sort()
        separation_key += [sep_pos]
    if size_range >= 0:
        initial_probe_size = probe_size
    elif size_range < 0:
        initial_probe_size = probe_size + size_range
    for probe_size in range(initial_probe_size, initial_probe_size + abs(size_range) + 1):
        allowance = int(math.ceil(probe_size * allowance_rate))
        split_sequences = []
        translate_sequences = []
        translate_sequences_matrix = []
        for nseq in range(input_sequences_number):
            split_sequence = [sequences[nseq][i:(i + probe_size):] for i in range(input_sequences_length[nseq] - probe_size + 1)]
            split_sequences.append(split_sequence)
            Nbase_count = [str(seq).lower().count("n") > allowance for seq in split_sequence]
            del split_sequence 
            translate_sequences.append(np.array([list('{:04b}'.format(int(n,16))) for n in list(sequences[nseq].lower().translate(encode_table)) if re.sub(r'[0-9a-f]', '', n) == ''], dtype = int).astype(np.uint8))
            translate_sequence_matrix = np.empty(((len(translate_sequences[nseq]) - probe_size + 1), 0), np.uint8)
            for i in range(probe_size - 1):
                translate_sequence_matrix = np.concatenate([translate_sequence_matrix.astype(np.uint8), translate_sequences[nseq][i:(i - probe_size + 1):].astype(np.uint8)], axis = 1)
            translate_sequence_matrix = np.concatenate([translate_sequence_matrix, translate_sequences[nseq][(probe_size - 1)::]], axis = 1).astype(np.uint8)
            translate_sequence_matrix[Nbase_count] = 0
            translate_sequences_matrix.append(translate_sequence_matrix)
            del translate_sequence_matrix
        Position_lists = np.array([])
        if (len(Exclude_sequences_list) != 0) & (str(Exclude_mode).lower() == 'fast'):
            if Search_mode != "exhaustive":
                if Search_mode == 'moderate':
                    Search_interval_updated = int(np.min([int(10), math.floor(probe_size / 3)]))
                elif Search_mode == 'sparse':
                    Search_interval_updated = int(probe_size)
                elif Search_mode == 'manual':
                    Search_interval_updated = np.max([int(1), int(math.floor(probe_size * Search_interval))])
                else:
                    Search_interval_updated = int(1)
                Criteria = np.repeat(False, len(split_sequences[-1]))
                index = np.array(range(initial_index, len(split_sequences[-1]), np.min([Search_interval_updated, len(split_sequences[-1]) - probe_size])))
                Criteria[index] = True
                Interval_factor = len(Criteria) / np.sum(Criteria)
                del index
            else:
                Criteria = np.repeat(True, len(split_sequences[-1])).astype(bool)
                Interval_factor = int(1)
            GPU = True if "cupy" in sys.modules else False
            if GPU:
                if homology_calculation_chunks == "Auto":
                    Test_chunk_size = 100
                    Next_trial = True
                    while Next_trial:
                        try:
                            Template_Vessel = {"Template_Vessel" + str(i): cp.zeros(shape = (probe_size * 4, len(Exclude_sequences[-1]) - probe_size + 1, ), dtype = cp.uint8) for i in range(1, CPU + 1)}
                            Chunk_Vessel = {"Chunk_Vessel" + str(i): cp.zeros(shape = (Test_chunk_size, len(Exclude_sequences[-1]) - probe_size + 1, ), dtype = cp.uint8) for i in range(1, CPU + 1)}
                            Ref_Vessel = {"Ref_Vessel" + str(i): cp.zeros(shape = (Test_chunk_size, probe_size * 4, ), dtype = cp.uint8) for i in range(1, CPU + 1)}
                            Test_chunk_size += 100
                            del Template_Vessel
                            del Chunk_Vessel
                            del Ref_Vessel
                            mempool.free_all_blocks()
                            if Test_chunk_size > np.sum(Criteria):
                                Next_trial = False
                        except:
                            Test_chunk_size = int(round(Test_chunk_size * 0.20, -1))
                            if "Template_Vessel" in locals(): del Template_Vessel
                            if "Chunk_Vessel" in locals(): del Chunk_Vessel
                            if "Ref_Vessel" in locals(): del Ref_Vessel
                            mempool.free_all_blocks()
                            Next_trial = False
                    homology_calculation_chunks_for_exclude = copy.deepcopy(Test_chunk_size)
                    updated_core_number = copy.deepcopy(CPU)
                else:
                    homology_calculation_chunks_for_exclude = int(copy.deepcopy(homology_calculation_chunks))
                    Test_core_number = copy.deepcopy(CPU)
                    Template_Vessel = {}
                    Chunk_Vessel = {}
                    Ref_Vessel = {}
                    try:
                        for core in range(1, Test_core_number + 1):
                            Template_Vessel.update({"Template_Vessel" + str(core): cp.zeros(shape = (int(probe_size * 4 * 4), len(Exclude_sequences[-1]) - probe_size + 1, ), dtype = cp.uint8)})
                            Chunk_Vessel.update({"Chunk_Vessel" + str(core): cp.zeros(shape = (int(homology_calculation_chunks_for_exclude * 4), len(Exclude_sequences[-1]) - probe_size + 1, ), dtype = cp.uint8)})
                            Ref_Vessel.update({"Ref_Vessel" + str(core): cp.zeros(shape = (int(homology_calculation_chunks_for_exclude * 4), int(probe_size * 4 * 4), ), dtype = cp.uint8)})
                        updated_core_number = int(core)
                    except:
                        updated_core_number = int(np.max([1, core - 1]))
                    del Template_Vessel, Chunk_Vessel, Ref_Vessel
                mempool.free_all_blocks()
            else:
                Available_memory = psutil.virtual_memory().available
                Vessel = np.zeros(shape = (probe_size * 4, len(Exclude_sequences[-1]) - probe_size + 1, ), dtype = np.uint8)
                Occupied_memory = Vessel.nbytes
                if homology_calculation_chunks == "Auto":
                    homology_calculation_chunks_for_exclude = int(np.min([1000, np.max([1, math.floor(((Available_memory * 0.5 / CPU - Occupied_memory * 2) / (Occupied_memory / (probe_size * 4))) / 5)])]))
                    updated_core_number = int(copy.deepcopy(CPU))
                else:
                    homology_calculation_chunks_for_exclude = int(copy.deepcopy(homology_calculation_chunks))
                    updated_core_number = int(np.max([1, np.min([CPU, math.floor(Available_memory / ((Occupied_memory / (probe_size * 4) * homology_calculation_chunks_for_exclude + Occupied_memory) * 5))])]))
                del Vessel
            Total_matrix_calculation = translate_sequences_matrix[-1].shape[0] / homology_calculation_chunks_for_exclude * len(Exclude_sequences_list)
            if progress_bar is not None: progress_bar.update(1)
            with tqdm(total = Total_matrix_calculation / Interval_factor, leave = False, position = 1, unit = "tasks", unit_scale = True, desc = "    Filter valid candidates based on Exclude sequences", bar_format = "{desc}: {percentage:.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}  {rate_fmt}]", smoothing = 0) as pbar:
                def Exclude_range_progressbar_update(Result):
                    pbar.update(Result[0][0])
                for neseq in range(len(Exclude_sequences)):
                    split_exclude_sequence = [Exclude_sequences[neseq][i:(i + probe_size):] for i in range(len(Exclude_sequences[neseq]) - probe_size + 1)]
                    Nbase_count = [str(seq).lower().count("n") > allowance for seq in split_exclude_sequence]
                    del split_exclude_sequence
                    translate_exclude_sequence = np.array([list('{:04b}'.format(int(n,16))) for n in list(Exclude_sequences[neseq].lower().translate(encode_table)) if re.sub(r'[0-9a-f]', '', n) == ''], dtype = int).astype(np.uint8)
                    translate_exclude_sequence_matrix = np.empty(((len(translate_exclude_sequence) - probe_size + 1), 0), np.uint8)
                    for i in range(probe_size - 1):
                        translate_exclude_sequence_matrix = np.concatenate([translate_exclude_sequence_matrix.astype(np.uint8), translate_exclude_sequence[i:(i - probe_size + 1):].astype(np.uint8)], axis = 1)
                    translate_exclude_sequence_matrix = np.concatenate([translate_exclude_sequence_matrix, translate_exclude_sequence[(probe_size - 1)::]], axis = 1).astype(np.uint8)
                    translate_exclude_sequence_matrix[Nbase_count] = 0
                    del Nbase_count
                    Criterion = []
                    translate_exclude_sequence_matrix = (translate_exclude_sequence_matrix.T).astype(np.uint8)
                    template_translate_sequences_matrix = (translate_sequences_matrix[-1])[Criteria]
                    Chunks_Start_positions = list(range(0, template_translate_sequences_matrix.shape[0], homology_calculation_chunks_for_exclude))
                    shm1 = SharedMemory(create = True, size = translate_exclude_sequence_matrix.nbytes)
                    Shared_translate_sequence_matrix = np.ndarray(shape = translate_exclude_sequence_matrix.shape, dtype = translate_exclude_sequence_matrix.dtype, buffer = shm1.buf)
                    Shared_translate_sequence_matrix[:] = translate_exclude_sequence_matrix[:]
                    shm2 = SharedMemory(create = True, size = template_translate_sequences_matrix.nbytes)
                    Shared_template_translate_sequences_matrix = np.ndarray(shape = template_translate_sequences_matrix.shape, dtype = template_translate_sequences_matrix.dtype, buffer = shm2.buf)
                    Shared_template_translate_sequences_matrix[:] = template_translate_sequences_matrix[:]
                    share_informations = ((shm1.name, translate_exclude_sequence_matrix.shape, translate_exclude_sequence_matrix.dtype, ), (shm2.name, template_translate_sequences_matrix.shape, template_translate_sequences_matrix.dtype, ), ("", ), ("", ))
                    update_factor = (len(translate_sequences_matrix[-1])/len(template_translate_sequences_matrix))
                    parameter = { \
                        'homology_calculation_chunks': homology_calculation_chunks_for_exclude, \
                        'share_informations': share_informations, \
                        'probe_size': probe_size, \
                        'allowance': allowance, \
                        'Mode': "Exclude", \
                        'GPU': GPU, \
                        'Allowance_adjustment': Allowance_adjustment, \
                        'input_sequences_length': exclude_sequences_length[neseq], \
                        'interval_distance': interval_distance, \
                        'Maximum_annealing_site_number': Maximum_annealing_site_number, \
                        'Annealing_site_number_threshold': 10, \
                        'update_factor': update_factor, \
                        'Interval_factor': Interval_factor \
                    }
                    multi_homology_calculation = partial(homology_calculation, parameter = parameter)
                    with get_context("spawn").Pool(processes = updated_core_number, initializer = init_worker) as pl:
                        try:
                            outputs = [pl.apply_async(multi_homology_calculation, args = (csp, ), callback = Exclude_range_progressbar_update) for csp in Chunks_Start_positions]
                            outputs = [output.get() for output in outputs]
                        except KeyboardInterrupt:
                            pl.terminate()
                            pl.join()
                            pl.close()
                            print("\n\n --- Keyboard Interrupt ---")
                            sys.exit()
                    [Criterion.extend(output[1]) for output in outputs] 
                    Criterion = np.array(Criterion).astype(bool)
                    Criteria[np.nonzero(Criteria)[0][np.nonzero(~Criterion)[0]]] = False
                    del Shared_translate_sequence_matrix, Shared_template_translate_sequences_matrix, share_informations
                    shm1.close(); shm2.close()
                    shm1.unlink(); shm2.unlink()
                    del translate_exclude_sequence_matrix, template_translate_sequences_matrix, translate_exclude_sequence, Criterion
                    if not np.any(Criteria):
                        pbar.update(pbar.total - pbar.n)
                        break
            del Exclude_range_progressbar_update
            Interval_factor = len(Criteria) / np.sum(Criteria)
        else:
            if Search_mode != "exhaustive":
                if Search_mode == 'moderate':
                    Search_interval_updated = int(np.min([int(10), math.floor(probe_size / 3)]))
                elif Search_mode == 'sparse':
                    Search_interval_updated = int(probe_size)
                elif Search_mode == 'manual':
                    Search_interval_updated = np.max([int(1), int(math.floor(probe_size * Search_interval))])
                else:
                    Search_interval_updated = int(1)
                Criteria = np.repeat(False, len(split_sequences[-1]))
                index = np.array(range(initial_index, len(split_sequences[-1]), np.min([Search_interval_updated, len(split_sequences[-1]) - probe_size])))
                Criteria[index] = True
                Interval_factor = len(Criteria) / np.sum(Criteria)
                del index
            else:
                Criteria = np.repeat(True, len(split_sequences[-1])).astype(bool)
                Interval_factor = int(1)
        if not np.any(Criteria):
            continue
        Exclusion_required_sequences = [[] for n in range(len(split_sequences[-1]))]
        GPU = True if "cupy" in sys.modules else False
        if GPU:
            if homology_calculation_chunks == "Auto":
                Test_chunk_size = 100
                Next_trial = True
                while Next_trial:
                    try:
                        Template_Vessel = {"Template_Vessel" + str(i): cp.zeros(shape = (probe_size * 4, len(sequences[-2]) - probe_size + 1, ), dtype = cp.uint8) for i in range(1, CPU + 1)}
                        Chunk_Vessel = {"Chunk_Vessel" + str(i): cp.zeros(shape = (Test_chunk_size, len(sequences[-2]) - probe_size + 1, ), dtype = cp.uint8) for i in range(1, CPU + 1)}
                        Ref_Vessel = {"Ref_Vessel" + str(i): cp.zeros(shape = (Test_chunk_size, probe_size * 4, ), dtype = cp.uint8) for i in range(1, CPU + 1)}
                        Test_chunk_size += 100
                        del Template_Vessel
                        del Chunk_Vessel
                        del Ref_Vessel
                        mempool.free_all_blocks()
                        if Test_chunk_size > np.sum(Criteria):
                            Next_trial = False
                    except:
                        Test_chunk_size = int(round(Test_chunk_size * 0.20, -1))
                        if "Template_Vessel" in locals(): del Template_Vessel
                        if "Chunk_Vessel" in locals(): del Chunk_Vessel
                        if "Ref_Vessel" in locals(): del Ref_Vessel
                        mempool.free_all_blocks()
                        Next_trial = False
                homology_calculation_chunks_for_explore = copy.deepcopy(Test_chunk_size)
                updated_core_number = copy.deepcopy(CPU)
            else:
                homology_calculation_chunks_for_explore = int(copy.deepcopy(homology_calculation_chunks))
                Test_core_number = copy.deepcopy(CPU)
                Template_Vessel = {}
                Chunk_Vessel = {}
                Ref_Vessel = {}
                try:
                    for core in range(1, Test_core_number + 1):
                        Template_Vessel.update({"Template_Vessel" + str(core): cp.zeros(shape = (int(probe_size * 4 * 4), len(sequences[-2]) - probe_size + 1, ), dtype = cp.uint8)})
                        Chunk_Vessel.update({"Chunk_Vessel" + str(core): cp.zeros(shape = (int(homology_calculation_chunks_for_explore * 4), len(sequences[-2]) - probe_size + 1, ), dtype = cp.uint8)})
                        Ref_Vessel.update({"Ref_Vessel" + str(core): cp.zeros(shape = (int(homology_calculation_chunks_for_explore * 4), int(probe_size * 4 * 4), ), dtype = cp.uint8)})
                    updated_core_number = int(core)
                except:
                    updated_core_number = int(np.max([1, core - 1]))
                del Template_Vessel, Chunk_Vessel, Ref_Vessel
            mempool.free_all_blocks()
        else:
            Available_memory = psutil.virtual_memory().available
            Vessel = np.zeros(shape = (probe_size * 4, len(sequences[-2]) - probe_size + 1, ), dtype = np.uint8)
            Occupied_memory = Vessel.nbytes
            if homology_calculation_chunks == "Auto":
                homology_calculation_chunks_for_explore = int(np.min([1000, np.max([1, math.floor(((Available_memory * 0.5 / CPU - Occupied_memory * 2) / (Occupied_memory / (probe_size * 4))) / 5)])]))
                updated_core_number = int(copy.deepcopy(CPU))
            else:
                homology_calculation_chunks_for_explore = int(copy.deepcopy(homology_calculation_chunks))
                updated_core_number = int(np.max([1, np.min([CPU, math.floor(Available_memory / ((Occupied_memory / (probe_size * 4) * homology_calculation_chunks_for_explore + Occupied_memory) * 5))])]))
            del Vessel
        homology_calculation_chunks_for_check = int(copy.deepcopy(homology_calculation_chunks_for_explore))
        updated_core_number_for_check = int(copy.deepcopy(updated_core_number))
        Total_matrix_calculation = translate_sequences_matrix[-1].shape[0] / homology_calculation_chunks_for_explore * input_sequences_number
        if progress_bar is not None: progress_bar.update(1)
        with tqdm(total = Total_matrix_calculation / Interval_factor, leave = False, position = 1, unit = "tasks", unit_scale = True, desc = "    Homology calculation ({0}/{1})".format((input_sequences_number + 1) * (probe_size - initial_probe_size) + 1, (size_range + 1) * (input_sequences_number + 1)), bar_format = "{desc}: {percentage:.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}  {rate_fmt}{postfix}]", smoothing = 0) as pbar:
            def Explore_progressbar_update(Result):
                pbar.set_postfix({"Processor": Result[0][1], "Optimized_allowance": Result[0][2], "Ave.ann.site":Result[0][3]})
                pbar.update(Result[0][0])
            for n in range(input_sequences_number):
                Position_list = []
                Criterion = []
                Exclusion_required_sequences_in_loop = []
                translate_sequence_matrix = (translate_sequences_matrix[n].T).astype(np.uint8)
                template_translate_sequences_matrix = (translate_sequences_matrix[-1])[Criteria].astype(np.uint8)
                Cumulative_valid_index = np.zeros(shape = (template_translate_sequences_matrix.shape[0], ), dtype = np.uint32)
                Chunks_Start_positions = list(range(0, template_translate_sequences_matrix.shape[0], homology_calculation_chunks_for_explore))
                shm1 = SharedMemory(create = True, size = translate_sequence_matrix.nbytes)
                Shared_translate_sequence_matrix = np.ndarray(shape = translate_sequence_matrix.shape, dtype = translate_sequence_matrix.dtype, buffer = shm1.buf)
                Shared_translate_sequence_matrix[:] = translate_sequence_matrix[:]
                shm2 = SharedMemory(create = True, size = template_translate_sequences_matrix.nbytes)
                Shared_template_translate_sequences_matrix = np.ndarray(shape = template_translate_sequences_matrix.shape, dtype = template_translate_sequences_matrix.dtype, buffer = shm2.buf)
                Shared_template_translate_sequences_matrix[:] = template_translate_sequences_matrix[:]
                Sequence = np.array([sequences[n]])
                shm3 = SharedMemory(create = True, size = Sequence.nbytes)
                Shared_Sequence = np.ndarray(shape = Sequence.shape, dtype = Sequence.dtype, buffer = shm3.buf)
                Shared_Sequence[:] = Sequence[:]
                shm4 = SharedMemory(create = True, size = Cumulative_valid_index.nbytes)
                Shared_Cumulative_valid_index = np.ndarray(shape = Cumulative_valid_index.shape, dtype = Cumulative_valid_index.dtype, buffer = shm4.buf)
                Shared_Cumulative_valid_index[:] = Cumulative_valid_index[:]
                Shared_Allowance_list = ShareableList([-100 for i in range(len(Chunks_Start_positions) + 1)])
                Shared_Allowance_list[0] = copy.deepcopy(allowance)
                share_informations = [(shm1.name, translate_sequence_matrix.shape, translate_sequence_matrix.dtype, ), (shm2.name, template_translate_sequences_matrix.shape, template_translate_sequences_matrix.dtype, ), (shm3.name, Sequence.shape, Sequence.dtype, ), (shm4.name, Cumulative_valid_index.shape, Cumulative_valid_index.dtype, ), (Shared_Allowance_list.shm.name, )]
                update_factor = (len(translate_sequences_matrix[-1])/len(template_translate_sequences_matrix))
                parameter = { \
                    'homology_calculation_chunks': homology_calculation_chunks_for_explore, \
                    'share_informations': share_informations, \
                    'probe_size': probe_size, \
                    'allowance': allowance, \
                    'Mode': "Explore", \
                    'GPU': GPU, \
                    'Allowance_adjustment': Allowance_adjustment, \
                    'input_sequences_length': input_sequences_length[n], \
                    'interval_distance': interval_distance, \
                    'Maximum_annealing_site_number': Maximum_annealing_site_number, \
                    'Annealing_site_number_threshold': 10, \
                    'update_factor': update_factor, \
                    'Interval_factor': Interval_factor \
                }
                multi_homology_calculation = partial(homology_calculation, parameter = parameter)
                with get_context("spawn").Pool(processes = updated_core_number, initializer = init_worker) as pl:
                    try:
                        outputs = [pl.apply_async(multi_homology_calculation, args = (csp, ), callback = Explore_progressbar_update) for csp in Chunks_Start_positions]
                        outputs = [output.get() for output in outputs]
                    except KeyboardInterrupt:
                        pl.terminate()
                        pl.join()
                        pl.close()
                        print("\n\n --- Keyboard Interrupt ---")
                        sys.exit()
                [Criterion.extend(output[1]) for output in outputs]
                [Position_list.extend(output[2]) for output in outputs]
                [Exclusion_required_sequences_in_loop.extend(output[3]) for output in outputs]
                [Exclusion_required_sequences[j].extend(Exclusion_required_sequences_in_loop[i]) for i, j in enumerate([j for j in range(len(Criteria)) if Criteria[j]])]
                Exclusion_required_sequences = [list(set(Exclusion_required_sequence)) for Exclusion_required_sequence in Exclusion_required_sequences]
                Criterion = np.array(Criterion).astype(bool)
                Criteria[np.nonzero(Criteria)[0][np.nonzero(~Criterion)[0]]] = False
                if len(Position_lists) == 0:
                    Position_lists = np.array(Position_list + [None], dtype = object)[:-1]
                    Position_lists = Position_lists.reshape(1, -1)
                else:
                    Position_list = np.array(Position_list + [None], dtype = object)[:-1]
                    Position_list = Position_list.reshape(1, -1)
                    Position_lists = np.append(Position_lists, Position_list, axis = 0)
                Position_lists = Position_lists[:, Criterion]
                del Shared_translate_sequence_matrix, Shared_template_translate_sequences_matrix, Shared_Sequence, Shared_Cumulative_valid_index, share_informations
                shm1.close(); shm2.close(); shm3.close(); shm4.close(); Shared_Allowance_list.shm.close()
                shm1.unlink(); shm2.unlink(); shm3.unlink(); shm4.unlink(); Shared_Allowance_list.shm.unlink()
                del translate_sequence_matrix, template_translate_sequences_matrix, Sequence, Cumulative_valid_index, Chunks_Start_positions, Criterion
                if not np.any(Criteria):
                    pbar.update(pbar.total - pbar.n)
                    break
        del Explore_progressbar_update
        if not np.any(Criteria):
            continue
        Filtered_split_sequences = np.array(split_sequences[-1])[Criteria]
        Exclusion_required_sequences = np.array(Exclusion_required_sequences, dtype = object)[Criteria]
        Storage = psutil.disk_usage('/')
        if (Position_lists.nbytes > Storage.free * 0.8) | withinMemory:
            Filtered_position_lists = Position_lists.tolist()
            del Position_lists, split_sequences
            outputs_list = np.array([])
            Criteria = np.repeat(True, len(Filtered_split_sequences)).astype(bool)
            for i in range(input_sequences_number):
                Combs = zip(Filtered_split_sequences[Criteria], np.array(Filtered_position_lists[i], dtype = object)[Criteria])
                Total_combination_length = len(Filtered_split_sequences[Criteria])
                Each_filtered_position_list_length = np.array([len(Ps) for Ps in Filtered_position_lists[i]])
                Data_size_estimation_factor = np.sum([np.sum([comb(Ps_length_range, Ps_length) * np.count_nonzero(Each_filtered_position_list_length == Ps_length_range) for Ps_length in range(1, Ps_length_range + 1)]) for Ps_length_range in range(1, np.min([15, np.max(Each_filtered_position_list_length)]) + 1)]) / np.sum(Each_filtered_position_list_length[Each_filtered_position_list_length <= 15])
                updated_core_number = int(copy.deepcopy(CPU))
                while ((sys.getsizeof(Filtered_split_sequences[Criteria]) + sys.getsizeof(np.array(Filtered_position_lists[i], dtype = object)[Criteria])) * Data_size_estimation_factor * updated_core_number > psutil.virtual_memory().available * 0.75) & (updated_core_number > 1):
                    updated_core_number = int(updated_core_number - 1)
                if progress_bar is not None: progress_bar.update(1)
                if updated_core_number == 1:
                    outputs = [search_position(comb, evaluating_sequence = "", input_sequence = sequences[i], allowance = allowance, interval_distance = interval_distance, Position_list = np.array([]), Match_rate = Match_rate, Maximum_annealing_site_number = Maximum_annealing_site_number, IgnoreLowQualityRegion = False) for comb in tqdm(Combs, total = Total_combination_length, leave = False, position = 1, unit = "tasks", unit_scale = True, desc = "    Homology calculation ({0}/{1})".format((input_sequences_number + 1) * (probe_size - initial_probe_size) + 2 + i, (size_range + 1) * (input_sequences_number + 1)), bar_format = "{desc}: {percentage:.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}  {rate_fmt}]", smoothing = 0)]
                else:
                    with get_context("spawn").Pool(processes = updated_core_number, initializer = init_worker) as pl:
                        try:
                            outputs = list(tqdm(pl.imap(partial(search_position, evaluating_sequence = "", input_sequence = sequences[i], allowance = allowance, interval_distance = interval_distance, Position_list = np.array([]), Match_rate = Match_rate, Maximum_annealing_site_number = Maximum_annealing_site_number, IgnoreLowQualityRegion = False), Combs), total = Total_combination_length, leave = False, position = 1, unit = "tasks", unit_scale = True, desc = "    Homology calculation ({0}/{1})".format((input_sequences_number + 1) * (probe_size - initial_probe_size) + 2 + i, (size_range + 1) * (input_sequences_number + 1)), bar_format = "{desc}: {percentage:.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}  {rate_fmt}]", smoothing = 0))
                        except KeyboardInterrupt:
                            pl.terminate()
                            pl.join()
                            pl.close()
                            print("\n\n --- Keyboard Interrupt ---")
                            sys.exit()
                if len(outputs_list) == 0:
                    outputs_list = np.array(outputs).reshape(1, len(outputs))
                else:
                    outputs_list = np.append(outputs_list, np.array(outputs).reshape(1, len(outputs)), axis = 0)
                Criterion = np.array([output is not None for output in outputs]).astype(bool)
                outputs_list = outputs_list[:, Criterion]
                Criteria[np.nonzero(Criteria)[0][np.nonzero(~Criterion)[0]]] = False
        else:
            with tempfile.TemporaryDirectory() as tmp:
                dumpfilenumber = len(Position_lists)
                for i in range(dumpfilenumber):
                    np.save(os.path.join(tmp, 'dumpfile'+str(i + 1)+'.npy'), Position_lists[i])
                del Position_lists, split_sequences
                outputs_list = np.array([])
                Criteria = np.repeat(True, len(Filtered_split_sequences)).astype(bool)
                for i in range(dumpfilenumber):
                    Filtered_position_list = np.load(os.path.join(tmp, 'dumpfile'+str(i + 1)+'.npy'), allow_pickle=True).tolist()
                    Combs = zip(Filtered_split_sequences[Criteria], np.array(Filtered_position_list, dtype = object)[Criteria])
                    Total_combination_length = len(Filtered_split_sequences[Criteria])
                    Each_filtered_position_list_length = np.array([len(Ps) for Ps in Filtered_position_list])
                    Data_size_estimation_factor = np.sum([np.sum([comb(Ps_length_range, Ps_length) * np.count_nonzero(Each_filtered_position_list_length == Ps_length_range) for Ps_length in range(1, Ps_length_range + 1)]) for Ps_length_range in range(1, np.min([15, np.max(Each_filtered_position_list_length)]) + 1)]) / np.sum(Each_filtered_position_list_length[Each_filtered_position_list_length <= 15])
                    updated_core_number = int(copy.deepcopy(CPU))
                    while ((sys.getsizeof(Filtered_split_sequences[Criteria]) + sys.getsizeof(np.array(Filtered_position_list, dtype = object)[Criteria])) * Data_size_estimation_factor * updated_core_number > psutil.virtual_memory().available * 0.75) & (updated_core_number > 1):
                        updated_core_number = int(updated_core_number - 1)
                    if progress_bar is not None: progress_bar.update(1)
                    if updated_core_number == 1:
                        outputs = [search_position(comb, evaluating_sequence = "", input_sequence = sequences[i], allowance = allowance, interval_distance = interval_distance, Position_list = np.array([]), Match_rate = Match_rate, Maximum_annealing_site_number = Maximum_annealing_site_number, IgnoreLowQualityRegion = False) for comb in tqdm(Combs, total = Total_combination_length, leave = False, position = 1, unit = "tasks", unit_scale = True, desc = "    Homology calculation ({0}/{1})".format((input_sequences_number + 1) * (probe_size - initial_probe_size) + 2 + i, (size_range + 1) * (input_sequences_number + 1)), bar_format = "{desc}: {percentage:.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}  {rate_fmt}]", smoothing = 0)]
                    else:
                        with get_context("spawn").Pool(processes = updated_core_number, initializer = init_worker) as pl:
                            try:
                                outputs = list(tqdm(pl.imap(partial(search_position, evaluating_sequence = "", input_sequence = sequences[i], allowance = allowance, interval_distance = interval_distance, Position_list = np.array([]), Match_rate = Match_rate, Maximum_annealing_site_number = Maximum_annealing_site_number, IgnoreLowQualityRegion = False), Combs), total = Total_combination_length, leave = False, position = 1, unit = "tasks", unit_scale = True, desc = "    Homology calculation ({0}/{1})".format((input_sequences_number + 1) * (probe_size - initial_probe_size) + 2 + i, (size_range + 1) * (input_sequences_number + 1)), bar_format = "{desc}: {percentage:.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}  {rate_fmt}]", smoothing = 0))
                            except KeyboardInterrupt:
                                pl.terminate()
                                pl.join()
                                pl.close()
                                print("\n\n --- Keyboard Interrupt ---")
                                sys.exit()
                    if len(outputs_list) == 0:
                        outputs_list = np.array(outputs).reshape(1, len(outputs))
                    else:
                        outputs_list = np.append(outputs_list, np.array(outputs).reshape(1, len(outputs)), axis = 0)
                    Criterion = np.array([output is not None for output in outputs]).astype(bool)
                    outputs_list = outputs_list[:, Criterion]
                    Criteria[np.nonzero(Criteria)[0][np.nonzero(~Criterion)[0]]] = False
        if not np.any(Criteria):
            continue
        Exclusion_required_sequences = Exclusion_required_sequences[Criteria]
        if progress_bar is not None: progress_bar.update(1)
        with get_context("spawn").Pool(processes = CPU, initializer = init_worker) as pl:
            try:
                Combs = ((outputs_list[:, n], Exclusion_required_sequences[n], ) for n in range(outputs_list.shape[1]))
                outputs = list(tqdm(pl.imap(partial(Extracted_Sequences_and_fragment, allowance = allowance, probe_size = probe_size), Combs) , total = outputs_list.shape[1], leave = False, position = 1, unit = "tasks", unit_scale = True, desc = "    Making degenerate primer", bar_format = "{desc}: {percentage:.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}  {rate_fmt}]", smoothing = 0))
            except KeyboardInterrupt:
                pl.terminate()
                pl.join()
                pl.close()
                print("\n\n --- Keyboard Interrupt ---")
                sys.exit()
        [[Start_positions.update({k:tuple([np.array(sorted(list(set(output[k][j].tolist() + v[j].tolist())), key = abs), dtype = object) for j in range(len(v))])}) if k in output.keys() else output.update({k:v}) for k, v in output.items()] for output in outputs]
        initial_index += 1
    if len(Start_positions) == 0:
        print("\nThere was no primer set that meets input conditions. Please change probe size or allowance value.\n")
        sys.exit()
    Melted_df_Start_positions_set = pd.DataFrame()
    for no in range(input_sequences_number - 1, -1, -1):
        frag_size = [Start_positions[key][no] for key in Start_positions]
        df_Start_positions = pd.DataFrame(frag_size).assign(Sequence = Start_positions.keys(), Fragment = frag_size)
        Melted_df_Start_positions = (pd.melt(df_Start_positions, id_vars = ["Sequence", 'Fragment'], var_name = "Position_number", value_name = "Position").dropna())
        Melted_df_Start_positions = Melted_df_Start_positions.iloc[Melted_df_Start_positions['Position'].abs().argsort()].reset_index(drop = True)
        Melted_df_Start_positions.index = Melted_df_Start_positions['Sequence'].astype(str).str.cat(Melted_df_Start_positions['Position_number'].astype(str), sep = '_')
        if len(Melted_df_Start_positions_set) == 0:
            Melted_df_Start_positions_set = pd.concat([Melted_df_Start_positions_set, Melted_df_Start_positions['Position']], axis = 1)
        Melted_df_Start_positions = Melted_df_Start_positions['Fragment']
        Melted_df_Start_positions_set = pd.concat([Melted_df_Start_positions_set, Melted_df_Start_positions], axis = 1)
    Sequence_name = [re.sub(r'_\d+', '', name) for name in Melted_df_Start_positions_set.index]
    Melted_df_Start_positions_set.insert(1, 'Sequence', Sequence_name)
    Melted_df_Start_positions_set = Melted_df_Start_positions_set[np.logical_not(Melted_df_Start_positions_set['Sequence'].map(lambda x:x.upper().find("X") >= 0))]
    del df_Start_positions, Sequence_name
    Maximum_candidate_length = np.max([probe_size, np.max([len(sequence) for sequence in Melted_df_Start_positions_set['Sequence']])])
    Index_candidate = [sequence + "".join(['N' for i in range(Maximum_candidate_length - len(sequence))]) if len(sequence) < Maximum_candidate_length else sequence for sequence in Melted_df_Start_positions_set['Sequence']]
    translate_candidate_matrix = np.array([np.ravel(np.array([list('{:04b}'.format(int(n,16))) for n in list(candidate.lower().translate(encode_table)) if re.sub(r'[0-9a-f]', '', n) == ''], dtype = int)) for candidate in Index_candidate], dtype = int).astype(np.uint8)
    Criteria = np.repeat(True, Melted_df_Start_positions_set.shape[0])
    Total_matrix_calculation = Melted_df_Start_positions_set.shape[0] / homology_calculation_chunks_for_check * input_sequences_number
    if progress_bar is not None: progress_bar.update(1)
    with tqdm(total = Total_matrix_calculation, leave = False, position = 1, unit = "tasks", unit_scale = True, desc = "    Check candidate primers", bar_format = "{desc}: {percentage:.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}  {rate_fmt}]", smoothing = 0) as pbar:
        def Check_progressbar_update(Result):
            pbar.update(Result[0][0])
        for nseq in range(input_sequences_number):
            Position_matrix = []
            translate_sequence_matrix = translate_sequences_matrix[nseq]
            template_translate_candidate_matrix = (translate_candidate_matrix)[Criteria]
            translate_sequence_matrix = (translate_sequence_matrix.T).astype(np.uint8)
            Chunks_Start_positions = list(range(0, template_translate_candidate_matrix.shape[0], homology_calculation_chunks_for_check))
            shm1 = SharedMemory(create = True, size = translate_sequence_matrix.nbytes)
            Shared_translate_sequence_matrix = np.ndarray(shape = translate_sequence_matrix.shape, dtype = translate_sequence_matrix.dtype, buffer = shm1.buf)
            Shared_translate_sequence_matrix[:] = translate_sequence_matrix[:]
            shm2 = SharedMemory(create = True, size = template_translate_candidate_matrix.nbytes)
            Shared_template_translate_sequences_matrix = np.ndarray(shape = template_translate_candidate_matrix.shape, dtype = template_translate_candidate_matrix.dtype, buffer = shm2.buf)
            Shared_template_translate_sequences_matrix[:] = template_translate_candidate_matrix[:]
            share_informations = ((shm1.name, translate_sequence_matrix.shape, translate_sequence_matrix.dtype, ), (shm2.name, template_translate_candidate_matrix.shape, template_translate_candidate_matrix.dtype, ), ("", ), ("", ))
            update_factor = (Melted_df_Start_positions_set.shape[0] / len(template_translate_candidate_matrix))
            parameter = { \
                'homology_calculation_chunks': homology_calculation_chunks_for_check, \
                'share_informations': share_informations, \
                'probe_size': Maximum_candidate_length, \
                'allowance': int(0), \
                'Mode': "Check", \
                'GPU': GPU, \
                'Allowance_adjustment': False, \
                'input_sequences_length': input_sequences_length[nseq], \
                'interval_distance': interval_distance, \
                'Maximum_annealing_site_number': input_sequences_length[nseq], \
                'Annealing_site_number_threshold': input_sequences_length[nseq], \
                'update_factor': update_factor, \
                'Interval_factor': int(1) \
            }
            multi_homology_calculation = partial(homology_calculation, parameter = parameter)
            with get_context("spawn").Pool(processes = updated_core_number, initializer = init_worker) as pl:
                try:
                    outputs = [pl.apply_async(multi_homology_calculation, args = (csp, ), callback = Check_progressbar_update) for csp in Chunks_Start_positions]
                    outputs = [output.get() for output in outputs]
                except KeyboardInterrupt:
                    pl.terminate()
                    pl.join()
                    pl.close()
                    print("\n\n --- Keyboard Interrupt ---")
                    sys.exit()
            [Position_matrix.extend(output[1]) for output in outputs]
            Criterion = np.array([set(checkposition) == set(testposition) if np.all([np.all(pd.notna(checkposition)), np.all(pd.notna(testposition))]) else True for checkposition, testposition in zip(Position_matrix, Melted_df_Start_positions_set[Criteria].iloc[:, (-1) * (nseq + 1)])]).astype(bool)
            Criteria[np.nonzero(Criteria)[0][np.nonzero(~Criterion)[0]]] = False
            del Shared_translate_sequence_matrix, Shared_template_translate_sequences_matrix, share_informations
            shm1.close(); shm2.close()
            shm1.unlink(); shm2.unlink()
            del translate_sequence_matrix, Criterion
            if not np.any(Criteria):
                print("\nThere was no primer set that meets input conditions.\n")
                sys.exit()
    Melted_df_Start_positions_set = Melted_df_Start_positions_set[Criteria]
    del Check_progressbar_update, translate_sequences_matrix, template_translate_candidate_matrix, Criteria, Index_candidate, Maximum_candidate_length
    if size_range != 0:
        Flexibility = [calculate_flexibility(seq) for seq in Melted_df_Start_positions_set['Sequence']]
        Sequence_Length = [len(seq) for seq in Melted_df_Start_positions_set['Sequence']]
        Melted_df_Start_positions_set.insert(2, 'Flexibility', Flexibility)
        Melted_df_Start_positions_set.insert(3, 'Sequence_Length', Sequence_Length)
        Melted_df_Start_positions_set = Melted_df_Start_positions_set.sort_values(['Flexibility', 'Sequence_Length'], ascending = [True, False])
        Melted_df_Start_positions_set = Melted_df_Start_positions_set[np.logical_not((Melted_df_Start_positions_set.iloc[:, 4:].map(lambda x:str(x))).duplicated())] if Pandas_later_210 else Melted_df_Start_positions_set[np.logical_not((Melted_df_Start_positions_set.iloc[:, 4:].applymap(lambda x:str(x))).duplicated())]
        Melted_df_Start_positions_set = Melted_df_Start_positions_set.iloc[Melted_df_Start_positions_set['Position'].abs().argsort()]
        Melted_df_Start_positions_set = Melted_df_Start_positions_set.drop(['Flexibility', 'Sequence_Length'], axis = 1)
    if Window_size >= 3:
        Criteria = np.array([], dtype = bool)
        Criterion1 = ((Melted_df_Start_positions_set.index.duplicated(keep = False)) | (Melted_df_Start_positions_set.index.map(calculate_flexibility) <= (allowance / probe_size * 0.2)))
        for i in range(math.ceil(Melted_df_Start_positions_set.shape[0]/Window_size)):
            Extraceted_dataframe = Melted_df_Start_positions_set.iloc[i*Window_size:(i + 1)*Window_size:, 2:]
            Extraceted_dataframe = Extraceted_dataframe.apply(lambda x:str(np.diff(list(it.chain.from_iterable(x.dropna())))), axis = 1)
            Criterion2 = np.logical_not((Extraceted_dataframe.duplicated(keep = 'first') & Extraceted_dataframe.duplicated(keep = 'last')))
            Criteria = np.append(Criteria, np.array(Criterion1[i*Window_size:(i + 1)*Window_size:] | Criterion2))
        if np.sum(Criteria) == 0:
            print("\nThere was no primer set that meets input conditions. Please change probe size or allowance value.\n")
            sys.exit()
        remain_sequences = set(Melted_df_Start_positions_set[Criteria]['Sequence'])
        Criteria = [((set([Melted_df_Start_positions_set.iloc[i]['Sequence']]) <= remain_sequences) | Criteria[i]) for i in range(Melted_df_Start_positions_set.shape[0])]
        Melted_df_Start_positions_set = Melted_df_Start_positions_set[Criteria]
    if progress_bar is not None: progress_bar.update(1)
    with Pool(processes = CPU, initializer = init_worker) as pl:
        try:
            outputs = list(pl.imap(partial(make_primer_set_and_amplicon_size, df = Melted_df_Start_positions_set, cut_off_lower = cut_off_lower, cut_off_upper = cut_off_upper, separation_key = separation_key[::-1]), tqdm(range(Melted_df_Start_positions_set.shape[0]-1), total = Melted_df_Start_positions_set.shape[0]-1, leave = False, position = 1, unit = "tasks", unit_scale = True, desc = "    Making primer set", smoothing = 0)))
        except KeyboardInterrupt:
            pl.terminate()
            pl.join()
            pl.close()
            print("\n\n --- Keyboard Interrupt ---")
            sys.exit()
    if progress_bar is not None: progress_bar.update(1)
    outputs = [output for output in tqdm(outputs, desc = "    Trimming data", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0) if output is not None]
    outputs = list(it.chain.from_iterable(outputs))
    Start_positions_dict = dict()
    if progress_bar is not None: progress_bar.update(1)
    [Start_positions_dict.update({key:[[tuple(exist)] + [tuple(add)] if type(exist[0]) is not tuple else exist + [tuple(add)] for exist, add in zip(Start_positions_dict[key], value)]}) if (key in Start_positions_dict.keys()) else Start_positions_dict.update({key:[[tuple(add)] for add in value]}) for key, value in tqdm(outputs, desc = "    Summarizing (1/3)", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0)]
    Result_temp = dict()
    if progress_bar is not None: progress_bar.update(1)
    [Result_temp.update({(key[1], key[0],):[exist + add for exist, add in zip(Result_temp[(key[1], key[0],)], value)]}) if (key[1], key[0],) in Result_temp.keys() else Result_temp.update({key:value}) for key, value in tqdm(Start_positions_dict.items(), desc = "    Summarizing (2/3)", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0)]
    Result = dict()
    if progress_bar is not None: progress_bar.update(1)
    Result = {key:[list(it.chain.from_iterable(list(set(each_value)))) for each_value in value] for key, value in tqdm(Result_temp.items(), desc = "    Summarizing (3/3)", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0)}
    if progress_bar is not None: progress_bar.update(1)
    Result = {key:value for key, value in tqdm(Result.items(), desc = "    Filtering", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0) if (sum([len(each_list) == 0 for each_list in value]) == 0)}
    df_Start_positions = pd.DataFrame(Result, index = [name[i] for i in range(len(name) - 1, -1, -1)]).T
    df_Start_positions = df_Start_positions.dropna(axis = 0)
    if df_Start_positions.empty:
        print("\nThere was no primer set that meets input conditions. Please change probe size or allowance value.\n")
        sys.exit()
    if (len(Exclude_sequences_list) != 0) & (str(Exclude_mode).lower() == 'standard'):
        Maximum_primer_length = np.max([len(id) for index in df_Start_positions.index for id in index])
        Index_fwd = [index[0] + "".join(['N' for i in range(Maximum_primer_length - len(index[0]))]) if len(index[0]) < Maximum_primer_length else index[0] for index in df_Start_positions.index]
        Index_rev = [index[1] + "".join(['N' for i in range(Maximum_primer_length - len(index[1]))]) if len(index[1]) < Maximum_primer_length else index[1] for index in df_Start_positions.index]
        translate_fwd_primer_sequence_matrix = np.array([np.ravel(np.array([list('{:04b}'.format(int(n,16))) for n in list(fwd.lower().translate(encode_table)) if re.sub(r'[0-9a-f]', '', n) == ''], dtype = int)) for fwd in Index_fwd], dtype = int).astype(np.uint8)
        translate_rev_primer_sequence_matrix = np.array([np.ravel(np.array([list('{:04b}'.format(int(n,16))) for n in list(rev.lower().translate(encode_table)) if re.sub(r'[0-9a-f]', '', n) == ''], dtype = int)) for rev in Index_rev], dtype = int).astype(np.uint8)
        Criteria = []
        if GPU:
            if homology_calculation_chunks == "Auto":
                Test_chunk_size = 100
                Next_trial = True
                while Next_trial:
                    try:
                        Template_Vessel = {"Template_Vessel" + str(i): cp.zeros(shape = (Maximum_primer_length * 4, len(Exclude_sequences[-1]) - Maximum_primer_length + 1, ), dtype = cp.uint8) for i in range(1, CPU + 1)}
                        Chunk_Vessel = {"Chunk_Vessel" + str(i): cp.zeros(shape = (Test_chunk_size, len(Exclude_sequences[-1]) - Maximum_primer_length + 1, ), dtype = cp.uint8) for i in range(1, CPU + 1)}
                        Ref_Vessel = {"Ref_Vessel" + str(i): cp.zeros(shape = (Test_chunk_size, Maximum_primer_length * 4, ), dtype = cp.uint8) for i in range(1, CPU + 1)}
                        Test_chunk_size += 100
                        del Template_Vessel
                        del Chunk_Vessel
                        del Ref_Vessel
                        mempool.free_all_blocks()
                        if Test_chunk_size > df_Start_positions.shape[0]:
                            Next_trial = False
                    except:
                        Test_chunk_size = int(round(Test_chunk_size * 0.20, -1))
                        if "Template_Vessel" in locals(): del Template_Vessel
                        if "Chunk_Vessel" in locals(): del Chunk_Vessel
                        if "Ref_Vessel" in locals(): del Ref_Vessel
                        mempool.free_all_blocks()
                        Next_trial = False
                homology_calculation_chunks_for_exclude = copy.deepcopy(Test_chunk_size)
                updated_core_number = copy.deepcopy(CPU)
            else:
                homology_calculation_chunks_for_exclude = int(copy.deepcopy(homology_calculation_chunks))
                Test_core_number = copy.deepcopy(CPU)
                Template_Vessel = {}
                Chunk_Vessel = {}
                Ref_Vessel = {}
                try:
                    for core in range(1, Test_core_number + 1):
                        Template_Vessel.update({"Template_Vessel" + str(core): cp.zeros(shape = (int(Maximum_primer_length * 4 * 4), len(Exclude_sequences[-1]) - Maximum_primer_length + 1, ), dtype = cp.uint8)})
                        Chunk_Vessel.update({"Chunk_Vessel" + str(core): cp.zeros(shape = (int(homology_calculation_chunks_for_exclude * 4), len(Exclude_sequences[-1]) - Maximum_primer_length + 1, ), dtype = cp.uint8)})
                        Ref_Vessel.update({"Ref_Vessel" + str(core): cp.zeros(shape = (int(homology_calculation_chunks_for_exclude * 4), int(Maximum_primer_length * 4 * 4), ), dtype = cp.uint8)})
                    updated_core_number = int(core)
                except:
                    updated_core_number = int(np.max([1, core - 1]))
                del Template_Vessel, Chunk_Vessel, Ref_Vessel
            mempool.free_all_blocks()
        else:
            Available_memory = psutil.virtual_memory().available
            Vessel = np.zeros(shape = (Maximum_primer_length * 4, len(Exclude_sequences[-1]) - Maximum_primer_length + 1, ), dtype = np.uint8)
            Occupied_memory = Vessel.nbytes
            if homology_calculation_chunks == "Auto":
                homology_calculation_chunks_for_exclude = int(np.min([1000, np.max([1, math.floor(((Available_memory * 0.5 / CPU - Occupied_memory * 2) / (Occupied_memory / (Maximum_primer_length * 4))) / 5)])]))
                updated_core_number = int(copy.deepcopy(CPU))
            else:
                homology_calculation_chunks_for_exclude = int(copy.deepcopy(homology_calculation_chunks))
                updated_core_number = int(np.max([1, np.min([CPU, math.floor(Available_memory / ((Occupied_memory / (Maximum_primer_length * 4) * homology_calculation_chunks_for_exclude + Occupied_memory) * 5))])]))
            del Vessel
        Total_matrix_calculation = df_Start_positions.shape[0] / homology_calculation_chunks_for_exclude * exclude_sequences_number * 2
        if progress_bar is not None: progress_bar.update(1)
        with tqdm(total = Total_matrix_calculation, leave = False, position = 1, unit = "tasks", unit_scale = True, desc = "    Filter candidate primer sets based on exclude sequences", bar_format = "{desc}: {percentage:.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}  {rate_fmt}]", smoothing = 0) as pbar:
            def Verbose_exclude_progressbar_update(Result):
                pbar.update(Result[0][0])
            for TTSM in [translate_fwd_primer_sequence_matrix, translate_rev_primer_sequence_matrix]:
                Criteria_each = []
                for neseq in range(len(Exclude_sequences)):
                    split_exclude_sequence = [Exclude_sequences[neseq][i:(i + Maximum_primer_length):] for i in range(len(Exclude_sequences[neseq]) - Maximum_primer_length + 1)]
                    Nbase_count = [str(seq).lower().count("n") > allowance for seq in split_exclude_sequence]
                    del split_exclude_sequence
                    translate_exclude_sequence = np.array([list('{:04b}'.format(int(n,16))) for n in list(Exclude_sequences[neseq].lower().translate(encode_table)) if re.sub(r'[0-9a-f]', '', n) == ''], dtype = int).astype(np.uint8)
                    translate_exclude_sequence_matrix = np.empty(((len(translate_exclude_sequence) - Maximum_primer_length + 1), 0), np.uint8)
                    for i in range(Maximum_primer_length - 1):
                        translate_exclude_sequence_matrix = np.concatenate([translate_exclude_sequence_matrix.astype(np.uint8), translate_exclude_sequence[i:(i - Maximum_primer_length + 1):].astype(np.uint8)], axis = 1)
                    translate_exclude_sequence_matrix = np.concatenate([translate_exclude_sequence_matrix, translate_exclude_sequence[(Maximum_primer_length - 1)::]], axis = 1).astype(np.uint8)
                    translate_exclude_sequence_matrix[Nbase_count] = 0
                    del Nbase_count
                    Criterion = []
                    template_translate_sequences_matrix = TTSM
                    translate_exclude_sequence_matrix = (translate_exclude_sequence_matrix.T).astype(np.uint8)
                    Chunks_Start_positions = list(range(0, template_translate_sequences_matrix.shape[0], homology_calculation_chunks_for_exclude))
                    shm1 = SharedMemory(create = True, size = translate_exclude_sequence_matrix.nbytes)
                    Shared_translate_sequence_matrix = np.ndarray(shape = translate_exclude_sequence_matrix.shape, dtype = translate_exclude_sequence_matrix.dtype, buffer = shm1.buf)
                    Shared_translate_sequence_matrix[:] = translate_exclude_sequence_matrix[:]
                    shm2 = SharedMemory(create = True, size = template_translate_sequences_matrix.nbytes)
                    Shared_template_translate_sequences_matrix = np.ndarray(shape = template_translate_sequences_matrix.shape, dtype = template_translate_sequences_matrix.dtype, buffer = shm2.buf)
                    Shared_template_translate_sequences_matrix[:] = template_translate_sequences_matrix[:]
                    share_informations = ((shm1.name, translate_exclude_sequence_matrix.shape, translate_exclude_sequence_matrix.dtype, ), (shm2.name, template_translate_sequences_matrix.shape, template_translate_sequences_matrix.dtype, ), ("", ), ("", ))
                    update_factor = (df_Start_positions.shape[0]/len(template_translate_sequences_matrix))
                    parameter = { \
                        'homology_calculation_chunks': homology_calculation_chunks_for_exclude, \
                        'share_informations': share_informations, \
                        'probe_size': Maximum_primer_length, \
                        'allowance': int(0), \
                        'Mode': "Exclude", \
                        'GPU': GPU, \
                        'Allowance_adjustment': False, \
                        'input_sequences_length': exclude_sequences_length[neseq], \
                        'interval_distance': int(0), \
                        'Maximum_annealing_site_number': int(len(Exclude_sequences[neseq])), \
                        'Annealing_site_number_threshold': int(len(Exclude_sequences[neseq])), \
                        'update_factor': update_factor, \
                        'Interval_factor': int(1) \
                    }
                    multi_homology_calculation = partial(homology_calculation, parameter = parameter)
                    with get_context("spawn").Pool(processes = updated_core_number, initializer = init_worker) as pl:
                        try:
                            outputs = [pl.apply_async(multi_homology_calculation, args = (csp, ), callback = Verbose_exclude_progressbar_update) for csp in Chunks_Start_positions]
                            outputs = [output.get() for output in outputs]
                        except KeyboardInterrupt:
                            pl.terminate()
                            pl.join()
                            pl.close()
                            print("\n\n --- Keyboard Interrupt ---")
                            sys.exit()
                    [Criterion.extend(output[1]) for output in outputs] 
                    Criterion = np.array(Criterion).astype(bool)
                    Criteria_each.append(Criterion)
                    del Shared_translate_sequence_matrix, Shared_template_translate_sequences_matrix, share_informations
                    shm1.close(); shm2.close()
                    shm1.unlink(); shm2.unlink()
                    del translate_exclude_sequence_matrix, translate_exclude_sequence, Criterion
                Criteria.append(Criteria_each)
        Criteria = [criteria_fwd | criteria_rev for criteria_fwd, criteria_rev in zip(Criteria[0], Criteria[1])]
        Criteria = np.array([np.all(criteria) for criteria in zip(*Criteria)])
        if not np.any(Criteria):
            print("\nThere was no primer set that meets input conditions.\n")
            sys.exit()
        df_Start_positions = df_Start_positions[Criteria]
        del Verbose_exclude_progressbar_update, template_translate_sequences_matrix, translate_fwd_primer_sequence_matrix, translate_rev_primer_sequence_matrix, Criteria
    Melted_df_Start_positions_set_wo_na = Melted_df_Start_positions_set.dropna(axis = 0)
    Melted_df_Start_positions_set_wo_na = Melted_df_Start_positions_set_wo_na.drop_duplicates(keep = 'first', subset = 'Sequence')
    Melted_df_Start_positions_set_wo_na.index = Melted_df_Start_positions_set_wo_na['Sequence']
    Melted_df_Start_positions_set_wo_na = Melted_df_Start_positions_set_wo_na.drop(['Position', 'Sequence'], axis = 1)
    Primer_positions = [[(pos1, pos2 * (-1), ) for pos1, pos2 in zip(Melted_df_Start_positions_set_wo_na.loc[idx1], Melted_df_Start_positions_set_wo_na.loc[complementary_sequence(idx2)])] if ((idx1 in Melted_df_Start_positions_set_wo_na.index) & (complementary_sequence(idx2) in Melted_df_Start_positions_set_wo_na.index)) else [(pos1 * (-1), pos2, ) for pos1, pos2 in zip(Melted_df_Start_positions_set_wo_na.loc[complementary_sequence(idx1)], Melted_df_Start_positions_set_wo_na.loc[idx2])] for idx1, idx2 in df_Start_positions.index]
    Primer_positions = pd.DataFrame(Primer_positions, index = df_Start_positions.index, columns = [name[i] for i in range(len(name) - 1, -1, -1)])
    return [df_Start_positions, Primer_positions]

def PCR_amplicon(forward, reverse, template, Single_amplicon = True, Sequence_Only = True, amplicon_size_limit = 10000, allowance = 0, Warning_ignore = False, circularDNAtemplate = False, IgnoreLowQualityRegion = True):
    '''
    In silico PCR.

    Parameters
    ----------
    forward: str or nucleotide_sequence
        Forward primer sequence (required).
    reverse: str or nucleotide_sequence
        Reverse primer sequence (required).
    template: str or nucleotide_sequence
        Template DNA sequence (required).
    Single_amplicon: bool
        All amplicons that will be amplified by an input primer set are outputed as list when False is specified. (default: True)
    Sequence_Only: bool
        The start and end positions of an amplicon in template sequence are outputed with the amplicon sequence when False is specified. (default: True)
    amplicon_size_limit: int
        The upper limit of amplicon size. (default: 10,000)
    allowance: int
        The acceptable mismatch number. (default: 0)
    Warning_ignore: bool
        Show all warnings if True is specified. (default: False)
    circularDNAtemplate: bool
        Specify True if the input sequence is circular DNA. (default: False)

    Returns
    -------
    PCR_amplicon: str or list

    '''
    if Warning_ignore:
        warnings.simplefilter('ignore')
    Original_template_length = len(str(template))
    if circularDNAtemplate:
        template = str(template) + str(template)[0:int(np.min([amplicon_size_limit, Original_template_length * 0.1])):]
    if IgnoreLowQualityRegion:
        IGNORE = math.ceil(np.max([(np.min([len(str(forward)), len(str(reverse))]) - allowance) / 2, 2]))
        IGNORE = r"".join(["N" for n in range(IGNORE)]) + r'+'
        IGNORE = re.findall(IGNORE, template)
        IGNORE.sort(reverse = True)
        for igr in IGNORE:
            template = re.sub(igr, igr.replace("N", "X"), template)
    PCR_amplicon = None
    forward_position = search_position(evaluating_sequence = forward, input_sequence = template, allowance = allowance, interval_distance = 0, Match_rate = 0.0, Maximum_annealing_site_number = len(template), IgnoreLowQualityRegion = False)
    reverse_position = search_position(evaluating_sequence = complementary_sequence(reverse), input_sequence = template, allowance = allowance, interval_distance = 0, Match_rate = 0.0, Maximum_annealing_site_number = len(template), IgnoreLowQualityRegion = False)
    if (forward_position is not None) & (reverse_position is not None):
        forward_position = sorted(sorted(list(set(list(it.chain.from_iterable([v for v in forward_position.values()]))))), key = abs)
        reverse_position = sorted(sorted(list(set(list(it.chain.from_iterable([v for v in reverse_position.values()]))))), key = abs)
        if Sequence_Only:
            Amplicon_size = [array_diff([f], reverse_position, lower = 0, upper = amplicon_size_limit, logical = False, separation_key = []) + len(reverse) if f >= 0 else array_diff([f], reverse_position, lower = 0, upper = amplicon_size_limit, logical = False, separation_key = []) + len(forward) for f in forward_position]
            PCR_amplicon = [template[int(f):int(f+a):] if f >= 0 else template[int(np.abs(f) + len(forward) - a):int(np.abs(f) + len(forward)):] for f, amp in zip(forward_position, Amplicon_size) for a in amp]
            PCR_amplicon = list(set([amp for amp in PCR_amplicon if ((len(amp) <= amplicon_size_limit) & (len(amp) != 0) & (amp.find("X") < 0))]))
        else:
            Amplicon_size = [array_diff([f], reverse_position, lower = 0, upper = amplicon_size_limit, logical = False, separation_key = []) + len(reverse) if f >= 0 else array_diff([f], reverse_position, lower = 0, upper = amplicon_size_limit, logical = False, separation_key = []) + len(forward) for f in forward_position]
            PCR_amplicon = [(int(f + 1), int(f + a), template[int(f):int(f+a):], ) if f >= 0 else (int(f - len(forward)), int(f - len(forward) + a - 1), template[int(np.abs(f) + len(forward) - a):int(np.abs(f) + len(forward)):], ) for f, amp in zip(forward_position, Amplicon_size) for a in amp]
            PCR_amplicon = [(f, r, amp, ) for f, r, amp in PCR_amplicon if ((len(amp) <= amplicon_size_limit) & (len(amp) != 0) & (amp.find("X") < 0))]
            PCR_amplicon = [(f - Original_template_length, r, amp, ) if f >= Original_template_length else (f, r, amp, ) for f, r, amp in PCR_amplicon]
            PCR_amplicon = [(f, r - Original_template_length, amp, ) if r >= Original_template_length else (f, r, amp, ) for f, r, amp in PCR_amplicon]
            PCR_amplicon = sorted(list(set(PCR_amplicon)))
    if ((PCR_amplicon is None) | (PCR_amplicon == [])):
        PCR_amplicon = None
    elif Single_amplicon:
        PCR_amplicon = PCR_amplicon[0]
    else:
        PCR_amplicon = PCR_amplicon
    if ((forward_position is None) | (reverse_position is None) | (PCR_amplicon is None)):
        warnings.warn("\nNo amplicon was obtained.\n", stacklevel = 2)
    elif Single_amplicon & ((len(PCR_amplicon) > 1) & np.logical_not(((type(PCR_amplicon) is str)) | (type(PCR_amplicon) is tuple))):
        warnings.warn("\nTwo or more fragments will be amplified.\n", stacklevel = 2)
    else:
        pass
    return PCR_amplicon

def PCR_check(primer_set = "", forward = "", reverse = "", template = "", mode = 'any', Warning_ignore = True):
    '''
    The program for confirming that the amplicon(s) will be obtained from a template sequence and an input primer set. (private)

    Parameters
    ----------
    primer_set: list or tuple
        [forward primer, reverse primer] (required.)
    forward: str or nucleotide_sequence
        Required if primer_set argument is NOT inputted.
    reverse: str or nucleotide_sequence
        Required if primer_set argument is NOT inputted.
    template: str, nucleotide_sequence, list, tuple, dict, numpy.ndarray of sequences
        Template sequence(s) (required).
    mode: str
        'any', 'all', ''. A list of check results obtained from each template sequence will be returned if specify ''. (default: any)
    Warning_ignore: bool
        Show all warnings if True is specified. (default: False)

    Returns
    -------
    Check_result: bool or list

    '''
    if (template == "") | ((primer_set == "") & ((forward == "") | (reverse == ""))):
        try:
            raise TypeError
        except:
            print("TypeError: PCR_check takes at least 'primer_set' and 'template' or 'forward', 'reverse' and 'template' argument.\n")
            return None
    if primer_set != "":
        forward = primer_set[0]
        reverse = primer_set[1]
    if (type(template) is list) | (type(template) is tuple) | (type(template) is np.ndarray) | (type(template) is dict):
        if type(template) is dict:
            template = [seq for seq in template.values()]
        if mode == 'all':
            Result = np.all([PCR_amplicon(forward, reverse, seq, Warning_ignore = Warning_ignore) is not None for seq in template])
        elif mode == 'any':
            Result = np.any([PCR_amplicon(forward, reverse, seq, Warning_ignore = Warning_ignore) is not None for seq in template])
        else:
            Result = [PCR_amplicon(forward, reverse, seq, Warning_ignore = Warning_ignore) is not None for seq in template]
    elif (type(template) is str) | (type(template) is nucleotide_sequence):
        Result = PCR_amplicon(forward, reverse, template, Warning_ignore = Warning_ignore) is not None
    else:
        try:
            raise TypeError
        except:
            print("TypeError: Template sequence should be 'list', 'tuple', 'numpy.ndarray', 'dict', 'str' or 'nucleotide_sequence'.\n")
            return None
    return Result

def SHRsearch(input, probe_size, size_range, allowance_rate, Match_rate, interval_distance = 0, CPU = int(1), homology_calculation_chunks = 100, Maximum_annealing_site_number = 10, Exclude_sequences_list = {}, Search_mode = "moderate", Search_interval = float(0.5), Exclude_mode = 'fast', withinMemory = True, Allowance_adjustment = True, progress_bar = None):
    """
    Function for searching short-length homologous region in input sequences. (private)
    
    """
    warnings.simplefilter('ignore')
    sequences = []
    name = []
    Start_positions = dict()
    initial_index = 0
    if type(input) is dict:
        for key in input:
            name.append(key); sequences.append(input[key])
    elif (type(input) is list) | (type(input) is tuple):
        sequences = input; name = ["".join(["Sequence", str(i)]) for i in range(1, len(input) + 1)]
    elif (type(input) is str):
        sequences = [input]; name = ["Sequence"]
    elif (type(input) is nucleotide_sequence):
        sequences = [str(input)]; name = ["Sequence"]
    else:
        print("\nInput file should be 'dictionary {name:seq}', 'list [seqs]', 'tuple (seqs,)' or 'str (seq)' including Nucleotide sequence(s)\n")
        sys.exit()
    if len(Exclude_sequences_list) != 0:
        Exclude_name = []
        Exclude_sequences = []
        if type(Exclude_sequences_list) is dict:
            for key in Exclude_sequences_list:
                Exclude_name.append(key); Exclude_sequences.append(Exclude_sequences_list[key])
        elif (type(Exclude_sequences_list) is list) | (type(Exclude_sequences_list) is tuple):
            Exclude_sequences = Exclude_sequences_list; Exclude_name = ["".join(["Sequence", str(i)]) for i in range(1, len(Exclude_sequences_list) + 1)]
        elif (type(Exclude_sequences_list) is str):
            Exclude_sequences = [Exclude_sequences_list]; Exclude_name = ["Sequence"]
        elif (type(Exclude_sequences_list) is nucleotide_sequence):
            Exclude_sequences = [str(Exclude_sequences_list)]; Exclude_name = ["Sequence"]
        exclude_sequences_number = len(Exclude_sequences)
        exclude_sequences_length = [len(seq) for seq in Exclude_sequences]
    encode_table = {"a":'1', "t":'8', "g":'2', "c":'4', "b":'e', "d":'b', "h":'d', "k":'a', "m":'5', "r":'3', "s":'6', "v":'7', "w":'9', "y":'c', "n":'f', "x":'0'}
    encode_table = str.maketrans(encode_table)
    input_sequences_number = len(sequences)
    input_sequences_length = [len(seq) for seq in sequences]
    separation_key = []
    for sequence in sequences:
        sep_pos = []
        pos = 0
        while (len(sep_pos) == 0) | (sequence.lower().find("x", pos + 1) != -1):
            pos = sequence.lower().find("x", pos + 1)
            sep_pos.append(pos)
        sep_pos = sep_pos + [sp * (-1) for sp in sep_pos if sp != -1]
        sep_pos.sort()
        separation_key += [sep_pos]
    if size_range >= 0:
        initial_probe_size = probe_size
    elif size_range < 0:
        initial_probe_size = probe_size + size_range
    for probe_size in range(initial_probe_size, initial_probe_size + abs(size_range) + 1):
        allowance = int(math.ceil(probe_size * allowance_rate))
        split_sequences = []
        translate_sequences = []
        translate_sequences_matrix = []
        for nseq in range(input_sequences_number):
            split_sequence = [sequences[nseq][i:(i + probe_size):] for i in range(input_sequences_length[nseq] - probe_size + 1)]
            split_sequences.append(split_sequence)
            Nbase_count = [str(seq).lower().count("n") > allowance for seq in split_sequence]
            del split_sequence 
            translate_sequences.append(np.array([list('{:04b}'.format(int(n,16))) for n in list(sequences[nseq].lower().translate(encode_table)) if re.sub(r'[0-9a-f]', '', n) == ''], dtype = int).astype(np.uint8))
            translate_sequence_matrix = np.empty(((len(translate_sequences[nseq]) - probe_size + 1), 0), np.uint8)
            for i in range(probe_size - 1):
                translate_sequence_matrix = np.concatenate([translate_sequence_matrix.astype(np.uint8), translate_sequences[nseq][i:(i - probe_size + 1):].astype(np.uint8)], axis = 1)
            translate_sequence_matrix = np.concatenate([translate_sequence_matrix, translate_sequences[nseq][(probe_size - 1)::]], axis = 1).astype(np.uint8)
            translate_sequence_matrix[Nbase_count] = 0
            translate_sequences_matrix.append(translate_sequence_matrix)
            del translate_sequence_matrix
        Position_lists = np.array([])
        if (len(Exclude_sequences_list) != 0) & (str(Exclude_mode).lower() == 'fast'):
            if Search_mode != "exhaustive":
                if Search_mode == 'moderate':
                    Search_interval_updated = int(np.min([int(10), math.floor(probe_size / 3)]))
                elif Search_mode == 'sparse':
                    Search_interval_updated = int(probe_size)
                elif Search_mode == 'manual':
                    Search_interval_updated = np.max([int(1), int(math.floor(probe_size * Search_interval))])
                else:
                    Search_interval_updated = int(1)
                Criteria = np.repeat(False, len(split_sequences[-1]))
                index = np.array(range(initial_index, len(split_sequences[-1]), np.min([Search_interval_updated, len(split_sequences[-1]) - probe_size])))
                Criteria[index] = True
                Interval_factor = len(Criteria) / np.sum(Criteria)
                del index
            else:
                Criteria = np.repeat(True, len(split_sequences[-1])).astype(bool)
                Interval_factor = int(1)
            GPU = True if "cupy" in sys.modules else False
            if GPU:
                if homology_calculation_chunks == "Auto":
                    Test_chunk_size = 100
                    Next_trial = True
                    while Next_trial:
                        try:
                            Template_Vessel = {"Template_Vessel" + str(i): cp.zeros(shape = (probe_size * 4, len(Exclude_sequences[-1]) - probe_size + 1, ), dtype = cp.uint8) for i in range(1, CPU + 1)}
                            Chunk_Vessel = {"Chunk_Vessel" + str(i): cp.zeros(shape = (Test_chunk_size, len(Exclude_sequences[-1]) - probe_size + 1, ), dtype = cp.uint8) for i in range(1, CPU + 1)}
                            Ref_Vessel = {"Ref_Vessel" + str(i): cp.zeros(shape = (Test_chunk_size, probe_size * 4, ), dtype = cp.uint8) for i in range(1, CPU + 1)}
                            Test_chunk_size += 100
                            del Template_Vessel
                            del Chunk_Vessel
                            del Ref_Vessel
                            mempool.free_all_blocks()
                            if Test_chunk_size > np.sum(Criteria):
                                Next_trial = False
                        except:
                            Test_chunk_size = int(round(Test_chunk_size * 0.20, -1))
                            if "Template_Vessel" in locals(): del Template_Vessel
                            if "Chunk_Vessel" in locals(): del Chunk_Vessel
                            if "Ref_Vessel" in locals(): del Ref_Vessel
                            mempool.free_all_blocks()
                            Next_trial = False
                    homology_calculation_chunks_for_exclude = copy.deepcopy(Test_chunk_size)
                    updated_core_number = copy.deepcopy(CPU)
                else:
                    homology_calculation_chunks_for_exclude = int(copy.deepcopy(homology_calculation_chunks))
                    Test_core_number = copy.deepcopy(CPU)
                    Template_Vessel = {}
                    Chunk_Vessel = {}
                    Ref_Vessel = {}
                    try:
                        for core in range(1, Test_core_number + 1):
                            Template_Vessel.update({"Template_Vessel" + str(core): cp.zeros(shape = (int(probe_size * 4 * 4), len(Exclude_sequences[-1]) - probe_size + 1, ), dtype = cp.uint8)})
                            Chunk_Vessel.update({"Chunk_Vessel" + str(core): cp.zeros(shape = (int(homology_calculation_chunks_for_exclude * 4), len(Exclude_sequences[-1]) - probe_size + 1, ), dtype = cp.uint8)})
                            Ref_Vessel.update({"Ref_Vessel" + str(core): cp.zeros(shape = (int(homology_calculation_chunks_for_exclude * 4), int(probe_size * 4 * 4), ), dtype = cp.uint8)})
                        updated_core_number = int(core)
                    except:
                        updated_core_number = int(np.max([1, core - 1]))
                    del Template_Vessel, Chunk_Vessel, Ref_Vessel
                mempool.free_all_blocks()
            else:
                Available_memory = psutil.virtual_memory().available
                Vessel = np.zeros(shape = (probe_size * 4, len(Exclude_sequences[-1]) - probe_size + 1, ), dtype = np.uint8)
                Occupied_memory = Vessel.nbytes
                if homology_calculation_chunks == "Auto":
                    homology_calculation_chunks_for_exclude = int(np.min([1000, np.max([1, math.floor(((Available_memory * 0.5 / CPU - Occupied_memory * 2) / (Occupied_memory / (probe_size * 4))) / 5)])]))
                    updated_core_number = int(copy.deepcopy(CPU))
                else:
                    homology_calculation_chunks_for_exclude = int(copy.deepcopy(homology_calculation_chunks))
                    updated_core_number = int(np.max([1, np.min([CPU, math.floor(Available_memory / ((Occupied_memory / (probe_size * 4) * homology_calculation_chunks_for_exclude + Occupied_memory) * 5))])]))
                del Vessel
            Total_matrix_calculation = translate_sequences_matrix[-1].shape[0] / homology_calculation_chunks_for_exclude * len(Exclude_sequences_list)
            if progress_bar is not None: progress_bar.update(1)
            with tqdm(total = Total_matrix_calculation / Interval_factor, leave = False, position = 1, unit = "tasks", unit_scale = True, desc = "    Filter valid candidates based on Exclude sequences", bar_format = "{desc}: {percentage:.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}  {rate_fmt}]", smoothing = 0) as pbar:
                def Exclude_range_progressbar_update(Result):
                    pbar.update(Result[0][0])
                for neseq in range(len(Exclude_sequences)):
                    split_exclude_sequence = [Exclude_sequences[neseq][i:(i + probe_size):] for i in range(len(Exclude_sequences[neseq]) - probe_size + 1)]
                    Nbase_count = [str(seq).lower().count("n") > allowance for seq in split_exclude_sequence]
                    del split_exclude_sequence
                    translate_exclude_sequence = np.array([list('{:04b}'.format(int(n,16))) for n in list(Exclude_sequences[neseq].lower().translate(encode_table)) if re.sub(r'[0-9a-f]', '', n) == ''], dtype = int).astype(np.uint8)
                    translate_exclude_sequence_matrix = np.empty(((len(translate_exclude_sequence) - probe_size + 1), 0), np.uint8)
                    for i in range(probe_size - 1):
                        translate_exclude_sequence_matrix = np.concatenate([translate_exclude_sequence_matrix.astype(np.uint8), translate_exclude_sequence[i:(i - probe_size + 1):].astype(np.uint8)], axis = 1)
                    translate_exclude_sequence_matrix = np.concatenate([translate_exclude_sequence_matrix, translate_exclude_sequence[(probe_size - 1)::]], axis = 1).astype(np.uint8)
                    translate_exclude_sequence_matrix[Nbase_count] = 0
                    del Nbase_count
                    Criterion = []
                    translate_exclude_sequence_matrix = (translate_exclude_sequence_matrix.T).astype(np.uint8)
                    template_translate_sequences_matrix = (translate_sequences_matrix[-1])[Criteria]
                    Chunks_Start_positions = list(range(0, template_translate_sequences_matrix.shape[0], homology_calculation_chunks_for_exclude))
                    shm1 = SharedMemory(create = True, size = translate_exclude_sequence_matrix.nbytes)
                    Shared_translate_sequence_matrix = np.ndarray(shape = translate_exclude_sequence_matrix.shape, dtype = translate_exclude_sequence_matrix.dtype, buffer = shm1.buf)
                    Shared_translate_sequence_matrix[:] = translate_exclude_sequence_matrix[:]
                    shm2 = SharedMemory(create = True, size = template_translate_sequences_matrix.nbytes)
                    Shared_template_translate_sequences_matrix = np.ndarray(shape = template_translate_sequences_matrix.shape, dtype = template_translate_sequences_matrix.dtype, buffer = shm2.buf)
                    Shared_template_translate_sequences_matrix[:] = template_translate_sequences_matrix[:]
                    share_informations = ((shm1.name, translate_exclude_sequence_matrix.shape, translate_exclude_sequence_matrix.dtype, ), (shm2.name, template_translate_sequences_matrix.shape, template_translate_sequences_matrix.dtype, ), ("", ), ("", ))
                    update_factor = (len(translate_sequences_matrix[-1])/len(template_translate_sequences_matrix))
                    parameter = { \
                        'homology_calculation_chunks': homology_calculation_chunks_for_exclude, \
                        'share_informations': share_informations, \
                        'probe_size': probe_size, \
                        'allowance': allowance, \
                        'Mode': "Exclude", \
                        'GPU': GPU, \
                        'Allowance_adjustment': Allowance_adjustment, \
                        'input_sequences_length': exclude_sequences_length[neseq], \
                        'interval_distance': interval_distance, \
                        'Maximum_annealing_site_number': Maximum_annealing_site_number, \
                        'Annealing_site_number_threshold': 10, \
                        'update_factor': update_factor, \
                        'Interval_factor': Interval_factor \
                    }
                    multi_homology_calculation = partial(homology_calculation, parameter = parameter)
                    with get_context("spawn").Pool(processes = updated_core_number, initializer = init_worker) as pl:
                        try:
                            outputs = [pl.apply_async(multi_homology_calculation, args = (csp, ), callback = Exclude_range_progressbar_update) for csp in Chunks_Start_positions]
                            outputs = [output.get() for output in outputs]
                        except KeyboardInterrupt:
                            pl.terminate()
                            pl.join()
                            pl.close()
                            print("\n\n --- Keyboard Interrupt ---")
                            sys.exit()
                    [Criterion.extend(output[1]) for output in outputs] 
                    Criterion = np.array(Criterion).astype(bool)
                    Criteria[np.nonzero(Criteria)[0][np.nonzero(~Criterion)[0]]] = False
                    del Shared_translate_sequence_matrix, Shared_template_translate_sequences_matrix, share_informations
                    shm1.close(); shm2.close()
                    shm1.unlink(); shm2.unlink()
                    del translate_exclude_sequence_matrix, template_translate_sequences_matrix, translate_exclude_sequence, Criterion
                    if not np.any(Criteria):
                        pbar.update(pbar.total - pbar.n)
                        break
            del Exclude_range_progressbar_update
            Interval_factor = len(Criteria) / np.sum(Criteria)
        else:
            if Search_mode != "exhaustive":
                if Search_mode == 'moderate':
                    Search_interval_updated = int(np.min([int(10), math.floor(probe_size / 3)]))
                elif Search_mode == 'sparse':
                    Search_interval_updated = int(probe_size)
                elif Search_mode == 'manual':
                    Search_interval_updated = np.max([int(1), int(math.floor(probe_size * Search_interval))])
                else:
                    Search_interval_updated = int(1)
                Criteria = np.repeat(False, len(split_sequences[-1]))
                index = np.array(range(initial_index, len(split_sequences[-1]), np.min([Search_interval_updated, len(split_sequences[-1]) - probe_size])))
                Criteria[index] = True
                Interval_factor = len(Criteria) / np.sum(Criteria)
                del index
            else:
                Criteria = np.repeat(True, len(split_sequences[-1])).astype(bool)
                Interval_factor = int(1)
        if not np.any(Criteria):
            continue
        Exclusion_required_sequences = [[] for n in range(len(split_sequences[-1]))]
        GPU = True if "cupy" in sys.modules else False
        if GPU:
            if homology_calculation_chunks == "Auto":
                Test_chunk_size = 100
                Next_trial = True
                while Next_trial:
                    try:
                        Template_Vessel = {"Template_Vessel" + str(i): cp.zeros(shape = (probe_size * 4, len(sequences[-2]) - probe_size + 1, ), dtype = cp.uint8) for i in range(1, CPU + 1)}
                        Chunk_Vessel = {"Chunk_Vessel" + str(i): cp.zeros(shape = (Test_chunk_size, len(sequences[-2]) - probe_size + 1, ), dtype = cp.uint8) for i in range(1, CPU + 1)}
                        Ref_Vessel = {"Ref_Vessel" + str(i): cp.zeros(shape = (Test_chunk_size, probe_size * 4, ), dtype = cp.uint8) for i in range(1, CPU + 1)}
                        Test_chunk_size += 100
                        del Template_Vessel
                        del Chunk_Vessel
                        del Ref_Vessel
                        mempool.free_all_blocks()
                        if Test_chunk_size > np.sum(Criteria):
                            Next_trial = False
                    except:
                        Test_chunk_size = int(round(Test_chunk_size * 0.20, -1))
                        if "Template_Vessel" in locals(): del Template_Vessel
                        if "Chunk_Vessel" in locals(): del Chunk_Vessel
                        if "Ref_Vessel" in locals(): del Ref_Vessel
                        mempool.free_all_blocks()
                        Next_trial = False
                homology_calculation_chunks_for_explore = copy.deepcopy(Test_chunk_size)
                updated_core_number = copy.deepcopy(CPU)
            else:
                homology_calculation_chunks_for_explore = int(copy.deepcopy(homology_calculation_chunks))
                Test_core_number = copy.deepcopy(CPU)
                Template_Vessel = {}
                Chunk_Vessel = {}
                Ref_Vessel = {}
                try:
                    for core in range(1, Test_core_number + 1):
                        Template_Vessel.update({"Template_Vessel" + str(core): cp.zeros(shape = (int(probe_size * 4 * 4), len(sequences[-2]) - probe_size + 1, ), dtype = cp.uint8)})
                        Chunk_Vessel.update({"Chunk_Vessel" + str(core): cp.zeros(shape = (int(homology_calculation_chunks_for_explore * 4), len(sequences[-2]) - probe_size + 1, ), dtype = cp.uint8)})
                        Ref_Vessel.update({"Ref_Vessel" + str(core): cp.zeros(shape = (int(homology_calculation_chunks_for_explore * 4), int(probe_size * 4 * 4), ), dtype = cp.uint8)})
                    updated_core_number = int(core)
                except:
                    updated_core_number = int(np.max([1, core - 1]))
                del Template_Vessel, Chunk_Vessel, Ref_Vessel
            mempool.free_all_blocks()
        else:
            Available_memory = psutil.virtual_memory().available
            Vessel = np.zeros(shape = (probe_size * 4, len(sequences[-2]) - probe_size + 1, ), dtype = np.uint8)
            Occupied_memory = Vessel.nbytes
            if homology_calculation_chunks == "Auto":
                homology_calculation_chunks_for_explore = int(np.min([1000, np.max([1, math.floor(((Available_memory * 0.5 / CPU - Occupied_memory * 2) / (Occupied_memory / (probe_size * 4))) / 5)])]))
                updated_core_number = int(copy.deepcopy(CPU))
            else:
                homology_calculation_chunks_for_explore = int(copy.deepcopy(homology_calculation_chunks))
                updated_core_number = int(np.max([1, np.min([CPU, math.floor(Available_memory / ((Occupied_memory / (probe_size * 4) * homology_calculation_chunks_for_explore + Occupied_memory) * 5))])]))
            del Vessel
        homology_calculation_chunks_for_check = int(copy.deepcopy(homology_calculation_chunks_for_explore))
        Total_matrix_calculation = translate_sequences_matrix[-1].shape[0] / homology_calculation_chunks_for_explore * input_sequences_number
        if progress_bar is not None: progress_bar.update(1)
        with tqdm(total = Total_matrix_calculation / Interval_factor, leave = False, position = 1, unit = "tasks", unit_scale = True, desc = "    Homology calculation ({0}/{1})".format((input_sequences_number + 1) * (probe_size - initial_probe_size) + 1, (size_range + 1) * (input_sequences_number + 1)), bar_format = "{desc}: {percentage:.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}  {rate_fmt}{postfix}]", smoothing = 0) as pbar:
            def Explore_progressbar_update(Result):
                pbar.set_postfix({"Processor": Result[0][1], "Optimized_allowance": Result[0][2], "Ave.ann.site":Result[0][3]})
                pbar.update(Result[0][0])
            for n in range(input_sequences_number):
                Position_list = []
                Criterion = []
                Exclusion_required_sequences_in_loop = []
                translate_sequence_matrix = (translate_sequences_matrix[n].T).astype(np.uint8)
                template_translate_sequences_matrix = (translate_sequences_matrix[-1])[Criteria].astype(np.uint8)
                Cumulative_valid_index = np.zeros(shape = (template_translate_sequences_matrix.shape[0], ), dtype = np.uint32)
                Chunks_Start_positions = list(range(0, template_translate_sequences_matrix.shape[0], homology_calculation_chunks_for_explore))
                shm1 = SharedMemory(create = True, size = translate_sequence_matrix.nbytes)
                Shared_translate_sequence_matrix = np.ndarray(shape = translate_sequence_matrix.shape, dtype = translate_sequence_matrix.dtype, buffer = shm1.buf)
                Shared_translate_sequence_matrix[:] = translate_sequence_matrix[:]
                shm2 = SharedMemory(create = True, size = template_translate_sequences_matrix.nbytes)
                Shared_template_translate_sequences_matrix = np.ndarray(shape = template_translate_sequences_matrix.shape, dtype = template_translate_sequences_matrix.dtype, buffer = shm2.buf)
                Shared_template_translate_sequences_matrix[:] = template_translate_sequences_matrix[:]
                Sequence = np.array([sequences[n]])
                shm3 = SharedMemory(create = True, size = Sequence.nbytes)
                Shared_Sequence = np.ndarray(shape = Sequence.shape, dtype = Sequence.dtype, buffer = shm3.buf)
                Shared_Sequence[:] = Sequence[:]
                shm4 = SharedMemory(create = True, size = Cumulative_valid_index.nbytes)
                Shared_Cumulative_valid_index = np.ndarray(shape = Cumulative_valid_index.shape, dtype = Cumulative_valid_index.dtype, buffer = shm4.buf)
                Shared_Cumulative_valid_index[:] = Cumulative_valid_index[:]
                Shared_Allowance_list = ShareableList([-100 for i in range(len(Chunks_Start_positions) + 1)])
                Shared_Allowance_list[0] = copy.deepcopy(allowance)
                share_informations = [(shm1.name, translate_sequence_matrix.shape, translate_sequence_matrix.dtype, ), (shm2.name, template_translate_sequences_matrix.shape, template_translate_sequences_matrix.dtype, ), (shm3.name, Sequence.shape, Sequence.dtype, ), (shm4.name, Cumulative_valid_index.shape, Cumulative_valid_index.dtype, ), (Shared_Allowance_list.shm.name, )]
                update_factor = (len(translate_sequences_matrix[-1])/len(template_translate_sequences_matrix))
                parameter = { \
                    'homology_calculation_chunks': homology_calculation_chunks_for_explore, \
                    'share_informations': share_informations, \
                    'probe_size': probe_size, \
                    'allowance': allowance, \
                    'Mode': "Explore", \
                    'GPU': GPU, \
                    'Allowance_adjustment': Allowance_adjustment, \
                    'input_sequences_length': input_sequences_length[n], \
                    'interval_distance': interval_distance, \
                    'Maximum_annealing_site_number': Maximum_annealing_site_number, \
                    'Annealing_site_number_threshold': 10, \
                    'update_factor': update_factor, \
                    'Interval_factor': Interval_factor \
                }
                multi_homology_calculation = partial(homology_calculation, parameter = parameter)
                with get_context("spawn").Pool(processes = updated_core_number, initializer = init_worker) as pl:
                    try:
                        outputs = [pl.apply_async(multi_homology_calculation, args = (csp, ), callback = Explore_progressbar_update) for csp in Chunks_Start_positions]
                        outputs = [output.get() for output in outputs]
                    except KeyboardInterrupt:
                        pl.terminate()
                        pl.join()
                        pl.close()
                        print("\n\n --- Keyboard Interrupt ---")
                        sys.exit()
                [Criterion.extend(output[1]) for output in outputs]
                [Position_list.extend(output[2]) for output in outputs]
                [Exclusion_required_sequences_in_loop.extend(output[3]) for output in outputs]
                [Exclusion_required_sequences[j].extend(Exclusion_required_sequences_in_loop[i]) for i, j in enumerate([j for j in range(len(Criteria)) if Criteria[j]])]
                Exclusion_required_sequences = [list(set(Exclusion_required_sequence)) for Exclusion_required_sequence in Exclusion_required_sequences]
                Criterion = np.array(Criterion).astype(bool)
                Criteria[np.nonzero(Criteria)[0][np.nonzero(~Criterion)[0]]] = False
                if len(Position_lists) == 0:
                    Position_lists = np.array(Position_list + [None], dtype = object)[:-1]
                    Position_lists = Position_lists.reshape(1, -1)
                else:
                    Position_list = np.array(Position_list + [None], dtype = object)[:-1]
                    Position_list = Position_list.reshape(1, -1)
                    Position_lists = np.append(Position_lists, Position_list, axis = 0)
                Position_lists = Position_lists[:, Criterion]
                del Shared_translate_sequence_matrix, Shared_template_translate_sequences_matrix, Shared_Sequence, Shared_Cumulative_valid_index, share_informations
                shm1.close(); shm2.close(); shm3.close(); shm4.close(); Shared_Allowance_list.shm.close()
                shm1.unlink(); shm2.unlink(); shm3.unlink(); shm4.unlink(); Shared_Allowance_list.shm.unlink()
                del translate_sequence_matrix, template_translate_sequences_matrix, Sequence, Cumulative_valid_index, Chunks_Start_positions, Criterion
                if not np.any(Criteria):
                    pbar.update(pbar.total - pbar.n)
                    break
        del Explore_progressbar_update
        if not np.any(Criteria):
            continue
        Filtered_split_sequences = np.array(split_sequences[-1])[Criteria]
        Exclusion_required_sequences = np.array(Exclusion_required_sequences, dtype = object)[Criteria]
        Storage = psutil.disk_usage('/')
        if (Position_lists.nbytes > Storage.free * 0.8) | withinMemory:
            Filtered_position_lists = Position_lists.tolist()
            del Position_lists, split_sequences
            outputs_list = np.array([])
            Criteria = np.repeat(True, len(Filtered_split_sequences)).astype(bool)
            for i in range(input_sequences_number):
                Combs = zip(Filtered_split_sequences[Criteria], np.array(Filtered_position_lists[i], dtype = object)[Criteria])
                Total_combination_length = len(Filtered_split_sequences[Criteria])
                Each_filtered_position_list_length = np.array([len(Ps) for Ps in Filtered_position_lists[i]])
                Data_size_estimation_factor = np.sum([np.sum([comb(Ps_length_range, Ps_length) * np.count_nonzero(Each_filtered_position_list_length == Ps_length_range) for Ps_length in range(1, Ps_length_range + 1)]) for Ps_length_range in range(1, np.min([15, np.max(Each_filtered_position_list_length)]) + 1)]) / np.sum(Each_filtered_position_list_length[Each_filtered_position_list_length <= 15])
                updated_core_number = int(copy.deepcopy(CPU))
                while ((sys.getsizeof(Filtered_split_sequences[Criteria]) + sys.getsizeof(np.array(Filtered_position_lists[i], dtype = object)[Criteria])) * Data_size_estimation_factor * updated_core_number > psutil.virtual_memory().available * 0.75) & (updated_core_number > 1):
                    updated_core_number = int(updated_core_number - 1)
                if progress_bar is not None: progress_bar.update(1)
                if updated_core_number == 1:
                    outputs = [search_position(comb, evaluating_sequence = "", input_sequence = sequences[i], allowance = allowance, interval_distance = interval_distance, Position_list = np.array([]), Match_rate = Match_rate, Maximum_annealing_site_number = Maximum_annealing_site_number, IgnoreLowQualityRegion = False) for comb in tqdm(Combs, total = Total_combination_length, leave = False, position = 1, unit = "tasks", unit_scale = True, desc = "    Homology calculation ({0}/{1})".format((input_sequences_number + 1) * (probe_size - initial_probe_size) + 2 + i, (size_range + 1) * (input_sequences_number + 1)), bar_format = "{desc}: {percentage:.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}  {rate_fmt}]", smoothing = 0)]
                else:
                    with get_context("spawn").Pool(processes = updated_core_number, initializer = init_worker) as pl:
                        try:
                            outputs = list(tqdm(pl.imap(partial(search_position, evaluating_sequence = "", input_sequence = sequences[i], allowance = allowance, interval_distance = interval_distance, Position_list = np.array([]), Match_rate = Match_rate, Maximum_annealing_site_number = Maximum_annealing_site_number, IgnoreLowQualityRegion = False), Combs), total = Total_combination_length, leave = False, position = 1, unit = "tasks", unit_scale = True, desc = "    Homology calculation ({0}/{1})".format((input_sequences_number + 1) * (probe_size - initial_probe_size) + 2 + i, (size_range + 1) * (input_sequences_number + 1)), bar_format = "{desc}: {percentage:.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}  {rate_fmt}]", smoothing = 0))
                        except KeyboardInterrupt:
                            pl.terminate()
                            pl.join()
                            pl.close()
                            print("\n\n --- Keyboard Interrupt ---")
                            sys.exit()
                if len(outputs_list) == 0:
                    outputs_list = np.array(outputs).reshape(1, len(outputs))
                else:
                    outputs_list = np.append(outputs_list, np.array(outputs).reshape(1, len(outputs)), axis = 0)
                Criterion = np.array([output is not None for output in outputs]).astype(bool)
                outputs_list = outputs_list[:, Criterion]
                Criteria[np.nonzero(Criteria)[0][np.nonzero(~Criterion)[0]]] = False
        else:
            with tempfile.TemporaryDirectory() as tmp:
                dumpfilenumber = len(Position_lists)
                for i in range(dumpfilenumber):
                    np.save(os.path.join(tmp, 'dumpfile'+str(i + 1)+'.npy'), Position_lists[i])
                del Position_lists, split_sequences
                outputs_list = np.array([])
                Criteria = np.repeat(True, len(Filtered_split_sequences)).astype(bool)
                for i in range(dumpfilenumber):
                    Filtered_position_list = np.load(os.path.join(tmp, 'dumpfile'+str(i + 1)+'.npy'), allow_pickle=True).tolist()
                    Combs = zip(Filtered_split_sequences[Criteria], np.array(Filtered_position_list, dtype = object)[Criteria])
                    Total_combination_length = len(Filtered_split_sequences[Criteria])
                    Each_filtered_position_list_length = np.array([len(Ps) for Ps in Filtered_position_list])
                    Data_size_estimation_factor = np.sum([np.sum([comb(Ps_length_range, Ps_length) * np.count_nonzero(Each_filtered_position_list_length == Ps_length_range) for Ps_length in range(1, Ps_length_range + 1)]) for Ps_length_range in range(1, np.min([15, np.max(Each_filtered_position_list_length)]) + 1)]) / np.sum(Each_filtered_position_list_length[Each_filtered_position_list_length <= 15])
                    updated_core_number = int(copy.deepcopy(CPU))
                    while ((sys.getsizeof(Filtered_split_sequences[Criteria]) + sys.getsizeof(np.array(Filtered_position_list, dtype = object)[Criteria])) * Data_size_estimation_factor * updated_core_number > psutil.virtual_memory().available * 0.75) & (updated_core_number > 1):
                        updated_core_number = int(updated_core_number - 1)
                    if progress_bar is not None: progress_bar.update(1)
                    if updated_core_number == 1:
                        outputs = [search_position(comb, evaluating_sequence = "", input_sequence = sequences[i], allowance = allowance, interval_distance = interval_distance, Position_list = np.array([]), Match_rate = Match_rate, Maximum_annealing_site_number = Maximum_annealing_site_number, IgnoreLowQualityRegion = False) for comb in tqdm(Combs, total = Total_combination_length, leave = False, position = 1, unit = "tasks", unit_scale = True, desc = "    Homology calculation ({0}/{1})".format((input_sequences_number + 1) * (probe_size - initial_probe_size) + 2 + i, (size_range + 1) * (input_sequences_number + 1)), bar_format = "{desc}: {percentage:.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}  {rate_fmt}]", smoothing = 0)]
                    else:
                        with get_context("spawn").Pool(processes = updated_core_number, initializer = init_worker) as pl:
                            try:
                                outputs = list(tqdm(pl.imap(partial(search_position, evaluating_sequence = "", input_sequence = sequences[i], allowance = allowance, interval_distance = interval_distance, Position_list = np.array([]), Match_rate = Match_rate, Maximum_annealing_site_number = Maximum_annealing_site_number, IgnoreLowQualityRegion = False), Combs), total = Total_combination_length, leave = False, position = 1, unit = "tasks", unit_scale = True, desc = "    Homology calculation ({0}/{1})".format((input_sequences_number + 1) * (probe_size - initial_probe_size) + 2 + i, (size_range + 1) * (input_sequences_number + 1)), bar_format = "{desc}: {percentage:.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}  {rate_fmt}]", smoothing = 0))
                            except KeyboardInterrupt:
                                pl.terminate()
                                pl.join()
                                pl.close()
                                print("\n\n --- Keyboard Interrupt ---")
                                sys.exit()
                    if len(outputs_list) == 0:
                        outputs_list = np.array(outputs).reshape(1, len(outputs))
                    else:
                        outputs_list = np.append(outputs_list, np.array(outputs).reshape(1, len(outputs)), axis = 0)
                    Criterion = np.array([output is not None for output in outputs]).astype(bool)
                    outputs_list = outputs_list[:, Criterion]
                    Criteria[np.nonzero(Criteria)[0][np.nonzero(~Criterion)[0]]] = False
        if not np.any(Criteria):
            continue
        Exclusion_required_sequences = Exclusion_required_sequences[Criteria]
        if progress_bar is not None: progress_bar.update(1)
        with get_context("spawn").Pool(processes = CPU, initializer = init_worker) as pl:
            try:
                Combs = ((outputs_list[:, n], Exclusion_required_sequences[n], ) for n in range(outputs_list.shape[1]))
                outputs = list(tqdm(pl.imap(partial(Extracted_Sequences_and_fragment, allowance = allowance, probe_size = probe_size), Combs) , total = outputs_list.shape[1], leave = False, position = 1, unit = "tasks", unit_scale = True, desc = "    Making degenerate probe", bar_format = "{desc}: {percentage:.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}  {rate_fmt}]", smoothing = 0))
            except KeyboardInterrupt:
                pl.terminate()
                pl.join()
                pl.close()
                print("\n\n --- Keyboard Interrupt ---")
                sys.exit()
        [[Start_positions.update({k:tuple([np.array(sorted(list(set(output[k][j].tolist() + v[j].tolist())), key = abs), dtype = object) for j in range(len(v))])}) if k in output.keys() else output.update({k:v}) for k, v in output.items()] for output in outputs]
        initial_index += 1
    if len(Start_positions) == 0:
        print("\nThere was no probe that meets input conditions. Please change probe size or allowance value.\n")
        sys.exit()
    Melted_df_Start_positions_set = pd.DataFrame()
    for no in range(input_sequences_number - 1, -1, -1):
        frag_size = [Start_positions[key][no] for key in Start_positions]
        df_Start_positions = pd.DataFrame(frag_size).assign(Sequence = Start_positions.keys(), Fragment = frag_size)
        Melted_df_Start_positions = (pd.melt(df_Start_positions, id_vars = ["Sequence", 'Fragment'], var_name = "Position_number", value_name = "Position").dropna())
        Melted_df_Start_positions = Melted_df_Start_positions.iloc[Melted_df_Start_positions['Position'].abs().argsort()].reset_index(drop = True)
        Melted_df_Start_positions.index = Melted_df_Start_positions['Sequence'].astype(str).str.cat(Melted_df_Start_positions['Position_number'].astype(str), sep = '_')
        if len(Melted_df_Start_positions_set) == 0:
            Melted_df_Start_positions_set = pd.concat([Melted_df_Start_positions_set, Melted_df_Start_positions['Position']], axis = 1)
        Melted_df_Start_positions = Melted_df_Start_positions['Fragment']
        Melted_df_Start_positions_set = pd.concat([Melted_df_Start_positions_set, Melted_df_Start_positions], axis = 1)
    Sequence_name = [re.sub(r'_\d+', '', name) for name in Melted_df_Start_positions_set.index]
    Melted_df_Start_positions_set.insert(1, 'Sequence', Sequence_name)
    Melted_df_Start_positions_set = Melted_df_Start_positions_set[np.logical_not(Melted_df_Start_positions_set['Sequence'].map(lambda x:x.upper().find("X") >= 0))]
    del df_Start_positions, Sequence_name
    Maximum_candidate_length = np.max([probe_size, np.max([len(sequence) for sequence in Melted_df_Start_positions_set['Sequence']])])
    Index_candidate = [sequence + "".join(['N' for i in range(Maximum_candidate_length - len(sequence))]) if len(sequence) < Maximum_candidate_length else sequence for sequence in Melted_df_Start_positions_set['Sequence']]
    translate_candidate_matrix = np.array([np.ravel(np.array([list('{:04b}'.format(int(n,16))) for n in list(candidate.lower().translate(encode_table)) if re.sub(r'[0-9a-f]', '', n) == ''], dtype = int)) for candidate in Index_candidate], dtype = int).astype(np.uint8)
    Criteria = np.repeat(True, Melted_df_Start_positions_set.shape[0])
    Total_matrix_calculation = Melted_df_Start_positions_set.shape[0] / homology_calculation_chunks_for_check * input_sequences_number
    if progress_bar is not None: progress_bar.update(1)
    with tqdm(total = Total_matrix_calculation, leave = False, position = 1, unit = "tasks", unit_scale = True, desc = "    Check candidate probe", bar_format = "{desc}: {percentage:.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}  {rate_fmt}]", smoothing = 0) as pbar:
        def Check_progressbar_update(Result):
            pbar.update(Result[0][0])
        for nseq in range(input_sequences_number):
            Position_matrix = []
            translate_sequence_matrix = translate_sequences_matrix[nseq]
            template_translate_candidate_matrix = (translate_candidate_matrix)[Criteria]
            translate_sequence_matrix = (translate_sequence_matrix.T).astype(np.uint8)
            Chunks_Start_positions = list(range(0, template_translate_candidate_matrix.shape[0], homology_calculation_chunks_for_check))
            shm1 = SharedMemory(create = True, size = translate_sequence_matrix.nbytes)
            Shared_translate_sequence_matrix = np.ndarray(shape = translate_sequence_matrix.shape, dtype = translate_sequence_matrix.dtype, buffer = shm1.buf)
            Shared_translate_sequence_matrix[:] = translate_sequence_matrix[:]
            shm2 = SharedMemory(create = True, size = template_translate_candidate_matrix.nbytes)
            Shared_template_translate_sequences_matrix = np.ndarray(shape = template_translate_candidate_matrix.shape, dtype = template_translate_candidate_matrix.dtype, buffer = shm2.buf)
            Shared_template_translate_sequences_matrix[:] = template_translate_candidate_matrix[:]
            share_informations = ((shm1.name, translate_sequence_matrix.shape, translate_sequence_matrix.dtype, ), (shm2.name, template_translate_candidate_matrix.shape, template_translate_candidate_matrix.dtype, ), ("", ), ("", ))
            update_factor = (Melted_df_Start_positions_set.shape[0] / len(template_translate_candidate_matrix))
            parameter = { \
                'homology_calculation_chunks': homology_calculation_chunks_for_check, \
                'share_informations': share_informations, \
                'probe_size': Maximum_candidate_length, \
                'allowance': int(0), \
                'Mode': "Check", \
                'GPU': GPU, \
                'Allowance_adjustment': False, \
                'input_sequences_length': input_sequences_length[nseq], \
                'interval_distance': interval_distance, \
                'Maximum_annealing_site_number': input_sequences_length[nseq], \
                'Annealing_site_number_threshold': input_sequences_length[nseq], \
                'update_factor': update_factor, \
                'Interval_factor': int(1) \
            }
            multi_homology_calculation = partial(homology_calculation, parameter = parameter)
            with get_context("spawn").Pool(processes = updated_core_number, initializer = init_worker) as pl:
                try:
                    outputs = [pl.apply_async(multi_homology_calculation, args = (csp, ), callback = Check_progressbar_update) for csp in Chunks_Start_positions]
                    outputs = [output.get() for output in outputs]
                except KeyboardInterrupt:
                    pl.terminate()
                    pl.join()
                    pl.close()
                    print("\n\n --- Keyboard Interrupt ---")
                    sys.exit()
            [Position_matrix.extend(output[1]) for output in outputs]
            Criterion = np.array([set(checkposition) == set(testposition) if np.all([np.all(pd.notna(checkposition)), np.all(pd.notna(testposition))]) else True for checkposition, testposition in zip(Position_matrix, Melted_df_Start_positions_set[Criteria].iloc[:, (-1) * (nseq + 1)])]).astype(bool)
            Criteria[np.nonzero(Criteria)[0][np.nonzero(~Criterion)[0]]] = False
            del Shared_translate_sequence_matrix, Shared_template_translate_sequences_matrix, share_informations
            shm1.close(); shm2.close()
            shm1.unlink(); shm2.unlink()
            del translate_sequence_matrix, Criterion
            if not np.any(Criteria):
                print("\nThere was no probe that meets input conditions.\n")
                sys.exit()
    Melted_df_Start_positions_set = Melted_df_Start_positions_set[Criteria]
    del Check_progressbar_update, translate_sequences_matrix, template_translate_candidate_matrix, Criteria, Index_candidate, Maximum_candidate_length
    if size_range != 0:
        Flexibility = [calculate_flexibility(seq) for seq in Melted_df_Start_positions_set['Sequence']]
        Sequence_Length = [len(seq) for seq in Melted_df_Start_positions_set['Sequence']]
        Melted_df_Start_positions_set.insert(2, 'Flexibility', Flexibility)
        Melted_df_Start_positions_set.insert(3, 'Sequence_Length', Sequence_Length)
        Melted_df_Start_positions_set = Melted_df_Start_positions_set.sort_values(['Flexibility', 'Sequence_Length'], ascending = [True, False])
        Melted_df_Start_positions_set = Melted_df_Start_positions_set[np.logical_not((Melted_df_Start_positions_set.iloc[:, 4:].map(lambda x:str(x))).duplicated())] if Pandas_later_210 else Melted_df_Start_positions_set[np.logical_not((Melted_df_Start_positions_set.iloc[:, 4:].applymap(lambda x:str(x))).duplicated())]
        Melted_df_Start_positions_set = Melted_df_Start_positions_set.iloc[Melted_df_Start_positions_set['Position'].abs().argsort()]
        Melted_df_Start_positions_set = Melted_df_Start_positions_set.drop(['Flexibility', 'Sequence_Length'], axis = 1)
    df_Start_positions = Melted_df_Start_positions_set.drop('Position', axis = 1)
    df_Start_positions = df_Start_positions.dropna(axis = 0)
    df_Start_positions = df_Start_positions.groupby("Sequence").aggregate(lambda x:list(it.chain.from_iterable(x)))
    df_Start_positions = df_Start_positions.map(lambda x:sorted(list(set(x)), key = abs)) if Pandas_later_210 else df_Start_positions.applymap(lambda x:sorted(list(set(x)), key = abs))
    df_Start_positions.columns = [name[i] for i in range(len(name) - 1, -1, -1)]
    if df_Start_positions.empty:
        print("\nThere was no probe that meets input conditions. Please change probe size or allowance value.\n")
        sys.exit()
    if (len(Exclude_sequences_list) != 0) & (str(Exclude_mode).lower() == 'standard'):
        Maximum_probe_length = np.max([len(index) for index in df_Start_positions.index])
        Index_sequence = [index + "".join(['N' for i in range(Maximum_probe_length - len(index))]) if len(index) < Maximum_probe_length else index for index in df_Start_positions.index]
        translate_probe_sequence_matrix = np.array([np.ravel(np.array([list('{:04b}'.format(int(n,16))) for n in list(seq.lower().translate(encode_table)) if re.sub(r'[0-9a-f]', '', n) == ''], dtype = int)) for seq in Index_sequence], dtype = int).astype(np.uint8)
        Criteria = []
        if GPU:
            if homology_calculation_chunks == "Auto":
                Test_chunk_size = 100
                Next_trial = True
                while Next_trial:
                    try:
                        Template_Vessel = {"Template_Vessel" + str(i): cp.zeros(shape = (Maximum_probe_length * 4, len(Exclude_sequences[-1]) - Maximum_probe_length + 1, ), dtype = cp.uint8) for i in range(1, CPU + 1)}
                        Chunk_Vessel = {"Chunk_Vessel" + str(i): cp.zeros(shape = (Test_chunk_size, len(Exclude_sequences[-1]) - Maximum_probe_length + 1, ), dtype = cp.uint8) for i in range(1, CPU + 1)}
                        Ref_Vessel = {"Ref_Vessel" + str(i): cp.zeros(shape = (Test_chunk_size, Maximum_probe_length * 4, ), dtype = cp.uint8) for i in range(1, CPU + 1)}
                        Test_chunk_size += 100
                        del Template_Vessel
                        del Chunk_Vessel
                        del Ref_Vessel
                        mempool.free_all_blocks()
                        if Test_chunk_size > df_Start_positions.shape[0]:
                            Next_trial = False
                    except:
                        Test_chunk_size = int(round(Test_chunk_size * 0.20, -1))
                        if "Template_Vessel" in locals(): del Template_Vessel
                        if "Chunk_Vessel" in locals(): del Chunk_Vessel
                        if "Ref_Vessel" in locals(): del Ref_Vessel
                        mempool.free_all_blocks()
                        Next_trial = False
                homology_calculation_chunks_for_exclude = copy.deepcopy(Test_chunk_size)
                updated_core_number = copy.deepcopy(CPU)
            else:
                homology_calculation_chunks_for_exclude = int(copy.deepcopy(homology_calculation_chunks))
                Test_core_number = copy.deepcopy(CPU)
                Template_Vessel = {}
                Chunk_Vessel = {}
                Ref_Vessel = {}
                try:
                    for core in range(1, Test_core_number + 1):
                        Template_Vessel.update({"Template_Vessel" + str(core): cp.zeros(shape = (int(Maximum_probe_length * 4 * 4), len(Exclude_sequences[-1]) - Maximum_probe_length + 1, ), dtype = cp.uint8)})
                        Chunk_Vessel.update({"Chunk_Vessel" + str(core): cp.zeros(shape = (int(homology_calculation_chunks_for_exclude * 4), len(Exclude_sequences[-1]) - Maximum_probe_length + 1, ), dtype = cp.uint8)})
                        Ref_Vessel.update({"Ref_Vessel" + str(core): cp.zeros(shape = (int(homology_calculation_chunks_for_exclude * 4), int(Maximum_probe_length * 4 * 4), ), dtype = cp.uint8)})
                    updated_core_number = int(core)
                except:
                    updated_core_number = int(np.max([1, core - 1]))
                del Template_Vessel, Chunk_Vessel, Ref_Vessel
            mempool.free_all_blocks()
        else:
            Available_memory = psutil.virtual_memory().available
            Vessel = np.zeros(shape = (Maximum_probe_length * 4, len(Exclude_sequences[-1]) - Maximum_probe_length + 1, ), dtype = np.uint8)
            Occupied_memory = Vessel.nbytes
            if homology_calculation_chunks == "Auto":
                homology_calculation_chunks_for_exclude = int(np.min([1000, np.max([1, math.floor(((Available_memory * 0.5 / CPU - Occupied_memory * 2) / (Occupied_memory / (Maximum_probe_length * 4))) / 5)])]))
                updated_core_number = int(copy.deepcopy(CPU))
            else:
                homology_calculation_chunks_for_exclude = int(copy.deepcopy(homology_calculation_chunks))
                updated_core_number = int(np.max([1, np.min([CPU, math.floor(Available_memory / ((Occupied_memory / (Maximum_probe_length * 4) * homology_calculation_chunks_for_exclude + Occupied_memory) * 5))])]))
            del Vessel
        Total_matrix_calculation = df_Start_positions.shape[0] / homology_calculation_chunks_for_exclude * exclude_sequences_number
        if progress_bar is not None: progress_bar.update(1)
        with tqdm(total = Total_matrix_calculation, leave = False, position = 1, unit = "tasks", unit_scale = True, desc = "    Filter candidate probe based on exclude sequences", bar_format = "{desc}: {percentage:.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}  {rate_fmt}]", smoothing = 0) as pbar:
            def Verbose_exclude_progressbar_update(Result):
                pbar.update(Result[0][0])
            for neseq in range(len(Exclude_sequences)):
                Criterion = []
                split_exclude_sequence = [Exclude_sequences[neseq][i:(i + Maximum_probe_length):] for i in range(len(Exclude_sequences[neseq]) - Maximum_probe_length + 1)]
                Nbase_count = [str(seq).lower().count("n") > allowance for seq in split_exclude_sequence]
                del split_exclude_sequence
                translate_exclude_sequence = np.array([list('{:04b}'.format(int(n,16))) for n in list(Exclude_sequences[neseq].lower().translate(encode_table)) if re.sub(r'[0-9a-f]', '', n) == ''], dtype = int).astype(np.uint8)
                translate_exclude_sequence_matrix = np.empty(((len(translate_exclude_sequence) - Maximum_probe_length + 1), 0), np.uint8)
                for i in range(Maximum_probe_length - 1):
                    translate_exclude_sequence_matrix = np.concatenate([translate_exclude_sequence_matrix.astype(np.uint8), translate_exclude_sequence[i:(i - Maximum_probe_length + 1):].astype(np.uint8)], axis = 1)
                translate_exclude_sequence_matrix = np.concatenate([translate_exclude_sequence_matrix, translate_exclude_sequence[(Maximum_probe_length - 1)::]], axis = 1).astype(np.uint8)
                translate_exclude_sequence_matrix[Nbase_count] = 0
                del Nbase_count
                translate_exclude_sequence_matrix = (translate_exclude_sequence_matrix.T).astype(np.uint8)
                Chunks_Start_positions = list(range(0, translate_probe_sequence_matrix.shape[0], homology_calculation_chunks_for_exclude))
                shm1 = SharedMemory(create = True, size = translate_exclude_sequence_matrix.nbytes)
                Shared_translate_sequence_matrix = np.ndarray(shape = translate_exclude_sequence_matrix.shape, dtype = translate_exclude_sequence_matrix.dtype, buffer = shm1.buf)
                Shared_translate_sequence_matrix[:] = translate_exclude_sequence_matrix[:]
                shm2 = SharedMemory(create = True, size = translate_probe_sequence_matrix.nbytes)
                Shared_template_translate_sequences_matrix = np.ndarray(shape = translate_probe_sequence_matrix.shape, dtype = translate_probe_sequence_matrix.dtype, buffer = shm2.buf)
                Shared_template_translate_sequences_matrix[:] = translate_probe_sequence_matrix[:]
                share_informations = ((shm1.name, translate_exclude_sequence_matrix.shape, translate_exclude_sequence_matrix.dtype, ), (shm2.name, translate_probe_sequence_matrix.shape, translate_probe_sequence_matrix.dtype, ), ("", ), ("", ))
                update_factor = (df_Start_positions.shape[0]/len(translate_probe_sequence_matrix))
                parameter = { \
                    'homology_calculation_chunks': homology_calculation_chunks_for_exclude, \
                    'share_informations': share_informations, \
                    'probe_size': Maximum_probe_length, \
                    'allowance': int(0), \
                    'Mode': "Exclude", \
                    'GPU': GPU, \
                    'Allowance_adjustment': False, \
                    'input_sequences_length': exclude_sequences_length[neseq], \
                    'interval_distance': int(0), \
                    'Maximum_annealing_site_number': int(len(Exclude_sequences[neseq])), \
                    'Annealing_site_number_threshold': int(len(Exclude_sequences[neseq])), \
                    'update_factor': update_factor, \
                    'Interval_factor': int(1) \
                }
                multi_homology_calculation = partial(homology_calculation, parameter = parameter)
                with get_context("spawn").Pool(processes = updated_core_number, initializer = init_worker) as pl:
                    try:
                        outputs = [pl.apply_async(multi_homology_calculation, args = (csp, ), callback = Verbose_exclude_progressbar_update) for csp in Chunks_Start_positions]
                        outputs = [output.get() for output in outputs]
                    except KeyboardInterrupt:
                        pl.terminate()
                        pl.join()
                        pl.close()
                        print("\n\n --- Keyboard Interrupt ---")
                        sys.exit()
                [Criterion.extend(output[1]) for output in outputs]
                Criteria.append(Criterion)
                del Shared_translate_sequence_matrix, Shared_template_translate_sequences_matrix, share_informations
                shm1.close(); shm2.close()
                shm1.unlink(); shm2.unlink()
                del translate_exclude_sequence_matrix, translate_exclude_sequence
            Criteria = np.array([np.all(criteria) for criteria in zip(*Criteria)]).astype(bool)
        if not np.any(Criteria):
            print("\nThere was no probe that meets input conditions.\n")
            sys.exit()
        df_Start_positions = df_Start_positions[Criteria]
        del Verbose_exclude_progressbar_update, translate_probe_sequence_matrix, Criteria
    return df_Start_positions