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

def DesignProbe(args):
    """
    Probe design algorithm for downstream application.

    Parameters
    ----------
    args: ArgumentParser, class containing appropriate property as below
        input_file: Input file path (required)\n
        exclude_file: File path for exclusion sequence(s). Specify the sequence(s) file path of the bacteria if there are some bacteria that you would like to not hybridize.\n
        probe_size: Probe size\n
        allowance: Mismatch allowance ratio. The value means that x base [probe size * allowance] mismatch is accepted. Note that setting this parameter too large might causes the increased run time and excessive memory consumption.\n
        range: Search range from probe size. If the value is 1 and probe size is 25, the probe sets that have 25-26 base length are explored.\n
        distance: The minimum distance between annealing sites that are hybridized with a probe\n
        output: Output directory path (Make a new directory if the directory does not exist)\n
        process: The number of processes (sometimes the number of CPU core) used for analysis\n
        Exclude_mode: Choose the method for excluding the sequence(s) from 'fast' or 'standard' when you specify some sequence(s) file path of the bacteria that you would like to exclude using '-e' option\n
        Result_output: The upper limit of result output\n
        Match_rate: The ratio of trials for which the probe candidate fulfilled all criteria when the allowance value is decreased. The higher the number is, the more specific the probe obtained is\n
        Chunks: The chunk size for calculation. If the memory usage for calculation using the chunk size exceeds the GPU memory size, the processing unit for calculation will be switched to the CPU automatically\n
        Maximum_annealing_site_number: The maximum acceptable value of the number of annealing site of the candidate of the probe in the input sequence\n
        Search_mode: There are four options: exhaustive/moderate/sparse/manual. If you choose the 'manual' option, type the ratio to probe length after 'manual'. (e.g. --Search_mode manual 0.2.) (default: moderate when the average input sequence length is >5000, and exhaustive when the average input sequence length is ≤5000)\n
        withinMemory: All analyses are performed within memory\n
        Without_allowance_adjustment: Use this option if you do not want to modify the allowance value for every homology calculation\n

    Returns
    -------
    CSV_file: CSV file contains probe sequences and position on input sequences which the probe hybridize.

    """
    import sys
    import os
    import warnings
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    import re
    import time
    from datetime import datetime as dt
    import math
    import csv
    from tqdm import tqdm
    from shrslib.basicfunc import read_sequence_file, calculate_Tm_value, circularDNA, check_input_file
    from shrslib.scores import calculate_flexibility
    from shrslib.explore import SHRsearch
    import numpy as np
    import pandas as pd
    import itertools as it
    from multiprocessing import cpu_count
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
    probe_size = args.probe_size
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
    Match_rate = args.Match_rate
    if args.Chunks is not None:
        if str(args.Chunks).isdecimal():
            homology_calculation_chunks = args.Chunks
        else:
            homology_calculation_chunks = str("Auto")
    else:
        homology_calculation_chunks = str("Auto")
    Maximum_annealing_site_number = args.Maximum_annealing_site_number
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
    if probe_size < 2 * size_range:
        warnings.warn("\nThe range searching a primer set should be below a half of probe size.\n")
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
    TimeStamp = dt.now().strftime('%Y%m%d_%H%M%S')
    if len(seq_dict.keys()) <= 10:
        InputInformation = [name + " [circular]" if circular_index[name] else name for name in Sort_index]
        print("[Target_microorganisms]", "\n ", "Input sequences:", input_seq, "/ Average length:", Average_length, "\n  ", "\n   ".join(InputInformation))
    else:
        PreInputInformation = [name + " [circular]" if circular_index[name] else name for name in Sort_index[0:3]]
        PostInputInformation = [name + " [circular]" if circular_index[name] else name for name in Sort_index[(len(Sort_index)-3):len(Sort_index)]]
        print("[Target_microorganisms]", "\n ", "Input sequences:", input_seq, "/ Average length:", Average_length, "\n  ", "\n   ".join(PreInputInformation), "\n\n    ... \n\n  ", "\n   ".join(PostInputInformation))
    print("[Parameters]", "\n  ", "Probe size: {0}\n   Allowance: {1}\n   Interval_distance: {2}\n   Match_rate: {3}\n   CPU usage: {4}\n   Homology_calculation_chunks: {5}\n   Maximum_annealing_site_number: {6}\n   Exclude_sequences_list: {7}\n   Search_mode: {8}".format(Probe_size_range_description, allowance, interval_distance, Match_rate, CPU, homology_calculation_chunks, Maximum_annealing_site_number, "\n                           ".join([name + " [circular]" if exclude_circular_index[name] else name for name in [str(es) for es in Exclude_sequences_list.keys()]]) if len(Exclude_sequences_list) != 0 else "empty", Search_mode))
    if size_range == 0:
        if len(Exclude_sequences_list) == 0:
            Total_procedure = input_seq + 6
        else:
            Total_procedure = input_seq + 7
    else:
        if len(Exclude_sequences_list) == 0:
            Total_procedure = (input_seq + 2) * (np.abs(size_range) + 1) + 4
        elif Exclude_mode == "standard":
            Total_procedure = (input_seq + 2) * (np.abs(size_range) + 1) + 5
        else:
            Total_procedure = (input_seq + 3) * (np.abs(size_range) + 1) + 4
    with tqdm(total = Total_procedure, desc = "  - Workflow status - ", leave = False, position = 0, bar_format = "{desc} Step no.{n:.0f} in {total:.0f}", smoothing = 0) as progress_bar:
        Result = SHRsearch(input = seq_dict, probe_size = probe_size, size_range = size_range, allowance_rate = allowance, Match_rate = Match_rate, interval_distance = interval_distance, CPU = CPU, homology_calculation_chunks = homology_calculation_chunks, Maximum_annealing_site_number = Maximum_annealing_site_number, Exclude_sequences_list = Exclude_sequences_list, Search_mode = Search_mode, Search_interval = Search_interval, Exclude_mode = Exclude_mode, withinMemory = withinMemory, Allowance_adjustment = Allowance_adjustment, progress_bar = progress_bar)
        if not os.path.isdir(output_folder+"Result"):
            os.mkdir(output_folder+"Result")
        else:
            pass
        Result = Result.iloc[0:Result_output]
        Result = Result.reindex(columns = Sort_index)
        Result = Result.map(lambda x:[a + 1 if a >= 0 else a - 1 for a in x]) if Pandas_later_210 else Result.applymap(lambda x:[a + 1 if a >= 0 else a - 1 for a in x])
        progress_bar.update(1)
        Flexibility_score = [calculate_flexibility(sequence, detailed = True) for sequence in tqdm(Result.index, desc = "    Calculating scores", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0)]
        progress_bar.update(1)
        Tm_value = [calculate_Tm_value(sequence) for sequence in tqdm(Result.index, desc = "    Calculating Tm values", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0)]
        Result = Result.assign(Flexibility = Flexibility_score, Tm_value = Tm_value)
        Result = Result.sort_values(['Flexibility', 'Tm_value'], ascending = [True, False])
        os.mkdir(output_folder+'Result/'+TimeStamp+'UniversalProbe')
        value = [input_file, ", ".join(list(seq_dict.keys())), str(args.exclude_file) + "[" + str(Exclude_mode) + "]" if args.exclude_file is not None else "None", ", ".join(list(Exclude_sequences_list.keys())), Probe_size_range_description, allowance, interval_distance, Match_rate, Result_output, Search_mode, Maximum_annealing_site_number, pd.NA]
        args = ["Input_file_name", "Target", "Exclude_file_name", "Exclude_target", "Probe_size_range_description", "allowance", "Interval_distance", "Match_rate", "Result_output", "Search_mode", "Maximum_annealing_site_number", "Probe sequence(s) generated and its annealing position(s) are below."]
        Argument_input = pd.DataFrame(value, index = [args], columns = ["Arguments"])
        Argument_input.to_csv(output_folder+'Result/'+TimeStamp+'UniversalProbe'+'/'+TimeStamp+'UniversalProbe.csv', mode = 'a', sep=',')
        Result.to_csv(output_folder+'Result/'+TimeStamp+'UniversalProbe'+'/'+TimeStamp+'UniversalProbe.csv', mode = 'a', sep = ",")
        progress_bar.update(1)