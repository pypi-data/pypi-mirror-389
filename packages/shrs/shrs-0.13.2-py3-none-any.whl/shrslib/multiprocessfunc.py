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
import re
import copy
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
import pandas as pd
import itertools as it
from shrslib.basicfunc import read_sequence_file, nucleotide_sequence, circularDNA, check_input_file
from shrslib.explore import PCR_amplicon
from shrslib.scores import pairwise_identity
from Bio.Align import PairwiseAligner
try:
    import cupy as cp
    mempool = cp.get_default_memory_pool()
except:
    pass

def trim_seq_worker_process_all(fp, fwd, rev, Sequence_Only, amplicon_size_limit ,allowance, Warning_ignore, overlap_region, circular_index, Removal_sequences, LowQualitySequences, Feature = False, annotation = {}, distance = int(0)):
    """
    Function for generating fragment based on template DNA, forward and reverse primer set by parallel process. (private)
    
    """
    seq_dict = read_sequence_file(fp)[0]
    seq_dict = {key:seq_dict[key] for key in seq_dict if (key not in Removal_sequences)}
    if (LowQualitySequences == "ignore"):
        seq_dict = {key:nucleotide_sequence(seq_dict[key].replace("N", "X")) for key in seq_dict}
    Sequence_length_list = [np.min([amplicon_size_limit, seq_dict[key].sequence_length]) for key in seq_dict]
    seq_dict = {key:circularDNA(sequence = seq_dict[key], overlap = int(np.min([overlap_region, seq_dict[key].sequence_length]))) if circular_index[key] else circularDNA(sequence = seq_dict[key], overlap = int(0)) for key in seq_dict}
    trimmed_seq = [(fp, name, PCR_amplicon(forward = fwd, reverse = rev, template = seq_dict[name], Single_amplicon = False, Sequence_Only = Sequence_Only, amplicon_size_limit = limit, allowance = allowance, Warning_ignore = Warning_ignore), ) for limit, name in zip(Sequence_length_list, seq_dict)]
    trimmed_seq = [ts for ts in trimmed_seq if ts[2] is not None]
    if np.logical_not(Sequence_Only) & Feature & (len(annotation) > 0): 
        annotated_trimmed_seq = []
        for ts in trimmed_seq: 
            Gene = [[position for position in re.sub(r"[^0-9]+", " ", target).split(" ") if len(position) != 0] + [annotation[ts[1]][target]] for target in annotation[ts[1]].keys() if (ts[1] in annotation.keys())] 
            Amplicon_annotation = {str(amp[0]) + str(amp[1]): [(g[0], g[1], g[2], ) for g in Gene if (((int(g[0]) - int(distance)) <= np.abs(amp[0])) & ((int(g[1]) + int(distance)) >= np.abs(amp[0]))) | (((int(g[0]) - int(distance)) <= np.abs(amp[1])) & ((int(g[1]) + int(distance)) >= np.abs(amp[1]))) | (((int(g[0]) - int(distance)) >= np.abs(amp[0])) & ((int(g[1]) + int(distance)) <= np.abs(amp[1])))] for amp in ts[2]} 
            annotated_trimmed_seq.append((ts[0], ts[1], [tuple(list(amp) + [Amplicon_annotation[str(amp[0]) + str(amp[1])]]) for amp in ts[2]], )) 
        trimmed_seq = ([[(ts[0], ts[1]+"_amplicon_"+str(j+1)+"_("+str(seq[0])+" -> "+str(seq[1])+")", seq[2], seq[3], ) for j, seq in enumerate(ts[2])] if len(ts[2]) > 0 else ts for ts in annotated_trimmed_seq]) if len(annotated_trimmed_seq) > 0 else annotated_trimmed_seq
        del annotated_trimmed_seq
    elif np.logical_not(Sequence_Only):
        trimmed_seq = ([[(ts[0], ts[1]+"_amplicon_"+str(j+1)+"_("+str(seq[0])+" -> "+str(seq[1])+")", seq[2], [], ) for j, seq in enumerate(ts[2])] if len(ts[2]) > 0 else ts for ts in trimmed_seq]) if len(trimmed_seq) > 0 else trimmed_seq
    else:
        trimmed_seq = ([[(ts[0], ts[1]+"_amplicon_"+str(j+1), seq, [], ) for j, seq in enumerate(ts[2])] if len(ts[2]) > 0 else ts for ts in trimmed_seq]) if len(trimmed_seq) > 0 else trimmed_seq
    trimmed_seq = list(it.chain.from_iterable(trimmed_seq))
    return trimmed_seq

