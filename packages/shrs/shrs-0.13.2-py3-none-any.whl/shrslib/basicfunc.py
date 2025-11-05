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
import shutil
import warnings
import re
from chardet import detect
from chardet.universaldetector import UniversalDetector
import signal
import math
import numpy as np
import pandas as pd
import itertools as it
from scipy.cluster.hierarchy import distance, linkage, fcluster
try:
    import cupy as cp
    mempool = cp.get_default_memory_pool()
except:
    pass

def init_worker():
    """
    Keyboard interrapt function during parallel process. (private)

    """
    signal.signal(signal.SIGINT, signal.SIG_IGN)

class nucleotide():
    """
    Single nucleotide definition.

    Attributes
    ----------
    base: str
        Nucleotide, One character description.
    Tm: float
        Tm value used for nucleotide sequence Tm value calculation by GC method.
    code: str
        binary code described nucleotide.
    """
    def __init__(self, args):
        """
        Parameters
        ----------
        args: str
            Nucleotide, One character description.
        """
        self.description = args.lower()
        if args in ("a", "A"):
            self.base = args.lower()
            self.Tm = 2.0
            self.code = '{:04b}'.format(int('1',16))
        elif args in ("t", "T"):
            self.base = args.lower()
            self.Tm = 2.0
            self.code = '{:04b}'.format(int('8',16))
        elif args in ("g", "G"):
            self.base = args.lower()
            self.Tm = 4.0
            self.code = '{:04b}'.format(int('2',16))
        elif args in ("c", "C"):
            self.base = args.lower()
            self.Tm = 4.0
            self.code = '{:04b}'.format(int('4',16))
        elif args in ("b", "B"):
            self.base = ("c", "g", "t")
            self.Tm = 3.33
            self.code = '{:04b}'.format(int('e',16))
        elif args in ("d", "D"):
            self.base = ("a", "g", "t")
            self.Tm = 2.67
            self.code = '{:04b}'.format(int('b',16))
        elif args in ("h", "H"):
            self.base = ("a", "c", "t")
            self.Tm = 2.67
            self.code = '{:04b}'.format(int('d',16))
        elif args in ("k", "K"):
            self.base = ("g", "t")
            self.Tm = 3.0
            self.code = '{:04b}'.format(int('a',16))
        elif args in ("m", "M"):
            self.base = ("a", "c")
            self.Tm = 3.0
            self.code = '{:04b}'.format(int('5',16))
        elif args in ("n", "N"):
            self.base = ("a", "c", "g", "t")
            self.Tm = 3.0
            self.code = '{:04b}'.format(int('f',16))
        elif args in ("r", "R"):
            self.base = ("a", "g")
            self.Tm = 3.0
            self.code = '{:04b}'.format(int('3',16))
        elif args in ("s", "S"):
            self.base = ("c", "g")
            self.Tm = 4.0
            self.code = '{:04b}'.format(int('6',16))
        elif args in ("v", "V"):
            self.base = ("a", "c", "g")
            self.Tm = 3.33
            self.code = '{:04b}'.format(int('7',16))
        elif args in ("w", "W"):
            self.base = ("a", "t")
            self.Tm = 2.0
            self.code = '{:04b}'.format(int('9',16))
        elif args in ("x", "X"):
            self.base = args.lower()
            self.Tm = 0.0
            self.code = '{:04b}'.format(int('0',16))
        elif args in ("y", "Y"):
            self.base = ("c", "t")
            self.Tm = 3.0
            self.code = '{:04b}'.format(int('c',16))
        else:
            self.base = ("a", "c", "g", "t")
            self.Tm = 3.0
            self.code = '{:04b}'.format(int('f',16))
        if args in ("a", "g", "r", "A", "G", "R"):
            self.type = "Pr"
            self.type_code = "01"
        elif args in ("c", "t", "y", "C", "T", "Y"):
            self.type = "Py"
            self.type_code = "10"
        elif args in ("n", "N"):
            self.type = "nt"
            self.type_code = "00"
        else:
            self.type = "Unknown"
            self.type_code = "00"
    def __repr__(self):
        return self.description
    def __str__(self):
        return self.description

