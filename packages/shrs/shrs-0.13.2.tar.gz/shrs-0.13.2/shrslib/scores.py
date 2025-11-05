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
import math
import copy
import itertools as it
import numpy as np
from tqdm import tqdm
import pandas as pd
from shrslib.basicfunc import nucleotide, nucleotide_sequence, complementary_sequence
try:
    import cupy as cp
    mempool = cp.get_default_memory_pool()
except:
    pass

def calculate_flexibility(sequence, detailed = False):
    '''
    Calculate the score for degeneracy.

    Parameters
    ----------
    sequence: str, list or tuple
    detailed: bool
        The score when specifying True will be more accurate. (default: False)

    Returns
    -------
    Flexibility: float
        The higher the score is, the more wobble base pairs the sequence has.

    '''
    if detailed:
        if (type(sequence) == list) | (type(sequence) == tuple):
            sequence = [str(seq).upper() for seq in sequence]
            each_flexibility = [(seq.count("N") * 1 + seq.count("V") * 0.9902 + seq.count("B") * 0.9901 + seq.count("D") * 0.9900 + seq.count("H") * 0.9899 + seq.count("S") * 0.8502 + seq.count("K") * 0.8501 + seq.count("M") * 0.8500 + seq.count("W") * 0.8499 + seq.count("R") * 0.7501 + seq.count("Y") * 0.7499)/len(seq) if len(re.sub(r"[ATGC]", "", seq)) != 0 else 0.25/len(seq) for seq in sequence]
            flexibility = np.array(each_flexibility).prod() ** (1/len(sequence))
        else:
            sequence = str(sequence).upper()
            flexibility = (sequence.count("N") * 1 + sequence.count("V") * 0.9902 + sequence.count("B") * 0.9901 + sequence.count("D") * 0.9900 + sequence.count("H") * 0.9899 + sequence.count("S") * 0.9502 + sequence.count("K") * 0.9501 + sequence.count("M") * 0.9500 + sequence.count("W") * 0.9499 + sequence.count("R") * 0.7501 + sequence.count("Y") * 0.7499)/len(sequence)
        return float(flexibility)
    else:
        if (type(sequence) == list) | (type(sequence) == tuple):
            sequence = [str(seq).upper() for seq in sequence]
            each_flexibility = [(len(re.sub(r"[ATGCRY]", "", seq))+(len(seq)-len(re.sub(r"[RY]", "", seq)))*0.75)/len(seq) if len(re.sub(r"[ATGC]", "", seq)) != 0 else 0.25/len(seq) for seq in sequence]
            flexibility = np.array(each_flexibility).prod() ** (1/len(sequence))
        else:
            sequence = str(sequence).upper()
            flexibility = (len(re.sub(r"[ATGCRY]", "", sequence))+(len(sequence)-len(re.sub(r"[RY]", "", sequence)))*0.75)/len(sequence)
        return float(flexibility)

def calculate_score(seq1, seq2):
    '''
    Calculate the similarity between two sequences. The higher the value is, the more similar the two sequences are.

    Parameters
    ----------
    seq1: str or nucleotide_sequence
    seq2: str or nucleotide_sequence

    Returns
    -------
    Similarity_score: float

    '''
    s1 = np.array([list(nucleotide(nt).code) + list(map(lambda x:float(x)/2, list(nucleotide(nt).type_code))) for nt in list(seq1)], dtype = float).astype(np.float32)
    s2 = np.array([list(nucleotide(nt).code) + list(map(lambda x:float(x)/2, list(nucleotide(nt).type_code))) for nt in list(seq2)], dtype = float).astype(np.float32)
    score = np.sum(np.max(s1 * s2, axis = 1))
    score = score/len(seq1)
    return score