def trim_seq_worker_process_single(fp, fwd, rev, Sequence_Only, amplicon_size_limit ,allowance, Warning_ignore, overlap_region, circular_index, Removal_sequences, LowQualitySequences, Feature = False, annotation = {}, distance = int(0)):
    """
    Function for generating fragment based on template DNA, forward and reverse primer set by parallel process. (private)
    
    """
    seq_dict = read_sequence_file(fp)[0]
    seq_dict = {key:seq_dict[key] for key in seq_dict if (key not in Removal_sequences)}
    if (LowQualitySequences == "ignore"):
        seq_dict = {key:nucleotide_sequence(seq_dict[key].replace("N", "X")) for key in seq_dict}
    Sequence_length_list = [np.min([amplicon_size_limit, seq_dict[key].sequence_length]) for key in seq_dict]
    seq_dict = {key:circularDNA(sequence = seq_dict[key], overlap = int(np.min([overlap_region, seq_dict[key].sequence_length]))) if circular_index[key] else circularDNA(sequence = seq_dict[key], overlap = int(0)) for key in seq_dict}
    trimmed_seq = [(fp, name, PCR_amplicon(forward = fwd, reverse = rev, template = seq_dict[name], Single_amplicon = True, Sequence_Only = Sequence_Only, amplicon_size_limit = limit, allowance = allowance, Warning_ignore = Warning_ignore), ) for limit, name in zip(Sequence_length_list, seq_dict)]
    trimmed_seq = [ts for ts in trimmed_seq if ts[2] is not None]
    if np.logical_not(Sequence_Only) & Feature & (len(annotation) > 0): 
        annotated_trimmed_seq = []
        for ts in trimmed_seq: 
            Gene = [[position for position in re.sub(r"[^0-9]+", " ", target).split(" ") if len(position) != 0] + [annotation[ts[1]][target]] for target in annotation[ts[1]].keys()] 
            Amplicon_annotation = {str(ts[2][0]) + str(ts[2][1]): [(g[0], g[1], g[2], ) for g in Gene if (((int(g[0]) - int(distance)) <= np.abs(ts[2][0])) & ((int(g[1]) + int(distance)) >= np.abs(ts[2][0]))) | (((int(g[0]) - int(distance)) <= np.abs(ts[2][1])) & ((int(g[1]) + int(distance)) >= np.abs(ts[2][1]))) | (((int(g[0]) - int(distance)) >= np.abs(ts[2][0])) & ((int(g[1]) + int(distance)) <= np.abs(ts[2][1])))]} 
            annotated_trimmed_seq.append((ts[0], ts[1], tuple(list(ts[2]) + [Amplicon_annotation[str(ts[2][0]) + str(ts[2][1])]]), ))
        trimmed_seq = [(ts[0], ts[1]+"_("+str(ts[2][0])+" -> "+str(ts[2][1])+")", ts[2][2], ts[2][3], ) for ts in annotated_trimmed_seq]
        del annotated_trimmed_seq
    elif np.logical_not(Sequence_Only):
        trimmed_seq = [(ts[0], ts[1]+"_("+str(ts[2][0])+" -> "+str(ts[2][1])+")", ts[2][2], [], ) for ts in trimmed_seq]
    else:
        trimmed_seq = [(ts[0], ts[1], ts[2], [], ) for ts in trimmed_seq]
    return trimmed_seq

def trim_seq_worker_process_all_df(fp, fwd, rev, Sequence_Only, amplicon_size_limit, allowance, Warning_ignore, overlap_region, circular_index, Removal_sequences, LowQualitySequences):
    """
    Function for generating fragment based on template DNA, forward and reverse primer set by parallel process. (private)
    
    """
    seq_dict = read_sequence_file(fp)[0]
    seq_dict = {key:seq_dict[key] for key in seq_dict if (key not in Removal_sequences)}
    if (LowQualitySequences == "ignore"):
        seq_dict = {key:nucleotide_sequence(seq_dict[key].replace("N", "X")) for key in seq_dict}
    Sequence_length_list = [np.min([amplicon_size_limit, seq_dict[key].sequence_length]) for key in seq_dict]
    seq_dict = {key:circularDNA(sequence = seq_dict[key], overlap = int(np.min([overlap_region, seq_dict[key].sequence_length]))) if circular_index[key] else circularDNA(sequence = seq_dict[key], overlap = int(0)) for key in seq_dict}
    Amplicon = [PCR_amplicon(forward = fwd, reverse = rev, template = seq, Single_amplicon = False, Sequence_Only = Sequence_Only, amplicon_size_limit = limit, allowance = allowance, Warning_ignore = Warning_ignore) for limit, seq in zip(Sequence_length_list, seq_dict.values())]
    Amplicon = [[] if seq is None else seq for seq in Amplicon]
    Amplicon = {name:{"Amplicon_sequence_"+str(i + 1):amp for i, amp in enumerate(amps)} if len(amps) > 0 else {"Amplicon_sequence_1":None} for name, amps in zip(seq_dict.keys(), Amplicon)}
    return Amplicon