class nucleotide_sequence(str):
    """
    Nucleotide sequence definition.

    Attributes
    ----------
    string: str
        Input character
    description: str
        Nuclotide sequence.
    sequence_length: int
        Nucleotide sequence length (nt).

    """
    def __init__(self, sequence):
        """
        Parameters
        ----------
        sequence: str
            Nucleotide sequence.
        """
        self.string = sequence
        self.description = sequence.upper()
        self.sequence_length = len(sequence)
    def __repr__(self):
        if len(self.description) > 100:
            return "<Sequence; [ {0} ... {1} ], Sequence length; {2}>".format(self.description[0:25], self.description[(len(self.description) - 25):len(self.description)], self.sequence_length)
        else:
            return "<Sequence; [ {0} ], Sequence length; {1}>".format(self.description, self.sequence_length)
    def __str__(self):
        return self.string
    def Nucleotide_composition(self):
        """
        Calculate the nucleotide composition.
        
        """
        return {"A":round(self.description.count("A")/(self.sequence_length - self.description.count("X")), 3), "T":round(self.description.count("T")/(self.sequence_length - self.description.count("X")), 3), "C":round(self.description.count("C")/(self.sequence_length - self.description.count("X")), 3), "G":round(self.description.count("G")/(self.sequence_length - self.description.count("X")), 3), "Others":round(((self.sequence_length - self.description.count("X")) - self.description.count("A") - self.description.count("T") - self.description.count("G") - self.description.count("C"))/(self.sequence_length - self.description.count("X")), 3)}
    def Decompress(self):
        """
        Generate the list of nucleotide sequences converted from a wobble base pair to ATGC from a sequence that has a wobble base pair.

        Parameters
        ----------
        None

        Returns
        ------
        sequences: list
        
        """
        return [str("".join(ntcomb)).upper() for ntcomb in it.product(*[nucleotide(nt).base for nt in list(self.description)])]
    def complementary_sequence(self):
        """
        Convert an input sequence to a complementary sequence.

        Parameters
        ----------
        None

        Returns
        -------
        New_sequences: str
            The complementary sequence of the sequence in the object.
        """
        subdict = {"a":"t", "t":"a", "g":"c", "c":"g", "b":"v", "d":"h", "h":"d", "k":"m", "m":"k", "r":"y", "s":"s", "v":"b", "w":"w", "y":"r", "n":"n", "x":"x"}
        sequence = str(self.description)[::-1].lower()
        new_sequences = "".join([subdict[nt] for nt in list(sequence)])
        new_sequences = new_sequences.upper()
        return new_sequences
    def calculate_score(self, seq):
        '''
        Calculate the similarity between two sequences. The higher the value is, the more similar the two sequences are.

        Parameters
        ----------
        seq: str or nucleotide_sequence

        Returns
        -------
        Similarity_score: float
        '''
        seq1 = self.description
        if type(seq) is nucleotide_sequence:
            seq2 = seq.description
        elif type(seq) is str:
            seq2 = seq
        elif len(re.sub(r"[A-Za-z]|\n", "", seq)) == 0:
            seq2 = str(seq)
        else:
            print("Input sequence should be class <str>, <nucleotide_sequence> or str-like object.")
            return None
        if len(seq1) == len(seq2):
            s1 = np.array([list(nucleotide(nt).code) + list(map(lambda x:float(x)/2, list(nucleotide(nt).type_code))) for nt in list(seq1)], dtype = float).astype(np.float32)
            s2 = np.array([list(nucleotide(nt).code) + list(map(lambda x:float(x)/2, list(nucleotide(nt).type_code))) for nt in list(seq2)], dtype = float).astype(np.float32)
            score = np.sum(np.max(s1 * s2, axis = 1))
            score = score/len(seq1)
            return score
        else:
            print("The length of sequences compared should be corresponded to each other.")
            return None
    def calculate_flexibility(self, detailed = False):
        '''
        Calculate the score for degeneracy.

        Parameters
        ----------
        detailed: bool
            The score when specifying True will be more accurate. (default: False)

        Returns
        -------
        Flexibility: float
            The higher the score is, the more wobble base pairs the sequence has.

        '''
        sequence = self.description
        if detailed:
            if (type(sequence) == list) | (type(sequence) == tuple):
                each_flexibility = [(seq.count("N") * 1 + seq.count("V") * 0.9902 + seq.count("B") * 0.9901 + seq.count("D") * 0.9900 + seq.count("H") * 0.9899 + seq.count("S") * 0.8502 + seq.count("K") * 0.8501 + seq.count("M") * 0.8500 + seq.count("W") * 0.8499 + seq.count("R") * 0.7501 + seq.count("Y") * 0.7499)/len(seq) if len(re.sub(r"[ATGC]", "", seq)) != 0 else 0.25/len(seq) for seq in sequence]
                flexibility = np.array(each_flexibility).prod() ** (1/len(sequence))
            else:
                flexibility = (sequence.count("N") * 1 + sequence.count("V") * 0.9902 + sequence.count("B") * 0.9901 + sequence.count("D") * 0.9900 + sequence.count("H") * 0.9899 + sequence.count("S") * 0.9502 + sequence.count("K") * 0.9501 + sequence.count("M") * 0.9500 + sequence.count("W") * 0.9499 + sequence.count("R") * 0.7501 + sequence.count("Y") * 0.7499)/len(sequence)
            return float(flexibility)
        else:
            if (type(sequence) == list) | (type(sequence) == tuple):
                each_flexibility = [(len(re.sub(r"[ATGCRY]", "", seq))+(len(seq)-len(re.sub(r"[RY]", "", seq)))*0.75)/len(seq) if len(re.sub(r"[ATGC]", "", seq)) != 0 else 0.25/len(seq) for seq in sequence]
                flexibility = np.array(each_flexibility).prod() ** (1/len(sequence))
            else:
                flexibility = (len(re.sub(r"[ATGCRY]", "", sequence))+(len(sequence)-len(re.sub(r"[RY]", "", sequence)))*0.75)/len(sequence)
            return float(flexibility)
    def array_diff(self, arr1, arr2, lower, upper, logical = False, separation_key = []):
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
            res = np.all([(np.any((ans > lower) & (ans < upper)) & np.all((ans > lower) | (ans <= 0) | (np.isnan(ans)))) if np.any(pd.notna(ans)) else True for ans in diff_ans])
        else:
            res = [ans[(ans > lower) & (ans < upper)] if np.any(pd.notnull(ans)) else np.array([]) for ans in diff_ans]
        return res
    def calculate_Tm_value(self, conc = 0.5, Na_conc = 0.05, mode = 'min'):
        '''
        Calculate the Tm value. 

        Parameters
        ----------
        conc: float
            The concentration of a primer when PCR amplification is performed. (default: 0.5 picomole/microliter)
        Na_conc: float
            The concentration of sodium when PCR amplification is performed. (default: 0.05 mole/liter)
        mode: str
            Choose a method from 'min', 'max', 'average', or ''. (default: min)

        Returns
        -------
        Tm_value: numpy.float or list

        '''
        Decompressed_sequence = self.Decompress()
        Parameter = {"AA": [-9.1, -0.0240], "TT": [-9.1, -0.0240], "AT": [-8.6, -0.0239], "TA": [-6.0, -0.0169], \
            "CA": [-5.8, -0.0129], "TG": [-5.8, -0.0129], "GT": [-6.5, -0.0173], "AC": [-6.5, -0.0173], \
            "CT": [-7.8, -0.0208], "AG": [-7.8, -0.0208], "GA": [-5.6, -0.0135], "TC": [-5.6, -0.0135], \
            "CG": [-11.9, -0.0278], "GC": [-11.1, -0.0267], "GG": [-11.0, -0.0266], "CC": [-11.0, -0.0266]}
        if len(Decompressed_sequence[0]) > 17:
            Enthalpy = [np.sum([Parameter[sequence[i:(i + 2):]][0] for i in range(len(sequence) - 1)]) for sequence in Decompressed_sequence]
            Entropy = [np.sum([Parameter[sequence[i:(i + 2):]][1] for i in range(len(sequence) - 1)]) for sequence in Decompressed_sequence]
            Tm_value = [round(((dH / (-0.0108 + dS + 0.001987 * math.log((conc / 1000000) / 4))) - 273.15 + 16.6 * math.log10(Na_conc)), 1) for dH, dS in zip(Enthalpy, Entropy)]
        else:
            Tm_value = [round(np.sum([nucleotide(nt).Tm for nt in list(sequence)]), 1) for sequence in Decompressed_sequence]
        if mode == 'min':
            Result = np.min(Tm_value)
        elif mode == 'max':
            Result = np.max(Tm_value)
        elif mode == 'average':
            Result = np.mean(Tm_value)
        else:
            Result = Tm_value
        return Result
    def search_position(self, evaluating_sequence, allowance = 0, interval_distance = 0, Match_rate = 0.0, circularDNAtemplate = False, IgnoreLowQualityRegion = True):
        '''
        Search an annealing site position .

        Parameters
        ----------
        evaluating_sequence: str or nucleotide_sequence
            The sequence for which you want to identify the annealing site position in a template sequence.

        Returns
        -------
        Start_position: dict
            The annealing site position between an evaluated sequence and a template (self) sequence.
            The absolute value of a position number indicates the onset point of the annealing site of a template sequence.
            e.g., If the "evaluating_sequence" is "ATGC", {"ATGC": [10, −35]} will be obtained.\n
                Template : ttggaatgagATGCtgtgaacagtcgtatatacgcGCATcgagattacgctattcgcgcggcg\n

        '''
        input_sequence = self.description
        if circularDNAtemplate:
            input_sequence = str(input_sequence) + str(input_sequence)[0:int(len(evaluating_sequence) - 1):]
        if IgnoreLowQualityRegion:
            IGNORE = math.ceil(np.max([(len(str(evaluating_sequence)) - allowance) / 2, 2]))
            IGNORE = r"".join(["N" for n in range(IGNORE)]) + r'+'
            IGNORE = re.findall(IGNORE, input_sequence)
            IGNORE.sort(reverse = True)
            for igr in IGNORE:
                input_sequence = re.sub(igr, igr.replace("N", "X"), input_sequence)
        if type(evaluating_sequence) is nucleotide_sequence:
            evaluating_sequence = evaluating_sequence.description
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
                translate_evaluating_sequence_GPU = cp.asarray(translate_evaluating_sequence.flatten().astype(np.uint8))
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
                translate_evaluating_sequence_CPU = translate_evaluating_sequence.flatten().astype(np.uint8)
                score_list_preparation = np.dot(translate_evaluating_sequence_CPU, translate_sequence_matrix_CPU).astype(np.uint8)
                complementary_score_list_preparation = np.dot(translate_evaluating_sequence_CPU, np.flipud(translate_sequence_matrix_CPU)).astype(np.uint8)
        else:
            translate_sequence_matrix_CPU = (translate_sequence_matrix.T).astype(np.uint8)
            translate_evaluating_sequence_CPU = translate_evaluating_sequence.flatten().astype(np.uint8)
            score_list_preparation = np.dot(translate_evaluating_sequence_CPU, translate_sequence_matrix_CPU).astype(np.uint8)
            complementary_score_list_preparation = np.dot(translate_evaluating_sequence_CPU, np.flipud(translate_sequence_matrix_CPU)).astype(np.uint8)
        IDX = np.where(score_list_preparation.astype(np.float32) >= (len(evaluating_sequence) - allowance))[0]
        score_list = score_list_preparation.astype(np.float32) / len(evaluating_sequence)
        score_list[IDX] = [nucleotide_sequence(evaluating_sequence).calculate_score(input_sequence[id:(id + len(evaluating_sequence)):]) for id in IDX]
        score_list_criteria = list(np.where(np.array(score_list) >= ((len(evaluating_sequence) - allowance)/len(evaluating_sequence)))[0])
        IDX = np.where(complementary_score_list_preparation.astype(np.float32) >= (len(evaluating_sequence) - allowance))[0]
        complementary_score_list = complementary_score_list_preparation.astype(np.float32) / len(evaluating_sequence)
        complementary_score_list[IDX] = [nucleotide_sequence(evaluating_sequence).calculate_score(complementary_sequence(input_sequence[id:(id + len(evaluating_sequence)):])) for id in IDX]
        score_list = np.maximum(score_list, complementary_score_list)
        Start_positions = dict()
        Mismatch_Counter = 0
        Total_Counter = 0
        Maximum_position_list_size = 12
        Maximum_combination_size = 30000
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
                Position_combinations = [tuple([sorted(list(it.chain.from_iterable(Grouping_position_list)), key = abs)])]
            else:
                Group_combination_numbers = [[np.array(Grouping_combination_number) for Grouping_combination_number in list(it.combinations(range(len(Grouping_position_list)), i))] for i in range(1, len(Grouping_position_list) + 1)]
                Position_combinations = list(it.chain.from_iterable([[tuple(sorted(it.chain.from_iterable(np.array(Grouping_position_list, dtype = object)[Gcn].tolist()), key = abs)) for Gcn in Group_combination_number] for Group_combination_number in Group_combination_numbers]))
                Split_sequences_combinations = list(it.chain.from_iterable([[tuple(it.chain.from_iterable(np.array(Grouping_split_sequences, dtype = object)[Gcn].tolist())) for Gcn in Group_combination_number] for Group_combination_number in Group_combination_numbers]))
                Combination_in_allowance = [len(re.sub('[ATGC]', '', make_wobble(*Split_sequences_combination)[0])) <= np.max([allowance, np.max([len(re.sub('[ATGC]', '', seq)) for seq in Split_sequences_combination])]) for Split_sequences_combination in Split_sequences_combinations]
                Position_combinations = [Position_combinations[i] for i in range(len(Position_combinations)) if Combination_in_allowance[i]]
                if len(Position_combinations) > Maximum_combination_size:
                    Position_combinations = np.array(tuple([sorted(list(it.chain.from_iterable(Grouping_position_list)), key = abs)]), dtype = object)
            Criteria = np.array([[np.count_nonzero(np.array(posc) == pos) > 0 for pos in Position_list] for posc in Position_combinations])
            score_list = [np.array(score_list)[cr] for cr in Criteria]
            del split_sequences
            for i in range(len(Position_combinations)):
                for in_allowance in range(allowance + 1):
                    Position_index = np.array(Position_combinations[i])[np.where(np.array(score_list[i]) >= ((len(evaluating_sequence) - in_allowance)/len(evaluating_sequence)))[0].tolist()]
                    if np.any([np.all([np.all(np.diff(np.sort(np.abs(Position_index))) >= interval_distance)]), (len(Position_index) == 1)]):
                        extract_input_sequences = [input_sequence[Position:(Position + len(evaluating_sequence)):] if Position >= 0 else complementary_sequence(input_sequence[np.abs(Position):(np.abs(Position) + len(evaluating_sequence)):]) for Position in Position_index]
                        extract_input_sequences = [nucleotide_sequence(extract_input_sequence).Decompress() if len(re.sub('[ATGC]', '', extract_input_sequence)) > 0 else [extract_input_sequence] for extract_input_sequence in extract_input_sequences]
                        extract_input_sequence_score = [np.argmax([nucleotide_sequence(decompressed_seq).calculate_score(evaluating_sequence) for decompressed_seq in extract_input_sequence]) for extract_input_sequence in extract_input_sequences]
                        extract_input_sequences = [str(np.array(extract_input_sequences[i])[extract_input_sequence_score[i]]) for i in range(len(extract_input_sequences))]
                        seq = make_wobble(*([evaluating_sequence] + extract_input_sequences))
                        Position_index = Position_list[np.array([nucleotide_sequence(seq[0]).calculate_score(input_sequence[Position:(Position + len(evaluating_sequence)):]) == 1 if Position >= 0 else nucleotide_sequence(seq[0]).calculate_score(complementary_sequence(input_sequence[np.abs(Position):(np.abs(Position) + len(evaluating_sequence)):])) == 1 for Position in Position_list])].astype(object)
                        Start_position = {seq[0]:Position_index} if np.all([(nucleotide_sequence(seq[0]).calculate_flexibility() <= (nucleotide_sequence(evaluating_sequence).calculate_flexibility() + (in_allowance/len(evaluating_sequence)))), (nucleotide_sequence(seq[0]).calculate_flexibility() < 1.0), len(Position_index) > 0]) else None
                        Start_positions.update({list(Start_position.keys())[0]:np.array(sorted(list(set(Start_positions[list(Start_position.keys())[0]].tolist() + Start_position[list(Start_position.keys())[0]].tolist())), key = abs), dtype = object)} if (set(Start_position.keys()) <= set(Start_positions.keys())) else Start_position) if Start_position is not None else Start_positions.update()
                        Mismatch_Counter = Mismatch_Counter if np.any([np.all([np.all(np.diff(np.sort(np.abs(Position_index))) >= interval_distance)]), (len(Position_index) == 1)]) else Mismatch_Counter + 1
                    else:
                        Mismatch_Counter += 1
                    Total_Counter += 1
        else:
            pass
        Mismatch_rate = Mismatch_Counter / Total_Counter if ((allowance > 0) & (Total_Counter > 0)) else 0
        if len(Palindrome_sequence_list) != 0:
            Start_positions = {Key: Position.tolist() + [pp * (-1) if set(Position) >= set([pp]) else pp for palseq, Ppos in Palindrome_sequence_list.items() if ((nucleotide_sequence(Key).calculate_score(palseq) == 1.0) & (nucleotide_sequence(Key).calculate_score(complementary_sequence(palseq)) == 1.0)) for pp in Ppos] for Key, Position in Start_positions.items()}
            Start_positions = {Key: np.array(sorted(sorted(list(set(Position))), key = abs), dtype = object) for Key, Position in Start_positions.items()}
        Start_positions = {Key:Position for Key, Position in Start_positions.items() if np.all(np.diff(np.sort(np.abs(Position))) >= interval_distance)}
        if (len(Start_positions) != 0) & ((1 - Mismatch_rate) >= Match_rate):
            return Start_positions
        else:
            return None
    def PCR_amplicon(self, forward, reverse, allowance = 0, Single_amplicon = True, Sequence_Only = True, amplicon_size_limit = 10000, Warning_ignore = False, circularDNAtemplate = False, IgnoreLowQualityRegion = True):
        '''
        In silico PCR.

        Parameters
        ----------
        forward: str or nucleotide_sequence
            Forward primer sequence (required).
        reverse: str or nucleotide_sequence
            Reverse primer sequence (required).
        allowance: int
            The acceptable mismatch number. (default: 0)
        Single_amplicon: bool
            All amplicons that will be amplified by an input primer set are outputed as list when False is specified. (default: True)
        Sequence_Only: bool
            The start and end positions of an amplicon in template sequence are outputed with the amplicon sequence when False is specified. (default: True)
        Warning_ignore: bool
            Show all warnings if specify True. (default: False)
        circularDNAtemplate: bool
            Specify True if the input sequence is circular DNA. (default: False)

        Returns
        -------
        PCR_amplicon: str or list

        '''
        if Warning_ignore:
            warnings.simplefilter('ignore')
        template = self.description
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
        template = nucleotide_sequence(template)
        PCR_amplicon = None
        if type(forward) is not nucleotide_sequence:
            forward = nucleotide_sequence(forward)
        if type(reverse) is not nucleotide_sequence:
            reverse = nucleotide_sequence(reverse)
        forward_position = template.search_position(evaluating_sequence = forward.description, allowance = allowance, interval_distance = 0, Match_rate = 0.0, IgnoreLowQualityRegion = False)
        reverse_position = template.search_position(evaluating_sequence = reverse.complementary_sequence(), allowance = allowance, interval_distance = 0, Match_rate = 0.0, IgnoreLowQualityRegion = False)
        if (forward_position is not None) & (reverse_position is not None):
            forward_position = sorted(sorted(list(set(list(it.chain.from_iterable([v for v in forward_position.values()]))))), key = abs)
            reverse_position = sorted(sorted(list(set(list(it.chain.from_iterable([v for v in reverse_position.values()]))))), key = abs)
            if Sequence_Only:
                Amplicon_size = [self.array_diff([f], reverse_position, lower = 0, upper = amplicon_size_limit, logical = False, separation_key = []) + reverse.sequence_length if f >= 0 else self.array_diff([f], reverse_position, lower = 0, upper = amplicon_size_limit, logical = False, separation_key = []) + forward.sequence_length for f in forward_position]
                PCR_amplicon = [template[int(f):int(f+a):] if f >= 0 else template[int(np.abs(f) + forward.sequence_length - a):int(np.abs(f) + forward.sequence_length):] for f, amp in zip(forward_position, Amplicon_size) for a in amp]
                PCR_amplicon = list(set([amp for amp in PCR_amplicon if ((len(amp) <= amplicon_size_limit) & (len(amp) != 0) & (amp.find("X") < 0))]))
            else:
                Amplicon_size = [self.array_diff([f], reverse_position, lower = 0, upper = amplicon_size_limit, logical = False, separation_key = []) + reverse.sequence_length if f >= 0 else self.array_diff([f], reverse_position, lower = 0, upper = amplicon_size_limit, logical = False, separation_key = []) + forward.sequence_length for f in forward_position]
                PCR_amplicon = [(int(f + 1), int(f + a), template[int(f):int(f+a):], ) if f >= 0 else (int(f - forward.sequence_length), int(f - forward.sequence_length + a - 1), template[int(np.abs(f) + forward.sequence_length - a):int(np.abs(f) + forward.sequence_length):], ) for f, amp in zip(forward_position, Amplicon_size) for a in amp]
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

