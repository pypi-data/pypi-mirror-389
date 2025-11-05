# This file is part of the xlms-tools package
#
# Copyright (c) 2023 - Topf Lab, Leibniz-Institut für Virologie
# and Center for Data and Computing in Natural Sciences, Universität Hamburg
# Hamburg, Germany.
#
# This module was developed by:
#   Karen Manalastas-Cantos    <karen.manalastas-cantos AT cssb-hamburg.de>

from xlms_tools.parsers import parsebiopystructure
import numpy as np

atomradius={'CA': 1.90,
            'C': 1.88,
            'N': 1.63,
            'O': 1.48,
            'S': 1.78,
            'H': 1.2,
            'P': 1.87,
            'CB': 1.96,
            'NE': 1.63,
            'FE': 0.74,
            'default': 1.8, 
            'OX': 1.48, 
            'HX': 1.2}

def selectfromatomhash(hashtab, atomname):
    if atomname[0] == 'C':
        if atomname == 'CA':
            return hashtab['CA']
        elif atomname == 'C':
            return hashtab['C']
        else:
            return hashtab['CB']
    elif atomname[0] == 'O':
        if atomname == 'O':
            return hashtab['O']
        else:
            return hashtab['OX']
    elif atomname[0] == 'N':
        if atomname == 'N':
            return hashtab['N']
        else:
            return hashtab['NE']
    elif atomname[0] == 'S':
        return hashtab['S']
    elif atomname[0] == 'P':
        return hashtab['P']
    elif atomname[0] == 'H':
        return hashtab['H']
    elif atomname[0:2] == 'FE':
        return hashtab['FE']
    else:
        return hashtab['default']

def computedepth(biopdbstruct, scale=0.5, proberadius=2.5, margin=2.5, return_indices=False, verbose=True):
    atomlist, coords = listpdbatoms(biopdbstruct)

    if return_indices == False:
        depths, residues = computedepth_nobiopy(atomlist, coords, scale=scale, proberadius=proberadius, margin=margin, return_indices=return_indices, verbose=verbose)
        return depths, residues
    else:
        depths, residues, edt, nearestwaters, image, atomlist, translatedatoms = computedepth_nobiopy(atomlist, coords, scale=scale, proberadius=proberadius, margin=margin, return_indices=return_indices, verbose=verbose)
        return depths, residues, edt, nearestwaters, image, atomlist, translatedatoms


#    atommasks = sphericalatommasks(scale, proberadius)
#    objectbox, translatedatoms, scale = spacefillingmodel(coords, atomlist, atommasks, proberadius, scale, margin)
    
#    if verbose:
#        print (f'{time.time()-start:.3f}s')    
        
#    start = time.time()
#    edt, nearestwaters, image = edt_scipy(objectbox,scale)
#    depths, residues = getresiduedepths(edt, translatedatoms, atomlist, proberadius)
    
#    if verbose:
#        print (f"-- Calculating residue depths: {time.time()-start:.3f}s")
        
#    if return_indices == False:
#        return depths, residues
#    else:
#        return depths, residues, edt, nearestwaters, image, atomlist, translatedatoms


def computedepth_nobiopy(atomlist, coords, scale=0.5, proberadius=2.5, margin=2.5, return_indices=False, verbose=True):
    """
    depth computation independent of biopython structure object
    
    """
    import time

    if verbose:
        print ("-- Building space-filling model: ", end="")
        
    start = time.time()
    atommasks = sphericalatommasks(scale, proberadius)
    objectbox, translatedatoms, scale = spacefillingmodel(coords, atomlist, atommasks, proberadius, scale, margin)
    
    if verbose:
        print (f'{time.time()-start:.3f}s')    
        
    start = time.time()
    edt, nearestwaters, image = edt_scipy(objectbox,scale)
    depths, residues = getresiduedepths(edt, translatedatoms, atomlist, proberadius)
    
    if verbose:
        print (f"-- Calculating residue depths: {time.time()-start:.3f}s")
        
    if return_indices == False:
        return depths, residues
    else:
        return depths, residues, edt, nearestwaters, image, atomlist, translatedatoms
    

# atomlist = listpdbatoms(biopdbstruct)
def listpdbatoms(biopdbstruct):
    atomlst = []
    coordslst = []
    for chain in biopdbstruct[0]:   # get only first model in structure
        for res in chain:
            for atom in res:
                if not atomisH(atom):
                    if (res.id[0][0:1] != 'W'):     # if not water atom
                        atomlst.append((chain.id, res.id[1], atom.name, res.resname, selectfromatomhash(atomradius, atom.name)))
                        coordslst.append(atom.coord)
    coords = np.array(coordslst)
    return atomlst, coords


def atomisH(biopdbatom):
    if biopdbatom.element == 'H':
        return True
    if biopdbatom.name[0] == 'H':
        return True
    return False

# atommasks = sphericalatommasks(scale, proberadius)
def sphericalatommasks(scale, proberadius):
    
    mask = {}   # voxels with atom 1, background voxels 0
    for atom in atomradius.keys():
        tradius = (atomradius[atom]+proberadius)*scale + 0.5
        sradius = tradius*tradius
        widxz = int(tradius) + 1
        depty = []
        indx = 0
        for j in range(widxz):
            for k in range(widxz):
                txz = j*j + k*k
                if (txz > sradius):
                    depty.append(-1)
                else:
                    tdept=np.sqrt(sradius-txz)
                    depty.append(int(tdept))
        mask[atom] = makesphere(widxz, depty)        
    return mask

