#!/usr/bin/env python3

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

def main():
    import os
    import sys
    python_version = sys.version_info
    required_python_version = {"major": int(3), "minor": int(8)}
    if python_version.major * 10000 + python_version.minor < required_python_version['major'] * 10000 + required_python_version['minor']:
        raise RuntimeError("Python3.8 or later required. You use python{0}.{1} now.".format(python_version.major, python_version.minor))
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    import argparse
    from time import time
    from shrslib.__version__ import __version__
    from . import AdditionalAnalysis, DesignIdentifyPrimer, DesignUniversalPrimer, DesignProbe, InputSequencePreprocessing, insilicoPCR
    start = time()
    parser = argparse.ArgumentParser(description = '--- HELP message ---', prog = 'shrs', epilog = "--- END ---")
    parser.add_argument('-v', '--version', action='version', version = __version__)
    subparsers = parser.add_subparsers()
    
    #Perform Additional analysis using primer sets obtained from DIP or DUP.
    parser_AA = subparsers.add_parser('AA', formatter_class = lambda prog: argparse.HelpFormatter(prog, max_help_position = 40), help = "see 'AA -h'.\tMake a fragment size matrix from a new template sequence and the result containing primer sets that you have already generated.", description = "Make a fragment size matrix from a new template sequence and the result containing primer sets that you have already generated.")
    parser_AA.add_argument('-i', '--input_file', type = str, metavar = "str", required = True, help = 'Input file path (required, format: FASTA or Genbank)')
    parser_AA.add_argument('-f', '--csv_file', type = str, metavar = "str", help = 'File path of the CSV data obtained from other analysis (DIP or DUP) (required)')
    parser_AA.add_argument('-o', '--output', type = str, metavar = "str", help = 'Output directory path (Make a new directory if the directory does not exist)')
    parser_AA.add_argument('-s', '--size_limit', type = int, metavar = "int", default = 3000, help = 'The upper limit of amplicon size (default: 3,000)')
    parser_AA.add_argument('-P', '--process', type = int, metavar = "int", help = 'The number of processes (sometimes the number of CPU core) used for analysis')
    parser_AA.add_argument('-fwd', '--forward', type = str, metavar = "str", help = "Forward primer sequence (required if you don't provide a CSV file with the '-f' option)")
    parser_AA.add_argument('-rev', '--reverse', type = str, metavar = "str", help = "Reverse primer sequence (required if you don't provide a CSV file with the '-f' option)")
    parser_AA.add_argument('--circularDNA', type = str, metavar = "str", default = None, nargs = '*', help = "If there are some circular DNAs in the input sequences, use this option (default: n/a. It means all input sequences are linear DNA. When there are some circular DNA input sequences, type 'all', 'individually', 'n/a', or the file path of the text that specify which sequence is circularDNA, after the '--circularDNA' option. See Readme for more detailed information.)")
    parser_AA.add_argument('--warning', action = 'store_false', help = 'Shows all warnings when you use this option.')
    parser_AA.set_defaults(handler = AdditionalAnalysis.AdditionalAnalysis)

    #Design primer set for identification.
    parser_DIP = subparsers.add_parser('DIP', formatter_class = lambda prog: argparse.HelpFormatter(prog, max_help_position = 45), help = "see 'DIP -h'.\tPrimer design algorithm for the identification of bacteria", description = "Primer design algorithm for the identification of bacteria")
    parser_DIP.add_argument('-i', '--input_file', type = str, metavar = "str", required = True, help = 'Input file path (required, format: FASTA or Genbank)')
    parser_DIP.add_argument('-e', '--exclude_file', type = str, metavar = "str", help = 'File path for exclusion sequence(s). Specify the sequence(s) file path of the bacteria if there are some bacteria that you would like to not amplify. (format: FASTA or Genbank)')
    parser_DIP.add_argument('-s', '--primer_size', type = int, metavar = "int", default = 25, help = 'Primer size (default: 25)')
    parser_DIP.add_argument('-a', '--allowance', type = float, metavar = "float", default = 0.15, help = 'Mismatch allowance ratio (default: 0.15. The value means that a 4-base [25 * 0.15] mismatch is accepted). Note that setting this parameter too large might causes the increased run time and excessive memory consumption.')
    parser_DIP.add_argument('-r', '--range', type = int, metavar = "int", default = 0, help = 'Search range from primer size (default: 0. If the value is 1, the primer sets that have 25–26 base length are explored)')
    parser_DIP.add_argument('-d', '--distance', type = int, metavar = "int", default = 10000, help = 'The minimum distance between annealing sites that are hybridized with a primer (default: 10,000)')
    parser_DIP.add_argument('-o', '--output', type = str, metavar = "str", help = 'Output directory path (Make a new directory if the directory does not exist)')
    parser_DIP.add_argument('-P', '--process', type = int, metavar = "int", help = 'The number of processes (sometimes the number of CPU core) used for analysis')
    parser_DIP.add_argument('-g', '--Group_id', type = str, metavar = "str", default = None, help = "Type the file path of the text that specifies which sequences are same group, after the '--Group_id' option. Please avoid to contain a sequence name in ID like as combination of sequence name '12' and ID 'SeqID12'. See Readme for more detailed information. (default: None.)")
    parser_DIP.add_argument('--Exclude_mode', type = str, metavar = "str", default = 'fast', choices = ['fast', 'standard'], help = "Choose the method for excluding the sequence(s) from 'fast' or 'standard' when you specify some sequence(s) file path of the bacteria that you would like to exclude using '-e' option (default: fast.)")
    parser_DIP.add_argument('--Result_output', type = int, metavar = "int", default = 10000, help = 'The upper limit of result output (default: 10,000)')
    parser_DIP.add_argument('--Cut_off_lower', type = float, metavar = "float", default = 50, help = 'The lower limit of amplicon size (default: 50)')
    parser_DIP.add_argument('--Cut_off_upper', type = float, metavar = "float", default = 1000, help = 'The upper limit of amplicon size (default: 1,000)')
    parser_DIP.add_argument('--Match_rate', type = float, metavar = "float", default = 0.8, help = 'The ratio of trials for which the primer candidate fulfilled all criteria when the allowance value is decreased. The higher the number is, the more specific the primer obtained is (default: 0.8)')
    parser_DIP.add_argument('--Chunks', default = 'Auto', metavar = "int/str", help = 'The chunk size for calculation. If the memory usage for calculation using the chunk size exceeds the GPU memory size, the processing unit for calculation will be switched to the CPU automatically (default: Auto)')
    parser_DIP.add_argument('--Maximum_annealing_site_number', type = int, metavar = "int", default = 5, help = 'The maximum acceptable value of the number of annealing site of the candidate of the primer in the input sequence (default: 5)')
    parser_DIP.add_argument('--Window_size', type = int, metavar = "int", default = 950, help = 'The duplicated candidates containing this window will be removed (default: 950)')
    parser_DIP.add_argument('--Search_mode', type = str, metavar = "str", nargs = '+', default = None, help = "There are four options: exhaustive/moderate/sparse/manual. If you choose the 'manual' option, type the ratio to primer length after 'manual'. (e.g. --Search_mode manual 0.2.) (default: moderate when the average input sequence length is >5000, and exhaustive when the average input sequence length is ≤5000)")
    parser_DIP.add_argument('--withinMemory', action = 'store_true', help = 'All analyses are performed within memory (default: False)')
    parser_DIP.add_argument('--Without_allowance_adjustment', action = 'store_false', help = "Use this option if you do not want to modify the allowance value for every homology calculation (default: False)")
    parser_DIP.add_argument('--circularDNA', type = str, metavar = "str", default = None, nargs = '*', help = "If there are some circular DNAs in the input sequences, use this option (default: n/a. It means all input sequences are linear DNA. When there are some circular DNA input sequences, type 'all', 'individually', 'n/a', or the file path of the text that specify which sequence is circularDNA, after the '--circularDNA' option. See Readme for more detailed information.)")
    parser_DIP.add_argument('--exclude_circularDNA', type = str, metavar = "str", default = None, nargs = '*', help = "If there are some circular DNAs in the input sequence(s) that you do not want to amplify, use this option (default: n/a. It means all input sequences are linear DNA. When there is some circular DNA in the sequence file for exclusion, type 'all', 'individually', 'n/a', or the file path of the text that specifies which sequence is circularDNA, after the '--exclude_circularDNA' option. See Readme for more detailed information.)")
    parser_DIP.add_argument('--Score_calculation', type = str, metavar = "str", default = 'Fragment', choices = ['Fragment', 'Sequence'], help = "The calculation method of the score for identifying microorganisms. Fragment length or sequence. When the 'Sequence' is specified, the primer set that produces only a single amplicon will be obtained in order to reduce computational complexity.")
    parser_DIP.add_argument('--Combination_number', type = int, metavar = "int", default = 3, help = "The number of primer sets to be used for identification (default: 3).")
    parser_DIP.add_argument('--Correlation_threshold', type = float, metavar = "float", default = 0.9, help = "The primer sets with a correlation coefficient greater than this are grouped, and two or more primer sets from the same group are never chosen sets (default: 0.9).")
    parser_DIP.add_argument('--Dendrogram_output', type = int, metavar = "int", default = 10, help = "The number supplied in this parameter will be used to construct dendrograms. As a result, the default parameters yield 10 dendrograms (default: 10, max: 100).")
    parser_DIP.add_argument('--Reference_tree', type = str, metavar = "str", default = None, help = "Use this option if you evaluate a primer set based on the distance between the output tree and the reference tree. Specify a newick tree or a file path of newick format phylogenetic tree after '--Reference_tree' option (default: None).")
    parser_DIP.add_argument('--Only_sequence_with_feature_key', action = 'store_true', default = False, help = "Use this option if designing primer sets based solely on the sequences with feature key, such as gene (default: False).")
    parser_DIP.add_argument('--Fragment_size_pattern_matrix', type = str, metavar = "str", default = None, help = "When you have a csv file of fragment size pattern matrix, you can reanalyse from the csv file. Specify the file path (default: None.)")
    parser_DIP.add_argument('--Fragment_start_position_matrix', type = str, metavar = "str", default = None, help = "When you reanalyse from fragment size pattern matrix by 'Sequence' mode, specify the csv file path of fragment start position matrix (default: None.)")
    parser_DIP.set_defaults(handler = DesignIdentifyPrimer.DesignIdentifyPrimer)

    #Design universal primer set for amplifying similar length fragment.
    parser_DUP = subparsers.add_parser('DUP', formatter_class = lambda prog: argparse.HelpFormatter(prog, max_help_position = 45), help = "see 'DUP -h'.\tPrimer design algorithm for universal primer", description = "Primer design algorithm for universal primer")
    parser_DUP.add_argument('-i', '--input_file', type = str, metavar = "str", required = True, help = 'Input file path (required, format: FASTA or Genbank)')
    parser_DUP.add_argument('-o', '--output', type = str, metavar = "str", help = 'Output directory path (Make a new directory if the directory does not exist)')
    parser_DUP.add_argument('-e', '--exclude_file', type = str, metavar = "str", help = 'File path for exclusion sequence(s). Specify the sequence(s) file path of the bacteria if there are some bacteria that you would like to not amplify. (format: FASTA or Genbank)')
    parser_DUP.add_argument('-s', '--primer_size', type = int, metavar = "int", default = 20, help = 'Primer size (default: 20)')
    parser_DUP.add_argument('-a', '--allowance', type = float, metavar = "float", default = 0.20, help = 'Mismatch allowance ratio (default: 0.20. The value means that a 4-base [20 * 0.20] mismatch is accepted). Note that setting this parameter too large might causes the increased run time and excessive memory consumption.')
    parser_DUP.add_argument('-r', '--range', type = int, metavar = "int", default = 0, help = 'Search range from primer size (default: 0. If the value is 1, the primer sets that have 20–21 base length are explored)')
    parser_DUP.add_argument('-d', '--distance', type = int, metavar = "int", default = 5000, help = 'The minimum distance between annealing sites that are hybridized with a primer (default: 5,000)')
    parser_DUP.add_argument('-P', '--process', type = int, metavar = "int", help = 'The number of processes (sometimes the number of CPU core) used for analysis')
    parser_DUP.add_argument('--Exclude_mode', type = str, metavar = "str", default = 'fast', choices = ['fast', 'standard'], help = "Choose the method for excluding the sequence(s) from 'fast' or 'standard' when you specify some sequence(s) file path of the bacteria that you would like to exclude using '-e' option (default: fast.)")
    parser_DUP.add_argument('--Cut_off_lower', type = float, metavar = "float", default = 50, help = 'The lower limit of amplicon size (default: 50)')
    parser_DUP.add_argument('--Cut_off_upper', type = float, metavar = "float", default = 3000, help = 'The upper limit of amplicon size (default: 3,000)')
    parser_DUP.add_argument('--Match_rate', type = float, metavar = "float", default = 0.0, help = 'The ratio of trials for which the primer candidate fulfilled all criteria when the allowance value is decreased. The higher the number is, the more specific the primer obtained is (default: 0.0)')
    parser_DUP.add_argument('--Result_output', type = int, metavar = "int", default = 10000, help = 'The upper limit of result output (default: 10,000)')
    parser_DUP.add_argument('--Omit_similar_fragment_size_pair', action = "store_true", help = "Use this option if you want to omit primer sets that amplify similar fragment lengths")
    parser_DUP.add_argument('--Window_size', type = int, metavar = "int", default = 50, help = 'The duplicated candidates containing this window will be removed (default: 50)')
    parser_DUP.add_argument('--Maximum_annealing_site_number', type = int, metavar = "int", default = None, help = 'The maximum acceptable value of the number of annealing site of the candidate of the primer in the input sequence (default: unlimited)')
    parser_DUP.add_argument('--Chunks', default = 'Auto', metavar = "int/str", help = 'The chunk size for calculation. If the memory usage for calculation using the chunk size exceeds the GPU memory size, the processing unit for calculation will be switched to the CPU automatically (default: Auto)')
    parser_DUP.add_argument('--Search_mode', type = str, metavar = "str", nargs = '+', default = None, help = "There are four options: exhaustive/moderate/sparse/manual. If you choose the 'manual' option, type the ratio to primer length after 'manual'. (e.g. --Search_mode manual 0.2.) (default: moderate when the average input sequence length is >5000, and exhaustive when the average input sequence length is ≤5000)")
    parser_DUP.add_argument('--withinMemory', action = 'store_true', help = 'All analyses are performed within memory (default: False)')
    parser_DUP.add_argument('--Without_allowance_adjustment', action = 'store_false', help = "Use this option if you do not want to modify the allowance value for every homology calculation (default: False)")
    parser_DUP.add_argument('--circularDNA', type = str, metavar = "str", default = None, nargs = '*', help = "If there are some circular DNAs in the input sequences, use this option (default: n/a. It means all input sequences are linear DNA. When there are some circular DNA input sequences, type 'all', 'individually', 'n/a', or the file path of the text that specify which sequence is circularDNA, after the '--circularDNA' option. See Readme for more detailed information.)")
    parser_DUP.add_argument('--exclude_circularDNA', type = str, metavar = "str", default = None, nargs = '*', help = "If there are some circular DNAs in the input sequence(s) that you do not want to amplify, use this option (default: n/a. It means all input sequences are linear DNA. When there is some circular DNA in the sequence file for exclusion, type 'all', 'individually', 'n/a', or the file path of the text that specifies which sequence is circularDNA, after the '--exclude_circularDNA' option. See Readme for more detailed information.)")
    parser_DUP.add_argument('--Fragment_size_pattern_matrix', type = str, metavar = "str", default = None, help = "When you have a csv file of fragment size pattern matrix, you can reanalyse from the csv file. Specify the file path (default: None.)")
    parser_DUP.set_defaults(handler = DesignUniversalPrimer.DesignUniversalPrimer)

    #Preprocessing program for DUP or DIP.
    parser_ISP = subparsers.add_parser('ISP', formatter_class = lambda prog: argparse.HelpFormatter(prog, max_help_position = 40), help = "see 'ISP -h'.\tInput sequences preprocessing program for DUP or DIP", description = "Input sequences preprocessing program for DUP or DIP")
    parser_ISP.add_argument('-i', '--input_file', type = str, metavar = "str", required = True, help = 'Input file path (required, format: FASTA or Genbank)')
    parser_ISP.add_argument('-o', '--output', type = str, metavar = "str", help = 'Output directory path (Make a new directory if the directory does not exist)')
    parser_ISP.add_argument('--circularDNA', type = str, metavar = "str", default = None, nargs = '*', help = "If there are some circular DNAs in the input sequences, use this option (default: n/a. It means all input sequences are linear DNA. When there are some circular DNA input sequences, type 'all', 'individually', 'n/a', or the file path of the text that specify which sequence is circularDNA, after the '--circularDNA' option. See Readme for more detailed information.)")
    parser_ISP.add_argument('--circularDNAoverlap', type = int, metavar = "int", default = 10000, help = "Maximum value of overlapped region in circular DNA (default: 10,000). For reducing computational complexity, you can reduce this value to the larger one of the upper limit of amplicon size and interval distance that will be set by '--Cut_off_upper' and '--distance' in following DIP or DUP.")
    parser_ISP.add_argument('--Single_target', action = "store_false", help = "All input files will be concatenated and generated as one sequence if you use this option, even if separated multi-FASTA files are inputted.")
    parser_ISP.add_argument('--Multiple_targets', action = "store_true", help = "All input files are recognized as an individual file, and every file is preprocessed separately.")
    parser_ISP.add_argument('--Single_file', action = "store_true", help = "When you use the '--Multiple_targets' option and this option, a preprocessed sequence file will be outputted as one multi-FASTA file.")
    parser_ISP.set_defaults(handler = InputSequencePreprocessing.InputSequencePreprocessing)

    #in silico PCR amplification algorithm.
    parser_iPCR = subparsers.add_parser('iPCR', formatter_class = lambda prog: argparse.HelpFormatter(prog, max_help_position = 40), help = "see 'iPCR -h'.\tIn silico PCR amplification algorithm", description = "In silico PCR amplification algorithm")
    parser_iPCR.add_argument('-i', '--input_file', type = str, metavar = "str", required = True, help = 'Input file path (required, format: FASTA or Genbank)')
    parser_iPCR.add_argument('-o', '--output', type = str, metavar = "str", help = 'Output directory path (Make a new directory if the directory does not exist)')
    parser_iPCR.add_argument('-s', '--size_limit', type = int, metavar = "int", default = 10000, help = 'The upper limit of amplicon size (default: 10,000)')
    parser_iPCR.add_argument('-P', '--process', type = int, metavar = "int", default = 1, help = "The number of processes (sometimes the number of CPU core) used for analysis. Enter '-1' as the argument to set the number of processes automatically. (default: 1)")
    parser_iPCR.add_argument('-fwd', '--forward', type = str, metavar = "str", default = "", help = "The forward primer sequence used for amplification (required)")
    parser_iPCR.add_argument('-rev', '--reverse', type = str, metavar = "str", default = "", help = "The reverse primer sequence used for amplification (required)")
    parser_iPCR.add_argument('-f', '--primerset_filepath', type = str, metavar = "str", default = "", help = "The filepath of the text file containing forward and reverse primer sequence (required if forward and reverse primer set with -fwd and -rev option are not provided)")
    parser_iPCR.add_argument('--fasta', action = 'store_false', help = "Output format. A FASTA file will be generated if you use this option.")
    parser_iPCR.add_argument('--Single_file', action = 'store_true', help = "Output format. One single FASTA-format file will be generated even if you input some separate FASTA files, when using this option with the '--fasta' option.")
    parser_iPCR.add_argument('--Mismatch_allowance', type = int, metavar = "int", default = 0, help = "The acceptable mismatch number (default: 0)")
    parser_iPCR.add_argument('--Only_one_amplicon', action = "store_false", help ="Only one amplicon is outputted, even if multiple amplicons are obtained by PCR when you use this option.")
    parser_iPCR.add_argument('--Position_index', action = "store_true", help = "The result has the information of the amplification position when this option is enabled.")
    parser_iPCR.add_argument('--circularDNA', type = str, metavar = "str", default = None, nargs = '*', help = "If there are some circular DNAs in the input sequences, use this option (default: n/a. It means all input sequences are linear DNA. When there are some circular DNA input sequences, type 'all', 'individually', 'n/a', or the file path of the text that specify which sequence is circularDNA, after the '--circularDNA' option. See Readme for more detailed information.)")
    parser_iPCR.add_argument('--gene_annotation_search_range', type = int, metavar = "int", default = 100, help = "The gene annotation search range in the GenBank-format file. (default: 100)")
    parser_iPCR.add_argument('--Annotation', action = 'store_true', help = "If the input sequence file is in GenBank format, the amplicon(s) is annotated automatically.")
    parser_iPCR.add_argument('--LowQualitySequences', type = str, metavar = "str", default = "remain", choices = ['remove', 'individually', 'ignore', 'remain'], help = "In in silico PCR analysis, all sequences containing the regions with a high proportion of 'N' bases will be omitted when you specify 'remove' option. This option helps to reduce a computational effort and calculation time. If you select the omitted sequences individually, specify 'individually'. When the 'ignore' option is selected, regions spanning 'N' bases will not be amplified. To use all input sequences for the in silico PCR template, specify the 'remain' option. (Default: 'remain')")
    parser_iPCR.add_argument('--warning', action = 'store_false', help = 'Shows all warnings when you use this option.')
    parser_iPCR.set_defaults(handler = insilicoPCR.insilicoPCR)

    #Design probe.
    parser_DP = subparsers.add_parser('DP', formatter_class = lambda prog: argparse.HelpFormatter(prog, max_help_position = 45), help = "see 'DP -h'.\tProbe design algorithm", description = "Probe design algorithm")
    parser_DP.add_argument('-i', '--input_file', type = str, metavar = "str", required = True, help = 'Input file path (required, format: FASTA or Genbank)')
    parser_DP.add_argument('-e', '--exclude_file', type = str, metavar = "str", help = 'File path for exclusion sequence(s). Specify the sequence(s) file path of the bacteria if there are some bacteria that you would like to not hybridize. (format: FASTA or Genbank)')
    parser_DP.add_argument('-s', '--probe_size', type = int, metavar = "int", default = 25, help = 'Probe size (default: 25)')
    parser_DP.add_argument('-a', '--allowance', type = float, metavar = "float", default = 0.25, help = 'Mismatch allowance ratio (default: 0.25. The value means that a 7-base [25 * 0.25] mismatch is accepted). Note that setting this parameter too large might causes the increased run time and excessive memory consumption.')
    parser_DP.add_argument('-r', '--range', type = int, metavar = "int", default = 0, help = 'Search range from probe size (default: 0. If the value is 1, the probe that have 25–26 base length is explored)')
    parser_DP.add_argument('-d', '--distance', type = int, metavar = "int", default = 100, help = 'The minimum distance between annealing sites that are hybridized with a probe (default: 100)')
    parser_DP.add_argument('-o', '--output', type = str, metavar = "str", help = 'Output directory path (Make a new directory if the directory does not exist)')
    parser_DP.add_argument('-P', '--process', type = int, metavar = "int", help = 'The number of processes (sometimes the number of CPU core) used for analysis')
    parser_DP.add_argument('--Exclude_mode', type = str, metavar = "str", default = 'fast', choices = ['fast', 'standard'], help = "Choose the method for excluding the sequence(s) from 'fast' or 'standard' when you specify some sequence(s) file path of the bacteria that you would like to exclude using '-e' option (default: fast.)")
    parser_DP.add_argument('--Result_output', type = int, metavar = "int", default = 10000, help = 'The upper limit of result output (default: 10,000)')
    parser_DP.add_argument('--Match_rate', type = float, metavar = "float", default = 0.8, help = 'The ratio of trials for which the probe candidate fulfilled all criteria when the allowance value is decreased. The higher the number is, the more specific the probe obtained is (default: 0.8)')
    parser_DP.add_argument('--Chunks', default = 'Auto', metavar = "int/str", help = 'The chunk size for calculation. If the memory usage for calculation using the chunk size exceeds the GPU memory size, the processing unit for calculation will be switched to the CPU automatically (default: Auto)')
    parser_DP.add_argument('--Maximum_annealing_site_number', type = int, metavar = "int", default = 5, help = 'The maximum acceptable value of the number of annealing site of the candidate of the probe in the input sequence (default: 5)')
    parser_DP.add_argument('--Search_mode', type = str, metavar = "str", nargs = '+', default = None, help = "There are four options: exhaustive/moderate/sparse/manual. If you choose the 'manual' option, type the ratio to probe length after 'manual'. (e.g. --Search_mode manual 0.2.) (default: moderate when the average input sequence length is >5000, and exhaustive when the average input sequence length is ≤5000)")
    parser_DP.add_argument('--withinMemory', action = 'store_true', help = 'All analyses are performed within memory (default: False)')
    parser_DP.add_argument('--Without_allowance_adjustment', action = 'store_false', help = "Use this option if you do not want to modify the allowance value for every homology calculation (default: False)")
    parser_DP.set_defaults(handler = DesignProbe.DesignProbe)

    args = parser.parse_args()
    if hasattr(args, 'handler'):
        args.handler(args)
        end = time()
        elapsed_time = end - start
        print("Elapsed time: {0}d {1}h {2}m {3}s".format(int(round(((elapsed_time//60)//60)//24, 0)), int(round(((elapsed_time//60)//60)%24, 0)), int(round((elapsed_time//60)%60, 0)), round(elapsed_time%60, 1)))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()