def complementary_sequence(sequence):
    """
    Convert an input sequence to a complementary sequence.

    Parameters
    ----------
    sequence: str, nucleotide_sequence, list, tuple

    Returns
    ------
    New_sequences: str
        The complementary sequence of the sequence in the object.
    """
    subdict = {"a":"t", "t":"a", "g":"c", "c":"g", "b":"v", "d":"h", "h":"d", "k":"m", "m":"k", "r":"y", "s":"s", "v":"b", "w":"w", "y":"r", "n":"n", "x":"x"}
    if (type(sequence) is pd.DataFrame) | (type(sequence) is pd.Series) | (type(sequence) is list) | (type(sequence) is tuple):
        if (type(sequence) is pd.DataFrame) | (type(sequence) is pd.Series):
            index = sequence.index
            sequences = list(sequence.values)
        sequences = list(sequence)
        new_sequences = []
        for sequence in sequences:
            sequence = str(sequence)[::-1].lower()
            sequence = "".join([subdict[nt] for nt in list(sequence)])
            new_sequences.append(sequence.upper())
        if (type(sequence) is pd.DataFrame) | (type(sequence) is pd.Series):
            new_sequences = pd.Series(new_sequences, index = index)
    else:
        sequence = str(sequence)[::-1].lower()
        new_sequences = "".join([subdict[nt] for nt in list(sequence)])
        new_sequences = new_sequences.upper()
    return new_sequences

