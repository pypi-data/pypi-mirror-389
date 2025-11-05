# This file is part of the xlms-tools package
#
# Copyright (c) 2023 - Topf Lab, Leibniz-Institut für Virologie
# and Center for Data and Computing in Natural Sciences, Universität Hamburg
# Hamburg, Germany.
#
# This module was developed by:
#   Karen Manalastas-Cantos    <karen.manalastas-cantos AT cssb-hamburg.de>

from Bio.PDB import MMCIFParser, PDBParser
import numpy as np

def parsebiopystructure(infile):
    parser = None
    if infile[-3:].lower() == 'pdb':
        parser = PDBParser(QUIET=True)
    elif infile[-3:].lower() == 'cif':
        parser = MMCIFParser(QUIET=True)
    else:
        print (f'File suffix {infile[-3:]} not recognized: must either be pdb or cif')
        return None
    structure = parser.get_structure(infile[:-4], infile)
    return structure
    
def extractCAcoordsfrompdb(pdbfile):
    structure = parsebiopystructure(pdbfile)
    CAcoords = np.zeros(3)
    residues = structure.get_residues()
    nres = 0
    for res in residues:
        if res.has_id("CA"):
            atom = np.asarray(res["CA"].get_coord())
            CAcoords = np.concatenate((CAcoords, atom), axis=0)
            nres += 1        
    CAcoords = np.reshape(CAcoords[3:], (nres,3))
    return CAcoords

def maxCAdistfromstructure(structure):
    CAcoords = np.zeros(3)
    residues = structure.get_residues()
    nres = 0
    for res in residues:
        if res.has_id("CA"):
            atom = np.asarray(res["CA"].get_coord())
            CAcoords = np.concatenate((CAcoords, atom), axis=0)
            nres += 1        
    CAcoords = np.reshape(CAcoords[3:], (nres,3))
    distmat = distancematrix(CAcoords, CAcoords)
    return distmat.max()
    
    
def distancematrix(a, b):
    distmat = np.linalg.norm(a[:, None, :] - b[None, :, :], axis=-1)
    return distmat
