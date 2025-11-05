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

def AdditionalAnalysis(args):
    """
    Make fragment size matrix from new template sequence and the result containing primer sets that you have already generated.

    Parameters
    ----------
    args: ArgumentParser, class containing appropriate property as below
        input_file: Input file path (required)\n
        csv_file: File path of the CSV data obtained from other analysis (DesignIdentifyPrimer, DesignUniversalPrimer. required)\n
        output: Output directory path (Make a new directory if the directory does not exist)\n
        size_limit: The upper limit of amplicon size\n
        process: The number of processes (sometimes the number of CPU core) used for analysis\n
        forward: Forward primer sequence (required if you don't provide a CSV file with the '-f' option)\n
        reverse: Reverse primer sequence (required if you don't provide a CSV file with the '-f' option)\n
        circularDNA: If there are some circular DNAs in the input sequences, use this option (default: n/a. It means all input sequences are linear DNA. When there are some circular DNA input sequences, type 'all', 'individually', 'n/a', or the file path of the text that specify which sequence is circularDNA, after the '--circularDNA' option. See Readme for more detailed information.)\n
            Text file example:\n
                Sequence_name1 circularDNA\n
                Sequence_name2 linearDNA\n
                Sequence_name3 linearDNA\n
                    ...\n
                Sequence_nameN circularDNA\n
        warning: Shows all warnings when you use this option.

    Returns
    -------
    CSV_file: CSV file will be generated
    """

    import sys
    import os
    import re
    import warnings
    from functools import partial
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    from tqdm import tqdm
    import math
    import csv
    import itertools as it
    import numpy as np
    import pandas as pd
    from multiprocessing import Pool, get_context, cpu_count
    from shrslib.basicfunc import init_worker, read_sequence_file, circularDNA, check_input_file, complementary_sequence
    from shrslib.scores import fragment_size_distance, calculate_score
    from shrslib.explore import PCR_amplicon
    from shrslib.multiprocessfunc import add_anal_worker_process, PCR_amplicon_with_progress_bar, cumulative_pairwise_identity
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
    if args.output is not None:
        output_folder = args.output
        if not output_folder.endswith("/"):
            output_folder = output_folder+"/"
    else:
        output_folder = ""
    isSummary_data = False
    Score_calculation = 'Fragment'
    if args.csv_file is not None:
        csv_file_path = args.csv_file
        csv_file_path = re.sub("\\\\", "/", os.path.abspath(csv_file_path))
        try:
            test_sequence = pd.read_csv(csv_file_path, header = 0)
            isSummary_data = True if ('Arguments' in test_sequence.columns) else isSummary_data
            isSummary_data = True if ('Arguments' in test_sequence.iloc[0].tolist()) else isSummary_data
            if 'Score_calculation_mode' in test_sequence.iloc[:, 0].tolist():
                Score_calculation = 'Sequence' if str(test_sequence.iloc[test_sequence.iloc[:, 0].tolist().index('Score_calculation_mode'), 1]) == 'Sequence' else Score_calculation
        except:
            with open(csv_file_path, "r", encoding = "utf-8") as fin:
                Read_Data = csv.reader(fin)
                max_col = np.max([len(line) for line in Read_Data])
            test_sequence = pd.read_csv(csv_file_path, names = range(max_col), dtype = object)
            isSummary_data = True if ('Arguments' in test_sequence.columns) else isSummary_data
            isSummary_data = True if ('Arguments' in test_sequence.iloc[0].tolist()) else isSummary_data
            if 'Score_calculation_mode' in test_sequence.iloc[:, 0].tolist():
                Score_calculation = 'Sequence' if str(test_sequence.iloc[test_sequence.iloc[:, 0].tolist().index('Score_calculation_mode'), 1]) == 'Sequence' else Score_calculation
            test_sequence = test_sequence.drop(0)
        if np.any(test_sequence.iloc[:, 2:].isnull().all(axis = 1)):
            test_sequence = test_sequence[~test_sequence.iloc[:, 2:].isnull().all(axis = 1)]
            test_sequence.columns = test_sequence.iloc[0]
            test_sequence.columns.name = None
            test_sequence = test_sequence.drop(test_sequence.index[0])
            test_sequence = test_sequence.drop(['No', 'Flexibility', 'Score', 'Fragment_number', 'Forward_Tm_value', 'Reverse_Tm_value', 'Tm_value_difference', 'Identical_sequences', 'TreeTopology_Adjusted_Score'], errors='ignore', axis = 1)
        fwd = list(test_sequence.iloc[:, 0])
        rev = list(test_sequence.iloc[:, 1])
        Check_File_Format = (np.sum(test_sequence.iloc[:, 0].apply(lambda x:len(re.sub("[ATGCBDHKMRSVWYNXatgcbdhkmrsvwynx]", "", str(x))))) == 0) & (np.sum(test_sequence.iloc[:, 1].apply(lambda x:len(re.sub("[ATGCBDHKMRSVWYNXatgcbdhkmrsvwynx]", "", str(x))))) == 0)
        Check_File_Format = Check_File_Format & (test_sequence.iloc[:, 2:].map(lambda x:(str(x).replace(".", "").replace("-", "").isnumeric()) | (str(x).startswith("["))).all().all() if Pandas_later_210 else test_sequence.iloc[:, 2:].applymap(lambda x:(str(x).replace(".", "").replace("-", "").isnumeric()) | (str(x).startswith("["))).all().all())
        Check_File_Format = Check_File_Format | (test_sequence.iloc[:, 2:].map(lambda x:len(re.sub("[ATGCBDHKMRSVWYNXatgcbdhkmrsvwynx]", "", str(x))) == 0).all(axis = 1).any() if Pandas_later_210 else test_sequence.iloc[:, 2:].applymap(lambda x:len(re.sub("[ATGCBDHKMRSVWYNXatgcbdhkmrsvwynx]", "", str(x))) == 0).all(axis = 1).any())
        if np.logical_not(Check_File_Format):
            print("Unexpected data format. Check CSV file.")
            sys.exit()
        if isSummary_data:
            isUniversal = ((np.sum(np.sum(test_sequence.iloc[:, 2:].map(lambda x:str(x).find("[") >= 0) if Pandas_later_210 else test_sequence.iloc[:, 2:].applymap(lambda x:str(x).find("[") >= 0), axis = 0)) / test_sequence.iloc[:, 2:].size) < 1/6) & ((np.sum(np.sum(test_sequence.iloc[:, 2:].map(lambda x:len(re.sub("[ATGCBDHKMRSVWYNXatgcbdhkmrsvwynx]", "", str(x))) == 0) if Pandas_later_210 else test_sequence.iloc[:, 2:].applymap(lambda x:len(re.sub("[ATGCBDHKMRSVWYNXatgcbdhkmrsvwynx]", "", str(x))) == 0), axis = 0)) / test_sequence.iloc[:, 2:].size) < 1/5)
            Dataset_type = 'Universal' if isUniversal else 'Identify'
        else:
            Dataset_type = 'Unknown'
    else:
        if args.forward is not None:
            fwd = [args.forward]
        else:
            sys.exit("Need forward primer or sequence sets csv file.")
        if args.reverse is not None:
            rev = [args.reverse]
        else:
            sys.exit("Need reverse primer or sequence sets csv file.")
        csv_file_path = ''
        Dataset_type = 'Unknown'
        isSummary_data = False
        test_sequence = pd.DataFrame([[fwd, rev]])
    amplicon_size_limit = args.size_limit
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
    Seq_no = []
    for file_path in file_paths:
        with open(file_path, "rt", encoding = "utf-8") as fin:
            read_FASTA = fin.read()
            Seq_no += [read_FASTA.count(">")]
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
    Warning_ignore = args.warning
    if Warning_ignore:
        warnings.simplefilter('ignore')
    if ((np.all([type(f) is str for f in fwd])) & (np.all([type(r) is str for r in rev]))):
        Fragment_matrix = pd.DataFrame([])
        if len(fwd) > len(Seq_no):
            with tqdm(total = np.sum(Seq_no) * len(fwd), desc = "Now analyzing ...", leave = False, unit = "tasks", unit_scale = True, smoothing = 0) as pbar:
                def Progressbar_update(Result):
                    pbar.update(Result[1])
                for file_path in file_paths:
                    seq_dict = read_sequence_file(file_path)[0]
                    Sequence_length_list = [np.min([amplicon_size_limit, seq_dict[key].sequence_length]) for key in seq_dict]
                    seq_dict = {key:circularDNA(sequence = seq_dict[key], overlap = int(np.min([overlap_region, seq_dict[key].sequence_length]))) if circular_index[key] else circularDNA(sequence = seq_dict[key], overlap = int(0)) for key in seq_dict}
                    if (CPU > 1):
                        for limit, name in zip(Sequence_length_list, seq_dict):
                            with get_context("spawn").Pool(processes = min([CPU, len(fwd)]), initializer = init_worker) as pl:
                                try:
                                    Amplicons = [pl.apply_async(PCR_amplicon_with_progress_bar, kwds = {"forward": f, "reverse": r, "template": seq_dict[name], "Single_amplicon": False, "Sequence_Only": True, "amplicon_size_limit": limit, "allowance": 0, "Warning_ignore": Warning_ignore}, callback = Progressbar_update) for f, r in zip(fwd, rev)]
                                except KeyboardInterrupt:
                                    pl.terminate()
                                    pl.join()
                                    pl.close()
                                    print("\n\n --- Keyboard Interrupt ---")
                                    sys.exit("")
                                Amplicons = [amp.get()[0] for amp in Amplicons]
                            if Score_calculation == 'Sequence':
                                Amplicons = [amps if amps is not None else [] for amps in Amplicons]
                                Amplicons = [amps[0] if len(amps) == 1 else np.nan for amps in Amplicons]
                            else:
                                Amplicons = [[len(amp) for amp in amps] if amps is not None else np.nan for amps in Amplicons]
                            Amplicons = pd.DataFrame(pd.Series(Amplicons, index = pd.MultiIndex.from_tuples([mid for mid in zip(fwd, rev)]), name = name))
                            Fragment_matrix = pd.concat([Fragment_matrix, Amplicons], axis = 1, join = "outer")
                    else:
                        for limit, name in zip(Sequence_length_list, seq_dict):
                            Amplicons = [(PCR_amplicon(forward = f, reverse = r, template = seq_dict[name], Single_amplicon = False, Sequence_Only = True, amplicon_size_limit = limit, allowance = int(0), Warning_ignore = Warning_ignore), pbar.update(1), ) for f, r in zip(fwd, rev)]
                            Amplicons = [amp[0] for amp in Amplicons]
                            if Score_calculation == 'Sequence':
                                Amplicons = [amps if amps is not None else [] for amps in Amplicons]
                                Amplicons = [amps[0] if len(amps) == 1 else np.nan for amps in Amplicons]
                            else:
                                Amplicons = [[len(amp) for amp in amps] if amps is not None else np.nan for amps in Amplicons]
                            Amplicons = pd.DataFrame(pd.Series(Amplicons, index = pd.MultiIndex.from_tuples([mid for mid in zip(fwd, rev)]), name = name))
                            Fragment_matrix = pd.concat([Fragment_matrix, Amplicons], axis = 1, join = "outer")
        else:
            with get_context("spawn").Pool(processes = min([CPU, len(file_paths)]), initializer = init_worker) as pl:
                try:
                    Amplicons = list(tqdm(pl.imap(partial(add_anal_worker_process, fwd = fwd, rev = rev, amplicon_size_limit = amplicon_size_limit, overlap_region = overlap_region, circular_index = circular_index, Score_calculation = Score_calculation), file_paths), total = len(file_paths), desc = "Now analyzing ...", leave = False, unit = "tasks", unit_scale = True, smoothing = 0))
                except KeyboardInterrupt:
                    pl.terminate()
                    pl.join()
                    pl.close()
                    print("\n\n --- Keyboard Interrupt ---")
                    sys.exit()
            for amp in Amplicons:
                Fragment_matrix = pd.concat([Fragment_matrix, amp], axis = 1, join = "outer")
        if Dataset_type == 'Universal':
            Fragment_matrix = Fragment_matrix if np.any(Fragment_matrix.fillna('').map(lambda x:len(x) > 1) if Pandas_later_210 else Fragment_matrix.fillna('').applymap(lambda x:len(x) > 1)) else (Fragment_matrix.map(lambda x:x[0] if type(x) is list else x) if Pandas_later_210 else Fragment_matrix.applymap(lambda x:x[0] if type(x) is list else x))
        else:
            if Score_calculation == 'Sequence':
                for i in range(Fragment_matrix.shape[0]):
                    Fragment_matrix.iloc[i] = np.array(['' if np.all(pd.isna(Fragment_matrix.iloc[i, j])) else str(Fragment_matrix.iloc[i, j]) if calculate_score(Fragment_matrix.index[i][0], str(Fragment_matrix.iloc[i, j])[0:len(Fragment_matrix.index[i][0])]) == 1 else str(complementary_sequence(Fragment_matrix.iloc[i, j])) for j in range(len(Fragment_matrix.iloc[i]))], dtype = str)
            else:
                for i in range(Fragment_matrix.shape[0]):
                    Fragment_matrix.iloc[i] = np.array([str(sorted(list(set([(x, round(Fragment_matrix.iloc[i, j].count(x)/len(Fragment_matrix.iloc[i, j]), 2),) for x in Fragment_matrix.iloc[i, j]])))) if np.all(pd.notna(Fragment_matrix.iloc[i, j])) else '' for j in range(len(Fragment_matrix.iloc[i]))], dtype = object)
        if (csv_file_path != '') & (('max_col' in locals()) | (len(np.where(test_sequence.iloc[:, 0].isna() == True)[0].tolist()) == 1) | isSummary_data):
            Fragment_matrix = Fragment_matrix.add_prefix("[Additional_analysis]")
            if 'max_col' in locals():
                Template_matrix = pd.read_csv(csv_file_path, names = range(max_col), header = None, sep = ",")
            else:
                Template_matrix = pd.read_csv(csv_file_path, header = None, sep = ",")
            Template_matrix.index = pd.MultiIndex.from_tuples(zip(Template_matrix.iloc[:, 0], Template_matrix.iloc[:, 1]))
            Template_matrix = Template_matrix.drop(Template_matrix.columns[[0,1]], axis = 1)
            Template_analisys_information = Template_matrix[Template_matrix.isnull().all(axis = 1)]
            Template_matrix = Template_matrix[~Template_matrix.isnull().all(axis = 1)]
            Template_matrix.columns = Template_matrix.iloc[0]
            Template_matrix = Template_matrix.drop(Template_matrix.index[0])
            Template_matrix.index = Template_matrix.index.rename(Template_matrix.columns.names[0])
            Template_matrix.columns.name = None
            New_label = (['No'] if 'No' in Template_matrix.columns else []) + list(Fragment_matrix.columns) + list(Template_matrix.columns[Template_matrix.columns != 'No'] if 'No' in Template_matrix.columns else Template_matrix.columns)
            Fragment_matrix = pd.concat([Template_matrix, Fragment_matrix], axis = 1, join = "outer")
            Fragment_matrix = Fragment_matrix.reindex(columns = New_label)
            Fragment_matrix.index = Fragment_matrix.index.rename(['Forward', 'Reverse'])
            if (Dataset_type == 'Identify') & ("Score" in Fragment_matrix.columns):
                if Score_calculation == 'Sequence':
                    Reevaluation_matrix = Fragment_matrix.loc[:,Fragment_matrix.columns[Fragment_matrix.map(lambda x:len(re.sub("[ATGCBDHKMRSVWYNXatgcbdhkmrsvwynx]", "", str(x))) == 0 if np.all(pd.notna(x)) else False).all(axis = 0)]] if Pandas_later_210 else Fragment_matrix.loc[:,Fragment_matrix.columns[Fragment_matrix.applymap(lambda x:len(re.sub("[ATGCBDHKMRSVWYNXatgcbdhkmrsvwynx]", "", str(x))) == 0 if np.all(pd.notna(x)) else False).all(axis = 0)]]
                    Reevaluation_matrix = Reevaluation_matrix.map(lambda x:str(x) if np.all(pd.notna(x)) else np.nan) if Pandas_later_210 else Reevaluation_matrix.applymap(lambda x:str(x) if np.all(pd.notna(x)) else np.nan)
                    with get_context("spawn").Pool(processes = CPU, initializer = init_worker) as pl:
                        try:
                            Score = list(pl.imap(partial(cumulative_pairwise_identity, df = Reevaluation_matrix, method = 'average'), range(Reevaluation_matrix.shape[0])))
                            Score = [round(sc, 4) for sc in Score]
                        except KeyboardInterrupt:
                            pl.terminate()
                            pl.join()
                            pl.close()
                            print("\n\n --- Keyboard Interrupt ---")
                            sys.exit()
                    Fragment_matrix.insert(list(Fragment_matrix.columns).index("Score") + 1, "Recalculated_score", Score)
                else:
                    Reevaluation_matrix = Fragment_matrix.loc[:,Fragment_matrix.columns[Fragment_matrix.map(lambda x:True if x is None else True if np.all(pd.isna(x)) else np.any([x.count("[") > 0, x.lower() == 'nan', len(x) == 0]) if type(x) is str else type(x) is list).all(axis = 0)]] if Pandas_later_210 else Fragment_matrix.loc[:,Fragment_matrix.columns[Fragment_matrix.applymap(lambda x:True if x is None else True if np.all(pd.isna(x)) else np.any([x.count("[") > 0, x.lower() == 'nan', len(x) == 0]) if type(x) is str else type(x) is list).all(axis = 0)]]
                    Reevaluation_matrix = Reevaluation_matrix.map(lambda x:np.nan if np.any([x is None, x == '']) else x) if Pandas_later_210 else Reevaluation_matrix.applymap(lambda x:np.nan if np.any([x is None, x == '']) else x)
                    Reevaluation_matrix = Reevaluation_matrix.map(lambda x:eval(x) if (type(x) is str) else x) if Pandas_later_210 else Reevaluation_matrix.applymap(lambda x:eval(x) if (type(x) is str) else x)
                    if (Reevaluation_matrix.map(lambda x:type(x[0]) is tuple if type(x) is list else False).any().any() if Pandas_later_210 else Reevaluation_matrix.applymap(lambda x:type(x[0]) is tuple if type(x) is list else False).any().any()):
                        Reevaluation_matrix = Reevaluation_matrix.map(lambda x:[x1[0] for x1 in x] if np.all(pd.notna(x)) else np.nan) if Pandas_later_210 else Reevaluation_matrix.applymap(lambda x:[x1[0] for x1 in x] if np.all(pd.notna(x)) else np.nan)
                    Score = Reevaluation_matrix.apply(lambda x:round(fragment_size_distance(x[np.logical_not(x == '')], sum = False, method = 'average'), 1), axis = 1)
                    Fragment_number = Reevaluation_matrix.apply(lambda x:len(list(it.chain.from_iterable(x[pd.notna(x)]))), axis = 1)
                    Score = Score / (Fragment_number - np.min(Fragment_number) + 1)
                    Fragment_matrix.insert(list(Fragment_matrix.columns).index("Score") + 1, "Recalculated_score", Score)
                    Fragment_matrix.insert(list(Fragment_matrix.columns).index("Fragment_number") + 1, "Recalculated_fragment_number", Fragment_number)
        if output_folder != "":
            if not os.path.exists(output_folder):
                os.mkdir(output_folder)
            if (csv_file_path != '') & (('max_col' in locals()) | (len(np.where(test_sequence.iloc[:, 0].isna() == True)[0].tolist()) == 1) | isSummary_data):
                Template_analisys_information.to_csv(output_folder + csv_file_path[int(np.max([csv_file_path.rfind("/"), csv_file_path.rfind("\\")])) + 1 : csv_file_path.rfind(".csv")] + "_Additional_analysis_result.csv", header = False, sep = ",")
                Fragment_matrix.to_csv(output_folder + csv_file_path[int(np.max([csv_file_path.rfind("/"), csv_file_path.rfind("\\")])) + 1 : csv_file_path.rfind(".csv")] + "_Additional_analysis_result.csv", mode = "a", header = True, index = True, sep = ",")
            elif (csv_file_path != ''):
                Fragment_matrix.to_csv(output_folder + csv_file_path[int(np.max([csv_file_path.rfind("/"), csv_file_path.rfind("\\")])) + 1 : csv_file_path.rfind(".csv")] + "_Additional_analysis_result.csv", header = True, index = True, sep = ",")
            else:
                Fragment_matrix.to_csv(output_folder + "Additional_analysis_result.csv", sep = ",")
        elif csv_file_path == '':
            if os.path.isdir(input_file):
                if input_file.endswith("/"):
                    Fragment_matrix.to_csv(input_file+"Additional_analysis_result.csv", header = True, index = True, sep = ",")
                else:
                    Fragment_matrix.to_csv(input_file+"/Additional_analysis_result.csv", header = True, index = True, sep = ",")
            else:
                if input_file.find("/") == -1:
                    Fragment_matrix.to_csv("./Additional_analysis_result.csv", header = True, index = True, sep = ",")
                else:
                    Fragment_matrix.to_csv(input_file[0:input_file.rfind("/")]+"/Additional_analysis_result.csv", header = True, index = True, sep = ",")
        else:
            if (csv_file_path != '') & (('max_col' in locals()) | (len(np.where(test_sequence.iloc[:, 0].isna() == True)[0].tolist()) == 1) | isSummary_data):
                Template_analisys_information.to_csv(csv_file_path[0:csv_file_path.rfind(".csv")]+"_Additional_analysis_result.csv", header = False, sep = ",")
                Fragment_matrix.to_csv(csv_file_path[0:csv_file_path.rfind(".csv")]+"_Additional_analysis_result.csv", mode = "a", header = True, index = True, sep = ",")
            elif (csv_file_path != ''):
                Fragment_matrix.to_csv(csv_file_path[0:csv_file_path.rfind(".csv")]+"_Additional_analysis_result.csv", header = True, index = True, sep = ",")
            else:
                Fragment_matrix.to_csv(csv_file_path[0:csv_file_path.rfind(".csv")]+"_Additional_analysis_result.csv", header = True, index = True, sep = ",")
    else:
        print("Unexpected data format. Check CSV file.")
        sys.exit()