def calculate_Tm_value(sequence, conc = 0.5, Na_conc = 0.05, mode = 'min'):
    '''
    Calculate the Tm value. 

    Parameters
    ----------
    sequence: str, nucleotide_sequence, list, tuple or numpy.ndarray
        The sequence for which you would like to know the Tm value, or its list, tuple, or ndarray. (required)
    conc: float
        The concentration of a primer when PCR amplification is performed. (default: 0.5 picomole/microliter)
    Na_conc: float
        The concentration of sodium when PCR amplification is performed. (default: 0.05 mole/liter)
    mode: str
        Choose a method from 'min', 'max', 'average', or ''. (default: min)

    Returns
    -------
    Tm_value: numpy.float or list

    '''
    if (type(sequence) is list) | (type(sequence) is tuple):
        sequences = list(sequence)
    elif (type(sequence) is np.ndarray):
        sequences = sequence.tolist()
    elif (type(sequence) is str) | (type(sequence) is nucleotide_sequence):
        sequences = [str(sequence)]
    else:
        try:
            raise TypeError
        except:
            print("TypeError: ")
    Decompressed_sequences = [[str("".join(ntcomb)).upper() for ntcomb in it.product(*[nucleotide(nt).base for nt in list(seq)])] for seq in sequences]
    Tm_value_list = []
    Parameter = {"AA": [-9.1, -0.0240], "TT": [-9.1, -0.0240], "AT": [-8.6, -0.0239], "TA": [-6.0, -0.0169], \
        "CA": [-5.8, -0.0129], "TG": [-5.8, -0.0129], "GT": [-6.5, -0.0173], "AC": [-6.5, -0.0173], \
        "CT": [-7.8, -0.0208], "AG": [-7.8, -0.0208], "GA": [-5.6, -0.0135], "TC": [-5.6, -0.0135], \
        "CG": [-11.9, -0.0278], "GC": [-11.1, -0.0267], "GG": [-11.0, -0.0266], "CC": [-11.0, -0.0266]}
    for Decompressed_sequence in Decompressed_sequences:
        if len(Decompressed_sequence[0]) > 17:
            Enthalpy = [np.sum([Parameter[sequence[i:(i + 2):]][0] for i in range(len(sequence) - 1)]) for sequence in Decompressed_sequence]
            Entropy = [np.sum([Parameter[sequence[i:(i + 2):]][1] for i in range(len(sequence) - 1)]) for sequence in Decompressed_sequence]
            Tm_value = [round(((dH / (-0.0108 + dS + 0.001987 * math.log((conc / 1000000) / 4))) - 273.15 + 16.6 * math.log10(Na_conc)), 1) for dH, dS in zip(Enthalpy, Entropy)]
        else:
            Tm_value = [round(np.sum([nucleotide(nt).Tm for nt in list(sequence)]), 1) for sequence in Decompressed_sequence]
        if mode == 'min':
            Tm_value_list.append(np.min(Tm_value))
        elif mode == 'max':
            Tm_value_list.append(np.max(Tm_value))
        elif mode == 'average':
            Tm_value_list.append(np.mean(Tm_value))
        else:
            Tm_value_list.append(Tm_value)
    Result = dict(zip(sequences, Tm_value_list))
    Result = float(Result[list(Result.keys())[0]]) if (len(Result) == 1) & (type(Result[list(Result.keys())[0]]) is not list) else Result
    return Result

