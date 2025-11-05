# This file is part of the xlms-tools package
#
# Copyright (c) 2023 - Topf Lab, Leibniz-Institut für Virologie
# and Center for Data and Computing in Natural Sciences, Universität Hamburg
# Hamburg, Germany.
#
# This module was developed by:
#   Karen Manalastas-Cantos    <karen.manalastas-cantos AT cssb-hamburg.de>

from xlms_tools.depth import computedepth, getvoxelposition
from xlms_tools.parsers import parsebiopystructure
from os.path import splitext
from math import sqrt, ceil
import numpy as np

# GLOBAL VARIABLES
image = None
nearestwaters = None
candidatepaths = None
neighbor_offsets = [(dx, dy, dz) for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1) if (dx, dy, dz) != (0, 0, 0)]
backbone = ['N', 'CA', 'C', 'O']

def outputSASDs(pdbfile, linker='BS3/DSS', outfile=None):
    if outfile == None:
        outfile = splitext(pdbfile)[0] + '_sasds.txt'
    structure = parsebiopystructure(pdbfile)
    sasds = computeSASDs(structure, linker=linker)

    # print SASDs
    for atomA, atomB, sasdAB in sasds:
        print(atomA, atomB, sasdAB)
        
def computeSASDs(biopdbstruct, linker='BS3/DSS', maxdepth=6.25):
    global image
    global nearestwaters
    
    taggedresidues = {'BS3/DSS':['LYS'],
                        'DSBSO':['LYS'],
                        'PHOX':['LYS']
                    }
                    
    depths, residues, edt, nearestwaters, image, atomlist, translatedatoms = computedepth(biopdbstruct, return_indices=True)
    
    # note voxel locations of taggable Calphas
    allatoms = [(atomlist[i], translatedatoms[i,:]) for i in range(len(atomlist))]
    taggedatoms = [i for i in allatoms if i[0][3] in taggedresidues[linker] and depths[f'{i[0][0]}:{i[0][1]}'] <= maxdepth]
    taggedCAs = [i for i in taggedatoms if i[0][2] == 'CA']
    
    # find sidechain ends of tagged residues
    taggedSCends = []
    for ca in taggedCAs:
        curratoms = [i for i in taggedatoms if (i[0][0] == ca[0][0]) and (i[0][1] == ca[0][1]) and i[0][2] not in backbone]
        sortedatoms = sorted(curratoms, key = lambda x: euclideandistance(x[1], ca[1]))
        taggedSCends.append(sortedatoms[-1])
        
    # represent outershell as graph and compute all shortest paths between voxels
    distmatrix, voxelindex = graphshortestpaths(image, 0)
    
    # compute SASD for each pair of taggable Calphas
    sasds = []

    for i in range(len(taggedSCends)-1):
        voxi = getvoxelposition(taggedSCends[i][1])
        surfvoxi = watervoxel(voxi, nearestwaters)
        for j in range(i+1, len(taggedSCends)):
            voxj = getvoxelposition(taggedSCends[j][1])
            surfvoxj = watervoxel(voxj, nearestwaters)
            dist = distmatrix[voxelindex[surfvoxi], voxelindex[surfvoxj]]
            totalsasd = edt[voxi] + edt[voxj] + \
                        euclideandistance(voxi, taggedCAs[i][1]) + \
                        euclideandistance(voxj, taggedCAs[j][1]) + \
                        dist

            
            sasds.append((taggedCAs[i][0], taggedCAs[j][0], totalsasd))
    
#    for atom in allatoms:
#        chainid = atom[0][0]
#        resnum = atom[0][1]
#        atomname = atom[0][2]
#        resname = atom[0][3]
#        coords = atom[1]
    
    
#    for i in range(len(atomlist)):
#        chainid = atomlist[i][0]
#        resnum = atomlist[i][1]
#        atomname = atomlist[i][2]
#        resname = atomlist[i][3]
        ## reference for tuple format: atomlst.append((chain.id, res.id[1], atom.name, res.resname, selectfromatomhash(atomradius, atom.name)))
        
