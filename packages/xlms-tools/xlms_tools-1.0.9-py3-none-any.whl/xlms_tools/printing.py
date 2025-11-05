# This file is part of the xlms-tools package
#
# Copyright (c) 2023 - Topf Lab, Leibniz-Institut für Virologie
# and Center for Data and Computing in Natural Sciences, Universität Hamburg
# Hamburg, Germany.
#
# This module was developed by:
#   Karen Manalastas-Cantos    <karen.manalastas-cantos AT cssb-hamburg.de>

from xlms_tools.score import *

def printsoftwareheader():
    print("\n\033[1mxlms-tools\033[0m: a software suite for modeling protein structures\n            with crosslinking mass spectrometry data\n")

def openscorefile(model, outname="xlms-scores"):
    # order output file columns
    intra = [i for i in model.xlscores if len(i) == 1]
    inter = [i for i in model.xlscores if len(i) == 2]
    intra.sort()
    inter.sort()
    
    # open output file
    ptr = open(outname+".tsv", "w")
    
    # print header
    ptr.write(f'model\tmlscore\t')
    for i in intra:
        ptr.write(f'xl_{i}\t')
    for i in inter:
        ptr.write(f'xl_{i}\t')
    ptr.write(f'#depth_violations\t')
    ptr.write(f'#max_distance_violations\t')
    ptr.write('ave_xl\n')
    
    return ptr