def trim_seq_worker_process_single_df(fp, fwd, rev, Sequence_Only, amplicon_size_limit ,allowance, Warning_ignore, overlap_region, circular_index, Removal_sequences, LowQualitySequences):
    """
    Function for generating fragment based on template DNA, forward and reverse primer set by parallel process. (private)
    
    """
    seq_dict = read_sequence_file(fp)[0]
    seq_dict = {key:seq_dict[key] for key in seq_dict if (key not in Removal_sequences)}
    if (LowQualitySequences == "ignore"):
        seq_dict = {key:nucleotide_sequence(seq_dict[key].replace("N", "X")) for key in seq_dict}
    Sequence_length_list = [np.min([amplicon_size_limit, seq_dict[key].sequence_length]) for key in seq_dict]
    seq_dict = {key:circularDNA(sequence = seq_dict[key], overlap = int(np.min([overlap_region, seq_dict[key].sequence_length]))) if circular_index[key] else circularDNA(sequence = seq_dict[key], overlap = int(0)) for key in seq_dict}
    Amplicon = [PCR_amplicon(forward = fwd, reverse = rev, template = seq, Single_amplicon = True, Sequence_Only = Sequence_Only, amplicon_size_limit = limit, allowance = allowance, Warning_ignore = Warning_ignore) for limit, seq in zip(Sequence_length_list, seq_dict.values())]
    Amplicon = ['' if seq is None else seq for seq in Amplicon]
    Amplicon = {name:[amp, len(amp[2])] if type(amp) is tuple else [amp, len(amp)] for name, amp in zip(seq_dict.keys(), Amplicon)}
    return Amplicon

def add_anal_worker_process(fp, fwd, rev, amplicon_size_limit, overlap_region, circular_index, Score_calculation):
    """
    Function for generating fragment based on template DNA, forward and reverse primer set by parallel process. (private)
    
    """
    seq_dict = read_sequence_file(fp)[0]
    Sequence_length_list = [np.min([amplicon_size_limit, seq_dict[key].sequence_length]) for key in seq_dict]
    seq_dict = {key:circularDNA(sequence = seq_dict[key], overlap = int(np.min([overlap_region, seq_dict[key].sequence_length]))) if circular_index[key] else circularDNA(sequence = seq_dict[key], overlap = int(0)) for key in seq_dict}
    Result = pd.DataFrame([])
    for limit, name in zip(Sequence_length_list, seq_dict):
        Amplicons = [PCR_amplicon(forward = f, reverse = r, template = seq_dict[name], Single_amplicon = False, Sequence_Only = True, amplicon_size_limit = limit, allowance = int(0), Warning_ignore = True) for f, r in zip(fwd, rev)]
        if Score_calculation == 'Sequence':
            Amplicons = [amps if amps is not None else [] for amps in Amplicons]
            Amplicons = [amps[0] if len(amps) == 1 else np.nan for amps in Amplicons]
        else:
            Amplicons = [[len(amp) for amp in amps] if amps is not None else np.nan for amps in Amplicons]
        Amplicons = pd.DataFrame(pd.Series(Amplicons, index = pd.MultiIndex.from_tuples([mid for mid in zip(fwd, rev)]), name = name))
        Result = pd.concat([Result, Amplicons], axis = 1, join = "outer")
    return Result

def PCR_amplicon_with_progress_bar(*args, **kwargs):
    """
    Wrapper for using tqdm in PCR_amplicon function with parallel process. (private)
    
    """
    amplicon = PCR_amplicon(*args, **kwargs)
    return (amplicon, 1, )

def cumulative_pairwise_identity(i, df, method = 'average'):
    """
    Function for calculating pairwise identity by parallel process. (private)
    
    """
    try:
        Aligner = PairwiseAligner()
        Aligner.mode = "global"
        Align_score_list = [pairwise_identity(Aligner.align(p1, p2)) for p1, p2 in it.combinations(df.iloc[i][np.logical_not(df.iloc[i] == '')], 2) if np.all(pd.notna([p1, p2]))]
        Align_sequence_number = [0 for p1, p2 in it.combinations(df.iloc[i][np.logical_not(df.iloc[i] == '')], 2) if np.all(pd.notna([p1, p2]))]
        Average_identity_score = np.exp(np.sum(np.log(Align_score_list)) / len(Align_sequence_number))
        Maximum_identity_score = np.max(Align_score_list)
        Minimum_identity_score = np.min(Align_score_list)
        if str(method).lower() == 'average':
            Identity_score = Average_identity_score
        elif str(method).lower() == 'max':
            Identity_score = Maximum_identity_score
        elif str(method).lower() == 'min':
            Identity_score = Minimum_identity_score
        elif str(method).lower() == 'all':
            Identity_score = [Average_identity_score, Minimum_identity_score, Maximum_identity_score]
    except ValueError:
        Identity_score = np.nan
    return Identity_score