def calculate_diff_length_score(sequence_pair_set, Reverse = False, pair_logical = False, return_sequence_name = False):
    '''
    Calculate similarity between two different length sequences. The higher the value is, the more similar the two sequences are.

    Parameters
    ----------
    sequence_pair_set: tuple of two sequences, list of two sequences or list of them
    Reverse: bool
    pair_logical: bool
        Return True if the score is 1, when 'pair_logical' is True.
    return_sequence_name: bool
        Return two input sequences and its score when 'return_sequence_name' is True.

    Returns
    -------
    Similarity_score: float
        
    '''
    if pair_logical:
        if (type(sequence_pair_set[0]) == list) | (type(sequence_pair_set[0]) == tuple): 
            seqsA, seqsB = sequence_pair_set
            if Reverse:
                seqA1, seqA2 = seqsA
                seqB2, seqB1 = seqsB
            else:
                seqA1, seqA2 = seqsA
                seqB1, seqB2 = seqsB
            if len(seqA1) == len(seqB1):
                score1 = calculate_score(seqA1, seqB1)
            elif len(seqA1) < len(seqB1):
                score1 = np.max([calculate_score(seqA1, seqB1[i:(i+len(seqA1)):]) for i in range(len(seqB1)-len(seqA1)+1)])
            else:
                score1 = np.max([calculate_score(seqA1[i:(i+len(seqB1)):], seqB1) for i in range(len(seqA1)-len(seqB1)+1)])
            if len(seqA2) == len(seqB2):
                score2 = calculate_score(seqA2, seqB2)
            elif len(seqA2) < len(seqB2):
                score2 = np.max([calculate_score(seqA2, seqB2[i:(i+len(seqA2)):]) for i in range(len(seqB2)-len(seqA2)+1)])
            else:
                score2 = np.max([calculate_score(seqA2[i:(i+len(seqB2)):], seqB2) for i in range(len(seqA2)-len(seqB2)+1)])
            score = score1 * score2
            if score == 1:
                if return_sequence_name:
                    return sequence_pair_set
                else:
                    return True
            else:
                if return_sequence_name:
                    return None
                else:
                    return False
        else:
            seqA1, seqB1 = sequence_pair_set
            if len(seqA1) == len(seqB1):
                score = calculate_score(seqA1, seqB1)
            elif len(seqA1) < len(seqB1):
                score = np.max([calculate_score(seqA1, seqB1[i:(i+len(seqA1)):]) for i in range(len(seqB1)-len(seqA1)+1)])
            else:
                score = np.max([calculate_score(seqA1[i:(i+len(seqB1)):], seqB1) for i in range(len(seqA1)-len(seqB1)+1)])
            if score == 1:
                if return_sequence_name:
                    return sequence_pair_set
                else:
                    return True
            else:
                if return_sequence_name:
                    return None
                else:
                    return False
    else:
        if (type(sequence_pair_set[0]) == list) | (type(sequence_pair_set[0]) == tuple): 
            seqsA, seqsB = sequence_pair_set
            if Reverse:
                seqA1, seqA2 = seqsA
                seqB2, seqB1 = seqsB
            else:
                seqA1, seqA2 = seqsA
                seqB1, seqB2 = seqsB
            if len(seqA1) == len(seqB1):
                score1 = calculate_score(seqA1, seqB1)
            elif len(seqA1) < len(seqB1):
                score1 = np.max([calculate_score(seqA1, seqB1[i:(i+len(seqA1)):]) for i in range(len(seqB1)-len(seqA1)+1)])
            else:
                score1 = np.max([calculate_score(seqA1[i:(i+len(seqB1)):], seqB1) for i in range(len(seqA1)-len(seqB1)+1)])
            if len(seqA2) == len(seqB2):
                score2 = calculate_score(seqA2, seqB2)
            elif len(seqA2) < len(seqB2):
                score2 = np.max([calculate_score(seqA2, seqB2[i:(i+len(seqA2)):]) for i in range(len(seqB2)-len(seqA2)+1)])
            else:
                score2 = np.max([calculate_score(seqA2[i:(i+len(seqB2)):], seqB2) for i in range(len(seqA2)-len(seqB2)+1)])
            score = score1 * score2
            if return_sequence_name:
                return [sequence_pair_set, score]
            else:
                return score
        else:
            seqA1, seqB1 = sequence_pair_set
            if len(seqA1) == len(seqB1):
                score = calculate_score(seqA1, seqB1)
            elif len(seqA1) < len(seqB1):
                score = np.max([calculate_score(seqA1, seqB1[i:(i+len(seqA1)):]) for i in range(len(seqB1)-len(seqA1)+1)])
            else:
                score = np.max([calculate_score(seqA1[i:(i+len(seqB1)):], seqB1) for i in range(len(seqA1)-len(seqB1)+1)])
            if return_sequence_name:
                return [sequence_pair_set, score]
            else:
                return score