def read_sequence_file(input, format = "fasta", Feature = False):
    '''
    Read a sequence file. FASTA, Multi-FASTA, and GenBank sequence format files are accepted.

    Parameters
    ----------
    input: str
        File path. (required)
    format: str
        'fasta' or 'genbank' (default: fasta)
    Feature: bool
        The annotations are extracted if the GenBank format is input when True is specified. (default: False)

    Returns
    -------
    sequences: list
        A list will be returned as follows. [{'sequence name':sequence <nucleotide_sequence>}, input sequence number, average length of input sequence].
        In cases in which True is specified in a Feature argument, [{'sequence name':[sequence <nucleotide_sequence>, feature]}, input sequence number, average length of input sequence].

    '''
    with open(input, 'rb') as fin:
        detector = UniversalDetector()
        for line in fin:
            detector.feed(line)
            if detector.done:
                break
        detector.close()
        encoding = detector.result
    if encoding['encoding'] is None:
        with open(input, 'rb') as fin:
            f = fin.read()
            encoding = detect(f)
        del f
    with open(input, mode = "rt", encoding = encoding['encoding']) as fin:
        line = fin.readline()
        if line.startswith("LOCUS"):
            format = "genbank"
        if format.lower() == "fasta":
            name = ''
            seq = ''
            name_list = []
            seq_list = []
            while line:
                line = line.replace('\n','')
                if line.startswith('>'):
                    name = line[1::]
                    seq = ''
                else:
                    seq += line
                line = fin.readline()
                if not line or line.startswith('>'):
                    name_list.append(name)
                    seq_list.append(seq)
            seq_list = [nucleotide_sequence(re.sub('U', 'T', re.sub(r'[EFIJLOPQZ]', 'N', re.sub(r'[^A-Z]', '', seq.upper())))) for seq in seq_list]
            seq_dict = dict(zip(name_list,seq_list))
        elif format.lower() == "genbank":
            seq = ""
            gene_region = []
            gene_product = []
            SEQUENCE_Line = False
            FEATURES_Line = False
            GENE_Count = 0
            while len(line) > 0:
                if line.replace(" ", "").startswith("DEFINITION"):
                    name = line.replace("DEFINITION", "").replace("\n", "")
                    while True:
                        if not name.startswith(" "):
                            break
                        name = name[1::]
                if FEATURES_Line:
                    FEATURES_Key = ["C_region", "CDS", "D_segment", "exon", \
                                    "gene", "J_segment", "mat_peptide", "misc_feature", \
                                    "misc_RNA", "mRNA", "ncRNA", "N_region", "precursor_RNA", \
                                    "propeptide", "rRNA", "S_region", "sig_peptide", "tmRNA", \
                                    "transit_peptide", "tRNA", "V_region", "V_segment", "variation"]
                    if np.any([line.replace(" ", "").startswith(feature_key) for feature_key in FEATURES_Key]) & (re.search(r'[0-9]+\.+[^0-9]*[0-9]+', line) is not None):
                        GENE_Count += 1
                        gene_region.append(re.sub(r'['+r"|".join(FEATURES_Key)+r"|\n| |complement(|)]", "", line))
                    if line.replace(" ", "").startswith("/product="):
                        gene_product += ["" for n in range(GENE_Count - len(gene_product) - 1)]
                        PRODUCT = line.replace("/product=", "").replace('"', "").replace("\n", "")
                        while True:
                            if not PRODUCT.startswith(" "):
                                break
                            PRODUCT = PRODUCT[1::]
                        gene_product.append(PRODUCT)
                if SEQUENCE_Line:
                    seq += re.sub(r"[0-9| |\n|/]", "", line)
                if line.replace(" ", "").startswith("FEATURES"):
                    SEQUENCE_Line = False
                    FEATURES_Line = True
                if line.replace(" ", "").startswith("ORIGIN"):
                    SEQUENCE_Line = True
                    FEATURES_Line = False
                line = fin.readline()
            feature = {k:v for k, v in zip(gene_region, gene_product) if len(v) != 0}
            seq = re.sub('U', 'T', re.sub(r'[EFIJLOPQZ]', 'N', re.sub(r'[^A-Z]', '', seq.upper())))
            seq_list = [nucleotide_sequence(seq)]
            if 'name' not in locals():
                print("'{0}' is not Genbank file format. Reconfirm the file.\nWhen '--Annotaion' option is used, the input sequence file should be provided by genbank format.".format(input))
                sys.exit()
            if Feature:
                seq_dict = {name:[nucleotide_sequence(seq), feature]}
            else:
                seq_dict = {name:nucleotide_sequence(seq)}
        else:
            print("'{0}' format is not supported. Please convert '{0}' to 'fasta' or 'genbank'.".format(format))
            sys.exit()
    input_seq = len(seq_dict)
    Total_length = 0
    for inseq in seq_list:
        Total_length += inseq.sequence_length
    Average_length = Total_length/input_seq
    return [seq_dict, input_seq, Average_length]

