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

def DesignIdentifyPrimer(args):
    """
    Primer design algorithm for identification of bacteria.
    The primer sets obtained from this program are able to use for differentiaing each input sequence.

    Parameters
    ----------
    args: ArgumentParser, class containing appropriate property as below
        input_file: Input file path (required)\n
        exclude_file: File path for exclusion sequence(s). Specify the sequence(s) file path of the bacteria if there are some bacteria that you would like to not amplify.\n
        primer_size: Primer size\n
        allowance: Mismatch allowance ratio. The value means that x base [primer size * allowance] mismatch is accepted. Note that setting this parameter too large might causes the increased run time and excessive memory consumption.\n
        range: Search range from primer size. If the value is 1 and primer size is 25, the primer sets that have 25-26 base length are explored.\n
        distance: The minimum distance between annealing sites that are hybridized with a primer\n
        output: Output directory path (Make a new directory if the directory does not exist)\n
        process: The number of processes (sometimes the number of CPU core) used for analysis\n
        Group_id: Type the file path of the text that specifies which sequences are same group, after the '--Group_id' option. Please avoid to contain a sequence name in ID like as combination of sequence name '12' and ID 'SeqID12'. See Readme for more detailed information.\n
        Exclude_mode: Choose the method for excluding the sequence(s) from 'fast' or 'standard' when you specify some sequence(s) file path of the bacteria that you would like to exclude using '-e' option\n
        Result_output: The upper limit of result output\n
        Cut_off_lower: The lower limit of amplicon size\n
        Cut_off_upper: The upper limit of amplicon size\n
        Match_rate: The ratio of trials for which the primer candidate fulfilled all criteria when the allowance value is decreased. The higher the number is, the more specific the primer obtained is\n
        Chunks: The chunk size for calculation. If the memory usage for calculation using the chunk size exceeds the GPU memory size, the processing unit for calculation will be switched to the CPU automatically\n
        Maximum_annealing_site_number: The maximum acceptable value of the number of annealing site of the candidate of the primer in the input sequence\n
        Window_size: The duplicated candidates containing this window will be removed\n
        Search_mode: There are four options: exhaustive/moderate/sparse/manual. If you choose the 'manual' option, type the ratio to primer length after 'manual'. (e.g. --Search_mode manual 0.2.) (default: moderate when the average input sequence length is >5000, and exhaustive when the average input sequence length is ≤5000)\n
        withinMemory: All analyses are performed within memory\n
        Without_allowance_adjustment: Use this option if you do not want to modify the allowance value for every homology calculation\n
        circularDNA: If there are some circular DNAs in the input sequences, use this option (default: n/a. It means all input sequences are linear DNA. When there are some circular DNA input sequences, type 'all', 'individually', 'n/a', or the file path of the text that specify which sequence is circularDNA, after the '--circularDNA' option. See Readme for more detailed information.)\n
            Text file example:\n
                Sequence_name1 circularDNA\n
                Sequence_name2 linearDNA\n
                Sequence_name3 linearDNA\n
                    ...\n
                Sequence_nameN circularDNA\n
        exclude_circularDNA: If there are some circular DNAs in the input sequence(s) that you do not want to amplify, use this option (default: n/a. It means all input sequences are linear DNA. When there is some circular DNA in the sequence file for exclusion, type 'all', 'individually', 'n/a', or the file path of the text that specifies which sequence is circularDNA, after the '--exclude_circularDNA' option. See Readme for more detailed information.)\n
        Score_calculation: The calculation method of the score for identifying microorganisms. Fragment length or sequence. When the 'Sequence' is specified, the primer set that produces only a single amplicon will be obtained in order to reduce computational complexity.\n
        Combination_number: The number of primer sets to be used for identification.\n
        Correlation_threshold: The primer sets with a correlation coefficient greater than this are grouped, and two or more primer sets from the same group are never chosen sets.\n
        Dendrogram_output: The number supplied in this parameter will be used to construct dendrograms.\n
        Reference_tree: Use this option if you evaluate a primer set based on the distance between the output tree and the reference tree. Specify a newick tree or a file path of newick format phylogenetic tree after '--Reference_tree' option (default: None).\n
        Only_sequence_with_feature_key: This option should be used when designing primer sets based solely on the sequences with feature key, such as gene (default: False).\n
        Fragment_size_pattern_matrix: When you have a csv file of fragment size pattern matrix, you can reanalyse from the csv file. Specify the file path.\n
        Fragment_start_position_matrix: When you reanalyse from fragment size pattern matrix by 'Sequence' mode, specify the csv file path of fragment start position matrix.\n

    Returns
    -------
    CSV_file: CSV contained primer sets and fragment size matrix amplified by each primer set

    """
    import sys
    import os
    import warnings
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    import re
    import time
    import pickle
    import shutil
    import subprocess
    from tempfile import NamedTemporaryFile
    from datetime import datetime as dt
    import math
    from difflib import SequenceMatcher
    from collections import Counter
    import statistics
    import csv
    from tqdm import tqdm
    from shrslib.basicfunc import read_sequence_file, init_worker, calculate_Tm_value, circularDNA, check_input_file, complementary_sequence, combination_basedon_correlation, linkage_matrix2newick
    from shrslib.scores import calculate_flexibility, arr_length_in_arr, fragment_size_distance
    from shrslib.explore import identify_microorganisms, PCR_check
    from shrslib.multiprocessfunc import cumulative_pairwise_identity
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import itertools as it
    from functools import partial
    from multiprocessing import Pool, cpu_count, shared_memory, get_context
    from scipy.spatial.distance import pdist
    from scipy.cluster.hierarchy import distance, linkage, fcluster, dendrogram
    from Bio.Phylo.TreeConstruction import DistanceCalculator
    from Bio import AlignIO
    from Bio.Align import MultipleSeqAlignment
    from dendropy.calculate import treecompare
    import dendropy
    try:
        import cupy as cp
    except:
        pass
    Pandas_later_210 = pd.__version__ >= '2.1.0'
    try:
        input_file = args.input_file
    except:
        sys.exit("Need a FASTA file or folder containing FASTA files after '-i '. \nPlease use '-h' or '--help' option if you would like to confirm usage.")
    if os.path.isfile(input_file):
        file_paths = [input_file]
    elif os.path.isdir(input_file):
        file_names = os.listdir(input_file)
        if input_file.endswith("/"):
            file_paths = [input_file+file_name for file_name in file_names]
        else:
            file_paths = [input_file+"/"+file_name for file_name in file_names]
        file_paths = [file_path for file_path in file_paths if os.path.isfile(file_path)]
        for file_path in file_paths:
            with open(file_path, "rt", encoding = "utf-8") as fin:
                Firstline = fin.readline()
                if np.logical_not(Firstline.startswith(">") | Firstline.startswith("LOCUS")):
                    print("There are some file(s) of which are not FASTA or Genbank in folder inputed. Please remove the file(s).")
                    sys.exit()
    else:
        sys.exit("Error: The input file/folder does not exist.")
    probe_size = args.primer_size
    allowance = args.allowance
    size_range = args.range
    interval_distance = args.distance
    if interval_distance < 1:
        interval_distance = int(1)
    output_folder = args.output
    if output_folder is not None:
        if not output_folder.endswith("/"):
            output_folder = output_folder+"/"
        if not os.path.exists(output_folder):
            os.mkdir(output_folder)
    else:
        absolute_path = re.sub("\\\\", "/", os.path.abspath(file_paths[0]))
        output_folder = absolute_path[:absolute_path.rfind("/") + 1]
    Result_output = args.Result_output
    cut_off_lower = args.Cut_off_lower
    cut_off_upper = args.Cut_off_upper
    Match_rate = args.Match_rate
    Score_calculation = args.Score_calculation
    if args.Chunks is not None:
        if str(args.Chunks).isdecimal():
            homology_calculation_chunks = args.Chunks
        else:
            homology_calculation_chunks = str("Auto")
    else:
        homology_calculation_chunks = str("Auto")
    Maximum_annealing_site_number = args.Maximum_annealing_site_number
    Window_size = args.Window_size
    withinMemory = args.withinMemory
    Allowance_adjustment = args.Without_allowance_adjustment
    Combination_number = args.Combination_number
    Correlation_threshold = args.Correlation_threshold
    Dendrogram_output = args.Dendrogram_output
    ReferenceTree = args.Reference_tree
    OnlyFeature = args.Only_sequence_with_feature_key
    CPU = args.process
    if CPU is not None:
        if CPU > cpu_count():
            CPU = int(math.ceil(cpu_count()))
    else:
        if cpu_count() <= 3:
            CPU = int(1)
        elif cpu_count() <= 8:
            CPU = int(math.floor(cpu_count() / 2))
        elif cpu_count() <= 12:
            CPU = int(cpu_count() - 4)
        elif cpu_count() <= 24:
            CPU = int(math.floor(cpu_count() / 2) + 2)
        else:
            CPU = int(16)
    if size_range == 0:
        Probe_size_range_description = str(probe_size)
    else:
        if size_range < 0:
            Probe_size_range_description = "[{0} - {1}]".format(probe_size + size_range, probe_size)
        else:
            Probe_size_range_description = "[{0} - {1}]".format(probe_size, probe_size + size_range)
    if probe_size < 2 * size_range:
        warnings.warn("\nThe range searching a primer set should be below a half of probe size.\n")
    if args.circularDNA is not None:
        overlap_region = int(np.max([interval_distance, cut_off_upper]))
        if (len(args.circularDNA) == 0):
            circular_index = check_input_file(file_paths, circular = "all")
        elif (args.circularDNA[0].lower() == "all"):
            circular_index = check_input_file(file_paths, circular = "all")
        elif args.circularDNA[0].lower() == "individually":
            circular_index = check_input_file(file_paths, circular = "individually")
        elif os.path.isfile(args.circularDNA[0]):
            circular_index = check_input_file(file_paths, circular = args.circularDNA[0])
        elif args.circularDNA[0].lower() == "n/a":
            overlap_region = 0
            circular_index = check_input_file(file_paths, circular = "n/a")
        else:
            print(" Specify the file path, 'all', 'individually' or 'n/a' after --circularDNA option.\n All input sequence(s) are analysed as circular DNA")
            circular_index = check_input_file(file_paths, circular = "all")
    else:
        overlap_region = 0
        circular_index = check_input_file(file_paths, circular = "n/a")
    seq_dict = dict()
    Total_length = 0
    Genbank_file_check = False
    for file_path in file_paths:
        with open(file_path, "rt") as fin:
            Genbank_file = fin.readline().startswith("LOCUS")
        Genbank_file_check = Genbank_file_check | Genbank_file
        if OnlyFeature & Genbank_file:
            read_data = read_sequence_file(file_path, Feature = True)
            GeneAnnotations = {k:read_data[0][k][1] for k in read_data[0].keys()}
            GenePositions = {k:[re.split(r"\.+", k) for k in GeneAnnotation.keys() if re.fullmatch(r"[0-9]+\.+[0-9]+", k)] for k, GeneAnnotation in GeneAnnotations.items()}
            StartEndPositions = {}
            StartEndPositions.update({k:{str(i) + "s": p[0] for i, p in enumerate(GenePosition)} for k, GenePosition in GenePositions.items()})
            [StartEndPositions[k].update({str(i) + "e": p[1] for i, p in enumerate(GenePosition)}) for k, GenePosition in GenePositions.items()]
            StartEndPositions = {k:dict(sorted(StartEndPositions[k].items(), key = lambda x: abs(int(x[1])))) for k in StartEndPositions.keys()}
            GenePositions = {}
            for key, StartEndPosition in StartEndPositions.items():
                StartEndCount = 0
                StartPositions = []
                EndPositions = []
                for k, v in StartEndPosition.items():
                    if (StartEndCount == 0) & (k[-1] == "s"):
                        StartPositions.append(abs(int(v)))
                    StartEndCount = StartEndCount + 1 if k[-1] == "s" else StartEndCount - 1
                    if (StartEndCount == 0) & (k[-1] == "e"):
                        EndPositions.append(abs(int(v)))
                GenePositions.update({key: [[int(s), int(e)] for s, e in zip(StartPositions, EndPositions)]})
            GeneExtractions = {k:"X".join([read_data[0][k][0][(int(p[0]) - 1) : int(p[1])] for p in GenePosition]) for k, GenePosition in GenePositions.items()}
            seq_dict.update({key:GeneExtractions[key] for key in GeneExtractions.keys()})
        else:
            read_data = read_sequence_file(file_path)
            seq_dict.update({key:circularDNA(sequence = read_data[0][key], overlap = int(overlap_region)) if circular_index[key] else circularDNA(sequence = read_data[0][key], overlap = int(0)) for key in read_data[0]})
        Total_length += read_data[1] * read_data[2]
    if OnlyFeature & np.logical_not(Genbank_file_check):
        print("Primer design based on the sequences with feature key requires at least one Genbank format file.")
        sys.exit()
    Remain_sequence = []
    Remove_sequence_length = 0
    for key in seq_dict:
        if np.max([str(seq_dict[key])[i:(i + probe_size - 1):].count('N') for i in range(len(str(seq_dict[key])) - probe_size + 1)]) > (probe_size - math.ceil(probe_size * allowance)):
            User_input = ''
            while True:
                User_input = input("'{}' has many 'N' base in the sequence. Do you remove this sequence? (Y/n): ".format(key))
                if (User_input.lower() == "y") | (User_input.lower() == "yes") | (User_input.lower() == "n") | (User_input.lower() == "no"):
                    break
            if (User_input.lower() == "y") | (User_input.lower() == "yes"):
                Remain_sequence += [False]
                Remove_sequence_length += len(seq_dict[key])
            elif (User_input.lower() == "n") | (User_input.lower() == "no"):
                Remain_sequence += [True]
        else:
            Remain_sequence += [True]
    seq_dict = {list(seq_dict.keys())[i]:seq_dict[list(seq_dict.keys())[i]] for i in range(len(seq_dict)) if Remain_sequence[i]}
    del Remain_sequence
    input_seq = len(seq_dict)
    Average_length = round((Total_length - Remove_sequence_length) / input_seq, 1)
    Sort_index = list(seq_dict.keys())
    seq_dict = dict(sorted(seq_dict.items(), key = lambda x:len(x[1])))
    Ref_template_name = list(seq_dict.keys())[0]
    Ref_template_seq = seq_dict.pop(Ref_template_name)
    seq_dict.update({Ref_template_name:Ref_template_seq})
    if args.exclude_file is not None:
        Exclude_sequence_files_input = args.exclude_file
        if os.path.isfile(Exclude_sequence_files_input):
            Exclude_sequences_file_paths = [Exclude_sequence_files_input]
        elif os.path.isdir(Exclude_sequence_files_input):
            file_names = os.listdir(Exclude_sequence_files_input)
            if Exclude_sequence_files_input.endswith("/"):
                Exclude_sequences_file_paths = [Exclude_sequence_files_input + file_name for file_name in file_names]
            else:
                Exclude_sequences_file_paths = [Exclude_sequence_files_input + "/"+file_name for file_name in file_names]
        else:
            print("Error: The exclude file/folder does not exist.")
            sys.exit()
        if args.exclude_circularDNA is not None:
            exclude_overlap_region = int(np.max([interval_distance, cut_off_upper]))
            if (len(args.exclude_circularDNA) == 0):
                exclude_circular_index = check_input_file(Exclude_sequences_file_paths, circular = "all")
            elif (args.exclude_circularDNA[0].lower() == "all"):
                exclude_circular_index = check_input_file(Exclude_sequences_file_paths, circular = "all")
            elif args.exclude_circularDNA[0].lower() == "individually":
                exclude_circular_index = check_input_file(Exclude_sequences_file_paths, circular = "individually")
            elif os.path.isfile(args.exclude_circularDNA[0]):
                exclude_circular_index = check_input_file(Exclude_sequences_file_paths, circular = args.exclude_circularDNA[0])
            elif args.exclude_circularDNA[0].lower() == "n/a":
                exclude_overlap_region = 0
                exclude_circular_index = check_input_file(Exclude_sequences_file_paths, circular = "n/a")
            else:
                print(" Specify the exclude circular file path, 'all', 'individually' or 'n/a' after --exclude_circularDNA option.\n All input sequence(s) for exclusion are analysed as circular DNA")
                exclude_circular_index = check_input_file(Exclude_sequences_file_paths, circular = "all")
        else:
            exclude_overlap_region = 0
            exclude_circular_index = check_input_file(Exclude_sequences_file_paths, circular = "n/a")
        Exclude_sequences_list = dict()
        for Exclude_sequences_file_path in Exclude_sequences_file_paths:
            read_data = read_sequence_file(Exclude_sequences_file_path)
            Exclude_sequences_list.update({key:circularDNA(sequence = read_data[0][key], overlap = int(exclude_overlap_region)) if exclude_circular_index[key] else circularDNA(sequence = read_data[0][key], overlap = int(0)) for key in read_data[0]})
        Exclude_sequences_list = dict(sorted(Exclude_sequences_list.items(), key = lambda x:len(x[1])))
    else:
        Exclude_sequences_list = {}
    Exclude_mode = args.Exclude_mode
    if args.Search_mode is not None:
        if args.Search_mode[0].lower() == "exhaustive":
            Search_mode = "exhaustive"
            Search_interval = int(1)
        elif args.Search_mode[0].lower() == "moderate":
            Search_mode = "moderate"
            Search_interval = int(0)
        elif args.Search_mode[0].lower() == "sparse":
            Search_mode = "sparse"
            Search_interval = int(0)
        elif args.Search_mode[0].lower() == "manual":
            Search_mode = "manual"
            try:
                Search_interval = float(args.Search_mode[1])
            except:
                print(" Numerical value is needed after manual option.\n The ratio to primer length should be inputed after ‘—Search_mode manual’ when you use ‘manual' in '—Search_mode’ option.")
                sys.exit()
        else:
            if Average_length > 5000:
                Search_mode = "moderate"
                Search_interval = int(0)
            else:
                Search_mode = "exhaustive"
                Search_interval = int(1)
    else:
        if Average_length > 5000:
            Search_mode = "moderate"
            Search_interval = int(0)
        else:
            Search_mode = "exhaustive"
            Search_interval = int(1)
    GroupIndex = args.Group_id
    if GroupIndex is not None:
        if os.path.isfile(GroupIndex):
            GID = []
            with open(GroupIndex, 'rt', encoding = "utf-8") as fin:
                line = fin.readline()
                while line:
                    GID.append(line)
                    line = fin.readline()
            if np.any([gid.startswith(" ") | gid.startswith("\t") | gid.startswith(",") for gid in GID]):
                print("Please remove a leading comma, leading tab character or leading space in Group_id file.")
                sys.exit()
            NAME2GROUP = {name:[str(gid.replace(name, '').replace(',', '').replace('\t', '').replace(' ', '').replace('\n', '')) for gid in GID if (((gid.count(name + " ") > 0) | (gid.count(name + "\t") > 0) | (gid.count(name + ",") > 0)) & ((gid.replace(name, "").startswith(" ")) | (gid.replace(name, "").startswith("\t")) | (gid.replace(name, "").startswith(","))))] for name in Sort_index}
            GROUP2NAME = {}
            Empty_number = len([len(i) for i in sorted(NAME2GROUP.values()) if len(i) == 0])
            if Empty_number > 0:
                print("\n The name of input sequence(s) didn't match that of sequence(s) in group index file. \n The sequence(s) that was not found in group index file was assigned new unique group index.")
                while True:
                    stop_signal = input(" Proceed (Y/n)?: ")
                    if (stop_signal.lower() == "y") | (stop_signal.lower() == "yes") | (stop_signal.lower() == "n") | (stop_signal.lower() == "no"):
                        break
                if (stop_signal.lower() == "n") | (stop_signal.lower() == "no"):
                    sys.exit()
                LastIndexCharacter = sorted(NAME2GROUP.values())[-1][-1]
                LastIndexCode = ord(sorted(NAME2GROUP.values())[-1][-1][-1])
                AdditionalCode = [LastIndexCode + i + 1 for i in range(Empty_number)]
                Empty_name = [name for name, gid in NAME2GROUP.items() if len(NAME2GROUP[name]) == 0]
                [NAME2GROUP.update({name:[LastIndexCharacter[0:len(LastIndexCharacter) - 1] + chr(code)]}) for name, code in zip(Empty_name, AdditionalCode)]
            [[GROUP2NAME.update({g : GROUP2NAME[g] + [name]}) if (g in GROUP2NAME.keys()) else GROUP2NAME.update({g : [name]}) for g in gid] for name, gid in NAME2GROUP.items()]
        else:
            print(" Group index file doesn't exist. Group index are ignored in this analysis.")
            while True:
                stop_signal = input(" Proceed (Y/n)?: ")
                if (stop_signal.lower() == "y") | (stop_signal.lower() == "yes") | (stop_signal.lower() == "n") | (stop_signal.lower() == "no"):
                    break
            if (stop_signal.lower() == "n") | (stop_signal.lower() == "no"):
                sys.exit()
            else:
                GroupIndex = None
    if ReferenceTree is not None:
        Taxon_namespace = dendropy.TaxonNamespace() 
        if os.path.isfile(ReferenceTree):
            ReferenceTree = dendropy.Tree.get(path = ReferenceTree, schema = "newick", taxon_namespace = Taxon_namespace, preserve_underscores = True)
        else:
            ReferenceTree = dendropy.Tree.get(data = ReferenceTree, schema = "newick", taxon_namespace = Taxon_namespace, preserve_underscores = True)
        ReferenceTree.is_rooted
        TreeDescription = ReferenceTree.__str__()
        Leaf = [taxon.label for taxon in ReferenceTree.taxon_namespace]
        if set(Sort_index) != set(Leaf):
            print("\n----- Check the reference tree -----\n All labels in reference tree specified by newick format text should correspond to the labels of sequence in input file. The labels in reference tree are below. \n  {} \n The labels in input sequence file are below. \n  {} ".format("\n  ".join(sorted(Leaf)), "\n  ".join(sorted([name for name in Sort_index]))))
            sys.exit()
    Size_matrix_path = args.Fragment_size_pattern_matrix
    Start_pos_matrix_path = args.Fragment_start_position_matrix
    TimeStamp = dt.now().strftime('%Y%m%d_%H%M%S')
    if len(seq_dict.keys()) <= 10:
        InputInformation = [name + " [circular]" if circular_index[name] else name for name in Sort_index]
        if GroupIndex is not None:
            GroupInformation = [" [Group ID: " + str(NAME2GROUP[name][0]) + "]" for name in Sort_index]
            InputInformation = [ii + gi for ii, gi in zip(InputInformation, GroupInformation)]
        print("[Target_microorganisms]", "\n ", "Input sequences:", input_seq, "/ Average length:", Average_length, "\n  ", "\n   ".join(InputInformation))
    else:
        PreInputInformation = [name + " [circular]" if circular_index[name] else name for name in Sort_index[0:3]]
        PostInputInformation = [name + " [circular]" if circular_index[name] else name for name in Sort_index[(len(Sort_index)-3):len(Sort_index)]]
        if GroupIndex is not None:
            PreGroupInformation = [" [Group ID: " + str(NAME2GROUP[name][0]) + "]" for name in Sort_index[0:3]]
            PostGroupInformation = [" [Group ID: " + str(NAME2GROUP[name][0]) + "]" for name in Sort_index[(len(Sort_index)-3):len(Sort_index)]]
            PreInputInformation = [ii + gi for ii, gi in zip(PreInputInformation, PreGroupInformation)]
            PostInputInformation = [ii + gi for ii, gi in zip(PostInputInformation, PostGroupInformation)]
        print("[Target_microorganisms]", "\n ", "Input sequences:", input_seq, "/ Average length:", Average_length, "\n  ", "\n   ".join(PreInputInformation), "\n\n    ... \n\n  ", "\n   ".join(PostInputInformation))
    print("[Parameters]", "\n  ", "Primer size: {0}\n   Allowance: {1}\n   Cut_off_lower: {2}\n   Cut_off_upper: {3}\n   Interval_distance: {4}\n   Match_rate: {5}\n   CPU usage: {6}\n   Homology_calculation_chunks: {7}\n   Maximum_annealing_site_number: {8}\n   Window_size: {9}\n   Exclude_sequences_list: {10}\n   Search_mode: {11}\n   Score_calculation_mode: {12}\n   Search_area: {13}\n   Reference_tree: {14}".format(Probe_size_range_description, allowance, cut_off_lower, cut_off_upper, interval_distance, Match_rate, CPU, homology_calculation_chunks, Maximum_annealing_site_number, Window_size, "\n                           ".join([name + " [circular]" if exclude_circular_index[name] else name for name in [str(es) for es in Exclude_sequences_list.keys()]]) if len(Exclude_sequences_list) != 0 else "empty", Search_mode, Score_calculation, "Extracted sequences based on feature key in genbank format" if OnlyFeature else "Whole genome sequence", TreeDescription if ReferenceTree is not None else "Not provided"))
    if size_range == 0:
        if len(Exclude_sequences_list) == 0:
            Total_procedure = input_seq + 12
        else:
            Total_procedure = input_seq + 13
    else:
        if len(Exclude_sequences_list) == 0:
            Total_procedure = (input_seq + 2) * (np.abs(size_range) + 1) + 10
        elif Exclude_mode == "standard":
            Total_procedure = (input_seq + 2) * (np.abs(size_range) + 1) + 11
        else:
            Total_procedure = (input_seq + 3) * (np.abs(size_range) + 1) + 10
    with tqdm(total = Total_procedure, desc = "  - Workflow status - ", leave = False, position = 0, bar_format = "{desc} Step no.{n:.0f} in {total:.0f}", smoothing = 0) as progress_bar:
        if Size_matrix_path is not None:
            if os.path.exists(Size_matrix_path):
                try:
                    Fragment_size_data = pd.read_csv(Size_matrix_path, sep = ",", header = 0, index_col = [0,1])
                    if set(Fragment_size_data.columns) == set(seq_dict.keys()):
                        Fragment_size_data = Fragment_size_data.map(eval) if Pandas_later_210 else Fragment_size_data.applymap(eval)
                        Fragment_size_data = Fragment_size_data.reindex(columns = Sort_index)
                        if np.logical_not(isinstance(Fragment_size_data.iloc[0,0][0], (int, float, np.int8, np.int16, np.int32, np.int64, np.uint8, np.uint16, np.uint32, np.uint64, np.float16, np.float32, np.float64, ))):
                            progress_bar.update(Total_procedure)
                            print("\033[1B" + "\r" + "Error: Unknown format. Check the fragment size pattern matrix file.")
                            raise TypeError
                        if not os.path.isdir(output_folder+"Result"):
                            os.mkdir(output_folder+"Result")
                        else:
                            pass
                        os.mkdir(output_folder+'Result/'+TimeStamp+'identify_primer_set')
                        if Start_pos_matrix_path is not None:
                            if os.path.exists(Start_pos_matrix_path):
                                try:
                                    Position_data = pd.read_csv(Start_pos_matrix_path, sep = ",", header = 0, index_col = [0,1])
                                    if set(Position_data.columns) == set(seq_dict.keys()):
                                        Position_data = Position_data.map(eval) if Pandas_later_210 else Position_data.applymap(eval)
                                        Position_data = Position_data.reindex(columns = Sort_index)
                                        if np.logical_not(isinstance(Position_data.iloc[0,0][0], (list, tuple, np.ndarray, pd.Series, ))) & (Score_calculation == "Sequence"):
                                            Score_calculation = "Fragment"
                                            print("\033[1B" + "\r" + "Unknown format. Check fragment start position matrix csv file. Score calculation method has been changed to 'Fragment' mode.")
                                    else:
                                        if Score_calculation == "Sequence":
                                            Score_calculation = "Fragment"
                                            print("\033[1B" + "\r" + "Unknown format. Check fragment start position matrix csv file. Columns name in csv file should be corresponded to the name of sequences in fasta file. Score calculation method has been changed to 'Fragment' mode.")
                                except:
                                    Score_calculation = "Fragment"
                                    print("\033[1B" + "\r" + "Unknown format. Check fragment start position matrix csv file. Score calculation method has been changed to 'Fragment' mode.")
                            else:
                                if Score_calculation == "Sequence":
                                    Score_calculation = "Fragment"
                                    print("\033[1B" + "\r" + "Fragment start position matrix csv file does not exist. Score calculation method has been changed to 'Fragment' mode.")
                            progress_bar.update(Total_procedure - 3)
                        else:
                            progress_bar.update(Total_procedure - 3)
                            if Score_calculation == "Sequence":
                                Score_calculation = "Fragment"
                                print("\033[1B" + "\r" + "Fragment start position matrix csv file is needed for 'Sequence' mode analysis. Score calculation method has been changed to 'Fragment' mode.")
                    else:
                        progress_bar.update(Total_procedure)
                        print("\033[1B" + "\r" + "Error: Unknown format. Check the fragment size pattern matrix file. Columns name in csv file should be corresponded to the name of sequences in fasta file.")
                        raise TypeError
                except TypeError:
                    sys.exit()
                except:
                    progress_bar.update(Total_procedure)
                    print("\033[1B" + "\r" + "Error: Unknown format. Check csv file.")
                    sys.exit()
            else:
                progress_bar.update(Total_procedure)
                print("\033[1B" + "\r" + "Error: The fragment size pattern matrix file does not exist.")
                sys.exit()
        else:
            Raw_Data = identify_microorganisms(input = seq_dict, probe_size = probe_size, size_range = size_range, allowance_rate = allowance, cut_off_lower = cut_off_lower, cut_off_upper = cut_off_upper, interval_distance = interval_distance, Match_rate = Match_rate, CPU = CPU, homology_calculation_chunks = homology_calculation_chunks, Maximum_annealing_site_number = Maximum_annealing_site_number, Window_size = Window_size, Exclude_sequences_list = Exclude_sequences_list, Search_mode = Search_mode, Search_interval = Search_interval, Exclude_mode = Exclude_mode, withinMemory = withinMemory, Allowance_adjustment = Allowance_adjustment, progress_bar = progress_bar)
            Fragment_size_data = Raw_Data[0].map(lambda x:[int(y) for y in x]) if Pandas_later_210 else Raw_Data[0].applymap(lambda x:[int(y) for y in x])
            Position_data = Raw_Data[1]
            Fragment_size_data = Fragment_size_data.reindex(columns = Sort_index)
            Position_data = Position_data.reindex(columns = Sort_index)
            if not os.path.isdir(output_folder+"Result"):
                os.mkdir(output_folder+"Result")
            else:
                pass
            os.mkdir(output_folder+'Result/'+TimeStamp+'identify_primer_set')
            if OnlyFeature:
                Fragment_size_data.to_csv(output_folder+'Result/'+TimeStamp+'identify_primer_set'+'/'+TimeStamp+'Fragment_size_pattern_matrix_using_featurekey_extraction.csv')
                Position_data.map(lambda x:[x[0].tolist(), x[1].tolist()]).to_csv(output_folder+'Result/'+TimeStamp+'identify_primer_set'+'/'+TimeStamp+'Fragment_start_position_matrix_using_featurekey_extraction.csv') if Pandas_later_210 else Position_data.applymap(lambda x:[x[0].tolist(), x[1].tolist()]).to_csv(output_folder+'Result/'+TimeStamp+'identify_primer_set'+'/'+TimeStamp+'Fragment_start_position_matrix_using_featurekey_extraction.csv')
            else:
                Fragment_size_data.to_csv(output_folder+'Result/'+TimeStamp+'identify_primer_set'+'/'+TimeStamp+'Fragment_size_pattern_matrix.csv')
                Position_data.map(lambda x:[x[0].tolist(), x[1].tolist()]).to_csv(output_folder+'Result/'+TimeStamp+'identify_primer_set'+'/'+TimeStamp+'Fragment_start_position_matrix.csv') if Pandas_later_210 else Position_data.applymap(lambda x:[x[0].tolist(), x[1].tolist()]).to_csv(output_folder+'Result/'+TimeStamp+'identify_primer_set'+'/'+TimeStamp+'Fragment_start_position_matrix.csv')
        Flexibility_score = [calculate_flexibility(sequences, detailed = True) for sequences in Fragment_size_data.index]
        Fragment_size_data = Fragment_size_data.assign(Flexibility = Flexibility_score)
        Fragment_size_data = Fragment_size_data.sort_values(['Flexibility'], ascending = [True])
        Fragment_size_data = Fragment_size_data.drop('Flexibility', axis = 1)
        if Score_calculation == "Fragment":
            Criteria = np.logical_not(Fragment_size_data.map(lambda x:str(x)).duplicated(subset  = Fragment_size_data.columns, keep = 'first')) if Pandas_later_210 else np.logical_not(Fragment_size_data.applymap(lambda x:str(x)).duplicated(subset  = Fragment_size_data.columns, keep = 'first'))
            Fragment_size_data = Fragment_size_data[Criteria]
            sequence_summary = Fragment_size_data.copy(deep = True)
            sequence_summary = sequence_summary.map(lambda x:sorted(list(set(x)))) if Pandas_later_210 else sequence_summary.applymap(lambda x:sorted(list(set(x))))
            Result = sequence_summary.copy(deep = True)
            for i in range(Result.shape[0]):
                Result.iloc[i] = np.array([str([(x, round(Fragment_size_data.iloc[i, j].count(x)/len(Fragment_size_data.iloc[i, j]), 2),) for x in sequence_summary.iloc[i, j]]) for j in range(len(sequence_summary.iloc[i]))], dtype = object)
            Fragment_number = [np.sum(arr_length_in_arr(sequence_summary.iloc[i])) for i in range(sequence_summary.shape[0])]
            progress_bar.update(1)
            if GroupIndex is not None:
                GROUPING_NAMES = list(GROUP2NAME.values())
                GROUPING_NAMES_LIST = list(it.product(*GROUPING_NAMES))
                ScoreValueListMatrix = [[fragment_size_distance(sequence_summary.loc[:, gn].iloc[i], sum = False, method = 'all') for gn in GROUPING_NAMES_LIST] for i in tqdm(range(sequence_summary.shape[0]), total = sequence_summary.shape[0], desc = "    Calculating score", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0)]
                Score = [np.min([ScoreValue[0] / (Fragment_number[i] - min(Fragment_number) + 1) for ScoreValue in ScoreValueList]) for i, ScoreValueList in enumerate(ScoreValueListMatrix)]
                Minimum_Score = [np.min([ScoreValue[1] for ScoreValue in ScoreValueList]) for ScoreValueList in ScoreValueListMatrix]
                GroupScoreValueListMatrix = [[fragment_size_distance(sequence_summary.loc[:, GROUP2NAME[gr]].iloc[i], sum = False, method = 'all') for gr in GROUP2NAME.keys() if len(GROUP2NAME[gr]) > 1] for i in tqdm(range(sequence_summary.shape[0]), total = sequence_summary.shape[0], desc = "    Calculating group score and sorting", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0)]
                Group_Score = [[GroupScoreValue[0] for GroupScoreValue in GroupScoreValueList] if len(GroupScoreValueList) > 0 else [] for GroupScoreValueList in GroupScoreValueListMatrix]
                Group_Score = [1 if len(gs) == 0 else np.std(gs) + np.mean(gs) if np.mean(gs) != 0 else 0.66 for gs in Group_Score]
                Maximum_Group_Score = [np.max([GroupScoreValue[2] for GroupScoreValue in GroupScoreValueList]) if len(GroupScoreValueList) > 0 else int(0) for GroupScoreValueList in GroupScoreValueListMatrix]
                Score = [s / g for s, g in zip(Score, Group_Score)]
                Result = Result.assign(Score = Score, Fragment_number = Fragment_number, Minimum_Score = Minimum_Score, Maximum_Group_Score = Maximum_Group_Score)
                if (np.any((Result['Minimum_Score'] > Result['Maximum_Group_Score']) & (Result['Score'] > 100)) & (np.sum(Result['Minimum_Score'] > Result['Maximum_Group_Score']) >= Combination_number)):
                    Result = Result[(Result['Minimum_Score'] > Result['Maximum_Group_Score'])]
                Result = Result.drop(['Minimum_Score', 'Maximum_Group_Score'], axis = 1)
            else:
                Score = [fragment_size_distance(sequence_summary.iloc[i], sum = False, method = 'average') / (Fragment_number[i] - min(Fragment_number) + 1) for i in tqdm(range(sequence_summary.shape[0]), total = sequence_summary.shape[0], desc = "    Calculating score and sorting", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0)]
                Result = Result.assign(Score = Score, Fragment_number = Fragment_number)
            Result = Result if Result[Result['Score'] != 0].empty else Result[Result['Score'] != 0]
            Result['Score'] = Result['Score'].apply(lambda x:round(x, -1))
            Result = Result.sort_values(['Fragment_number', 'Score'], ascending = [True, False])
        elif Score_calculation == "Sequence":
            Position_data = Position_data.assign(Flexibility = Flexibility_score)
            Position_data = Position_data.sort_values(['Flexibility'], ascending = [True])
            Position_data = Position_data.drop('Flexibility', axis = 1)
            sequence_summary = Fragment_size_data.copy(deep = True)
            Criteria = sequence_summary.apply(lambda x:np.all([len(a) == 1 for a in x]), axis = 1)
            sequence_summary = sequence_summary[Criteria]
            Position_data = Position_data[Criteria]
            Position_data = Position_data.map(lambda x:[(int([x1, x2][np.argmin(np.abs([x1, x2]))]), int(np.argmin(np.abs([x1, x2]))), ) if (((x1 >= 0) & (x2 < 0)) | ((x1 < 0) & (x2 >= 0))) else np.nan for x1 in x[0] for x2 in x[1] if np.all([((x1 + x2) * (-1) >= cut_off_lower), ((x1 + x2) * (-1) <= cut_off_upper)])]) if Pandas_later_210 else Position_data.applymap(lambda x:[(int([x1, x2][np.argmin(np.abs([x1, x2]))]), int(np.argmin(np.abs([x1, x2]))), ) if (((x1 >= 0) & (x2 < 0)) | ((x1 < 0) & (x2 >= 0))) else np.nan for x1 in x[0] for x2 in x[1] if np.all([((x1 + x2) * (-1) >= cut_off_lower), ((x1 + x2) * (-1) <= cut_off_upper)])])
            sequence_summary = sequence_summary.map(lambda x:int(x[0])) if Pandas_later_210 else sequence_summary.applymap(lambda x:int(x[0]))
            Position_data = Position_data.map(lambda x:x[0] if len(x) == 1 else np.nan) if Pandas_later_210 else Position_data.applymap(lambda x:x[0] if len(x) == 1 else np.nan)
            Criteria = Position_data.isnull().any(axis = 1)
            Position_data = Position_data[np.logical_not(Criteria)]
            sequence_summary = sequence_summary[np.logical_not(Criteria)]
            Result = {name: {sequence_summary.index[i]: str(seq[int(np.abs(Position_data[name].iloc[i][0])) : int(np.abs(Position_data[name].iloc[i][0]) + sequence_summary[name].iloc[i])]) if (Position_data[name].iloc[i][1] == 0) else complementary_sequence(str(seq[int(np.abs(Position_data[name].iloc[i][0])) : int(np.abs(Position_data[name].iloc[i][0]) + sequence_summary[name].iloc[i])])) for i in range(sequence_summary.shape[0])} for name, seq in seq_dict.items()}
            Result = pd.DataFrame(Result)
            Result = Result.reindex(columns = Sort_index)
            progress_bar.update(1)
            if GroupIndex is not None:
                GROUPING_NAMES = list(GROUP2NAME.values())
                GROUPING_NAMES_LIST = list(it.product(*GROUPING_NAMES))
                with get_context("spawn").Pool(processes = CPU, initializer = init_worker) as pl:
                    try:
                        Score = np.repeat(0.0, Result.shape[0]).tolist()
                        Group_Score = np.repeat(1.0, Result.shape[0]).tolist()
                        Maximum_intergroup_score = np.repeat(0.0, Result.shape[0]).tolist()
                        Minimum_intragroup_score = np.repeat(1.0, Result.shape[0]).tolist()
                        with tqdm(total = Result.shape[0] * (np.sum([len(li) > 1 for li in GROUPING_NAMES_LIST]) + np.sum([len(v) > 1 for v in GROUP2NAME.values()])), desc = "    Calculating score and sorting", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0) as pbar:
                            def Progress_bar_update(Result):
                                pbar.update(1)
                            for group_name in GROUPING_NAMES_LIST:
                                if len(group_name) > 1:
                                    Score_temp = {row: pl.apply_async(partial(cumulative_pairwise_identity, df = Result.loc[:, group_name], method = 'all'), args = (row, ), callback = Progress_bar_update) for row in range(Result.shape[0])}
                                    Score_temp = [Score_temp[row].get() for row in range(Result.shape[0])]
                                    Score = [np.max([so, st[0]]) for so, st in zip(Score, Score_temp)]
                                    Maximum_intergroup_score = [np.max([so, st[2]]) for so, st in zip(Maximum_intergroup_score, Score_temp)]
                            for gr in GROUP2NAME.keys():
                                if len(GROUP2NAME[gr]) > 1:
                                    Group_Score_temp = {row: pl.apply_async(partial(cumulative_pairwise_identity, df = Result.loc[:, GROUP2NAME[gr]], method = 'all'), args = (row, ), callback = Progress_bar_update) for row in range(Result.shape[0])}
                                    Group_Score_temp = [Group_Score_temp[row].get() for row in range(Result.shape[0])]
                                    Group_Score = [np.min([gso, gst[0]]) for gso, gst in zip(Group_Score, Group_Score_temp)]
                                    Minimum_intragroup_score = [np.min([gso, gst[1]]) for gso, gst in zip(Minimum_intragroup_score, Group_Score_temp)]
                    except KeyboardInterrupt:
                        pl.terminate()
                        pl.join()
                        pl.close()
                        print("\n\n --- Keyboard Interrupt ---")
                        sys.exit()
                Result = Result.assign(Score = Score, Group_Score = Group_Score, Maximum_intergroup_score = Maximum_intergroup_score, Minimum_intragroup_score = Minimum_intragroup_score)
                if np.any((Result['Minimum_intragroup_score'] > Result['Maximum_intergroup_score']) & (Result['Score'] < 0.99)):
                    Result = Result[Result['Minimum_intragroup_score'] > Result['Maximum_intergroup_score']]
                    Result['Group_Score'] = Result['Group_Score'].apply(lambda x:math.ceil(x * 10) / 10)
                else:
                    Result['Group_Score'] = Result['Group_Score'].apply(lambda x:math.ceil(x * 100) / 100)
                Result['Score'] = Result['Score'].apply(lambda x:round(x, 4))
                Result = Result.sort_values(['Group_Score', 'Score'], ascending = [False, True])
                Result = Result.drop(['Group_Score', 'Maximum_intergroup_score', 'Minimum_intragroup_score'], axis = 1)
            else:
                with get_context("spawn").Pool(processes = CPU, initializer = init_worker) as pl:
                    try:
                        Score = list(tqdm(pl.imap(partial(cumulative_pairwise_identity, df = Result, method = "average"), range(Result.shape[0])), total = Result.shape[0], desc = "    Calculating score and sorting", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0))
                    except KeyboardInterrupt:
                        pl.terminate()
                        pl.join()
                        pl.close()
                        print("\n\n --- Keyboard Interrupt ---")
                        sys.exit()
                Result = Result.assign(Score = Score)
                Result['Score'] = Result['Score'].apply(lambda x:round(x, 4))
                Result = Result.sort_values('Score', ascending = True)
        Tm_value = [tuple(calculate_Tm_value(seq).values()) for seq in Result.index]
        Tm_value_difference = [round(np.abs(np.diff(tm))[0], 1) for tm in Tm_value]
        if Score_calculation == "Fragment":
            Result = Result.assign(Forward_Tm_value = [tm[0] for tm in Tm_value], Reverse_Tm_value = [tm[1] for tm in Tm_value], Tm_value_difference = Tm_value_difference)
        elif Score_calculation == "Sequence":
            Identical_sequences = Result.loc[:, Sort_index].apply(lambda x: int(len(x) - len(set(x))), axis = 1)
            Result = Result.assign(Forward_Tm_value = [tm[0] for tm in Tm_value], Reverse_Tm_value = [tm[1] for tm in Tm_value], Tm_value_difference = Tm_value_difference, Identical_sequences = Identical_sequences)
        progress_bar.update(1)
        try:
            if Score_calculation == "Fragment":
                if Result.empty:
                    raise pd.errors.EmptyDataError
                elif Result.shape[0] >= 100:
                    TOP_hundred_Index = Result.iloc[0:100].index
                else:
                    TOP_hundred_Index = Result.index
                TOP_hundred_Result = Fragment_size_data.loc[TOP_hundred_Index]
                TOP_hundred_Result = TOP_hundred_Result.map(lambda x:list(set(x)) if len(set(x)) == 1 else x) if Pandas_later_210 else TOP_hundred_Result.applymap(lambda x:list(set(x)) if len(set(x)) == 1 else x)
                Primer_set_combinations = combination_basedon_correlation(TOP_hundred_Result, number = Combination_number, Correlation_threshold = Correlation_threshold)
                Primer_set_combinations_number = 0
                for x in combination_basedon_correlation(TOP_hundred_Result, number = Combination_number, Correlation_threshold = Correlation_threshold):
                    Primer_set_combinations_number += 1
                Distance_score = {}
                Maximum_distance = math.sqrt(Combination_number) * (cut_off_upper - cut_off_lower)
                for combs in tqdm(Primer_set_combinations, total = Primer_set_combinations_number, desc = "    Choose primer sets", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0):
                    Extract_fragment_size = Fragment_size_data.loc[list(combs)]
                    Maximum_element_number = np.max([np.max(Extract_fragment_size.iloc[:, i].apply(lambda x:len(x) if type(x) is list else 1)) for i in range(Extract_fragment_size.shape[1])])
                    Expand_Extract_fragment_size = pd.DataFrame([[[sorted(li)[j] if len(li) >= j + 1 else int(Counter(li).most_common()[0][0]) for j in range(Maximum_element_number)] for li in Extract_fragment_size.iloc[:, i]] for i in range(Extract_fragment_size.shape[1])], dtype = object).T
                    Expand_Extract_fragment_size.columns = Extract_fragment_size.columns
                    Extract_fragment_size = pd.DataFrame([list(it.chain.from_iterable(Expand_Extract_fragment_size.iloc[:, i])) for i in range(Expand_Extract_fragment_size.shape[1])], index = Expand_Extract_fragment_size.columns)
                    if GroupIndex is not None:
                        if len(GROUP2NAME) > 1:
                            for gn in GROUPING_NAMES_LIST:
                                Each_sample_distance = pdist(Extract_fragment_size.loc[list(gn)], metric = 'euclidean')
                                if combs in Distance_score:
                                    if np.all(Each_sample_distance > 0):
                                        if (Distance_score[combs] > (np.sum(np.log10(Each_sample_distance / Maximum_distance)) / len(Each_sample_distance))):
                                            Distance_score.update({combs: np.sum(np.log10(Each_sample_distance / Maximum_distance)) / len(Each_sample_distance)})
                                else:
                                    if np.all(Each_sample_distance > 0):
                                        Distance_score.update({combs: np.sum(np.log10(Each_sample_distance / Maximum_distance)) / len(Each_sample_distance)})
                        else:
                            Each_sample_distance = pdist(Extract_fragment_size, metric = 'euclidean')
                            Distance_score.update({combs: (-1) * np.mean(Each_sample_distance) / Maximum_distance})
                    else:
                        Each_sample_distance = pdist(Extract_fragment_size, metric = 'euclidean')
                        if np.all(Each_sample_distance > 0):
                            Distance_score.update({combs: np.sum(np.log10(Each_sample_distance / Maximum_distance)) / len(Each_sample_distance)})
                    if ReferenceTree is not None:
                        TargetTree = dendropy.Tree.get(data = linkage_matrix2newick(linkage(Each_sample_distance, method = "ward"), labels = Extract_fragment_size.index), schema = "newick", taxon_namespace = Taxon_namespace, preserve_underscores = True)
                        TargetTree.is_rooted
                        NormalizedRobinsonFoulds = treecompare.symmetric_difference(TargetTree, ReferenceTree) / (2 * len(Leaf) - 4)
                        Distance_score.update({combs: Distance_score[combs] * 10 ** NormalizedRobinsonFoulds} if (combs in Distance_score.keys()) else {})
                Distance_score = dict(sorted(Distance_score.items(), key = lambda x:x[1], reverse = True))
                Dendrogram_output = int(np.min([Dendrogram_output, len(Distance_score.keys()), 100]))
                Dendrogram_output = [list(Distance_score.keys())[n] for n in range(Dendrogram_output)]
                if len(Dendrogram_output) > 0:
                    for no, combs in enumerate(Dendrogram_output):
                        Row_numbers = ", ".join([str(row) for row in sorted([Result.index.get_loc(comb) + 1 for comb in combs])]) 
                        Extract_fragment_size = Fragment_size_data.loc[list(combs), :]
                        Maximum_element_number = np.max([np.max(Extract_fragment_size.iloc[:, i].apply(lambda x:len(x) if type(x) is list else 1)) for i in range(Extract_fragment_size.shape[1])])
                        Expand_Extract_fragment_size = pd.DataFrame([[[sorted(li)[j] if len(li) >= j + 1 else int(Counter(li).most_common()[0][0]) for j in range(Maximum_element_number)] for li in Extract_fragment_size.iloc[:, i]] for i in range(Extract_fragment_size.shape[1])], dtype = object).T
                        Expand_Extract_fragment_size.columns = Extract_fragment_size.columns
                        Extract_fragment_size = pd.DataFrame([list(it.chain.from_iterable(Expand_Extract_fragment_size.iloc[:, i])) for i in range(Expand_Extract_fragment_size.shape[1])], index = Expand_Extract_fragment_size.columns)
                        Distance_matrix = pdist(Extract_fragment_size, metric='euclidean')
                        Dendrogram_data = linkage(Distance_matrix, method = "ward")
                        Sequence_name = Extract_fragment_size.index
                        Sequence_Row_d = {comb: Result.index.get_loc(comb) + 1 for comb in combs}
                        Sequence_Row_d = dict(sorted(Sequence_Row_d.items(), key = lambda x:x[1]))
                        Primer_sequence = "\n".join(['No.' + str(value) + '| Forward: ' + str(key[0]) + ', ' + 'Reverse: ' + str(key[1]) for key, value in Sequence_Row_d.items()])
                        Maximum_sequence_length = np.max([len(name) for name in Sequence_name])
                        if Maximum_sequence_length > 60:
                            Font_size = 6
                        elif Maximum_sequence_length > 40:
                            Font_size = 8
                        elif Maximum_sequence_length > 20:
                            Font_size = 10
                        else:
                            Font_size = 12
                        if np.logical_not(os.path.exists(output_folder + 'Result/' + TimeStamp + 'identify_primer_set/Dendrogram')):
                            os.mkdir(output_folder + 'Result/' + TimeStamp + 'identify_primer_set/Dendrogram')
                        fig = plt.figure(figsize = (12, 6,), dpi = 300)
                        ax = fig.add_subplot(1,1,1)
                        ax.set_title("Primer set [" + Row_numbers + "] in Summary.csv.")
                        ax.grid(axis = 'x', linestyle='dashed', color = '#b0c4de')
                        fig.text(ax.get_position().x1 - 0.85, ax.get_position().y1 - 0.75, Primer_sequence)
                        dendrogram(Dendrogram_data, labels = Sequence_name, orientation='left', leaf_font_size = Font_size, color_threshold = 0, above_threshold_color = '#191970')
                        plt.subplots_adjust(left = 0.05, right = 0.6, bottom = 0.3, top = 0.9)
                        plt.savefig(output_folder + 'Result/' + TimeStamp + 'identify_primer_set/Dendrogram/' + TimeStamp + "PREDICT_DENDROGRAM_" + str(no + 1) + ".png", dpi = 300)
                else:
                    if np.logical_not(os.path.exists(output_folder + 'Result/' + TimeStamp + 'identify_primer_set/Dendrogram')):
                        os.mkdir(output_folder + 'Result/' + TimeStamp + 'identify_primer_set/Dendrogram')
                    fig = plt.figure(figsize = (12, 6,), dpi = 300)
                    fig.text(0.5, 0.5, "No appropriate combination of primer sets.", fontsize = "xx-large", horizontalalignment = "center", verticalalignment = "center")
                    plt.savefig(output_folder + 'Result/' + TimeStamp + 'identify_primer_set/Dendrogram/' + TimeStamp + "No_candidate" + ".png", dpi = 300)
            elif Score_calculation == "Sequence":
                Dendrogram_output = int(np.min([Result.shape[0], Dendrogram_output, 100]))
                Dendrogram_data = {}
                if Dendrogram_output > 0:
                    for no in tqdm(range(Result.shape[0]), total = Result.shape[0], desc = "    Alignment and calculating distance matrix among amplicon sequences", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0):
                        Extract_Result = Result.iloc[no]
                        FASTA = "\n".join([">" + str(i) + "\n" + Extract_Result.loc[name] for i, name in enumerate(Sort_index)])
                        Name_dict = {str(i) : name for i, name in enumerate(Sort_index)}
                        with NamedTemporaryFile(mode = "wt") as tmp_inf:
                            tmp_inf.write(FASTA)
                            tmp_inf.seek(0)
                            if shutil.which("mafft") is None:
                                raise subprocess.CalledProcessError(-3, "mafft")
                            MAFFT = subprocess.run(args = ["mafft", tmp_inf.name], capture_output = True, check = True, text = True)
                            MAFFT_Result = MAFFT.stdout
                            with NamedTemporaryFile(mode = "wt") as tmp_outf:
                                tmp_outf.write(MAFFT_Result)
                                tmp_outf.seek(0)
                                Aligned_FASTA = AlignIO.read(open(tmp_outf.name, encoding = "utf-8"), "fasta")
                        Aligned_FASTA = MultipleSeqAlignment([aln.upper() for aln in Aligned_FASTA])
                        calculator = DistanceCalculator('identity')
                        Distance_matrix = calculator.get_distance(Aligned_FASTA)
                        Sequence_name = [Name_dict[name] for name in Distance_matrix.names]
                        Distance_matrix = np.array([li + [0 for j in range(np.max([len(i) for i in Distance_matrix.matrix]) - len(li))] for li in Distance_matrix.matrix]).T
                        Distance_matrix = np.array(list(it.chain.from_iterable([a[(i+1):len(a)] for i, a in enumerate(Distance_matrix)])))
                        Dendrogram = linkage(Distance_matrix, method = "average")
                        if ReferenceTree is not None:
                            TargetTree = dendropy.Tree.get(data = linkage_matrix2newick(Dendrogram, labels = Sequence_name), schema = "newick", taxon_namespace = Taxon_namespace, preserve_underscores = True)
                            TargetTree.is_rooted
                            NormalizedRobinsonFoulds = treecompare.symmetric_difference(TargetTree, ReferenceTree) / (2 * len(Leaf) - 4)
                            TreeTopologyScore = Extract_Result['Score'] / (10 ** (1 - NormalizedRobinsonFoulds))
                            Dendrogram_data.update({no: (Dendrogram, TreeTopologyScore,)})
                        else:
                            Dendrogram_data.update({no: (Dendrogram, 0,)})
                    if ReferenceTree is not None:
                        Result = Result.assign(TreeTopology_Adjusted_Score = [v[1] for v in Dendrogram_data.values()])
                        Dendrogram_data = dict(sorted(Dendrogram_data.items(), key = lambda x:x[1][1], reverse = False))
                        Result = Result.iloc[list(Dendrogram_data.keys())]
                    for no in tqdm(range(Dendrogram_output), total = Dendrogram_output, desc = "    Generating dendrogram", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0):
                        Primer_sequence = 'No.' + str(no + 1) + '| Forward: ' + str(Result.index[no][0]) + ', ' + 'Reverse: ' + str(Result.index[no][1])
                        Maximum_sequence_length = np.max([len(name) for name in Sequence_name])
                        if Maximum_sequence_length > 60:
                            Font_size = 6
                        elif Maximum_sequence_length > 40:
                            Font_size = 8
                        elif Maximum_sequence_length > 20:
                            Font_size = 10
                        else:
                            Font_size = 12
                        if np.logical_not(os.path.exists(output_folder + 'Result/' + TimeStamp + 'identify_primer_set/Dendrogram')):
                            os.mkdir(output_folder + 'Result/' + TimeStamp + 'identify_primer_set/Dendrogram')
                        fig = plt.figure(figsize = (12, 6,), dpi = 300)
                        ax = fig.add_subplot(1,1,1)
                        ax.set_title("Primer set No." + str(no + 1) + " in Summary.csv.")
                        ax.grid(axis = 'x', linestyle='dashed', color = '#b0c4de')
                        fig.text(ax.get_position().x1 - 0.85, ax.get_position().y1 - 0.75, Primer_sequence)
                        dendrogram(Dendrogram_data[list(Dendrogram_data.keys())[no]][0], labels = Sequence_name, orientation='left', leaf_font_size = Font_size, color_threshold = 0, above_threshold_color = '#191970')
                        plt.subplots_adjust(left = 0.05, right = 0.6, bottom = 0.3, top = 0.9)
                        plt.savefig(output_folder + 'Result/' + TimeStamp + 'identify_primer_set/Dendrogram/' + TimeStamp + "PREDICT_DENDROGRAM_" + str(no + 1) + ".png", dpi = 300)
                        plt.close()
                else:
                    if np.logical_not(os.path.exists(output_folder + 'Result/' + TimeStamp + 'identify_primer_set/Dendrogram')):
                        os.mkdir(output_folder + 'Result/' + TimeStamp + 'identify_primer_set/Dendrogram')
                    fig = plt.figure(figsize = (12, 6,), dpi = 300)
                    fig.text(0.5, 0.5, "No appropriate primer set.", fontsize = "xx-large", horizontalalignment = "center", verticalalignment = "center")
                    plt.savefig(output_folder + 'Result/' + TimeStamp + 'identify_primer_set/Dendrogram/' + TimeStamp + "No_candidate" + ".png", dpi = 300)
        except PermissionError:
            print("\nA temporary file was not able to create due to permission error.")
        except subprocess.CalledProcessError:
            print("\nGenerating dendrogram was omitted. \nMAFFT program is required to generate dendrogram and compare it with reference tree. \nPlease install MAFFT program and add the binary of MAFFT to your PATH if you need a dendrogram.")
        except pd.errors.EmptyDataError:
            print("\nNo primer set candidate.")
        except:
            print("\nAn unknown error occured. \nA dendrogram has not been generated. \nThe result file has been saved. It is now in the output folder.")
            raise
        finally:
            Result = Result.iloc[0:Result_output]
            if Size_matrix_path is not None:
                value = [input_file, ", ".join(list(seq_dict.keys())), "-", "-", "-", "-", "-", "-", "-", "-", Result_output, "-", "-", "-", Score_calculation, "Extracted sequences based on feature key in genbank format" if OnlyFeature else "Whole genome sequence", TreeDescription if ReferenceTree is not None else "Not provided"]
            else:
                value = [input_file, ", ".join(list(seq_dict.keys())), str(args.exclude_file) + "[" + str(Exclude_mode) + "]" if args.exclude_file is not None else "None", ", ".join(list(Exclude_sequences_list.keys())), Probe_size_range_description, allowance, cut_off_lower, cut_off_upper, interval_distance, Match_rate, Result_output, Search_mode, Window_size, Maximum_annealing_site_number, Score_calculation, "Extracted sequences based on feature key in genbank format" if OnlyFeature else "Whole genome sequence", TreeDescription if ReferenceTree is not None else "Not provided"]
            args = ["Input_file_name", "Target", "Exclude_file_name", "Exclude_target", "Primer_size_range_description", "allowance", "cut_off_lower", "cut_off_upper", "Interval_distance", "Match_rate", "Result_output", "Search_mode", "Window_size", "Maximum_annealing_site_number", "Score_calculation_mode", "Search_area", "Reference_tree"]
            Argument_input = pd.DataFrame(value, index = [args], columns = ["Arguments"])
            Argument_input.to_csv(output_folder+'Result/'+TimeStamp+'identify_primer_set'+'/'+TimeStamp+'Summary.csv', mode = 'a', sep=',')
            Result_Output = Result.copy(deep = True)
            if Result_Output.empty:
                Message = pd.DataFrame(["No primer set that can be used for identification was generated."])
                Message.to_csv(output_folder+'Result/'+TimeStamp+'identify_primer_set'+'/'+TimeStamp+'Summary.csv', mode = 'a', sep =',', header = None, index = None)
                print("\nNo primer set that can be used for identification was generated.")
                progress_bar.update(1)
                sys.exit()
            Result_Output.insert(0, 'No', [no + 1 for no in range(Result_Output.shape[0])])
            Result_Output.set_index('No', append = True, inplace = True)
            Result_Output.index = Result_Output.index.rename(["Forward","Reverse", "No"])
            Result_Output.to_csv(output_folder+'Result/'+TimeStamp+'identify_primer_set'+'/'+TimeStamp+'Summary.csv', mode = 'a', sep =',')
            del Result_Output
            progress_bar.update(1)