def fragment_size_distance(array, sum = False, method = 'average'):
    '''
    Function for calculating the distance based on values in array.

    Parameters
    ----------
    array: list, tuple or numpy.ndarray
    sum: bool

    Returns
    -------
    distance: float
    '''
    array = [arr for arr in array if np.all(pd.notnull(arr))]
    array = [arr if ((type(arr) is list) | (type(arr) is tuple) | (type(arr) is np.ndarray)) else [arr] for arr in array]
    new_array = it.combinations(array, 2)
    Result = []
    for arr1, arr2 in new_array:
        darr1 = list(copy.deepcopy(arr1)); darr2 = list(copy.deepcopy(arr2))
        if len(arr1) > len(arr2):
            arr1_i_arr2 = []
            while len(darr2) > 0:
                distance = np.abs(np.array([np.array(darr1) - b for b in darr2]))
                arr1_i_arr2.append((np.array(darr1)[np.any(distance == np.min(distance), axis = 0)][0] - np.array(darr2)[np.any(distance == np.min(distance), axis = 1)][0]))
                darr1.remove(np.array(darr1)[np.any(distance == np.min(distance), axis = 0)][0])
                darr2.remove(np.array(darr2)[np.any(distance == np.min(distance), axis = 1)][0])
            REMAINDER = [np.abs(np.array(list(arr1) + list(arr2)) - b) for b in darr1]
            REMAINDER = np.sum([min([rem for rem in remain if rem != 0], default = 0) for remain in REMAINDER])
            Result.append(np.sum(np.array(arr1_i_arr2) ** 2) ** (1/2) + REMAINDER)
        elif len(arr1) < len(arr2):
            arr2_i_arr1 = []
            while len(darr1) > 0:
                distance = np.abs(np.array([np.array(darr2) - b for b in darr1]))
                arr2_i_arr1.append((np.array(darr2)[np.any(distance == np.min(distance), axis = 0)][0] - np.array(darr1)[np.any(distance == np.min(distance), axis = 1)][0]))
                darr2.remove(np.array(darr2)[np.any(distance == np.min(distance), axis = 0)][0])
                darr1.remove(np.array(darr1)[np.any(distance == np.min(distance), axis = 1)][0])
            REMAINDER = [np.abs(np.array(list(arr1) + list(arr2)) - b) for b in darr2]
            REMAINDER = np.sum([min([rem for rem in remain if rem != 0], default = 0) for remain in REMAINDER])
            Result.append(np.sum(np.array(arr2_i_arr1) ** 2) ** (1/2) + REMAINDER)
        else:
            arr1_arr2 = []
            while len(darr2) > 0:
                distance = np.abs(np.array([np.array(darr1) - b for b in darr2]))
                arr1_arr2.append((np.array(darr1)[np.any(distance == np.min(distance), axis = 0)][0] - np.array(darr2)[np.any(distance == np.min(distance), axis = 1)][0]))
                darr1.remove(np.array(darr1)[np.any(distance == np.min(distance), axis = 0)][0])
                darr2.remove(np.array(darr2)[np.any(distance == np.min(distance), axis = 1)][0])
            Result.append(np.sum(np.array(arr1_arr2) ** 2) ** (1/2))
    if len(Result) == 0:
        Result_average = int(0)
        Result_maximum = int(0)
        Result_minimum = int(0)
    elif sum:
        Result_average =  np.sum(Result) / len(Result)
        Result_maximum = np.max(Result)
        Result_minimum = np.min(Result)
    else:
        Result_average =  np.prod(Result) ** (1/len(Result))
        Result_maximum = np.max(Result)
        Result_minimum = np.min(Result)
    if method == 'average':
        return Result_average
    elif method == 'max':
        return Result_maximum
    elif method == 'min':
        return Result_minimum
    elif method == 'all':
        return [Result_average, Result_minimum, Result_maximum]
    else:
        return int(0)