def circularDNA(sequence, overlap = 0):
    """
    Convert linear DNA to circular DNA. (private)
    
    """
    new_sequence = str(sequence) + str(sequence)[0:int(overlap):]
    return new_sequence

def check_input_file(file_paths, circular = "all"):
    """
    Check input file. (private)
    
    """
    check_sequences = {}
    if type(file_paths) is str:
        file_paths = [file_paths]
    for file_path in file_paths:
        check_sequences.update(read_sequence_file(file_path)[0])
    if np.any([seq.sequence_length == 0 for name, seq in check_sequences.items()]):
        print("Some input sequence(s) doesn't contain sequence data.")
        sys.exit()
    if np.any([len(re.sub(r'[ATGC]', '', str(seq).upper()))/seq.sequence_length > 0.7 for name, seq in check_sequences.items()]) | np.any([len(re.sub(r'[ATGCBDHKMRSVWYNX]', '', str(seq).upper())) > 1 for name, seq in check_sequences.items()]):
        print("There is a possibility that Some input sequence(s) is not nucleotide sequence. Please check input sequence again.")
        sys.exit()
    if circular.lower() == "all":
        circular_DNA = [True for i in range(len(check_sequences))]
    elif circular.lower() == "individually":
        circular_DNA = [False for i in range(len(check_sequences))]
        for i in range(len(check_sequences)):
            check = ''
            while True:
                check = input("Is '{0}' circular DNA? (y/n/a-y[all yes after this sequence.]/a-n[all no after this sequence.]): ".format(str(list(check_sequences.keys())[i])))
                if (check.lower() == "all-yes") | (check.lower() == "a-y") | (check.lower() == "all-no") | (check.lower() == "a-n") |(check.lower() == "yes") | (check.lower() == "y") | (check.lower() == "no") | (check.lower() == "n"):
                    break
            if (check.lower() == "all-yes") | (check.lower() == "a-y"):
                circular_DNA[i:] = [True for i in range(len(check_sequences) - i)]
                break
            elif (check.lower() == "all-no") | (check.lower() == "a-n"):
                circular_DNA[i:] = [False for i in range(len(check_sequences) - i)]
                break
            elif (check.lower() == "yes") | (check.lower() == "y"):
                circular_DNA[i] = True
            elif (check.lower() == "no") | (check.lower() == "n"):
                circular_DNA[i] = False
    elif os.path.isfile(circular):
        circularDNAfile = []
        with open(circular, 'rt', encoding = "utf-8") as fin:
            line = fin.readline()
            while line:
                circularDNAfile.append(line)
                line = fin.readline()
        circular_DNA = [any([(n.replace(name, '').count('circularDNA') > 0) | (n.replace(name, '').count('circular') > 0) for n in circularDNAfile if ((n.count(name + " ") > 0) | (n.count(name + "\t") > 0) | (n.count(name + ",") > 0))]) for name in check_sequences.keys()]
    elif circular.lower() == "n/a":
        circular_DNA = [False for i in range(len(check_sequences))]
    else:
        print("Specify the file path, 'all', 'indivudually' or 'n/a' after circular argment.")
        sys.exit()
    circular_index = dict(zip(list(check_sequences.keys()), circular_DNA))
    return circular_index

