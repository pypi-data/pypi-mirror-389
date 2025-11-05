# This file is part of the xlms-tools package
#
# Copyright (c) 2023 - Topf Lab, Leibniz-Institut für Virologie
# and Center for Data and Computing in Natural Sciences, Universität Hamburg
# Hamburg, Germany.
#
# This module was developed by:
#   Karen Manalastas-Cantos    <karen.manalastas-cantos AT cssb-hamburg.de>

import sys
import os.path

# def createpb()
def createpb(pdb, visdir):
    gdfile = os.path.join(visdir, os.path.basename(pdb)[:-4]+'_gd.pb')
    midfile = os.path.join(visdir, os.path.basename(pdb)[:-4]+'_mid.pb')
    badfile = os.path.join(visdir, os.path.basename(pdb)[:-4]+'_bad.pb')
    
    g = open(gdfile, 'w')
    m = open(midfile, 'w') 
    b = open(badfile, 'w')
    
    g.write('; dashes = 1\n')
    m.write('; dashes = 1\n')
    b.write('; dashes = 1\n')
        
    return g, m, b

# def printcxc(pdblist, visdir):
def printcxc(pdbflist, visdir="viz", color="lightgray"):
    # print chimerax run script (.cxc)
    runscript = visdir+'.cxc'
    nents = 0
                
    f = open(runscript, 'w')
    f.write('graphics bgColor white\n')
    for pdb in pdbflist:  # open pdb files in order
        f.write(f"open {pdb}\n")
        nents += 1
        f.write(f"color #{nents} {color} cartoons\n")
            
    for pdb in pdbflist:  # open pdb files in order
        # open pseudobond files representing crosslinks
        # within tolerance
        i = os.path.join(visdir, os.path.basename(pdb)[:-4]+'_gd.pb')
        f.write(f"open {i}\n")
        nents += 1
        f.write(f"color #{nents} blue\n")
        
        # on threshold
        i = os.path.join(visdir, os.path.basename(pdb)[:-4]+'_mid.pb')
        f.write(f"open {i}\n")
        nents += 1
        f.write(f"color #{nents} yellow\n")            
        
        # maximum distance violations
        i = os.path.join(visdir, os.path.basename(pdb)[:-4]+'_bad.pb')
        f.write(f"open {i}\n")
        nents += 1
        f.write(f"color #{nents} red\n")

    # general graphics settings
    f.write('graphics silhouettes true\n')
    f.write('cartoon style modeHelix tube\n')
    f.write('lighting flat\n')

    # align structures to first one opened
    for i in range(2, len(pdbflist)+1):    
        f.write('mm #'+str(i)+'/A to #1/A\n')
    
    return f


