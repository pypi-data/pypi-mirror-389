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

def InputSequencePreprocessing(args):
    """
    Preprocessing program for DesignIdentifyPrimer or DesignUniversalPrimer.

    Parameters
    ----------
    args: ArgumentParser, class containing appropriate property as below
        input_file: Input file path (required)\n
        output: Output directory path (Make a new directory if the directory does not exist)\n
        circularDNA: If there are some circular DNAs in the input sequences, use this option (default: n/a. It means all input sequences are linear DNA. When there are some circular DNA input sequences, type 'all', 'individually', 'n/a', or the file path of the text that specify which sequence is circularDNA, after the '--circularDNA' option. See Readme for more detailed information.)\n
            Text file example:\n
                Sequence_name1 circularDNA\n
                Sequence_name2 linearDNA\n
                Sequence_name3 linearDNA\n
                    ...\n
                Sequence_nameN circularDNA\n
        circularDNAoverlap: Maximum value of overlapped region in circular DNA. It should be corresponded to the upper limit of amplicon size (set by '--Cut_off_upper' option) of following DIP or DUP.
        Single_target: All input files will be concatenated and generated as one sequence if you use this option, even if separated multi-FASTA files are inputted.\n
        Multiple_targets: All input files are recognized as an individual file, and every file is preprocessed separately.\n
        Single_file: When you use the '--Multiple_targets' option and this option, a preprocessed sequence file will be outputted as one multi-FASTA file.\n
    
    Returns
    -------
    FASTA_file: Preprocessed sequence(s) FASTA format file

    """
    import sys
    import os
    import re
    import warnings
    import math
    from tqdm import tqdm
    from datetime import datetime as dt
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    import numpy as np
    from multiprocessing import Pool, cpu_count
    from shrslib.basicfunc import read_sequence_file, circularDNA, check_input_file
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
    if args.circularDNA is not None:
        overlap_region = int(args.circularDNAoverlap)
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
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)
    if not args.Single_target:
        MultiFASTA_check = False
    elif args.Multiple_targets:
        MultiFASTA_check = True
        single_file = args.Single_file
    else:
        Seq_no = []
        for file_path in file_paths:
            with open(file_path, "rt", encoding = "utf-8") as fin:
                read_FASTA = fin.read()
                Seq_no += [read_FASTA.count(">")]
            if max(Seq_no) > 1:
                MultiFASTA_check = True
                single_file = args.Single_file
            else:
                MultiFASTA_check = False
    TimeStamp = dt.now().strftime('%Y%m%d_%H%M%S')
    if MultiFASTA_check:
        if single_file:
            for file_path in tqdm(file_paths, desc = "Preprocessing ... ", unit = "tasks", unit_scale = True, smoothing = 0):
                seqs = read_sequence_file(file_path)[0]
                seqs = {key:circularDNA(sequence = seqs[key], overlap = int(np.min([overlap_region, seqs[key].sequence_length]))) if circular_index[key] else circularDNA(sequence = seqs[key], overlap = int(0)) for key in seqs}
                New_sequence = list(seqs.values())
                New_sequence = "X".join(New_sequence)
                with open(output_folder + TimeStamp + "Preprocessed_sequence.fasta", "a", encoding = "utf-8") as fout:
                    fout.write(">" + list(seqs.keys())[0] + "_preprocessed" + "\n"+ New_sequence + "\n")
        else:
            if args.output is not None:
                pass
            else:
                output_folder = output_folder + TimeStamp + "Preprocessed" + "/"
                if not os.path.exists(output_folder):
                    os.mkdir(output_folder)
            for file_path in tqdm(file_paths, desc = "Preprocessing ... ", unit = "tasks", unit_scale = True, smoothing = 0):
                seqs = read_sequence_file(file_path)[0]
                seqs = {key:circularDNA(sequence = seqs[key], overlap = int(np.min([overlap_region, seqs[key].sequence_length]))) if circular_index[key] else circularDNA(sequence = seqs[key], overlap = int(0)) for key in seqs}
                New_sequence = list(seqs.values())
                New_sequence = "X".join(New_sequence)
                with open(output_folder + "Preprocessed_" + file_path.replace(file_path[:file_path.rfind("/") + 1], "").replace(file_path[file_path.rfind("."):], "") + ".fasta", "wt", encoding = "utf-8") as fout:
                    fout.write(">" + list(seqs.keys())[0] + "_preprocessed" + "\n"+ New_sequence + "\n")
    else:
        seq_dict = dict()
        for file_path in tqdm(file_paths, desc = "Preprocessing ... ", unit = "tasks", unit_scale = True, smoothing = 0):
            seqs = read_sequence_file(file_path)[0]
            seq_dict.update({key:circularDNA(sequence = seqs[key], overlap = int(np.min([overlap_region, seqs[key].sequence_length]))) if circular_index[key] else circularDNA(sequence = seqs[key], overlap = int(0)) for key in seqs})
        New_sequence = list(seq_dict.values())
        New_sequence = "X".join(New_sequence)
        with open(output_folder + TimeStamp + "Preprocessed_sequence.fasta", "wt", encoding = "utf-8") as fout:
            fout.write(">" + list(seq_dict.keys())[0] + "_preprocessed" + "\n"+ New_sequence + "\n")