def make_wobble(*args):
    '''
    Make a degenerate sequence from an input sequences list. (private)

    Parameters
    ----------
    args: str, unpacked list or unpacked tuple

    Returns
    -------
    New_sequence: list
        A list of a degenerate sequence and input sequences. [degenerate sequence, [Input sequences]]

    '''
    enc_submatrix = {"a":1, "t":8, "g":2, "c":4, "b":14, "d":11, "h":13, "k":10, "m":5, "r":3, "s":6, "v":7, "w":9, "y":12, "n":15, "x":0}
    dec_submatrix = {1:"a", 8:"t", 2:"g", 4:"c", 14:"b", 11:"d", 13:"h", 10:"k", 5:"m", 3:"r", 6:"s", 7:"v", 9:"w", 12:"y", 15:"n", 0:"x"}
    sequences = list(args)
    new_sequence = []
    nt_matrix = np.array([[enc_submatrix[nt.lower()] for nt in list(seq)] for seq in sequences]).T
    for i in range(nt_matrix.shape[0]):
        if np.any(nt_matrix[i] == 0):
            new_sequence.append(dec_submatrix[0])
        elif len(set(nt_matrix[i])) >= 9:
            new_sequence.append(dec_submatrix[15])
        else:
            bit_value = 0
            dec = []
            for n1 in set(nt_matrix[i]):
                bit_value += int(bin(n1)[2:])
            for n2 in str(bit_value):
                if int(n2) >= 1:
                    dec.append("1")
                else:
                    dec.append("0")
            dec = int("".join(dec),2)
            new_sequence.append(dec_submatrix[dec])
    new_sequence = "".join(new_sequence)
    result = [new_sequence.upper(), sequences]
    return result