def makesphere(widxz, depty):
    rad = widxz - 1
    dim = 2*rad + 1
    box = np.zeros((dim, dim, dim))
    
    nind = 0
    for i in range(widxz):
        for j in range(widxz):
            if (depty[nind] != -1):
                for ii in range(-1, 2):
                    for jj in range(-1, 2):
                        for kk in range(-1, 2):
                            if(ii!=0 and jj!=0 and kk!=0):
                                mi = ii*i
                                mk = kk*j
                                for k in range(depty[nind]+1):
                                    mj = k*jj
                                    si = rad+mi
                                    sj = rad+mj
                                    sk = rad+mk
                                    box[si][sj][sk] = 1
            nind += 1
    return box
    
# translatedatoms = scaleandtranslate(coords, scale, proberadius)
def scaleandtranslate(coord, scale, proberadius, margin):
    deltax = coord[:,0].min() - (proberadius+margin)
    deltay = coord[:,1].min() - (proberadius+margin)
    deltaz = coord[:,2].min() - (proberadius+margin)
    return (coord - np.array([deltax, deltay, deltaz]))*scale

#boxlenx, boxleny, boxlenz = computeboxsize(coords, scale, proberadius, margin)
def computeboxsize(coords, scale, proberadius, margin):
    boxlength = 128
    width = coords[:,0].max() - coords[:,0].min() + (proberadius+margin)*2
    length = coords[:,1].max() - coords[:,1].min() + (proberadius+margin)*2
    height = coords[:,2].max() - coords[:,2].min() + (proberadius+margin)*2

    boxlenx = int(np.ceil(scale*width) + 1)
    boxleny = int(np.ceil(scale*length) + 1)
    boxlenz = int(np.ceil(scale*height) + 1)

    return np.array([boxlenx, boxleny, boxlenz]), scale

#objectbox = spacefillingmodel(translatedatoms, atomlist, atommasks)
def spacefillingmodel(coords, atomlist, atommasks, proberadius, scale, margin):
    translatedatoms = scaleandtranslate(coords, scale, proberadius, margin)
    
    # compute box size
    boxlen, scale = computeboxsize(coords, scale, proberadius, margin)
    #print ("box: ", boxlen[0], boxlen[1], boxlen[2], "scale:", scale)
    objectbox=np.zeros((boxlen[0], boxlen[1], boxlen[2]))
    
    # for each atom, apply object and surface masks
    for i in range(len(atomlist)):
        atomtype = atomlist[i][2]
        obj = selectfromatomhash(atommasks, atomtype)
        #obj = selectatommask(atommasks, atomtype)
        radobj = (obj.shape[0]-1)/2
        objstart, objend = getboxbounds(translatedatoms[i,:], radobj)
        objectbox[objstart[0]:objend[0], objstart[1]:objend[1], objstart[2]:objend[2]] += obj

    objectbox[objectbox > 0] = 1

    return objectbox, translatedatoms, scale

# objstart, objend = getboxbounds(coord[i,:], radobj)
def getboxbounds(atomcoord, radius):
    rad = int(radius)
    centerx, centery, centerz = getvoxelposition(atomcoord)
    start = (centerx-rad, centery-rad, centerz-rad)
    end = (centerx+rad+1, centery+rad+1, centerz+rad+1)
    return start, end

def getvoxelposition(coords):
    vx = int(coords[0] + 0.5)
    vy = int(coords[1] + 0.5)
    vz = int(coords[2] + 0.5)
    
    return vx, vy, vz
        
# obj = selectatommask(objmasks, atomtype)
def selectatommask(masks, atomtype):
    return selectfromatomhash(masks, atomtype)

# depths = getresiduedepths(edt, translatedatoms, atomlist)
def getresiduedepths(edt, translatedatoms, atomlist, proberadius):
    depths = {}
    residues = {}
    for i in range(len(atomlist)):
        key = atomlist[i][0]+':'+str(atomlist[i][1])
        if key not in depths:
            depths[key] = []
            residues[key] = atomlist[i][3]
        x, y, z = getvoxelposition(translatedatoms[i])
        
        # check if minimum depth met
        if edt[x,y,z] - proberadius < atomlist[i][4]:
            curdep = atomlist[i][4] + proberadius
        else:
            curdep = edt[x,y,z]
             
        depths[key].append(curdep)
    
    for i in depths.keys():
        depths[i] = sum(depths[i])/len(depths[i])

    return depths, residues

def edt_scipy(image, scale):
    from scipy.ndimage import distance_transform_edt
    
    image, bg = peeloffouter(image)
    depths, nearestwater = distance_transform_edt(image, return_indices=True)
    depths[bg == -1] = -1    
    depths /= scale
    return depths, nearestwater, image

def peeloffouter(img):
    newimg = np.copy(img)
    bg = np.zeros((img.shape[0], img.shape[1], img.shape[2]))
    bg[img == 0] = -1
    
    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            for k in range(img.shape[2]):
                if img[i,j,k] > 0:  #is object pixel
                    istart = max(0, i-1)
                    jstart = max(0, j-1)
                    kstart = max(0, k-1)
                    iend = min(img.shape[0], i+2)
                    jend = min(img.shape[1], j+2)
                    kend = min(img.shape[2], k+2)
                    total = (iend - istart)*(jend-jstart)*(kend-kstart)
                    if np.sum(img[istart:iend, jstart:jend, kstart:kend]) < total:
                        newimg[i,j,k] = 0
    newimg -= bg
    return newimg, bg