def array_diff(arr1, arr2, lower, upper, logical = False, separation_key = []):
    '''
    Calculate the difference between two arrays.

    Parameters
    ----------
    arr1: int, float, list, tuple, numpy.ndarray
    arr2: int, float, list, tuple, numpy.ndarray
    lower: int, float
    upper: int, float
    logical: bool
    separation_key: int, float, list of int, list of float

    Returns
    -------
    Result: list
        A list containing the subtract value is returned at default settings.
        When the logical is True, it returns a logical value.
    
    Notes
    -----
    Subtract arr1 from arr2.
    Subtraction across Separation_key is NOT performed. 
    For example, arr1 is [1, 1000, 10000], arr2 is [50, 1100, 10150], lower is 40 and upper is 400.
    The answer [49, 100, 150] will be obtained when the Separation key is the default value (default: −1).
    However, when the Separation key is 1050, [49, 150] will be obtained.

    '''
    iterable_or_not1 = np.any([((type(arr_comp) is list) | (type(arr_comp) is tuple) | (type(arr_comp) is np.ndarray)) for arr_comp in arr1])
    iterable_or_not2 = np.any([((type(arr_comp) is list) | (type(arr_comp) is tuple) | (type(arr_comp) is np.ndarray)) for arr_comp in arr2])
    if iterable_or_not1 & iterable_or_not2:
        if separation_key == []:
            separation_key = [[-1] for i in range(len(list(zip(arr1, arr2))))]
        elif (type(separation_key) is int) | (type(separation_key) is float):
            separation_key = [[separation_key] for i in range(len(list(zip(arr1, arr2))))]
        diff_ans = [np.array([b - a if ((pd.notna(a) & pd.notna(b)) & (np.logical_not(np.any((a <= np.array(sk)).astype(bool) & (np.array(sk) <= b).astype(bool))))) else np.nan for a in array1 for b in array2]) if (np.any(pd.notna(array1)) & np.any(pd.notna(array2))) else np.nan for array1, array2, sk in zip(arr1, arr2, separation_key)]
    elif iterable_or_not1 & np.logical_not(iterable_or_not2):
        if separation_key == []:
            separation_key = [[-1] for i in range(len(list(it.product(arr1, [arr2]))))]
        elif (type(separation_key) is int) | (type(separation_key) is float):
            separation_key = [[separation_key] for i in range(len(list(zip(arr1, arr2))))]
        diff_ans = [np.array([b - a if ((pd.notna(a) & pd.notna(b)) & (np.logical_not(np.any((a <= np.array(sk)).astype(bool) & (np.array(sk) <= b).astype(bool))))) else np.nan for a in array[0] for b in array[1]]) if (np.any(pd.notna(array[0])) & np.any(pd.notna(array[1]))) else np.nan for array, sk in zip(it.product(arr1, [arr2]), separation_key)]
    elif np.logical_not(iterable_or_not1) & iterable_or_not2:
        if separation_key == []:
            separation_key = [[-1] for i in range(len(list(it.product([arr1], arr2))))]
        elif (type(separation_key) is int) | (type(separation_key) is float):
            separation_key = [[separation_key] for i in range(len(list(zip(arr1, arr2))))]
        diff_ans = [np.array([b - a if ((pd.notna(a) & pd.notna(b)) & (np.logical_not(np.any((a <= np.array(sk)).astype(bool) & (np.array(sk) <= b).astype(bool))))) else np.nan for a in array[0] for b in array[1]]) if (np.any(pd.notna(array[0])) & np.any(pd.notna(array[1]))) else np.nan for array, sk in zip(it.product([arr1], arr2), separation_key)]
    else:
        if separation_key == []:
            separation_key = [-1]
        elif (type(separation_key) is int) | (type(separation_key) is float):
            separation_key = [separation_key]
        diff_ans = np.array([b - a if ((pd.notna(a) & pd.notna(b)) & (np.logical_not(np.any((a <= np.array(separation_key)).astype(bool) & (np.array(separation_key) <= b).astype(bool))))) else np.nan for a in arr1 for b in arr2])
        if logical:
            return np.any((diff_ans > lower) & (diff_ans < upper))
        else:
            return diff_ans[(diff_ans > lower) & (diff_ans < upper)]
    if logical:
        res = np.all([(np.any((ans > lower) & (ans < upper)) & np.all((ans > lower) | (ans <= 0) | (np.isnan(ans))) & np.all((ans < upper) | (ans >= int(math.ceil(np.max([upper + 2000, upper * 5 / 3])))) | (np.isnan(ans)))) if np.any(pd.notna(ans)) else True for ans in diff_ans])
    else:
        res = [ans[(ans > lower) & (ans < upper)] if np.any(pd.notnull(ans)) else np.array([]) for ans in diff_ans]
    return res