def combination_basedon_correlation(df, number = 1, Correlation_threshold = 0.9):
    '''
    Generate iterator for combination of df.index based on a correlation calculated from values in every row. (private)

    Parameters
    ----------
    df: pandas.DataFrame.
    number: int
        The number of indexes contained in each combination. (default: 1)
    Correlation_threshold: float
        The indexes have the correlation score above this threshold are grouped, and two or more indexes are NEVER chosen from the indexes in same group. (default: 0.9)

    Returns
    -------
    Generator object

    '''
    try:
        df = df.fillna(0)
        if type(df.iloc[0,0]) is list:
            Maximum_element_number = [np.max(df.iloc[:, i].apply(lambda x:len(x) if type(x) is list else 1)) for i in range(df.shape[1])]
            new_df = pd.DataFrame([[[sorted(li)[j] if len(li) >= j + 1 else int(0) for j in range(n)] for li in df.iloc[:, i]] for i, n in enumerate(Maximum_element_number)], dtype = object).T
            new_df.index = df.index
            df = pd.DataFrame([list(it.chain.from_iterable(new_df.iloc[i])) for i in range(new_df.shape[0])], index = new_df.index)
        Cor_matrix = df.astype('float64').T.corr()
        Cor_matrix = np.nan_to_num(Cor_matrix)
        Cor_distance = distance.pdist(Cor_matrix)
        Cor_matrix[Cor_matrix < Correlation_threshold] = -10
        col_min_cor = [Cor_matrix[i, j] for i, j in enumerate(list(abs(Cor_matrix - Correlation_threshold).argmin(axis = 1)))]
        idx = [tuple([i, j]) for i, j in enumerate(list(abs(Cor_matrix - Correlation_threshold).argmin(axis = 1)))]
        row_min_idx = ([abs(num - Correlation_threshold) for num in col_min_cor]).index(min([abs(num - Correlation_threshold) for num in col_min_cor]))
        idx = idx[row_min_idx]
        Threshold = (distance.squareform(Cor_distance))[idx]
        Cor_linkage = linkage(Cor_distance, metric = "euclidean", method = "average")
        Group = fcluster(Cor_linkage, Threshold, criterion = "distance")
        Index = df.index
        Group_list = {}
        for i in set(Group):
            Group_list.update({i:list(Index[Group == i])})
        Group_iter = it.combinations(Group_list.keys(), number)
        for keys in Group_iter:
            GLE = [Group_list[key] for key in keys]
            for sequence_set in it.product(*GLE):
                yield sequence_set
    except AttributeError:
        print("First positional argument 'df' should be pandas.DataFrame.")
    except:
        raise

def file_existence(file_path, postfix = "_"):
    file_name, extension = os.path.splitext(file_path)
    i = 1
    if os.path.exists(file_path):
        new_file_path = file_name + postfix + str(i) + extension
        while os.path.exists(new_file_path):
            i += 1
            new_file_path = file_name + postfix + str(i) + extension
        return new_file_path
    else:
        return file_path

def move_file(Original_file_path, Destination_file_path, postfix = "_"):
    Destination_file_path = file_existence(Destination_file_path, postfix = postfix)
    shutil.move(Original_file_path, Destination_file_path)

def linkage_matrix2newick(linkage_matrix, labels = None, distance = False):
    '''
    Convert the linkage matrix generated from scipy.cluster.hierarchy.linkage to newick format. (private)

    Parameters
    ----------
    linkage_matrix: numpy.ndarray.
    labels: list, numpy.ndarray, pandas.Series.
        The labels for each leaf.
    distance: bool
        If this option is used, the newick outputted will contain each branch length. (default: False)

    Returns
    -------
    Generator object

    '''
    if labels is None:
        d = {i:str(i) for i in range(linkage_matrix.shape[0] + 1)}
    else:
        try:
            d = {i:str(label) for i, label in enumerate(labels)}
            if len(d) != linkage_matrix.shape[0] + 1:
                raise ValueError("Dimensions of linkage_matrix and labels must be consistent.")
        except TypeError:
            raise TypeError("The argument 'labels' should be a countable object, such as a NumPy.array or a list of labels.")
    if distance:
        branch_length = {i: 0 for i in range(linkage_matrix.shape[0] + 1)}
        [branch_length.update({len(branch_length): linkage_matrix[i][2]}) for i in range(linkage_matrix.shape[0])]
        [d.update({len(d): "({0}:{1},{2}:{3})".format(d[linkage_matrix[i][0]], round(linkage_matrix[i][2] - branch_length[int(linkage_matrix[i][0])], 2), d[linkage_matrix[i][1]], round(linkage_matrix[i][2] - branch_length[int(linkage_matrix[i][1])], 2))}) for i in range(linkage_matrix.shape[0])]
    else:
        [d.update({len(d): "({0},{1})".format(d[linkage_matrix[i][0]], d[linkage_matrix[i][1]])}) for i in range(linkage_matrix.shape[0])]
    return str(d[len(d) - 1]) + ";"