#        if (resname in taggedresidues[linker]):
#            key = f'{chainid}:{resnum}'
#            if key not in taggedatoms:
#                taggedatoms[key] = []
#            if atomname == 'CA':  # if CA atom found
#                if depths[key] <= maxdepth: # if within maximum residue depth
#                    taggedCAs.append((key, atomlist[i]))
#            taggedatoms[key].append(atomlist[i])
        
#        for key, atom in taggedCAs:
            
                #vx, vy, vz = getvoxelposition(translatedatoms[i,:])
                #taggedvoxels.append((vx, vy, vz))
                
    
    
    
#    for i in range(len(taggedvoxels)-1):
#    for i in range(1):
#        surfvoxi = watervoxel(taggedvoxels[i], nearestwaters)
#        for j in range(i+1, len(taggedvoxels)):
#        for j in range(i+1, 3):
#            candidatepaths = []
#            surfvoxj = watervoxel(taggedvoxels[j], nearestwaters)
#            if straightlinepathpossible(surfvoxi, surfvoxj):
#                dist = euclideandistance(surfvoxi, surfvoxj)
#            else:
                #crosslinkpathing([surfvoxi], surfvoxj)
                #dist = min([totaldistance(i) for i in candidatepaths])
#                dist = distmatrix[voxelindex[surfvoxi], voxelindex[surfvoxj]]

#            dist = distmatrix[voxelindex[surfvoxi], voxelindex[surfvoxj]]
#            totalsasd = edt[taggedvoxels[i][0], taggedvoxels[i][1], taggedvoxels[i][2]] + \
#                        edt[taggedvoxels[j][0], taggedvoxels[j][1], taggedvoxels[j][2]] + \
#                        dist
#            print (surfvoxi, edt[taggedvoxels[i][0], taggedvoxels[i][1], taggedvoxels[i][2]])
#            print (surfvoxj, edt[taggedvoxels[j][0], taggedvoxels[j][1], taggedvoxels[j][2]])
#            print (euclideandistance(surfvoxi, surfvoxj))
#            totalsasd = edt[taggedvoxels[i][0], taggedvoxels[i][1], taggedvoxels[i][2]] + edt[taggedvoxels[j][0], taggedvoxels[j][1], taggedvoxels[j][2]] + euclideandistance(surfvoxi, surfvoxj)

            
#            sasds.append((taggedCAs[i], taggedCAs[j], totalsasd))
    return sasds

def euclideandistance(voxA, voxB):
    return sqrt((voxA[0]-voxB[0])**2 + (voxA[1]-voxB[1])**2 + (voxA[2]-voxB[2])**2)
    

def watervoxel(vox, nearestwaters):
    watervox = (nearestwaters[0, vox[0], vox[1], vox[2]],
                 nearestwaters[1, vox[0], vox[1], vox[2]],
                 nearestwaters[2, vox[0], vox[1], vox[2]])
    return watervox

#distmatrix, voxelindex = graphshortestpaths(image, 0)
def graphshortestpaths(img, match):
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import shortest_path

    graph, voxelindex = constructgraph(img, match)
    graph = csr_matrix(graph)
    dist_matrix = shortest_path(csgraph=graph, directed=False, return_predecessors=False)
    return dist_matrix, voxelindex

def constructgraph(img, match):
    # get voxels in image that match a value
    nodes = [(i,j,k) for i in range(img.shape[0]) for j in range(img.shape[1]) for k in range(img.shape[2]) if img[(i,j,k)] <= match]
    
    # initialize adjacency matrix
    nnodes = len(nodes)
    adjmatrix = np.zeros((nnodes, nnodes))
    nodeindex = {}

    # get voxel numbering
    for i, vox in enumerate(nodes):
        nodeindex[vox] = i
	
    # fill in adjacency matrix, cubic grid rules (26 neighbors)
    for vox in nodeindex.keys():
        neighbors_all = [(vox[0] + offset[0], vox[1] + offset[1], vox[2] + offset[2]) for offset in neighbor_offsets]
        neighbors = [i for i in neighbors_all if i in nodeindex]
        for nb in neighbors:
            dist = euclideandistance(vox,nb)
            adjmatrix[nodeindex[vox], nodeindex[nb]] = dist
            adjmatrix[nodeindex[nb], nodeindex[vox]] = dist
            
    return adjmatrix, nodeindex
    
