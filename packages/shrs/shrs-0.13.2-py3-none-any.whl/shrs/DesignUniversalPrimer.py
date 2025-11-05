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

def DesignUniversalPrimer(args):
    """
    Universal primer design algorithm.

    Parameters
    ----------
    args: ArgumentParser, class containing appropriate property as below
        input_file: Input file path (required)\n
        output: Output directory path (Make a new directory if the directory does not exist)\n
        exclude_file: File path for exclusion sequence(s). Specify the sequence(s) file path of the bacteria if there are some bacteria that you would like to not amplify.\n
        primer_size: Primer size\n
        allowance: Mismatch allowance ratio. The value means that x base [primer size * allowance] mismatch is accepted. Note that setting this parameter too large might causes the increased run time and excessive memory consumption.\n
        range: Search range from primer size. If the value is 1 and primer size is 20, the primer sets that have 20 - 21 base length are explored.\n
        distance: The minimum distance between annealing sites that are hybridized with a primer\n
        process: The number of processes (sometimes the number of CPU core) used for analysis\n
        Exclude_mode: Choose the method for excluding the sequence(s) from 'fast' or 'standard' when you specify some sequence(s) file path of the bacteria that you would like to exclude using '-e' option\n
        Cut_off_lower: The lower limit of amplicon size\n
        Cut_off_upper: The upper limit of amplicon size\n
        Match_rate: The ratio of trials for which the primer candidate fulfilled all criteria when the allowance value is decreased. The higher the number is, the more specific the primer obtained is\n
        Result_output: The upper limit of result output\n
        Omit_similar_fragment_size_pair: Use this option if you want to omit primer sets that amplify similar fragment lengths\n
        Window_size: The duplicated candidates containing this window will be removed\n
        Maximum_annealing_site_number: The maximum acceptable value of the number of annealing site of the candidate of the primer in the input sequence\n
        Chunks: The chunk size for calculation. If the memory usage for calculation using the chunk size exceeds the GPU memory size, the processing unit for calculation will be switched to the CPU automatically\n
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
        Fragment_size_pattern_matrix: When you have a csv file of fragment size pattern matrix, you can reanalyse from the csv file. Specify the file path.\n

    Returns
    -------
    CSV_file: CSV contained primer sets and fragment size matrix amplified by each primer set

    """
    import sys
    import os
    import warnings
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    import re
    import copy
    from datetime import datetime as dt
    import math
    import statistics
    import csv
    from tqdm import tqdm
    from shrslib.basicfunc import init_worker, read_sequence_file, make_wobble, calculate_Tm_value, circularDNA, check_input_file
    from shrslib.scores import arr_length_in_arr, calculate_flexibility, fragment_size_distance
    from shrslib.explore import PCR_check, identify_microorganisms
    import numpy as np
    import pandas as pd
    from scipy.cluster.hierarchy import linkage, fcluster
    import itertools as it
    from functools import partial
    from multiprocessing import Pool, cpu_count, get_context
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
    output_folder = args.output
    if output_folder is not None:
        if not output_folder.endswith("/"):
            output_folder = output_folder+"/"
        if not os.path.exists(output_folder):
            os.mkdir(output_folder)
    else:
        absolute_path = re.sub("\\\\", "/", os.path.abspath(file_paths[0]))
        output_folder = absolute_path[:absolute_path.rfind("/") + 1]
    probe_size = args.primer_size
    allowance = args.allowance
    size_range = args.range
    interval_distance = args.distance
    if interval_distance < 1:
        interval_distance = int(1)
    cut_off_lower = args.Cut_off_lower
    cut_off_upper = args.Cut_off_upper
    Match_rate = args.Match_rate
    Result_output = args.Result_output
    Omit_similar_fragment_size_pair = args.Omit_similar_fragment_size_pair
    Window_size = args.Window_size
    withinMemory = args.withinMemory
    Allowance_adjustment = args.Without_allowance_adjustment
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
    for file_path in file_paths:
        read_data = read_sequence_file(file_path)
        seq_dict.update({key:circularDNA(sequence = read_data[0][key], overlap = int(overlap_region)) if circular_index[key] else circularDNA(sequence = read_data[0][key], overlap = int(0)) for key in read_data[0]})
        Total_length += read_data[1] * read_data[2]
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
    if args.Maximum_annealing_site_number is not None:
        Maximum_annealing_site_number = args.Maximum_annealing_site_number
    else:
        Maximum_annealing_site_number = int(Total_length)
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
    if args.Chunks is not None:
        if str(args.Chunks).isdecimal():
            homology_calculation_chunks = args.Chunks
        else:
            homology_calculation_chunks = str("Auto")
    else:
        homology_calculation_chunks = str("Auto")
    Size_matrix_path = args.Fragment_size_pattern_matrix
    TimeStamp = dt.now().strftime('%Y%m%d_%H%M%S')
    if len(seq_dict.keys()) <= 10:
        print("[Input sequences information]", "\n  ", "Input sequences:", input_seq, "/ Average length:", Average_length, "\n   ", "\n    ".join([name + " [circular]" if circular_index[name] else name for name in list(seq_dict.keys())]))
    else:
        print("[Input sequences information]", "\n  ", "Input sequences:", input_seq, "/ Average length:", Average_length, "\n   ", "\n    ".join([name + " [circular]" if circular_index[name] else name for name in list(seq_dict.keys())[0:3]]), "\n\n     ... \n\n   ", "\n    ".join([name + " [circular]" if circular_index[name] else name for name in list(seq_dict.keys())[(len(list(seq_dict.keys()))-3):len(list(seq_dict.keys()))]]))
    print("[Parameters]", "\n  ", "Primer size: {0}\n   Allowance: {1}\n   Cut_off_lower: {2}\n   Cut_off_upper: {3}\n   CPU usage: {4}\n   Homology_calculation_chunks: {5}\n   Maximum_annealing_site_number: {6}\n   Window_size: {7}\n   Exclude_sequences_list: {8}\n   Search_mode: {9}".format(Probe_size_range_description, allowance, cut_off_lower, cut_off_upper, CPU, homology_calculation_chunks, Maximum_annealing_site_number if args.Maximum_annealing_site_number is not None else "Unlimited.", Window_size, "\n                           ".join([name + " [circular]" if exclude_circular_index[name] else name for name in [str(es) for es in Exclude_sequences_list.keys()]]) if len(Exclude_sequences_list) != 0 else "empty", Search_mode))
    Sort_index = list(seq_dict.keys())
    seq_dict = dict(sorted(seq_dict.items(), key = lambda x:len(x[1])))
    Ref_template_name = list(seq_dict.keys())[0]
    Ref_template_seq = seq_dict.pop(Ref_template_name)
    seq_dict.update({Ref_template_name:Ref_template_seq})
    if size_range == 0:
        if len(Exclude_sequences_list) == 0:
            Total_procedure = input_seq + 11
        else:
            Total_procedure = input_seq + 12
    else:
        if len(Exclude_sequences_list) == 0:
            Total_procedure = (input_seq + 2) * (np.abs(size_range) + 1) + 9
        elif Exclude_mode == "standard":
            Total_procedure = (input_seq + 2) * (np.abs(size_range) + 1) + 10
        else:
            Total_procedure = (input_seq + 3) * (np.abs(size_range) + 1) + 9
    with tqdm(total = Total_procedure, desc = "  - Workflow status - ", leave = False, position = 0, bar_format = "{desc} Step no.{n:.0f} in {total:.0f}", smoothing = 0) as progress_bar:
        if Size_matrix_path is not None:
            if os.path.exists(Size_matrix_path):
                try:
                    sequence_summary = pd.read_csv(Size_matrix_path, sep = ",", header = 0, index_col = [0,1])
                    if set(sequence_summary.columns) == set(seq_dict.keys()):
                        sequence_summary = sequence_summary.map(eval) if Pandas_later_210 else sequence_summary.applymap(eval)
                        if np.logical_not(isinstance(sequence_summary.iloc[0,0][0], (int, float, np.int8, np.int16, np.int32, np.int64, np.uint8, np.uint16, np.uint32, np.uint64, np.float16, np.float32, np.float64, ))):
                            progress_bar.update(Total_procedure)
                            print("\033[1B" + "\r" + "Error: Unknown format. Check the fragment size pattern matrix file.")
                            raise TypeError
                        if not os.path.isdir(output_folder+"Result"):
                            os.mkdir(output_folder+"Result")
                        else:
                            pass
                        os.mkdir(output_folder+'Result/'+TimeStamp+'universal_primer_set')
                        sequence_summary = sequence_summary.reindex(columns = Sort_index)
                        progress_bar.update(Total_procedure - 2)
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
            sequence_summary = identify_microorganisms(input = seq_dict, probe_size = probe_size, size_range = size_range, allowance_rate = allowance, cut_off_lower = cut_off_lower, cut_off_upper = cut_off_upper, interval_distance = interval_distance, Match_rate = Match_rate, CPU = CPU, homology_calculation_chunks = homology_calculation_chunks, Maximum_annealing_site_number = Maximum_annealing_site_number, Window_size = Window_size, Exclude_sequences_list = Exclude_sequences_list, Search_mode = Search_mode, Search_interval = Search_interval, Exclude_mode = Exclude_mode, withinMemory = withinMemory, Allowance_adjustment = Allowance_adjustment, progress_bar = progress_bar)
            if not os.path.isdir(output_folder+"Result"):
                os.mkdir(output_folder+"Result")
            else:
                pass
            os.mkdir(output_folder+'Result/'+TimeStamp+'universal_primer_set')
            Position_data = sequence_summary[1]
            sequence_summary = sequence_summary[0].map(lambda x:[int(y) for y in x]) if Pandas_later_210 else sequence_summary[0].applymap(lambda x:[int(y) for y in x])
            sequence_summary = sequence_summary.reindex(columns = Sort_index)
            Position_data = Position_data.reindex(columns = Sort_index)
            sequence_summary.to_csv(output_folder+'Result/'+TimeStamp+'universal_primer_set'+'/'+TimeStamp+'Fragment_size_pattern_matrix.csv')
            Position_data.map(lambda x:[x[0].tolist(), x[1].tolist()]).to_csv(output_folder+'Result/'+TimeStamp+'universal_primer_set'+'/'+TimeStamp+'Fragment_start_position_matrix.csv') if Pandas_later_210 else Position_data.applymap(lambda x:[x[0].tolist(), x[1].tolist()]).to_csv(output_folder+'Result/'+TimeStamp+'universal_primer_set'+'/'+TimeStamp+'Fragment_start_position_matrix.csv')
        sequence_summary = sequence_summary.dropna(how='any')
        Result = sequence_summary.copy(deep = True)
        Result = Result.map(lambda x:x[0] if len(set(x)) == 1 else np.nan) if Pandas_later_210 else Result.applymap(lambda x:x[0] if len(set(x)) == 1 else np.nan)
        Result = Result.dropna(how='any')
        progress_bar.update(1)
        if np.logical_not(Result.empty):
            sequence_summary = sequence_summary.map(lambda x:x if len(set(x)) == 1 else np.nan) if Pandas_later_210 else sequence_summary.applymap(lambda x:x if len(set(x)) == 1 else np.nan)
            sequence_summary = sequence_summary.dropna(how='any')
            if Omit_similar_fragment_size_pair:
                try:
                    Z = linkage(Result, metric = "euclidean", method = "ward")
                    Classification = fcluster(Z, t = 50, criterion = "distance")
                    Fragment_number = [np.sum(arr_length_in_arr(sequence_summary.iloc[i])) for i in range(sequence_summary.shape[0])]
                    Score = [round(np.std(Result.iloc[i]) / np.mean(Result.iloc[i]), 2) for i in tqdm(range(Result.shape[0]), total = Result.shape[0], desc = "    Calculating score and sorting", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0)]
                    Result = Result.assign(Score = Score, Fragment_number = Fragment_number, Classification = Classification)
                    if Result.shape[0] > sum(Result['Fragment_number'] > input_seq):
                        Result = Result[Result['Fragment_number'] == input_seq]
                    Result = Result.sort_values('Score', ascending = True)
                    Result = Result.drop_duplicates(subset = 'Classification', keep = 'first')
                    Result = Result.drop('Classification', axis = 1)
                except:
                    Fragment_number = [np.sum(arr_length_in_arr(sequence_summary.iloc[i])) for i in range(sequence_summary.shape[0])]
                    Score = [round(np.std(Result.iloc[i]) / np.mean(Result.iloc[i]), 2) for i in tqdm(range(Result.shape[0]), total = Result.shape[0], desc = "    Calculating score and sorting", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0)]
                    Result = Result.assign(Score = Score, Fragment_number = Fragment_number)
                    if Result.shape[0] > sum(Result['Fragment_number'] > input_seq):
                        Result = Result[Result['Fragment_number'] == input_seq]
                    Result = Result.sort_values('Score', ascending = True)
            else:
                Fragment_number = [np.sum(arr_length_in_arr(sequence_summary.iloc[i])) for i in range(sequence_summary.shape[0])]
                Score = [round(np.std(Result.iloc[i]) / np.mean(Result.iloc[i]), 2) for i in tqdm(range(Result.shape[0]), total = Result.shape[0], desc = "    Calculating score and sorting", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0)]
                Result = Result.assign(Score = Score, Fragment_number = Fragment_number)
                if Result.shape[0] > sum(Result['Fragment_number'] > input_seq):
                    Result = Result[Result['Fragment_number'] == input_seq]
                Result = Result.sort_values('Score', ascending = True)
        else:
            Criteria = np.logical_not(sequence_summary.map(lambda x:str(x)).duplicated(subset  = sequence_summary.columns, keep = 'first')) if Pandas_later_210 else np.logical_not(sequence_summary.applymap(lambda x:str(x)).duplicated(subset  = sequence_summary.columns, keep = 'first'))
            sequence_summary = sequence_summary[Criteria]
            Fragment_size_data = sequence_summary.copy(deep = True)
            sequence_summary = sequence_summary.map(lambda x:sorted(list(set(x)))) if Pandas_later_210 else sequence_summary.applymap(lambda x:sorted(list(set(x))))
            Result = sequence_summary.copy(deep = True)
            for i in range(Result.shape[0]):
                Result.iloc[i] = np.array([str([(x, round(Fragment_size_data.iloc[i, j].count(x)/len(Fragment_size_data.iloc[i, j]), 2),) for x in sequence_summary.iloc[i, j]]) for j in range(len(sequence_summary.iloc[i]))], dtype = object)
            Fragment_number = [np.sum(arr_length_in_arr(sequence_summary.iloc[i])) for i in range(sequence_summary.shape[0])]
            Score = [fragment_size_distance(sequence_summary.iloc[i], sum = True, method = 'average') for i in tqdm(range(sequence_summary.shape[0]), total = sequence_summary.shape[0], desc = "    Calculating score and sorting", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0)]
            Result = Result.assign(Score = Score, Fragment_number = Fragment_number)
            Result = Result.sort_values(['Fragment_number', 'Score'], ascending = [True, True])
        Result = Result.drop('Fragment_number', axis = 1)
        Tm_value = [tuple(calculate_Tm_value(seq).values()) for seq in Result.index]
        Tm_value_difference = [round(np.abs(np.diff(tm))[0], 1) for tm in Tm_value]
        Result = Result.assign(Forward_Tm_value = [tm[0] for tm in Tm_value], Reverse_Tm_value = [tm[1] for tm in Tm_value], Tm_value_difference = Tm_value_difference)
        Result = Result.iloc[0:Result_output]
        Flexibility = [np.sum([calculate_flexibility(fwd), calculate_flexibility(rev)]) for fwd, rev in Result.index]
        Result = Result.assign(Flexibility = Flexibility)
        Result = Result.sort_values(['Score', 'Flexibility'], ascending = [True, True])
        if Size_matrix_path is not None:
            value = [input_file, ", ".join(list(seq_dict.keys())), "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"]            
        else:
            value = [input_file, ", ".join(list(seq_dict.keys())), str(args.exclude_file) + "[" + str(Exclude_mode) + "]" if args.exclude_file is not None else "None", ", ".join(list(Exclude_sequences_list.keys())), Probe_size_range_description, allowance, cut_off_lower, cut_off_upper, interval_distance, Match_rate, Search_mode, Window_size, Maximum_annealing_site_number if args.Maximum_annealing_site_number is not None else "Unlimited."]
        args = ["Input_file_name", "Target", "Exclude_file_name", "Exclude_target", "Primer_size_range_description", "allowance", "cut_off_lower", "cut_off_upper", "Interval_distance", "Match_rate", "Search_mode", "Window_size", "Maximum_annealing_site_number"]
        Argument_input = pd.DataFrame(value, index = [args], columns = ["Arguments"])
        Argument_input.to_csv(output_folder+'Result/'+TimeStamp+'universal_primer_set'+'/'+TimeStamp+'Summary.csv', mode = 'a', sep=',')
        Result_Output = Result.copy(deep = True)
        Result_Output.insert(0, 'No', [no + 1 for no in range(Result_Output.shape[0])])
        Result_Output.set_index('No', append = True, inplace = True)
        Result_Output.index = Result_Output.index.rename(["Forward","Reverse", "No"])
        Result_Output.to_csv(output_folder+'Result/'+TimeStamp+'universal_primer_set'+'/'+TimeStamp+'Summary.csv', mode = 'a', sep =',')
        if Result_Output.empty:
            progress_bar.update(1)
            Message = pd.DataFrame(["No universal primer set was generated."])
            Message.to_csv(output_folder+'Result/'+TimeStamp+'universal_primer_set'+'/'+TimeStamp+'Summary.csv', mode = 'a', sep =',', header = None, index = None)
            print("\n No universal primer set was generated.")
            sys.exit()
        progress_bar.update(1)