def arr_length_in_arr(arr):
    '''
    Return the number of element in array. (private)

    '''
    Result = [len(a) if ((type(a) is list) | (type(a) is tuple) | (type(a) is np.ndarray)) else 0 for a in arr]
    return Result

def pairwise_identity(alignment):
    '''
    Return pairwise identity score. (private)

    '''
    identity_score = alignment[0].score / len(alignment[0][0])
    return identity_score

def sequence_duplicated(sequence_list, keep = 'first', local = False, complementary = False):
    '''
    Extract duplicated sequences in list, tuple, numpy.ndarray or pandas.Series.

    Parameters
    ----------
    sequence_list: list, tuple, numpy.ndarray or pandas.Series
    keep: str
        Choose 'first', 'last', 'both', or 'null'. 'first' means that the first sequence in duplicates remains, and the others in its duplicates are discarded.
    local: bool
        Judge whether the sequence is duplicated or not based on a partial sequence when the local is 'True'.
    complementary: bool

    Returns
    -------
    Result: list
        Return True when the sequence is duplicated. 

    '''
    if (type(sequence_list) is np.ndarray) | (type(sequence_list) is pd.Series):
        sequence_list = sequence_list.tolist()
    elif type(sequence_list) is tuple:
        sequence_list = list(sequence_list)
    elif type(sequence_list) is list:
        pass
    else:
        raise TypeError("Not supported format. This function supports list, tuple, numpy.ndarray or pandas.Series")
    if keep == 'first':
        if local:
            if complementary:
                Res1 = np.array([np.max([calculate_diff_length_score((sequence_list[i], sequence_list[j], )) for j in range(len(sequence_list[0 : i]))]) == 1.0 if len(sequence_list[0 : i]) != 0 else False for i in range(len(sequence_list))])
                Res2 = np.array([np.max([calculate_diff_length_score((complementary_sequence(sequence_list[i]), sequence_list[j], )) for j in range(len(sequence_list[0 : i]))]) == 1.0 if len(sequence_list[0 : i]) != 0 else False for i in range(len(sequence_list))])
                Result = Res1 | Res2
            else:
                Result = np.array([np.max([calculate_diff_length_score((sequence_list[i], sequence_list[j], )) for j in range(len(sequence_list[0 : i]))]) == 1.0 if len(sequence_list[0 : i]) != 0 else False for i in range(len(sequence_list))])
        else:
            if complementary:
                Res1 = np.array([np.max([calculate_score(sequence_list[i], sequence_list[j]) if len(sequence_list[i]) == len(sequence_list[j]) else False for j in range(len(sequence_list[0 : i]))]) == 1.0 if len(sequence_list[0 : i]) != 0 else False for i in range(len(sequence_list))])
                Res2 = np.array([np.max([calculate_score(complementary_sequence(sequence_list[i]), sequence_list[j]) if len(sequence_list[i]) == len(sequence_list[j]) else False for j in range(len(sequence_list[0 : i]))]) == 1.0 if len(sequence_list[0 : i]) != 0 else False for i in range(len(sequence_list))])
                Result = Res1 | Res2
            else:
                Result = np.array([np.max([calculate_score(sequence_list[i], sequence_list[j]) if len(sequence_list[i]) == len(sequence_list[j]) else False for j in range(len(sequence_list[0 : i]))]) == 1.0 if len(sequence_list[0 : i]) != 0 else False for i in range(len(sequence_list))])
    elif keep == 'last':
        if local:
            if complementary:
                Res1 = np.array([np.max([calculate_diff_length_score((sequence_list[i], sequence_list[i + j + 1], )) for j in range(len(sequence_list[(i + 1):]))]) == 1.0 if len(sequence_list[(i + 1):]) != 0 else False for i in range(len(sequence_list))])
                Res2 = np.array([np.max([calculate_diff_length_score((complementary_sequence(sequence_list[i]), sequence_list[i + j + 1], )) for j in range(len(sequence_list[(i + 1):]))]) == 1.0 if len(sequence_list[(i + 1):]) != 0 else False for i in range(len(sequence_list))])
                Result = Res1 | Res2
            else:
                Result = np.array([np.max([calculate_diff_length_score((sequence_list[i], sequence_list[i + j + 1], )) for j in range(len(sequence_list[(i + 1):]))]) == 1.0 if len(sequence_list[(i + 1):]) != 0 else False for i in range(len(sequence_list))])
        else:
            if complementary:
                Res1 = np.array([np.max([calculate_score(sequence_list[i], sequence_list[i + j + 1]) if len(sequence_list[i]) == len(sequence_list[i + j + 1]) else False for j in range(len(sequence_list[(i + 1):]))]) == 1.0 if len(sequence_list[(i + 1):]) != 0 else False for i in range(len(sequence_list))])
                Res2 = np.array([np.max([calculate_score(complementary_sequence(sequence_list[i]), sequence_list[i + j + 1]) if len(sequence_list[i]) == len(sequence_list[i + j + 1]) else False for j in range(len(sequence_list[(i + 1):]))]) == 1.0 if len(sequence_list[(i + 1):]) != 0 else False for i in range(len(sequence_list))])
                Result = Res1 | Res2
            else:
                Result = np.array([np.max([calculate_score(sequence_list[i], sequence_list[i + j + 1]) if len(sequence_list[i]) == len(sequence_list[i + j + 1]) else False for j in range(len(sequence_list[(i + 1):]))]) == 1.0 if len(sequence_list[(i + 1):]) != 0 else False for i in range(len(sequence_list))])
    elif keep == 'both':
        if local:
            if complementary:
                Res1 = np.array([np.max([calculate_diff_length_score((sequence_list[i], sequence_list[j], )) for j in range(len(sequence_list[0 : i]))]) == 1.0 if len(sequence_list[0 : i]) != 0 else False for i in range(len(sequence_list))])
                Res2 = np.array([np.max([calculate_diff_length_score((complementary_sequence(sequence_list[i]), sequence_list[j], )) for j in range(len(sequence_list[0 : i]))]) == 1.0 if len(sequence_list[0 : i]) != 0 else False for i in range(len(sequence_list))])
                Res3 = np.array([np.max([calculate_diff_length_score((sequence_list[i], sequence_list[i + j + 1], )) for j in range(len(sequence_list[(i + 1):]))]) == 1.0 if len(sequence_list[(i + 1):]) != 0 else False for i in range(len(sequence_list))])
                Res4 = np.array([np.max([calculate_diff_length_score((complementary_sequence(sequence_list[i]), sequence_list[i + j + 1], )) for j in range(len(sequence_list[(i + 1):]))]) == 1.0 if len(sequence_list[(i + 1):]) != 0 else False for i in range(len(sequence_list))])
                Result = (Res1 | Res2) & (Res3 | Res4)
            else:
                Res1 = np.array([np.max([calculate_diff_length_score((sequence_list[i], sequence_list[j], )) for j in range(len(sequence_list[0 : i]))]) == 1.0 if len(sequence_list[0 : i]) != 0 else False for i in range(len(sequence_list))])
                Res2 = np.array([np.max([calculate_diff_length_score((sequence_list[i], sequence_list[i + j + 1], )) for j in range(len(sequence_list[(i + 1):]))]) == 1.0 if len(sequence_list[(i + 1):]) != 0 else False for i in range(len(sequence_list))])
                Result = Res1 & Res2
        else:
            if complementary:
                Res1 = np.array([np.max([calculate_score(sequence_list[i], sequence_list[j]) if len(sequence_list[i]) == len(sequence_list[j]) else False for j in range(len(sequence_list[0 : i]))]) == 1.0 if len(sequence_list[0 : i]) != 0 else False for i in range(len(sequence_list))])
                Res2 = np.array([np.max([calculate_score(complementary_sequence(sequence_list[i]), sequence_list[j]) if len(sequence_list[i]) == len(sequence_list[j]) else False for j in range(len(sequence_list[0 : i]))]) == 1.0 if len(sequence_list[0 : i]) != 0 else False for i in range(len(sequence_list))])
                Res3 = np.array([np.max([calculate_score(sequence_list[i], sequence_list[i + j + 1]) if len(sequence_list[i]) == len(sequence_list[i + j + 1]) else False for j in range(len(sequence_list[(i + 1):]))]) == 1.0 if len(sequence_list[(i + 1):]) != 0 else False for i in range(len(sequence_list))])
                Res4 = np.array([np.max([calculate_score(complementary_sequence(sequence_list[i]), sequence_list[i + j + 1]) if len(sequence_list[i]) == len(sequence_list[i + j + 1]) else False for j in range(len(sequence_list[(i + 1):]))]) == 1.0 if len(sequence_list[(i + 1):]) != 0 else False for i in range(len(sequence_list))])
                Result = (Res1 | Res2) & (Res3 | Res4)
            else:
                Res1 = np.array([np.max([calculate_score(sequence_list[i], sequence_list[j]) if len(sequence_list[i]) == len(sequence_list[j]) else False for j in range(len(sequence_list[0 : i]))]) == 1.0 if len(sequence_list[0 : i]) != 0 else False for i in range(len(sequence_list))])
                Res2 = np.array([np.max([calculate_score(sequence_list[i], sequence_list[i + j + 1]) if len(sequence_list[i]) == len(sequence_list[i + j + 1]) else False for j in range(len(sequence_list[(i + 1):]))]) == 1.0 if len(sequence_list[(i + 1):]) != 0 else False for i in range(len(sequence_list))])
                Result = Res1 & Res2
    elif keep == 'null':
        if local:
            if complementary:
                Res1 = np.array([np.max([calculate_diff_length_score((sequence_list[i], sequence_list[j], )) for j in range(len(sequence_list[0 : i]))]) == 1.0 if len(sequence_list[0 : i]) != 0 else False for i in range(len(sequence_list))])
                Res2 = np.array([np.max([calculate_diff_length_score((complementary_sequence(sequence_list[i]), sequence_list[j], )) for j in range(len(sequence_list[0 : i]))]) == 1.0 if len(sequence_list[0 : i]) != 0 else False for i in range(len(sequence_list))])
                Res3 = np.array([np.max([calculate_diff_length_score((sequence_list[i], sequence_list[i + j + 1], )) for j in range(len(sequence_list[(i + 1):]))]) == 1.0 if len(sequence_list[(i + 1):]) != 0 else False for i in range(len(sequence_list))])
                Res4 = np.array([np.max([calculate_diff_length_score((complementary_sequence(sequence_list[i]), sequence_list[i + j + 1], )) for j in range(len(sequence_list[(i + 1):]))]) == 1.0 if len(sequence_list[(i + 1):]) != 0 else False for i in range(len(sequence_list))])
                Result = (Res1 | Res2) | (Res3 | Res4)
            else:
                Res1 = np.array([np.max([calculate_diff_length_score((sequence_list[i], sequence_list[j], )) for j in range(len(sequence_list[0 : i]))]) == 1.0 if len(sequence_list[0 : i]) != 0 else False for i in range(len(sequence_list))])
                Res2 = np.array([np.max([calculate_diff_length_score((sequence_list[i], sequence_list[i + j + 1], )) for j in range(len(sequence_list[(i + 1):]))]) == 1.0 if len(sequence_list[(i + 1):]) != 0 else False for i in range(len(sequence_list))])
                Result = Res1 | Res2
        else:
            if complementary:
                Res1 = np.array([np.max([calculate_score(sequence_list[i], sequence_list[j]) if len(sequence_list[i]) == len(sequence_list[j]) else False for j in range(len(sequence_list[0 : i]))]) == 1.0 if len(sequence_list[0 : i]) != 0 else False for i in range(len(sequence_list))])
                Res2 = np.array([np.max([calculate_score(complementary_sequence(sequence_list[i]), sequence_list[j]) if len(sequence_list[i]) == len(sequence_list[j]) else False for j in range(len(sequence_list[0 : i]))]) == 1.0 if len(sequence_list[0 : i]) != 0 else False for i in range(len(sequence_list))])
                Res3 = np.array([np.max([calculate_score(sequence_list[i], sequence_list[i + j + 1]) if len(sequence_list[i]) == len(sequence_list[i + j + 1]) else False for j in range(len(sequence_list[(i + 1):]))]) == 1.0 if len(sequence_list[(i + 1):]) != 0 else False for i in range(len(sequence_list))])
                Res4 = np.array([np.max([calculate_score(complementary_sequence(sequence_list[i]), sequence_list[i + j + 1]) if len(sequence_list[i]) == len(sequence_list[i + j + 1]) else False for j in range(len(sequence_list[(i + 1):]))]) == 1.0 if len(sequence_list[(i + 1):]) != 0 else False for i in range(len(sequence_list))])
                Result = (Res1 | Res2) | (Res3 | Res4)
            else:
                Res1 = np.array([np.max([calculate_score(sequence_list[i], sequence_list[j]) if len(sequence_list[i]) == len(sequence_list[j]) else False for j in range(len(sequence_list[0 : i]))]) == 1.0 if len(sequence_list[0 : i]) != 0 else False for i in range(len(sequence_list))])
                Res2 = np.array([np.max([calculate_score(sequence_list[i], sequence_list[i + j + 1]) if len(sequence_list[i]) == len(sequence_list[i + j + 1]) else False for j in range(len(sequence_list[(i + 1):]))]) == 1.0 if len(sequence_list[(i + 1):]) != 0 else False for i in range(len(sequence_list))])
                Result = Res1 | Res2
    else:
        print("Choose 'keep' option from {'first', 'last', 'both', 'null'}")
        Result = None
    Result = Result.tolist() if Result is not None else None
    return Result