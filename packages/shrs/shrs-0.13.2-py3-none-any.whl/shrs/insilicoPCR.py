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

def insilicoPCR(args):
    """
    in silico PCR amplification algorithm.

    Parameters
    ----------
    args: ArgumentParser, class containing appropriate property as below
        input_file: Input file path (required)\n
        output: Output directory path (Make a new directory if the directory does not exist)\n
        size_limit: The upper limit of amplicon size\n
        process: The number of processes (sometimes the number of CPU core) used for analysis\n
        fasta: Output format. A FASTA file will be generated if you use this option.\n
        forward: The forward primer sequence used for amplification (required)\n
        reverse: The reverse primer sequence used for amplification (required)\n
        primerset_filepath: The filepath of the text file containing forward and reverse primer sequence (required if forward and reverse primer set with -fwd and -rev option are not provided)\n
        Single_file: Output format. One single FASTA-format file will be generated even if you input some separate FASTA files, when using this option with the '--fasta' option.\n
        Mismatch_allowance: The acceptable mismatch number\n
        Only_one_amplicon: Only one amplicon is outputted, even if multiple amplicons are obtained by PCR when you use this option.\n
        Position_index: The result has the information of the amplification position when this option is enabled.\n
        circularDNA: If there are some circular DNAs in the input sequences, use this option (default: n/a. It means all input sequences are linear DNA. When there are some circular DNA input sequences, type 'all', 'individually', 'n/a', or the file path of the text that specify which sequence is circularDNA, after the '--circularDNA' option. See Readme for more detailed information.)\n
            Text file example:\n
                Sequence_name1 circularDNA\n
                Sequence_name2 linearDNA\n
                Sequence_name3 linearDNA\n
                    ...\n
                Sequence_nameN circularDNA\n
        gene_annotation_search_range: The gene annotation search range in the GenBank-format file.\n
        Annotation: If the input sequence file is in GenBank format, the amplicon(s) is annotated automatically.\n
        LowQualitySequences: In in silico PCR analysis, all sequences containing the regions with a high proportion of 'N' bases will be omitted when you specify 'remove' option. This option helps to reduce a computational effort and calculation time. If you select the omitted sequences individually, specify 'individually'. When the 'ignore' option is selected, regions spanning 'N' bases will not be amplified. To use all input sequences for the in silico PCR template, specify the 'remain' option. (Default: 'remain')\n
        warning: Shows all warnings when you use this option.\n

    Returns
    -------
    FASTA/CSV: Amplified sequence(s) FASTA format file (or CSV file)

    """
    import sys
    import os
    import re
    import warnings
    from functools import partial
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    from tqdm import tqdm
    import math
    import itertools as it
    import numpy as np
    import pandas as pd
    from multiprocessing import Pool, get_context, cpu_count
    from shrslib.basicfunc import init_worker, nucleotide_sequence, read_sequence_file, circularDNA, check_input_file, file_existence
    from shrslib.explore import PCR_amplicon
    from shrslib.multiprocessfunc import trim_seq_worker_process_all, trim_seq_worker_process_all_df, trim_seq_worker_process_single, trim_seq_worker_process_single_df, PCR_amplicon_with_progress_bar
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
    else:
        sys.exit("Error: The input file/folder does not exist.")
    for file_path in file_paths:
        with open(file_path, "rt", encoding = "utf-8") as fin:
            Firstline = fin.readline()
            Others = fin.readlines()
            if np.logical_not(Firstline.startswith(">") | Firstline.startswith("LOCUS")):
                print("There are some file(s) of which are not FASTA or Genbank in folder inputed. Please remove the file(s).")
                sys.exit()
            elif (sum([x.replace(" ", "").startswith("LOCUS") for x in Others]) > 0) & (sum([x.replace(" ", "").startswith("ORIGIN") for x in Others]) > 1) & (sum([(x.replace(" ", "").startswith("//") & (len(x.replace(" ", "")) < 5)) for x in Others]) > 1):
                print("This program does not support the GenBank-format file containing multiple sequences. Please remove the file(s).")
                sys.exit()
    LowQualitySequences = args.LowQualitySequences
    Removal_sequences = []
    for file_path in file_paths:
        seqs = read_sequence_file(file_path)[0]
        for title, seq in seqs.items():
            if (LowQualitySequences == "remain") | (LowQualitySequences == "ignore"):
                pass
            elif (LowQualitySequences == "remove") | (LowQualitySequences == "individually"):
                N2 = sum([seq[i : i + 21].upper().count("N") > 1 for i in range(0, len(seq), 21)])
                N5 = sum([seq[i : i + 21].upper().count("N") > 4 for i in range(0, len(seq), 21)])
                N15 = sum([seq[i : i + 21].upper().count("N") > 14 for i in range(0, len(seq), 21)])
                if (N2 > 9) | (N5 > 4) | (N15 > 0):
                    if LowQualitySequences == "remove":
                        Removal_sequences += [title]
                    elif LowQualitySequences == "individually":
                        User_input = ''
                        while True:
                            User_input = input("'{}' has many 'N' base in the sequence. Do you remove this sequence? (Y/n): ".format(title))
                            if (User_input.lower() == "y") | (User_input.lower() == "yes") | (User_input.lower() == "n") | (User_input.lower() == "no"):
                                break
                        if (User_input.lower() == "y") | (User_input.lower() == "yes"):
                            Removal_sequences += [title]
                else:
                    pass
            else:
                print("Please specify 'remove', 'individually', 'ignore' or 'remain' after --LowQualitySequences option.")
                sys.exit()
    output_dataframe = args.fasta
    if args.output is not None:
        output_folder = args.output
        filename, extension = os.path.splitext(output_folder)
        Output_filename = ""
        if ((extension == ".csv") & (output_dataframe)) | (((extension == ".fasta") | (extension == ".fna") | (extension == ".fas") | (extension == ".gb") | (extension == ".gbk")) & np.logical_not(output_dataframe)):
            Output_filename = filename + extension
            output_folder = os.path.dirname(output_folder)
        elif not output_folder.endswith("/"):
            output_folder = output_folder+"/"
    else:
        output_folder = ""
    single_file = args.Single_file
    if ((args.forward != "") & (args.reverse != "")):
        FWDs = [args.forward]
        REVs = [args.reverse]
    elif (args.primerset_filepath != ""):
        Primerset_filepath = args.primerset_filepath
        if os.path.exists(Primerset_filepath):
            with open(Primerset_filepath, "rt", encoding = "utf-8") as fin:
                FWDs = []; REVs = []
                line = fin.readline()
                LINE_NUMBER = 1
                while line:
                    line = re.sub(r"\r\n|\n", "", line)
                    line = re.sub(r" +|\t+", ",", line)
                    line = re.sub(r",+", ",", line)
                    Input_Primer_Set = line.split(",")
                    Input_Primer_Set_Check = [len(re.sub(r"[ATGCBDHKMRSVWYNXatgcbdhkmrsvwynx]", "", x)) == 0 for x in Input_Primer_Set]
                    if np.sum(Input_Primer_Set_Check) == 2:
                        F, R = [Input_Primer_Set[i] for i in range(len(Input_Primer_Set_Check)) if Input_Primer_Set_Check[i]]
                        FWDs.append(F); REVs.append(R)
                    else:
                        warnings.warn("Primer set file contains some unrecognized character(s) in the primer sequence. The primer set was ignored. Please check your file. The delimiter between forward primer and reverse primer must be comma, tab or whitespace. Line number: {}".format(LINE_NUMBER))
                    line = fin.readline()
                    LINE_NUMBER += 1
        else:
            print("Error: No such file: '{}'".format(Primerset_filepath))
            sys.exit()            
    else:
        print("Error: The forward and reverse primer sequence should be provided. \nPlease specify primer sequence using -fwd and -rev option or the filepath of the text file containing primer set information using -f option.")
        sys.exit()
    amplicon_size_limit = args.size_limit
    allowance = args.Mismatch_allowance
    Remain_all_amplicons = args.Only_one_amplicon
    Position_index = args.Position_index
    if args.Annotation:
        Feature = True
        Position_index = True
    else:
        Feature = False
    CPU = args.process
    if CPU < 1:
        if cpu_count() <= 3:
            CPU = int(1)
        elif cpu_count() <= 8:
            CPU = int(math.floor(cpu_count() / 4))
        elif cpu_count() <= 12:
            CPU = int(math.floor(cpu_count() / 3))
        elif cpu_count() <= 24:
            CPU = int(math.floor(cpu_count() / 2))
        else:
            CPU = int(16)
    else:
        if CPU > cpu_count():
            CPU = int(math.floor(cpu_count()))
    if args.circularDNA is not None:
        overlap_region = amplicon_size_limit
        if len(args.circularDNA) == 0:
            circular_index = check_input_file(file_paths, circular = "all")
        elif args.circularDNA[0].lower() == "all":
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
    distance = args.gene_annotation_search_range
    Warning_ignore = args.warning
    if Warning_ignore:
        warnings.simplefilter('ignore')
    Seq_no = []
    for file_path in file_paths:
        with open(file_path, "rt", encoding = "utf-8") as fin:
            read_FILE = fin.read()
            if read_FILE.startswith(">"):
                Seq_no += [read_FILE.count(">")]
            else:
                Seq_no += [1]
    annotation = {}
    if ((len(FWDs) > 1) & (len(REVs) > 1) & (len(FWDs) == len(REVs)) & (len(Seq_no) == 1) & (np.max(Seq_no) == 1) & (len(file_paths) == 1)):
        if output_dataframe:
            Amplicon_Sequences = dict()
            with tqdm(total = len(FWDs), desc = "Dataframe of amplified sequences making", leave = False, unit = "tasks", unit_scale = True, smoothing = 0) as pbar:
                def Progressbar_update_dataframe_single(Result):
                    pbar.update(Result[1])
                if Feature:
                    seq_dict = read_sequence_file(input = file_paths[0], format = "genbank", Feature = True)[0]
                    annotation.update({key:seq_dict[key][1] for key in seq_dict if (key not in Removal_sequences)})
                    seq_dict = {key:seq_dict[key][0] for key in seq_dict if (key not in Removal_sequences)}
                    if (LowQualitySequences == "ignore"):
                        seq_dict = {key:nucleotide_sequence(seq_dict[key].replace("N", "X")) for key in seq_dict}
                else:
                    seq_dict = read_sequence_file(file_paths[0])[0]
                    seq_dict = {key:seq_dict[key] for key in seq_dict if (key not in Removal_sequences)}
                    if (LowQualitySequences == "ignore"):
                        seq_dict = {key:nucleotide_sequence(seq_dict[key].replace("N", "X")) for key in seq_dict}
                Sequence_length_limit = np.min([amplicon_size_limit, seq_dict[list(seq_dict.keys())[0]].sequence_length])
                seq_dict = {key:circularDNA(sequence = seq_dict[key], overlap = int(np.min([overlap_region, seq_dict[key].sequence_length]))) if circular_index[key] else circularDNA(sequence = seq_dict[key], overlap = int(0)) for key in seq_dict}
                if (CPU > 1):
                    with get_context("spawn").Pool(processes = CPU, initializer = init_worker) as pl:
                        try:
                            if Position_index:
                                Amplicon = [pl.apply_async(PCR_amplicon_with_progress_bar, kwds = {"forward": fwd, "reverse": rev, "template": seq_dict[list(seq_dict.keys())[0]], "Single_amplicon": False, "Sequence_Only": False, "amplicon_size_limit": Sequence_length_limit, "allowance": allowance, "Warning_ignore": Warning_ignore}, callback = Progressbar_update_dataframe_single) for fwd, rev in zip(FWDs, REVs)]
                            else:
                                Amplicon = [pl.apply_async(PCR_amplicon_with_progress_bar, kwds = {"forward": fwd, "reverse": rev, "template": seq_dict[list(seq_dict.keys())[0]], "Single_amplicon": False, "Sequence_Only": True, "amplicon_size_limit": Sequence_length_limit, "allowance": allowance, "Warning_ignore": Warning_ignore}, callback = Progressbar_update_dataframe_single) for fwd, rev in zip(FWDs, REVs)]
                        except KeyboardInterrupt:
                            pl.terminate()
                            pl.join()
                            pl.close()
                            print("\n\n --- Keyboard Interrupt ---")
                            sys.exit("")
                        Amplicon = [amp.get()[0] for amp in Amplicon]
                else:
                    if Position_index:
                        Amplicon = [(PCR_amplicon(forward = fwd, reverse = rev, template = seq_dict[list(seq_dict.keys())[0]], Single_amplicon = False, Sequence_Only = False, amplicon_size_limit = Sequence_length_limit, allowance = allowance, Warning_ignore = Warning_ignore), pbar.update(1), ) for fwd, rev in zip(FWDs, REVs)]
                    else:
                        Amplicon = [(PCR_amplicon(forward = fwd, reverse = rev, template = seq_dict[list(seq_dict.keys())[0]], Single_amplicon = False, Sequence_Only = True, amplicon_size_limit = Sequence_length_limit, allowance = allowance, Warning_ignore = Warning_ignore), pbar.update(1), ) for fwd, rev in zip(FWDs, REVs)]
                    Amplicon = [amp[0] for amp in Amplicon]
                Amplicon = [[] if seq is None else seq for seq in Amplicon]
                Amplicon = {"Amplicon_of_" + str(list(seq_dict.keys())[0]) + "_by_primer_no" + str(i + 1):amp for i, amp in zip(range(len(FWDs)), Amplicon)}
                Amplicon_Sequences.update(Amplicon)
                max_col = max([len(i) for i in Amplicon_Sequences.values()])
                Amplicon_Sequences = {name:[seqs[i] if len(seqs) > i else np.nan for i in range(max_col)] for name, seqs in Amplicon_Sequences.items()}
                Result = pd.DataFrame(Amplicon_Sequences).T
                Result.columns = ["Amplicon_sequence_"+ str(i + 1) for i in range(max_col)]
                if Position_index & Feature & (len(annotation) > 0):
                    Amplicon_annotation = {}
                    Gene = [[position for position in re.sub(r"[^0-9]+", " ", target).split(" ") if len(position) != 0] + [annotation[list(seq_dict.keys())[0]][target]] for target in annotation[list(seq_dict.keys())[0]].keys() if (list(seq_dict.keys())[0] in annotation.keys())]
                    for i in range(len(Result.index)):                        
                        Amplicon_annotation.update({Result.index[i]:{"Annotation_of_amplicon_sequence_" + str(j + 1): ["{0}..{1}: {2}".format(g[0], g[1], g[2]) for g in Gene if (((int(g[0]) - int(distance)) <= np.abs(Result.iloc[i, j][0])) & ((int(g[1]) + int(distance)) >= np.abs(Result.iloc[i, j][0]))) | (((int(g[0]) - int(distance)) <= np.abs(Result.iloc[i, j][1])) & ((int(g[1]) + int(distance)) >= np.abs(Result.iloc[i, j][1]))) | (((int(g[0]) - int(distance)) >= np.abs(Result.iloc[i, j][0])) & ((int(g[1]) + int(distance)) <= np.abs(Result.iloc[i, j][1])))] if pd.notna(Result.iloc[i, j]) else np.nan for j in range(Result.shape[1])}})
                    Amplicon_annotation = pd.DataFrame(Amplicon_annotation).T
                    Result = pd.concat([Result, Amplicon_annotation],axis = 1)
                if pbar.total - pbar.n > 0:
                    pbar.update(pbar.total - pbar.n)
            if output_folder != "":
                if not os.path.exists(output_folder):
                    os.mkdir(output_folder)
                if (Output_filename == ""):
                    if os.path.isfile(input_file):
                        if (input_file[(input_file.rfind("/") + 1):].rfind(".") == -1):
                            Output_filename = output_folder + input_file[(input_file.rfind("/") + 1):] + "_iPCR_result" + ".csv"
                        else:
                            Output_filename = output_folder + input_file[(input_file.rfind("/") + 1):input_file.rfind(".")] + "_iPCR_result" + ".csv"
                    else:
                        Output_filename = output_folder + "iPCR_result" + ".csv"
                if os.path.exists(Output_filename):
                    Output_filename = file_existence(Output_filename)
                Result.to_csv(Output_filename)
            else:
                if os.path.isfile(input_file):
                    if (input_file[(input_file.rfind("/") + 1):].rfind(".") == -1):
                        Output_filename = input_file + "_iPCR_result" + ".csv"
                    else:
                        Output_filename = input_file[0:input_file.rfind("."):] + "_iPCR_result" + ".csv"
                    if os.path.exists(Output_filename):
                        Output_filename = file_existence(Output_filename)
                    Result.to_csv(Output_filename)
                else:
                    if input_file.endswith("/"):
                        Output_filename = input_file + "iPCR_result"  + ".csv"
                    else:
                        Output_filename = input_file + "/" + "iPCR_result" + ".csv"
                    if os.path.exists(Output_filename):
                        Output_filename = file_existence(Output_filename)
                    Result.to_csv(Output_filename)
        else:
            trimmed_seqs = []
            with tqdm(total = len(FWDs), desc = "Writing PCR result", leave = False, unit = "tasks", unit_scale = True, smoothing = 0) as pbar:
                def Progressbar_update_fasta_single(Result):
                    pbar.update(Result[1])
                if Feature:
                    seq_dict = read_sequence_file(input = file_paths[0], format = "genbank", Feature = True)[0]
                    annotation.update({key:seq_dict[key][1] for key in seq_dict if (key not in Removal_sequences)})
                    seq_dict = {key:seq_dict[key][0] for key in seq_dict if (key not in Removal_sequences)}
                    if (LowQualitySequences == "ignore"):
                        seq_dict = {key:nucleotide_sequence(seq_dict[key].replace("N", "X")) for key in seq_dict}
                else:
                    seq_dict = read_sequence_file(file_paths[0])[0]
                    seq_dict = {key:seq_dict[key] for key in seq_dict if (key not in Removal_sequences)}
                    if (LowQualitySequences == "ignore"):
                        seq_dict = {key:nucleotide_sequence(seq_dict[key].replace("N", "X")) for key in seq_dict}
                Sequence_length_limit = np.min([amplicon_size_limit, seq_dict[list(seq_dict.keys())[0]].sequence_length])
                seq_dict = {key:circularDNA(sequence = seq_dict[key], overlap = int(np.min([overlap_region, seq_dict[key].sequence_length]))) if circular_index[key] else circularDNA(sequence = seq_dict[key], overlap = int(0)) for key in seq_dict}
                if (CPU > 1):
                    with get_context("spawn").Pool(processes = CPU, initializer = init_worker) as pl:
                        try:
                            if Position_index:
                                trimmed_seq = [(file_paths[0], list(seq_dict.keys())[0] + "_by_Primer_no" + str(i + 1), pl.apply_async(PCR_amplicon_with_progress_bar, kwds = {"forward": fwd, "reverse": rev, "template": seq_dict[list(seq_dict.keys())[0]], "Single_amplicon": False, "Sequence_Only": False, "amplicon_size_limit": Sequence_length_limit, "allowance": allowance, "Warning_ignore": Warning_ignore}, callback = Progressbar_update_fasta_single), ) for i, fwd, rev in zip(range(len(FWDs)), FWDs, REVs)]
                            else:
                                trimmed_seq = [(file_paths[0], list(seq_dict.keys())[0] + "_by_Primer_no" + str(i + 1), pl.apply_async(PCR_amplicon_with_progress_bar, kwds = {"forward": fwd, "reverse": rev, "template": seq_dict[list(seq_dict.keys())[0]], "Single_amplicon": False, "Sequence_Only": True, "amplicon_size_limit": Sequence_length_limit, "allowance": allowance, "Warning_ignore": Warning_ignore}, callback = Progressbar_update_fasta_single), ) for i, fwd, rev in zip(range(len(FWDs)), FWDs, REVs)]
                        except KeyboardInterrupt:
                            pl.terminate()
                            pl.join()
                            pl.close()
                            print("\n\n --- Keyboard Interrupt ---")
                            sys.exit("")
                        trimmed_seq = [(ts[0], ts[1], ts[2].get()[0], ) for ts in trimmed_seq]
                else:
                    if Position_index:
                        trimmed_seq = [(file_paths[0], list(seq_dict.keys())[0] + "_by_Primer_no" + str(i + 1), PCR_amplicon(forward = fwd, reverse = rev, template = seq_dict[list(seq_dict.keys())[0]], Single_amplicon = False, Sequence_Only = False, amplicon_size_limit = Sequence_length_limit, allowance = allowance, Warning_ignore = Warning_ignore), pbar.update(1), ) for i, fwd, rev in zip(range(len(FWDs)), FWDs, REVs)]
                    else:
                        trimmed_seq = [(file_paths[0], list(seq_dict.keys())[0] + "_by_Primer_no" + str(i + 1), PCR_amplicon(forward = fwd, reverse = rev, template = seq_dict[list(seq_dict.keys())[0]], Single_amplicon = False, Sequence_Only = True, amplicon_size_limit = Sequence_length_limit, allowance = allowance, Warning_ignore = Warning_ignore), pbar.update(1), ) for i, fwd, rev in zip(range(len(FWDs)), FWDs, REVs)]
                trimmed_seq = [ts for ts in trimmed_seq if ts[2] is not None]
                if Position_index & Feature & (len(annotation) > 0): 
                    annotated_trimmed_seq = []
                    Gene = [[position for position in re.sub(r"[^0-9]+", " ", target).split(" ") if len(position) != 0] + [annotation[list(seq_dict.keys())[0]][target]] for target in annotation[list(seq_dict.keys())[0]].keys() if (list(seq_dict.keys())[0] in annotation.keys())] 
                    for ts in trimmed_seq:                         
                        Amplicon_annotation = {str(amp[0]) + str(amp[1]): [(g[0], g[1], g[2], ) for g in Gene if (((int(g[0]) - int(distance)) <= np.abs(amp[0])) & ((int(g[1]) + int(distance)) >= np.abs(amp[0]))) | (((int(g[0]) - int(distance)) <= np.abs(amp[1])) & ((int(g[1]) + int(distance)) >= np.abs(amp[1]))) | (((int(g[0]) - int(distance)) >= np.abs(amp[0])) & ((int(g[1]) + int(distance)) <= np.abs(amp[1])))] for amp in ts[2]} 
                        annotated_trimmed_seq.append((ts[0], ts[1], [tuple(list(amp) + [Amplicon_annotation[str(amp[0]) + str(amp[1])]]) for amp in ts[2]], )) 
                    trimmed_seq = ([[(ts[0], ts[1]+"_amplicon_"+str(j+1)+"_("+str(seq[0])+" -> "+str(seq[1])+")", seq[2], seq[3], ) for j, seq in enumerate(ts[2])] if len(ts[2]) > 0 else ts for ts in annotated_trimmed_seq]) if len(annotated_trimmed_seq) > 0 else annotated_trimmed_seq 
                    del annotated_trimmed_seq
                elif Position_index:
                    trimmed_seq = ([[(ts[0], ts[1]+"_amplicon_"+str(j+1)+"_("+str(seq[0])+" -> "+str(seq[1])+")", seq[2], [], ) for j, seq in enumerate(ts[2])] if len(ts[2]) > 0 else ts for ts in trimmed_seq]) if len(trimmed_seq) > 0 else trimmed_seq
                else:
                    trimmed_seq = ([[(ts[0], ts[1]+"_amplicon_"+str(j+1), seq, [], ) for j, seq in enumerate(ts[2])] if len(ts[2]) > 0 else ts for ts in trimmed_seq]) if len(trimmed_seq) > 0 else trimmed_seq
                trimmed_seq = list(it.chain.from_iterable(trimmed_seq))
                trimmed_seqs += trimmed_seq
                if len(trimmed_seqs) == 0:
                    print("No amplicon was obtained.")
                    sys.exit()
                if output_folder != "":
                    if not os.path.exists(output_folder):
                        os.mkdir(output_folder)
                    if single_file:
                        if (Output_filename == ""):
                            if os.path.isfile(input_file):
                                if (input_file[(input_file.rfind("/") + 1):].rfind(".") == -1):
                                    Output_filename = output_folder + input_file[(input_file.rfind("/") + 1):] + "_iPCR_result" + ".fasta"
                                else:
                                    Output_filename = output_folder + input_file[(input_file.rfind("/") + 1):input_file.rfind(".")] + "_iPCR_result" + ".fasta"
                            else:
                                Output_filename = output_folder + "iPCR_result" + ".fasta"
                        if os.path.exists(Output_filename):
                            Output_filename = file_existence(Output_filename)
                        for trimmed_seq in trimmed_seqs:
                            with open(Output_filename, "a", encoding = "utf-8") as fout:
                                fout.write(">"+trimmed_seq[1]+"\n"+trimmed_seq[2]+"\n")
                    elif Feature:
                        OUTDIRTRUE_FILENAMEFALSE_FLAG = False
                        if (Output_filename != ""):
                            Original_Output_filename = Output_filename[:Output_filename.rfind(".")]
                        for i, trimmed_seq in enumerate(trimmed_seqs):
                            if ((Output_filename == "") | (OUTDIRTRUE_FILENAMEFALSE_FLAG)):
                                if os.path.isfile(input_file):
                                    if (input_file[(input_file.rfind("/") + 1):].rfind(".") == -1):
                                        Output_filename = output_folder + input_file[(input_file.rfind("/") + 1):] + trimmed_seq[1][trimmed_seq[1].find("_by_Primer_no"):re.search("_amplicon_[0-9]+", trimmed_seq[1]).span()[1]] + ".gb"
                                    else:
                                        Output_filename = output_folder + input_file[(input_file.rfind("/") + 1):input_file.rfind(".")] + trimmed_seq[1][trimmed_seq[1].find("_by_Primer_no"):re.search("_amplicon_[0-9]+", trimmed_seq[1]).span()[1]] + ".gb"
                                else:
                                    Output_filename = output_folder + "iPCR_result" + trimmed_seq[1][trimmed_seq[1].find("_by_Primer_no"):re.search("_amplicon_[0-9]+", trimmed_seq[1]).span()[1]] + ".gb"
                                OUTDIRTRUE_FILENAMEFALSE_FLAG = True
                            else:
                                Output_filename = Original_Output_filename + trimmed_seq[1][trimmed_seq[1].find("_by_Primer_no"):re.search("_amplicon_[0-9]+", trimmed_seq[1]).span()[1]] + ".gb"
                            if os.path.exists(Output_filename):
                                Output_filename = file_existence(Output_filename)
                            with open(Output_filename, "wt", encoding = "utf-8") as fout:
                                seq =  str(trimmed_seq[2])
                                Gene = trimmed_seq[3]
                                split_sequence_list = [seq[i * 10:(i+1) * 10:] for i in range(len(seq) // 10 + 1)]
                                Sequence = "".join([" ".join([str(i * 60 + 1).rjust(9)] + split_sequence_list[i * 6 : (i + 1) * 6:] + ["\n"]) for i in range(sum([len(split_sequence) == 10 for split_sequence in split_sequence_list]) // 6 + 1)])
                                LOCUS = "LOCUS".ljust(12) + str(trimmed_seq[1])
                                DEFINITION = "DEFINITION".ljust(12) + str(trimmed_seq[1])
                                TITLE = "TITLE".ljust(12) + str(trimmed_seq[1])
                                FEATURES = "FEATURES             Location/Qualifiers"
                                annotation_template1 = "     CDS             {0}..{1}" + "\n" + "".ljust(21) + '/product="{2}"'
                                annotation_template2 = "     CDS             complement({1}..{0})" + "\n" + "".ljust(21) + '/product="{2}"'
                                ANNOTATION = "\n".join([annotation_template1.format(g[0], g[1], g[2]) if int(g[0]) > 0 else annotation_template2.format(g[0], g[1], g[2]) for g in Gene])
                                SEQUENCE = "ORIGIN\n\n" + Sequence + "//"
                                OUTPUT_DATA = LOCUS + "\n" + DEFINITION + "\n" + TITLE + "\n" + FEATURES + "\n" + ANNOTATION + "\n" + SEQUENCE
                                fout.write(OUTPUT_DATA)
                    else:
                        OUTDIRTRUE_FILENAMEFALSE_FLAG = False
                        if (Output_filename != ""):
                            Original_Output_filename = Output_filename[:Output_filename.rfind(".")]
                        for i, trimmed_seq in enumerate(trimmed_seqs):
                            if ((Output_filename == "") | (OUTDIRTRUE_FILENAMEFALSE_FLAG)):
                                if os.path.isfile(input_file):
                                    if (input_file[(input_file.rfind("/") + 1):].rfind(".") == -1):
                                        Output_filename = output_folder + input_file[(input_file.rfind("/") + 1):] + trimmed_seq[1][trimmed_seq[1].find("_by_Primer_no"):re.search("_amplicon_[0-9]+", trimmed_seq[1]).span()[1]] + ".fasta"
                                    else:
                                        Output_filename = output_folder + input_file[(input_file.rfind("/") + 1):input_file.rfind(".")] + trimmed_seq[1][trimmed_seq[1].find("_by_Primer_no"):re.search("_amplicon_[0-9]+", trimmed_seq[1]).span()[1]] + ".fasta"
                                else:
                                    Output_filename = output_folder + "iPCR_result" + trimmed_seq[1][trimmed_seq[1].find("_by_Primer_no"):re.search("_amplicon_[0-9]+", trimmed_seq[1]).span()[1]] + ".fasta"
                                OUTDIRTRUE_FILENAMEFALSE_FLAG = True
                            else:
                                Output_filename = Original_Output_filename + trimmed_seq[1][trimmed_seq[1].find("_by_Primer_no"):re.search("_amplicon_[0-9]+", trimmed_seq[1]).span()[1]] + ".fasta"
                            if os.path.exists(Output_filename):
                                Output_filename = file_existence(Output_filename)
                            with open(Output_filename, "a", encoding = "utf-8") as fout:
                                fout.write(">"+trimmed_seq[1]+"\n"+trimmed_seq[2]+"\n")
                else:
                    if single_file:
                        Output_filename = os.path.splitext(file_paths[0])[0] + "_iPCR_result" + ".fasta"
                        if os.path.exists(Output_filename):
                            Output_filename = file_existence(Output_filename)
                        for trimmed_seq in trimmed_seqs:
                            with open(Output_filename, "a", encoding = "utf-8") as fout:
                                fout.write(">"+trimmed_seq[1]+"\n"+trimmed_seq[2]+"\n")
                    elif Feature:
                        for i, trimmed_seq in enumerate(trimmed_seqs):
                            Output_filename = os.path.splitext(file_paths[0])[0] + "_iPCR_result" + trimmed_seq[1][trimmed_seq[1].find("_by_Primer_no"):re.search("_amplicon_[0-9]+", trimmed_seq[1]).span()[1]] + ".gb"
                            if os.path.exists(Output_filename):
                                Output_filename = file_existence(Output_filename)
                            with open(Output_filename, "wt", encoding = "utf-8") as fout:
                                seq =  str(trimmed_seq[2])
                                Gene = trimmed_seq[3]
                                split_sequence_list = [seq[i * 10:(i+1) * 10:] for i in range(len(seq) // 10 + 1)]
                                Sequence = "".join([" ".join([str(i * 60 + 1).rjust(9)] + split_sequence_list[i * 6 : (i + 1) * 6:] + ["\n"]) for i in range(sum([len(split_sequence) == 10 for split_sequence in split_sequence_list]) // 6 + 1)])
                                LOCUS = "LOCUS".ljust(12) + str(trimmed_seq[1])
                                DEFINITION = "DEFINITION".ljust(12) + str(trimmed_seq[1])
                                TITLE = "TITLE".ljust(12) + str(trimmed_seq[1])
                                FEATURES = "FEATURES             Location/Qualifiers"
                                annotation_template1 = "     CDS             {0}..{1}" + "\n" + "".ljust(21) + '/product="{2}"'
                                annotation_template2 = "     CDS             complement({1}..{0})" + "\n" + "".ljust(21) + '/product="{2}"'
                                ANNOTATION = "\n".join([annotation_template1.format(g[0], g[1], g[2]) if int(g[0]) > 0 else annotation_template2.format(g[0], g[1], g[2]) for g in Gene])
                                SEQUENCE = "ORIGIN\n\n" + Sequence + "//"
                                OUTPUT_DATA = LOCUS + "\n" + DEFINITION + "\n" + TITLE + "\n" + FEATURES + "\n" + ANNOTATION + "\n" + SEQUENCE
                                fout.write(OUTPUT_DATA)
                    else:
                        for i, trimmed_seq in enumerate(trimmed_seqs):
                            Output_filename = os.path.splitext(file_paths[0])[0] + "_iPCR_result" + trimmed_seq[1][trimmed_seq[1].find("_by_Primer_no"):re.search("_amplicon_[0-9]+", trimmed_seq[1]).span()[1]] + ".fasta"
                            if os.path.exists(Output_filename):
                                Output_filename = file_existence(Output_filename)
                            with open(Output_filename, "a", encoding = "utf-8") as fout:
                                fout.write(">"+trimmed_seq[1]+"\n"+trimmed_seq[2]+"\n")
                if pbar.total - pbar.n > 0:
                    pbar.update(pbar.total - pbar.n)
    elif (len(FWDs) == len(REVs)):
        Primer_set_number = 1
        OUTDIRTRUE_FILENAMEFALSE_FLAG = False
        with tqdm(total = len(FWDs), leave = False, position = 0, smoothing = 0, bar_format = "{desc}") as progress_bar:
            for fwd, rev in zip(FWDs, REVs):
                progress_bar.set_description_str(f" In progress: Primer set number {Primer_set_number:.0f} in {len(FWDs):.0f}")
                if output_dataframe:
                    Amplicon_Sequences = dict()
                    if Remain_all_amplicons:
                        if np.mean(Seq_no) > len(Seq_no):
                            with tqdm(total = np.sum(Seq_no), desc = "Dataframe of amplified sequences making", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0) as pbar:
                                def Progressbar_update_alpha(Result):
                                    pbar.update(Result[1])
                                for file_path in file_paths:
                                    if Feature:
                                        seq_dict = read_sequence_file(input = file_path, format = "genbank", Feature = True)[0]
                                        annotation.update({key:seq_dict[key][1] for key in seq_dict if (key not in Removal_sequences)})
                                        seq_dict = {key:seq_dict[key][0] for key in seq_dict if (key not in Removal_sequences)}
                                        if (LowQualitySequences == "ignore"):
                                            seq_dict = {key:nucleotide_sequence(seq_dict[key].replace("N", "X")) for key in seq_dict}
                                    else:
                                        seq_dict = read_sequence_file(file_path)[0]
                                        seq_dict = {key:seq_dict[key] for key in seq_dict if (key not in Removal_sequences)}
                                        if (LowQualitySequences == "ignore"):
                                            seq_dict = {key:nucleotide_sequence(seq_dict[key].replace("N", "X")) for key in seq_dict}
                                    Sequence_length_list = [np.min([amplicon_size_limit, seq_dict[key].sequence_length]) for key in seq_dict]
                                    seq_dict = {key:circularDNA(sequence = seq_dict[key], overlap = int(np.min([overlap_region, seq_dict[key].sequence_length]))) if circular_index[key] else circularDNA(sequence = seq_dict[key], overlap = int(0)) for key in seq_dict}
                                    if (CPU > 1):
                                        with get_context("spawn").Pool(processes = min([CPU, len(seq_dict)]), initializer = init_worker) as pl:
                                            try:
                                                if Position_index:
                                                    Amplicon = [pl.apply_async(PCR_amplicon_with_progress_bar, kwds = {"forward": fwd, "reverse": rev, "template": seq, "Single_amplicon": False, "Sequence_Only": False, "amplicon_size_limit": limit, "allowance": allowance, "Warning_ignore": Warning_ignore}, callback = Progressbar_update_alpha) for limit, seq in zip(Sequence_length_list, seq_dict.values())]
                                                else:
                                                    Amplicon = [pl.apply_async(PCR_amplicon_with_progress_bar, kwds = {"forward": fwd, "reverse": rev, "template": seq, "Single_amplicon": False, "Sequence_Only": True, "amplicon_size_limit": limit, "allowance": allowance, "Warning_ignore": Warning_ignore}, callback = Progressbar_update_alpha) for limit, seq in zip(Sequence_length_list, seq_dict.values())]
                                            except KeyboardInterrupt:
                                                pl.terminate()
                                                pl.join()
                                                pl.close()
                                                print("\n\n --- Keyboard Interrupt ---")
                                                sys.exit("")
                                            Amplicon = [amp.get()[0] for amp in Amplicon]
                                    else:
                                        if Position_index:
                                            Amplicon = [(PCR_amplicon(forward = fwd, reverse = rev, template = seq, Single_amplicon = False, Sequence_Only = False, amplicon_size_limit = limit, allowance = allowance, Warning_ignore = Warning_ignore), pbar.update(1), ) for limit, seq in zip(Sequence_length_list, seq_dict.values())]
                                        else:
                                            Amplicon = [(PCR_amplicon(forward = fwd, reverse = rev, template = seq, Single_amplicon = False, Sequence_Only = True, amplicon_size_limit = limit, allowance = allowance, Warning_ignore = Warning_ignore), pbar.update(1), ) for limit, seq in zip(Sequence_length_list, seq_dict.values())]
                                        Amplicon = [amp[0] for amp in Amplicon]
                                    Amplicon = [[] if seq is None else seq for seq in Amplicon]
                                    Amplicon = {name:amp for name, amp in zip(seq_dict.keys(), Amplicon)}
                                    Amplicon_Sequences.update(Amplicon)
                                max_col = max([len(i) for i in Amplicon_Sequences.values()])
                                Amplicon_Sequences = {name:[seqs[i] if len(seqs) > i else np.nan for i in range(max_col)] for name, seqs in Amplicon_Sequences.items()}
                                Result = pd.DataFrame(Amplicon_Sequences).T
                                Result.columns = ["Amplicon_sequence_"+ str(i + 1) for i in range(max_col)]
                                if pbar.total - pbar.n > 0:
                                    pbar.update(pbar.total - pbar.n)
                        else:
                            Result = dict()
                            if Feature:
                                for file_path in file_paths:
                                    seq_dict = read_sequence_file(input = file_path, format = "genbank", Feature = True)[0]
                                    annotation.update({key:seq_dict[key][1] for key in seq_dict if (key not in Removal_sequences)})
                                    del seq_dict
                            with get_context("spawn").Pool(processes = np.min([CPU, len(file_paths)]), initializer = init_worker) as pl:
                                try:
                                    if Position_index:
                                        Amplicons = list(tqdm(pl.imap(partial(trim_seq_worker_process_all_df, fwd = fwd, rev = rev, Sequence_Only = False, amplicon_size_limit = amplicon_size_limit, allowance = allowance, Warning_ignore = Warning_ignore, overlap_region = overlap_region, circular_index = circular_index, Removal_sequences = Removal_sequences, LowQualitySequences = LowQualitySequences), file_paths), total = len(file_paths), desc = "Dataframe of amplified sequences making", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0))
                                    else:
                                        Amplicons = list(tqdm(pl.imap(partial(trim_seq_worker_process_all_df, fwd = fwd, rev = rev, Sequence_Only = True, amplicon_size_limit = amplicon_size_limit, allowance = allowance, Warning_ignore = Warning_ignore, overlap_region = overlap_region, circular_index = circular_index, Removal_sequences = Removal_sequences, LowQualitySequences = LowQualitySequences), file_paths), total = len(file_paths), desc = "Dataframe of amplified sequences making", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0))
                                except KeyboardInterrupt:
                                    pl.terminate()
                                    pl.join()
                                    pl.close()
                                    print("\n\n --- Keyboard Interrupt ---")
                                    sys.exit("")
                            [Result.update(amplicon) for amplicon in Amplicons]
                            Result = pd.DataFrame(Result).T
                        if Position_index & Feature & (len(annotation) > 0):
                            Amplicon_annotation = {}
                            for i in range(len(Result.index)):
                                Gene = [[position for position in re.sub(r"[^0-9]+", " ", target).split(" ") if len(position) != 0] + [annotation[Result.index[i]][target]] for target in annotation[Result.index[i]].keys() if (Result.index[i] in annotation.keys())]
                                Amplicon_annotation.update({Result.index[i]:{"Annotation_of_amplicon_sequence_" + str(j + 1): ["{0}..{1}: {2}".format(g[0], g[1], g[2]) for g in Gene if (((int(g[0]) - int(distance)) <= np.abs(Result.iloc[i, j][0])) & ((int(g[1]) + int(distance)) >= np.abs(Result.iloc[i, j][0]))) | (((int(g[0]) - int(distance)) <= np.abs(Result.iloc[i, j][1])) & ((int(g[1]) + int(distance)) >= np.abs(Result.iloc[i, j][1]))) | (((int(g[0]) - int(distance)) >= np.abs(Result.iloc[i, j][0])) & ((int(g[1]) + int(distance)) <= np.abs(Result.iloc[i, j][1])))] if pd.notna(Result.iloc[i, j]) else np.nan for j in range(Result.shape[1])}})
                            Amplicon_annotation = pd.DataFrame(Amplicon_annotation).T
                            Result = pd.concat([Result, Amplicon_annotation],axis = 1)
                    else:
                        if np.mean(Seq_no) > len(Seq_no):
                            with tqdm(total = np.sum(Seq_no), desc = "Dataframe of amplified sequences making", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0) as pbar:
                                def Progressbar_update_beta(Result):
                                    pbar.update(Result[1])
                                for file_path in file_paths:
                                    if Feature:
                                        seq_dict = read_sequence_file(input = file_path, format = "genbank", Feature = True)[0]
                                        annotation.update({key:seq_dict[key][1] for key in seq_dict if (key not in Removal_sequences)})
                                        seq_dict = {key:seq_dict[key][0] for key in seq_dict if (key not in Removal_sequences)}
                                        if (LowQualitySequences == "ignore"):
                                            seq_dict = {key:nucleotide_sequence(seq_dict[key].replace("N", "X")) for key in seq_dict}
                                    else:
                                        seq_dict = read_sequence_file(file_path)[0]
                                        seq_dict = {key:seq_dict[key] for key in seq_dict if (key not in Removal_sequences)}
                                        if (LowQualitySequences == "ignore"):
                                            seq_dict = {key:nucleotide_sequence(seq_dict[key].replace("N", "X")) for key in seq_dict}
                                    Sequence_length_list = [np.min([amplicon_size_limit, seq_dict[key].sequence_length]) for key in seq_dict]
                                    seq_dict = {key:circularDNA(sequence = seq_dict[key], overlap = int(np.min([overlap_region, seq_dict[key].sequence_length]))) if circular_index[key] else circularDNA(sequence = seq_dict[key], overlap = int(0)) for key in seq_dict}
                                    if (CPU > 1):
                                        with get_context("spawn").Pool(processes = min([CPU, len(seq_dict)]), initializer = init_worker) as pl:
                                            try:
                                                if Position_index:
                                                    Amplicon = [pl.apply_async(PCR_amplicon_with_progress_bar, kwds = {"forward": fwd, "reverse": rev, "template": seq, "Single_amplicon": True, "Sequence_Only": False, "amplicon_size_limit": limit, "allowance": allowance, "Warning_ignore": Warning_ignore}, callback = Progressbar_update_beta) for limit, seq in zip(Sequence_length_list, seq_dict.values())]
                                                else: 
                                                    Amplicon = [pl.apply_async(PCR_amplicon_with_progress_bar, kwds = {"forward": fwd, "reverse": rev, "template": seq, "Single_amplicon": True, "Sequence_Only": True, "amplicon_size_limit": limit, "allowance": allowance, "Warning_ignore": Warning_ignore}, callback = Progressbar_update_beta) for limit, seq in zip(Sequence_length_list, seq_dict.values())]
                                            except KeyboardInterrupt:
                                                pl.terminate()
                                                pl.join()
                                                pl.close()
                                                print("\n\n --- Keyboard Interrupt ---")
                                                sys.exit("")
                                            Amplicon = [amp.get()[0] for amp in Amplicon]
                                    else:
                                        if Position_index:
                                            Amplicon = [(PCR_amplicon(forward = fwd, reverse = rev, template = seq, Single_amplicon = True, Sequence_Only = False, amplicon_size_limit = limit, allowance = allowance, Warning_ignore = Warning_ignore), pbar.update(1), ) for limit, seq in zip(Sequence_length_list, seq_dict.values())]
                                        else:
                                            Amplicon = [(PCR_amplicon(forward = fwd, reverse = rev, template = seq, Single_amplicon = True, Sequence_Only = True, amplicon_size_limit = limit, allowance = allowance, Warning_ignore = Warning_ignore), pbar.update(1), ) for limit, seq in zip(Sequence_length_list, seq_dict.values())]
                                        Amplicon = [amp[0] for amp in Amplicon]
                                    Amplicon = ['' if seq is None else seq for seq in Amplicon]
                                    if Position_index:
                                        len_seqs = [len(seq[2]) if len(seq) > 1 else 0 for seq in Amplicon]
                                    else:
                                        len_seqs = [len(seq) for seq in Amplicon]
                                    Amplicon = list(zip(Amplicon, len_seqs))
                                    Amplicon = {name:amp for name, amp in zip(seq_dict.keys(), Amplicon)}
                                    Amplicon_Sequences.update(Amplicon)
                                Result = pd.DataFrame(Amplicon_Sequences).T
                                Result.columns = ["Amplicon_sequence", "Length"]
                                if pbar.total - pbar.n > 0:
                                    pbar.update(pbar.total - pbar.n)
                        else:
                            Result = dict()
                            if Feature:
                                for file_path in file_paths:
                                    seq_dict = read_sequence_file(input = file_path, format = "genbank", Feature = True)[0]
                                    annotation.update({key:seq_dict[key][1] for key in seq_dict if (key not in Removal_sequences)})
                                    del seq_dict
                            with get_context("spawn").Pool(processes = np.min([CPU, len(file_paths)]), initializer = init_worker) as pl:
                                try:
                                    if Position_index:
                                        Amplicons = list(tqdm(pl.imap(partial(trim_seq_worker_process_single_df, fwd = fwd, rev = rev, Sequence_Only = False, amplicon_size_limit = amplicon_size_limit, allowance = allowance, Warning_ignore = Warning_ignore, overlap_region = overlap_region, circular_index = circular_index, Removal_sequences = Removal_sequences, LowQualitySequences = LowQualitySequences), file_paths), total = len(file_paths), desc = "Dataframe of amplified sequences making", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0))
                                    else:
                                        Amplicons = list(tqdm(pl.imap(partial(trim_seq_worker_process_single_df, fwd = fwd, rev = rev, Sequence_Only = True, amplicon_size_limit = amplicon_size_limit, allowance = allowance, Warning_ignore = Warning_ignore, overlap_region = overlap_region, circular_index = circular_index, Removal_sequences = Removal_sequences, LowQualitySequences = LowQualitySequences), file_paths), total = len(file_paths), desc = "Dataframe of amplified sequences making", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0))
                                except KeyboardInterrupt:
                                    pl.terminate()
                                    pl.join()
                                    pl.close()
                                    print("\n\n --- Keyboard Interrupt ---")
                                    sys.exit("")
                            [Result.update(amplicon) for amplicon in Amplicons]
                            Result = pd.DataFrame(Result).T
                            Result.columns = ["Amplicon_sequence", "Length"]
                        if Position_index & Feature & (len(annotation) > 0):
                            Amplicon_annotation = {}
                            for i in range(len(Result.index)):
                                Gene = [[position for position in re.sub(r"[^0-9]+", " ", target).split(" ") if len(position) != 0] + [annotation[Result.index[i]][target]] for target in annotation[Result.index[i]].keys() if (Result.index[i] in annotation.keys())]
                                Amplicon_annotation.update({Result.index[i]: ["{0}..{1}: {2}".format(g[0], g[1], g[2]) for g in Gene if (((int(g[0]) - int(distance)) <= np.abs(Result.loc[Result.index[i], 'Amplicon_sequence'][0])) & ((int(g[1]) + int(distance)) >= np.abs(Result.loc[Result.index[i], 'Amplicon_sequence'][0]))) | (((int(g[0]) - int(distance)) <= np.abs(Result.loc[Result.index[i], 'Amplicon_sequence'][1])) & ((int(g[1]) + int(distance)) >= np.abs(Result.loc[Result.index[i], 'Amplicon_sequence'][1]))) | (((int(g[0]) - int(distance)) >= np.abs(Result.loc[Result.index[i], 'Amplicon_sequence'][0])) & ((int(g[1]) + int(distance)) <= np.abs(Result.loc[Result.index[i], 'Amplicon_sequence'][1])))] if pd.notna(Result.loc[Result.index[i], 'Amplicon_sequence']) else np.nan})
                            Amplicon_annotation = pd.Series(Amplicon_annotation)
                            Result = Result.assign(Annotation = Amplicon_annotation)
                    if output_folder != "":
                        if not os.path.exists(output_folder):
                            os.mkdir(output_folder)
                        if (Output_filename == "") | (OUTDIRTRUE_FILENAMEFALSE_FLAG):
                            Output_filename = output_folder + "iPCR_result" + "_by_PrimerSetNo" + str(Primer_set_number) + ".csv"
                            OUTDIRTRUE_FILENAMEFALSE_FLAG = True
                        if os.path.exists(Output_filename):
                            Output_filename = file_existence(Output_filename)
                        Result.to_csv(Output_filename)
                    else:
                        if os.path.isfile(input_file):
                            if (input_file[(input_file.rfind("/") + 1):].rfind(".") == -1):
                                Output_filename = input_file + "_iPCR_result" + "_by_PrimerSetNo" + str(Primer_set_number) + ".csv"
                                if os.path.exists(Output_filename):
                                    Output_filename = file_existence(Output_filename)
                                Result.to_csv(Output_filename)
                            else:
                                Output_filename = input_file[0:input_file.rfind("."):] + "_iPCR_result" + "_by_PrimerSetNo" + str(Primer_set_number) + ".csv"
                                if os.path.exists(Output_filename):
                                    Output_filename = file_existence(Output_filename)
                                Result.to_csv(Output_filename)
                        else:
                            if input_file.endswith("/"):
                                Output_filename = input_file + "iPCR_result" + "_by_PrimerSetNo" + str(Primer_set_number) + ".csv"
                                if os.path.exists(Output_filename):
                                    Output_filename = file_existence(Output_filename)
                                Result.to_csv(Output_filename)
                            else:
                                Output_filename = input_file + "/" + "iPCR_result" + "_by_PrimerSetNo" + str(Primer_set_number) + ".csv"
                                if os.path.exists(Output_filename):
                                    Output_filename = file_existence(Output_filename)
                                Result.to_csv(Output_filename)
                else:
                    trimmed_seqs = []
                    if Remain_all_amplicons:
                        if np.mean(Seq_no) > len(Seq_no):
                            with tqdm(total = np.sum(Seq_no), desc = "Writing PCR result", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0) as pbar:
                                def Progressbar_update_gamma(Result):
                                    pbar.update(Result[1])
                                for file_path in file_paths:
                                    if Feature:
                                        seq_dict = read_sequence_file(input = file_path, format = "genbank", Feature = True)[0]
                                        annotation.update({key:seq_dict[key][1] for key in seq_dict if (key not in Removal_sequences)})
                                        seq_dict = {key:seq_dict[key][0] for key in seq_dict if (key not in Removal_sequences)}
                                        if (LowQualitySequences == "ignore"):
                                            seq_dict = {key:nucleotide_sequence(seq_dict[key].replace("N", "X")) for key in seq_dict}
                                    else:
                                        seq_dict = read_sequence_file(file_path)[0]
                                        seq_dict = {key:seq_dict[key] for key in seq_dict if (key not in Removal_sequences)}
                                        if (LowQualitySequences == "ignore"):
                                            seq_dict = {key:nucleotide_sequence(seq_dict[key].replace("N", "X")) for key in seq_dict}
                                    Sequence_length_list = [np.min([amplicon_size_limit, seq_dict[key].sequence_length]) for key in seq_dict]
                                    seq_dict = {key:circularDNA(sequence = seq_dict[key], overlap = int(np.min([overlap_region, seq_dict[key].sequence_length]))) if circular_index[key] else circularDNA(sequence = seq_dict[key], overlap = int(0)) for key in seq_dict}
                                    if (CPU > 1):
                                        with get_context("spawn").Pool(processes = np.min([CPU, len(seq_dict)]), initializer = init_worker) as pl:
                                            try:
                                                if Position_index:
                                                    trimmed_seq = [(file_path, name, pl.apply_async(PCR_amplicon_with_progress_bar, kwds = {"forward": fwd, "reverse": rev, "template": seq_dict[name], "Single_amplicon": False, "Sequence_Only": False, "amplicon_size_limit": limit, "allowance": allowance, "Warning_ignore": Warning_ignore}, callback = Progressbar_update_gamma), ) for limit, name in zip(Sequence_length_list, seq_dict)]
                                                else:
                                                    trimmed_seq = [(file_path, name, pl.apply_async(PCR_amplicon_with_progress_bar, kwds = {"forward": fwd, "reverse": rev, "template": seq_dict[name], "Single_amplicon": False, "Sequence_Only": True, "amplicon_size_limit": limit, "allowance": allowance, "Warning_ignore": Warning_ignore}, callback = Progressbar_update_gamma), ) for limit, name in zip(Sequence_length_list, seq_dict)]
                                            except KeyboardInterrupt:
                                                pl.terminate()
                                                pl.join()
                                                pl.close()
                                                print("\n\n --- Keyboard Interrupt ---")
                                                sys.exit("")
                                            trimmed_seq = [(ts[0], ts[1], ts[2].get()[0], ) for ts in trimmed_seq]
                                    else:
                                        if Position_index:
                                            trimmed_seq = [(file_path, name, PCR_amplicon(forward = fwd, reverse = rev, template = seq_dict[name], Single_amplicon = False, Sequence_Only = False, amplicon_size_limit = limit, allowance = allowance, Warning_ignore = Warning_ignore), pbar.update(1), ) for limit, name in zip(Sequence_length_list, seq_dict)]
                                        else:
                                            trimmed_seq = [(file_path, name, PCR_amplicon(forward = fwd, reverse = rev, template = seq_dict[name], Single_amplicon = False, Sequence_Only = True, amplicon_size_limit = limit, allowance = allowance, Warning_ignore = Warning_ignore), pbar.update(1), ) for limit, name in zip(Sequence_length_list, seq_dict)]
                                    trimmed_seq = [ts for ts in trimmed_seq if ts[2] is not None]
                                    if Position_index & Feature & (len(annotation) > 0): 
                                        annotated_trimmed_seq = []
                                        for ts in trimmed_seq: 
                                            Gene = [[position for position in re.sub(r"[^0-9]+", " ", target).split(" ") if len(position) != 0] + [annotation[ts[1]][target]] for target in annotation[ts[1]].keys() if (ts[1] in annotation.keys())] 
                                            Amplicon_annotation = {str(amp[0]) + str(amp[1]): [(g[0], g[1], g[2], ) for g in Gene if (((int(g[0]) - int(distance)) <= np.abs(amp[0])) & ((int(g[1]) + int(distance)) >= np.abs(amp[0]))) | (((int(g[0]) - int(distance)) <= np.abs(amp[1])) & ((int(g[1]) + int(distance)) >= np.abs(amp[1]))) | (((int(g[0]) - int(distance)) >= np.abs(amp[0])) & ((int(g[1]) + int(distance)) <= np.abs(amp[1])))] for amp in ts[2]} 
                                            annotated_trimmed_seq.append((ts[0], ts[1], [tuple(list(amp) + [Amplicon_annotation[str(amp[0]) + str(amp[1])]]) for amp in ts[2]], )) 
                                        trimmed_seq = ([[(ts[0], ts[1]+"_amplicon_"+str(j+1)+"_("+str(seq[0])+" -> "+str(seq[1])+")", seq[2], seq[3], ) for j, seq in enumerate(ts[2])] if len(ts[2]) > 0 else ts for ts in annotated_trimmed_seq]) if len(annotated_trimmed_seq) > 0 else annotated_trimmed_seq 
                                        del annotated_trimmed_seq
                                    elif Position_index:
                                        trimmed_seq = ([[(ts[0], ts[1]+"_amplicon_"+str(j+1)+"_("+str(seq[0])+" -> "+str(seq[1])+")", seq[2], [], ) for j, seq in enumerate(ts[2])] if len(ts[2]) > 0 else ts for ts in trimmed_seq]) if len(trimmed_seq) > 0 else trimmed_seq
                                    else:
                                        trimmed_seq = ([[(ts[0], ts[1]+"_amplicon_"+str(j+1), seq, [], ) for j, seq in enumerate(ts[2])] if len(ts[2]) > 0 else ts for ts in trimmed_seq]) if len(trimmed_seq) > 0 else trimmed_seq
                                    trimmed_seq = list(it.chain.from_iterable(trimmed_seq))
                                    trimmed_seqs += trimmed_seq
                                if pbar.total - pbar.n > 0:
                                    pbar.update(pbar.total - pbar.n)
                        else:
                            if Feature: 
                                for file_path in file_paths: 
                                    seq_dict = read_sequence_file(input = file_path, format = "genbank", Feature = True)[0] 
                                    annotation.update({key:seq_dict[key][1] for key in seq_dict if (key not in Removal_sequences)}) 
                                    del seq_dict 
                            with get_context("spawn").Pool(processes = np.min([CPU, len(file_paths)]), initializer = init_worker) as pl:
                                try:
                                    if Position_index & Feature & (len(annotation) > 0):
                                        trimmed_seq = list(tqdm(pl.imap(partial(trim_seq_worker_process_all, fwd = fwd, rev = rev, Sequence_Only = False, amplicon_size_limit = amplicon_size_limit, allowance = allowance, Warning_ignore = Warning_ignore, overlap_region = overlap_region, circular_index = circular_index, Removal_sequences = Removal_sequences, LowQualitySequences = LowQualitySequences, Feature = Feature, annotation = annotation, distance = distance), file_paths), total = len(file_paths), desc = "Writing PCR result", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0))
                                    elif Position_index:
                                        trimmed_seq = list(tqdm(pl.imap(partial(trim_seq_worker_process_all, fwd = fwd, rev = rev, Sequence_Only = False, amplicon_size_limit = amplicon_size_limit, allowance = allowance, Warning_ignore = Warning_ignore, overlap_region = overlap_region, circular_index = circular_index, Removal_sequences = Removal_sequences, LowQualitySequences = LowQualitySequences), file_paths), total = len(file_paths), desc = "Writing PCR result", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0))
                                    else:
                                        trimmed_seq = list(tqdm(pl.imap(partial(trim_seq_worker_process_all, fwd = fwd, rev = rev, Sequence_Only = True, amplicon_size_limit = amplicon_size_limit, allowance = allowance, Warning_ignore = Warning_ignore, overlap_region = overlap_region, circular_index = circular_index, Removal_sequences = Removal_sequences, LowQualitySequences = LowQualitySequences), file_paths), total = len(file_paths), desc = "Writing PCR result", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0))
                                except KeyboardInterrupt:
                                    pl.terminate()
                                    pl.join()
                                    pl.close()
                                    print("\n\n --- Keyboard Interrupt ---")
                                    sys.exit("")
                            trimmed_seqs = list(it.chain.from_iterable(trimmed_seq))
                    else:
                        if np.mean(Seq_no) > len(Seq_no):
                            with tqdm(total = np.sum(Seq_no), desc = "Writing PCR result", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0) as pbar:
                                def Progressbar_update_delta(Result):
                                    pbar.update(Result[1])
                                for file_path in file_paths:
                                    if Feature:
                                        seq_dict = read_sequence_file(input = file_path, format = "genbank", Feature = True)[0]
                                        annotation.update({key:seq_dict[key][1] for key in seq_dict if (key not in Removal_sequences)})
                                        seq_dict = {key:seq_dict[key][0] for key in seq_dict if (key not in Removal_sequences)}
                                        if (LowQualitySequences == "ignore"):
                                            seq_dict = {key:nucleotide_sequence(seq_dict[key].replace("N", "X")) for key in seq_dict}
                                    else:
                                        seq_dict = read_sequence_file(file_path)[0]
                                        seq_dict = {key:seq_dict[key] for key in seq_dict if (key not in Removal_sequences)}
                                        if (LowQualitySequences == "ignore"):
                                            seq_dict = {key:nucleotide_sequence(seq_dict[key].replace("N", "X")) for key in seq_dict}
                                    Sequence_length_list = [np.min([amplicon_size_limit, seq_dict[key].sequence_length]) for key in seq_dict]
                                    seq_dict = {key:circularDNA(sequence = seq_dict[key], overlap = int(np.min([overlap_region, seq_dict[key].sequence_length]))) if circular_index[key] else circularDNA(sequence = seq_dict[key], overlap = int(0)) for key in seq_dict}
                                    if (CPU > 1):
                                        with get_context("spawn").Pool(processes = np.min([CPU, len(seq_dict)]), initializer = init_worker) as pl:
                                            try:
                                                if Position_index:
                                                    trimmed_seq = [(file_path, name, pl.apply_async(PCR_amplicon_with_progress_bar, kwds = {"forward": fwd, "reverse": rev, "template": seq_dict[name], "Single_amplicon": True, "Sequence_Only": False, "amplicon_size_limit": limit, "allowance": allowance, "Warning_ignore": Warning_ignore}, callback = Progressbar_update_delta), ) for limit, name in zip(Sequence_length_list, seq_dict)]
                                                else:
                                                    trimmed_seq = [(file_path, name, pl.apply_async(PCR_amplicon_with_progress_bar, kwds = {"forward": fwd, "reverse": rev, "template": seq_dict[name], "Single_amplicon": True, "Sequence_Only": True, "amplicon_size_limit": limit, "allowance": allowance, "Warning_ignore": Warning_ignore}, callback = Progressbar_update_delta), ) for limit, name in zip(Sequence_length_list, seq_dict)]
                                            except KeyboardInterrupt:
                                                pl.terminate()
                                                pl.join()
                                                pl.close()
                                                print("\n\n --- Keyboard Interrupt ---")
                                                sys.exit("")
                                            trimmed_seq = [(ts[0], ts[1], ts[2].get()[0], ) for ts in trimmed_seq]
                                    else:
                                        if Position_index:
                                            trimmed_seq = [(file_path, name, PCR_amplicon(forward = fwd, reverse = rev, template = seq_dict[name], Single_amplicon = True, Sequence_Only = False, amplicon_size_limit = limit, allowance = allowance, Warning_ignore = Warning_ignore), pbar.update(1), ) for limit, name in zip(Sequence_length_list, seq_dict)]
                                        else:
                                            trimmed_seq = [(file_path, name, PCR_amplicon(forward = fwd, reverse = rev, template = seq_dict[name], Single_amplicon = True, Sequence_Only = True, amplicon_size_limit = limit, allowance = allowance, Warning_ignore = Warning_ignore), pbar.update(1), ) for limit, name in zip(Sequence_length_list, seq_dict)]
                                    trimmed_seq = [ts for ts in trimmed_seq if ts[2] is not None]
                                    if Position_index & Feature & (len(annotation) > 0): 
                                        annotated_trimmed_seq = []
                                        for ts in trimmed_seq: 
                                            Gene = [[position for position in re.sub(r"[^0-9]+", " ", target).split(" ") if len(position) != 0] + [annotation[ts[1]][target]] for target in annotation[ts[1]].keys() if (ts[1] in annotation.keys())] 
                                            Amplicon_annotation = {str(ts[2][0]) + str(ts[2][1]): [(g[0], g[1], g[2], ) for g in Gene if (((int(g[0]) - int(distance)) <= np.abs(ts[2][0])) & ((int(g[1]) + int(distance)) >= np.abs(ts[2][0]))) | (((int(g[0]) - int(distance)) <= np.abs(ts[2][1])) & ((int(g[1]) + int(distance)) >= np.abs(ts[2][1]))) | (((int(g[0]) - int(distance)) >= np.abs(ts[2][0])) & ((int(g[1]) + int(distance)) <= np.abs(ts[2][1])))]} 
                                            annotated_trimmed_seq.append((ts[0], ts[1], tuple(list(ts[2]) + [Amplicon_annotation[str(ts[2][0]) + str(ts[2][1])]]), )) 
                                        trimmed_seq = [(ts[0], ts[1]+"_("+str(ts[2][0])+" -> "+str(ts[2][1])+")", ts[2][2], ts[2][3], ) for ts in annotated_trimmed_seq] 
                                        del annotated_trimmed_seq
                                    elif Position_index:
                                        trimmed_seq = [(ts[0], ts[1]+"_("+str(ts[2][0])+" -> "+str(ts[2][1])+")", ts[2][2], [], ) for ts in trimmed_seq]
                                    else:
                                        trimmed_seq = [(ts[0], ts[1], ts[2], [], ) for ts in trimmed_seq]
                                    trimmed_seqs += trimmed_seq
                                if pbar.total - pbar.n > 0:
                                    pbar.update(pbar.total - pbar.n)
                        else:
                            if Feature: 
                                for file_path in file_paths: 
                                    seq_dict = read_sequence_file(input = file_path, format = "genbank", Feature = True)[0] 
                                    annotation.update({key:seq_dict[key][1] for key in seq_dict if (key not in Removal_sequences)}) 
                                    del seq_dict 
                            with get_context("spawn").Pool(processes = np.min([CPU, len(file_paths)]), initializer = init_worker) as pl:
                                try:
                                    if Position_index & Feature & (len(annotation) > 0):
                                        trimmed_seqs = list(tqdm(pl.imap(partial(trim_seq_worker_process_single, fwd = fwd, rev = rev, Sequence_Only = False, amplicon_size_limit = amplicon_size_limit, allowance = allowance, Warning_ignore = Warning_ignore, overlap_region = overlap_region, circular_index = circular_index, Feature = Feature, annotation = annotation, distance = distance, Removal_sequences = Removal_sequences, LowQualitySequences = LowQualitySequences), file_paths), total = len(file_paths), desc = "Writing PCR result", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0))
                                    elif Position_index:
                                        trimmed_seqs = list(tqdm(pl.imap(partial(trim_seq_worker_process_single, fwd = fwd, rev = rev, Sequence_Only = False, amplicon_size_limit = amplicon_size_limit, allowance = allowance, Warning_ignore = Warning_ignore, overlap_region = overlap_region, circular_index = circular_index, Removal_sequences = Removal_sequences, LowQualitySequences = LowQualitySequences), file_paths), total = len(file_paths), desc = "Writing PCR result", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0))
                                    else:
                                        trimmed_seqs = list(tqdm(pl.imap(partial(trim_seq_worker_process_single, fwd = fwd, rev = rev, Sequence_Only = True, amplicon_size_limit = amplicon_size_limit, allowance = allowance, Warning_ignore = Warning_ignore, overlap_region = overlap_region, circular_index = circular_index, Removal_sequences = Removal_sequences, LowQualitySequences = LowQualitySequences), file_paths), total = len(file_paths), desc = "Writing PCR result", leave = False, position = 1, unit = "tasks", unit_scale = True, smoothing = 0))
                                except KeyboardInterrupt:
                                    pl.terminate()
                                    pl.join()
                                    pl.close()
                                    print("\n\n --- Keyboard Interrupt ---")
                                    sys.exit("")
                            trimmed_seqs = list(it.chain.from_iterable(trimmed_seqs))
                    if len(trimmed_seqs) == 0:
                        print("No amplicon was obtained.")
                        progress_bar.update(1)
                        Primer_set_number += 1
                        continue
                    if output_folder != "":
                        if not os.path.exists(output_folder):
                            os.mkdir(output_folder)
                        if (Output_filename == "") | (OUTDIRTRUE_FILENAMEFALSE_FLAG):
                            Output_filename = output_folder + "iPCR_result" + "_by_PrimerSetNo" + str(Primer_set_number) + ".fasta"
                            OUTDIRTRUE_FILENAMEFALSE_FLAG = True
                        if os.path.exists(Output_filename):
                            Output_filename = file_existence(Output_filename)
                        if single_file:
                            for trimmed_seq in trimmed_seqs:
                                with open(Output_filename, "a", encoding = "utf-8") as fout:
                                    fout.write(">"+trimmed_seq[1]+"\n"+trimmed_seq[2]+"\n")
                        elif Feature:
                            for trimmed_seq in trimmed_seqs:
                                Output_filename = output_folder + trimmed_seq[0][trimmed_seq[0].rfind("/") + 1:].replace(trimmed_seq[0][trimmed_seq[0].rfind("."):], "") + "_" + re.sub(r'_(.)_', r'\1', re.sub(r' (.) ', r'\1', re.sub(r'\.|,|-|>|:|;', "", str(trimmed_seq[1])))).replace("  ", " ").replace(" ", "_") + "_iPCR_result_by_PrimerSetNo" + str(Primer_set_number) + ".gb"
                                if os.path.exists(Output_filename):
                                    Output_filename = file_existence(Output_filename)
                                with open(Output_filename, "wt", encoding = "utf-8") as fout:
                                    seq =  str(trimmed_seq[2])
                                    Gene = trimmed_seq[3]
                                    split_sequence_list = [seq[i * 10:(i+1) * 10:] for i in range(len(seq) // 10 + 1)]
                                    Sequence = "".join([" ".join([str(i * 60 + 1).rjust(9)] + split_sequence_list[i * 6 : (i + 1) * 6:] + ["\n"]) for i in range(sum([len(split_sequence) == 10 for split_sequence in split_sequence_list]) // 6 + 1)])
                                    LOCUS = "LOCUS".ljust(12) + str(trimmed_seq[1])
                                    DEFINITION = "DEFINITION".ljust(12) + str(trimmed_seq[1])
                                    TITLE = "TITLE".ljust(12) + str(trimmed_seq[1])
                                    FEATURES = "FEATURES             Location/Qualifiers"
                                    annotation_template1 = "     CDS             {0}..{1}" + "\n" + "".ljust(21) + '/product="{2}"'
                                    annotation_template2 = "     CDS             complement({1}..{0})" + "\n" + "".ljust(21) + '/product="{2}"'
                                    ANNOTATION = "\n".join([annotation_template1.format(g[0], g[1], g[2]) if int(g[0]) > 0 else annotation_template2.format(g[0], g[1], g[2]) for g in Gene])
                                    SEQUENCE = "ORIGIN\n\n" + Sequence + "//"
                                    OUTPUT_DATA = LOCUS + "\n" + DEFINITION + "\n" + TITLE + "\n" + FEATURES + "\n" + ANNOTATION + "\n" + SEQUENCE
                                    fout.write(OUTPUT_DATA)
                        else:
                            Input_file_path = [trimmed_seq[0] for trimmed_seq in trimmed_seqs]
                            Input_file_path_number = [Input_file_path.index(x) for x in set(Input_file_path)]
                            for i, trimmed_seq in enumerate(trimmed_seqs):
                                CHECK_FILENAME = os.path.splitext(trimmed_seq[0])[0]
                                CHECK_FILENAME = CHECK_FILENAME[CHECK_FILENAME.rfind("/") + 1:] + "_iPCR_result_by_PrimerSetNo" + str(Primer_set_number)
                                if re.search(CHECK_FILENAME, Output_filename) is None:
                                    Output_filename = output_folder + CHECK_FILENAME + ".fasta"
                                if (os.path.exists(Output_filename) & (i in Input_file_path_number)):
                                    Output_filename = file_existence(Output_filename)
                                with open(Output_filename, "a", encoding = "utf-8") as fout:
                                    fout.write(">"+trimmed_seq[1]+"\n"+trimmed_seq[2]+"\n")
                    else:
                        if single_file:
                            Output_filename = ""
                            for i, trimmed_seq in enumerate(trimmed_seqs):
                                CHECK_FILENAME = trimmed_seq[0].replace(trimmed_seq[0][trimmed_seq[0].rfind("/") + 1:], "") + "iPCR_result_by_PrimerSetNo" + str(Primer_set_number)
                                if (re.search(CHECK_FILENAME, Output_filename) is None):
                                    Output_filename = CHECK_FILENAME + ".fasta"
                                if (os.path.exists(Output_filename) & (i == 0)):
                                    Output_filename = file_existence(Output_filename)
                                with open(Output_filename, "a", encoding = "utf-8") as fout:
                                    fout.write(">"+trimmed_seq[1]+"\n"+trimmed_seq[2]+"\n")
                        elif Feature:
                            for trimmed_seq in trimmed_seqs:
                                if os.path.isfile(trimmed_seq[0]):
                                    Output_filename = os.path.splitext(trimmed_seq[0])[0] + "_" + re.sub(r'_(.)_', r'\1', re.sub(r' (.) ', r'\1', re.sub(r'\.|,|-|>|:|;', "", str(trimmed_seq[1])))).replace("  ", " ").replace(" ", "_") + "_iPCR_result_by_PrimerSetNo" + str(Primer_set_number) + ".gb"
                                elif os.path.isdir(trimmed_seq[0]) & np.logical_not(trimmed_seq[0].endswith("/")):
                                    Output_filename = trimmed_seq[0] + "/" + re.sub(r'_(.)_', r'\1', re.sub(r' (.) ', r'\1', re.sub(r'\.|,|-|>|:|;', "", str(trimmed_seq[1])))).replace("  ", " ").replace(" ", "_") + "_iPCR_result_by_PrimerSetNo" + str(Primer_set_number) + ".gb"
                                else:
                                    Output_filename = trimmed_seq[0] + re.sub(r'_(.)_', r'\1', re.sub(r' (.) ', r'\1', re.sub(r'\.|,|-|>|:|;', "", str(trimmed_seq[1])))).replace("  ", " ").replace(" ", "_") + "_iPCR_result_by_PrimerSetNo" + str(Primer_set_number) + ".gb"
                                if os.path.exists(Output_filename):
                                    Output_filename = file_existence(Output_filename)
                                with open(Output_filename, "wt", encoding = "utf-8") as fout:
                                    seq =  str(trimmed_seq[2])
                                    Gene = trimmed_seq[3]
                                    split_sequence_list = [seq[i * 10:(i+1) * 10:] for i in range(len(seq) // 10 + 1)]
                                    Sequence = "".join([" ".join([str(i * 60 + 1).rjust(9)] + split_sequence_list[i * 6 : (i + 1) * 6:] + ["\n"]) for i in range(sum([len(split_sequence) == 10 for split_sequence in split_sequence_list]) // 6 + 1)])
                                    LOCUS = "LOCUS".ljust(12) + str(trimmed_seq[1])
                                    DEFINITION = "DEFINITION".ljust(12) + str(trimmed_seq[1])
                                    TITLE = "TITLE".ljust(12) + str(trimmed_seq[1])
                                    FEATURES = "FEATURES             Location/Qualifiers"
                                    annotation_template1 = "     CDS             {0}..{1}" + "\n" + "".ljust(21) + '/product="{2}"'
                                    annotation_template2 = "     CDS             complement({1}..{0})" + "\n" + "".ljust(21) + '/product="{2}"'
                                    ANNOTATION = "\n".join([annotation_template1.format(g[0], g[1], g[2]) if int(g[0]) > 0 else annotation_template2.format(g[0], g[1], g[2]) for g in Gene])
                                    SEQUENCE = "ORIGIN\n\n" + Sequence + "//"
                                    OUTPUT_DATA = LOCUS + "\n" + DEFINITION + "\n" + TITLE + "\n" + FEATURES + "\n" + ANNOTATION + "\n" + SEQUENCE
                                    fout.write(OUTPUT_DATA)
                        else:
                            Input_file_path = [trimmed_seq[0] for trimmed_seq in trimmed_seqs]
                            Input_file_path_number = [Input_file_path.index(x) for x in set(Input_file_path)]
                            Output_filename = ""
                            for i, trimmed_seq in enumerate(trimmed_seqs):
                                CHECK_FILENAME = os.path.splitext(trimmed_seq[0])[0] + "_iPCR_result_by_PrimerSetNo" + str(Primer_set_number)
                                if ((re.search(CHECK_FILENAME, Output_filename) is None) & (os.path.isfile(trimmed_seq[0]))):
                                    Output_filename = CHECK_FILENAME + ".fasta"
                                elif os.path.isdir(trimmed_seq[0]) & np.logical_not(trimmed_seq[0].endswith("/")):
                                    Output_filename = trimmed_seq[0] + "/" + re.sub(r'_(.)_', r'\1', re.sub(r' (.) ', r'\1', re.sub(r'\.|,|-|>|:|;', "", str(trimmed_seq[1])))).replace("  ", " ").replace(" ", "_") + "_iPCR_result_by_PrimerSetNo" + str(Primer_set_number) + ".fasta"
                                elif os.path.isdir(trimmed_seq[0]) & trimmed_seq[0].endswith("/"):
                                    Output_filename = trimmed_seq[0] + re.sub(r'_(.)_', r'\1', re.sub(r' (.) ', r'\1', re.sub(r'\.|,|-|>|:|;', "", str(trimmed_seq[1])))).replace("  ", " ").replace(" ", "_") + "_iPCR_result_by_PrimerSetNo" + str(Primer_set_number) + ".fasta"
                                else:
                                    pass
                                if (os.path.exists(Output_filename) & (i in Input_file_path_number)):
                                    Output_filename = file_existence(Output_filename)
                                with open(Output_filename, "a", encoding = "utf-8") as fout:
                                    fout.write(">"+trimmed_seq[1]+"\n"+trimmed_seq[2]+"\n")
                Primer_set_number += 1
                progress_bar.update(1)
    else:
        print("Error: The number of forward primer and reverse primer must be equal. Please check your primer set list in the text file.")
        sys.exit()
    if len(Removal_sequences) > 0:
        print("The program has omitted several input sequence(s). The omitted sequence(s) has been recorded in log file.")
        LogOutDir = "" if os.path.dirname(Output_filename) == "" else os.path.dirname(Output_filename) + "/" 
        with open(LogOutDir + os.path.basename(os.path.splitext(input_file)[0]) + "_omitted.log", "a", encoding = "utf-8") as fout:
            fout.write("\n".join(Removal_sequences))