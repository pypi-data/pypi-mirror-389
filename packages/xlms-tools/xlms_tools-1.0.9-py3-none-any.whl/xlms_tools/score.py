# This file is part of the xlms-tools package
#
# Copyright (c) 2023 - Topf Lab, Leibniz-Institut für Virologie
# and Center for Data and Computing in Natural Sciences, Universität Hamburg
# Hamburg, Germany.
#
# This module was developed by:
#   Karen Manalastas-Cantos    <karen.manalastas-cantos AT cssb-hamburg.de>

from Bio.PDB import *
from xlms_tools.depth import *
from xlms_tools.parsers import *
from xlms_tools.visualization import *
import numpy as np
import scipy.stats
import time

class StructModel:
    def __init__(self, infile, depths=None, verbose=True):
        if verbose:
            print ("MODEL:", infile)

        # if no depths computed, we are starting from a pdb/cif file
        if depths == None:
            self.filename = infile
            self.biopdbstruct = parsebiopystructure(infile)
            self.residuedepths, self.residues, self.edt, self.nearestwaters, self.voxelized, self.atomlist, self.translatedatomcoords = computedepth(self.biopdbstruct, return_indices=True, verbose=verbose)

        # depth has been precomputed, probably api access
        else:
            self.filename = None
            self.biopdbstruct = infile
            self.residuedepths = depths
            self.residues, self.edt, self.nearestwaters = None, None, None
            self.voxelized, self.atomlist, self.translatedatomcoords = None, None, None
        
        self.maxCAdist = maxCAdistfromstructure(self.biopdbstruct)
        self.maxdepth = max(self.residuedepths.values())
        self.xlps = {}
        self.xlscores = []
        self.mlscores = []
        self.avexlscore = 0
        self.avemlscore = 0
        self.depviols = 0
        self.distviols = 0
    
    def findCAatom(self, chain_id, residue_number):
        if self.biopdbstruct[0].__contains__(chain_id):
            if self.biopdbstruct[0][chain_id].__contains__(residue_number):
                if self.biopdbstruct[0][chain_id][residue_number].__contains__('CA'):
                    return self.biopdbstruct[0][chain_id][residue_number]['CA']
        return None
        
    def inmodel(self, link):
        found = False
        if link.__class__.__name__ == 'Monolink':
            if self.findCAatom(link.chainid, link.rnum) is not None:
                return True
#            if self.biopdbstruct[0].__contains__(link.chainid):
#                if self.biopdbstruct[0][link.chainid].__contains__(link.rnum):
#                    if self.biopdbstruct[0][link.chainid][link.rnum].__contains__('CA'):
#                        return True
        else:   #if crosslink
            if self.findCAatom(link.siteA.chainid, link.siteA.rnum) is not None:
                if self.findCAatom(link.siteB.chainid, link.siteB.rnum) is not None:
                    return True

#            if self.biopdbstruct[0].__contains__(link.siteA.chainid):
#                if self.biopdbstruct[0][link.siteA.chainid].__contains__(link.siteA.rnum):
#                    if self.biopdbstruct[0][link.siteA.chainid][link.siteA.rnum].__contains__('CA'):
#                        if self.biopdbstruct[0].__contains__(link.siteB.chainid):
#                            if self.biopdbstruct[0][link.siteB.chainid].__contains__(link.siteB.rnum):
#                                if self.biopdbstruct[0][link.siteB.chainid][link.siteB.rnum].__contains__('CA'):
#                                    return True
        return found
            
    def scoremodel(self, xlmslist, verbose=True):
        start = time.time()
        
        # accumulators for denominators
        totalmlweight = 0
        totalxlweight = 0
        xlweightbychain = {}
        
        # score each link
        for link in xlmslist:
            if self.inmodel(link):
                if link.__class__.__name__ == 'Monolink':
                    mlscore, depth, viol = link.score(self)
                    self.avemlscore += mlscore
                    totalmlweight += link.weight
                    self.mlscores.append((link, mlscore, depth))
                    if viol:
                        self.depviols += 1
                else:   # if crosslink
                    xlscore, dist, viol = link.score(self)
                    self.avexlscore += xlscore
                    totalxlweight += link.weight
                    self.xlscores.append((link, xlscore, dist))
                    chid = link.chains() 
                    if chid not in self.xlscores:
                        self.xlps[chid] = xlscore
                        xlweightbychain[chid] = link.weight
                    else:
                        self.xlps[chid] += xlscore
                        xlweightbychain[chid] += link.weight
                    if viol:
                        self.distviols += 1

        # get score averages
        if totalmlweight != 0:
            self.avemlscore /= totalmlweight
        if totalxlweight != 0:
            self.avexlscore /= totalxlweight
        for key in self.xlps:
            self.xlps[key] /= xlweightbychain[key]
        if verbose:
            print (f"-- Scoring model: {time.time()-start:.3f}s\n")    

    def printscores(self, ptr):
        
        # order output file columns
        intra = [i for i in self.xlscores if len(i) == 1]
        inter = [i for i in self.xlscores if len(i) == 2]
        intra.sort()
        inter.sort()
    
        
        ptr.write(f'{os.path.basename(self.filename)[:-4]}\t')
        if self.avemlscore != 0:
            ptr.write(f'{self.avemlscore:.3f}\t')
        else:
            ptr.write('--\t')
            
        
        for key in intra:
        	ptr.write(f'{self.xlscores[key]:.3f}\t')
        for key in inter:
        	ptr.write(f'{self.xlscores[key]:.3f}\t')
    
        ptr.write(f'{self.depviols}\t')
        ptr.write(f'{self.distviols}\t')
        ptr.write(f'{self.avexlscore:.3f}')            
        ptr.write('\n')
        
    def printindivscores(self, prefix=None):
        # open output file
        outname = f'{os.path.splitext(os.path.basename(self.filename))[0]}_scores.tsv'
        if prefix != None:
            outname = f'{prefix}_{outname}'
        with open(outname, 'w') as f:
            # print header
            f.write(f'ChainID_1\tRes#_1\tChainID_2\tRes#_2\tscore\tCA-CA_distance/Residue_depth\n')
            
            # print crosslinks
            for link, score, d in self.xlscores:
                f.write(f'{link.siteA.chainid}\t{str(link.siteA.rnum)}\t{link.siteB.chainid}\t{str(link.siteB.rnum)}\t{score:.3f}\t{d:.3f}\n')
            
            # print monolinks
            for link, score, d in self.mlscores:
                f.write(f'{link.chainid}\t{str(link.rnum)}\t-\t-\t{score:.3f}\t{d:.3f}\n')
             
                
    
    def printchimeraxfiles(self, cxdir, cxcptr, xlmslist, modelid):
        # open pseudobond files
        g, m, b = createpb(self.filename, cxdir)
        
        # go through crosslinks and monolinks
        for link in xlmslist:
            if self.inmodel(link):
                if link.__class__.__name__ == 'Monolink':
                    # add visualization of monolink to ChimeraX command file
                    cxcptr.write(f'show #{modelid}/{link.chainid}:{link.rnum} atoms\n')
                    cxcptr.write(f'color #{modelid}/{link.chainid}:{link.rnum} {link.color(self)} atoms\n')
                    
                else:   # if crosslink
                    dist = link.eudist(self)
                    pos1 = f'{link.siteA.chainid}:{link.siteA.rnum}'
                    pos2 = f'{link.siteB.chainid}:{link.siteB.rnum}'
                    
                    if dist <= link.fiftypercent():
                        g.write(f'#{modelid}/{pos1}@ca #{modelid}/{pos2}@ca\n')
                    elif dist <= link.cutoff():
                        m.write(f'#{modelid}/{pos1}@ca #{modelid}/{pos2}@ca\n')
                    else:
                        b.write(f'#{modelid}/{pos1}@ca #{modelid}/{pos2}@ca\n')

        # close pseudobond files
        g.close()
        m.close()
        b.close()
                    
    def outputdepth(self):
        with open(self.biopdbstruct.id+'-residue.depth', 'w') as f:
            for key in self.residuedepths.keys():
                f.write(f'{key}\t{self.residues[key]}\t{self.residuedepths[key]}\n')    
    
class Crosslink:
    def __init__(self, monolinkA, monolinkB, weight=1.0):
        self.siteA = monolinkA
        self.siteB = monolinkB
        self.weight = float(weight)

    def linkdetails(self):
        self.siteA.linkdetails()
        self.siteB.linkdetails()
        print (self.weight)
    
    def chains(self):
        if self.siteA.chainid == self.siteB.chainid:
            return self.siteA.chainid
        else:
            return self.siteA.chainid+self.siteB.chainid

    def probability(self, dist):
        # Parameters of logistic function
        bs3popt = [0.4792269560972168, 11.109773790791612, 0.3420292164964708]
        dsbsopopt = [0.525874721261341, 10.00573722419576, 0.2086340921842602]
        phoxpopt = [0.7787277889548966, 8.894304588639107, 0.21260030328899437]
        
        if self.siteA.linker == 'BS3/DSS':    # default situation, BS3 or DSS
            return 1/(1+np.exp(0.33*dist-7))    # this is the best from the benchmark
            #return logistic_function(dist, *bs3popt)
        elif self.siteA.linker == 'DSBSO':
            return logistic_function(dist, *dsbsopopt)
        elif self.siteA.linker == 'PhoX':
            return logistic_function(dist, *phoxpopt)
        else:
            print ('No information about linker. Using distance distribution for BS3/DSS')
            return logistic_function(dist, *bs3popt)

    def cutoff(self):
        cutoffs = {'BS3/DSS':33, 'DSBSO':42.5, 'PhoX':30.5}
        if self.siteA.linker in cutoffs:
            return cutoffs[self.siteA.linker]
        else:
            print ('No information about linker. Using distance cutoff for BS3/DSS')
            return cutoffs['BS3/DSS']
                
    def eudist(self, model):
        ca1 = model.findCAatom(self.siteA.chainid, self.siteA.rnum)
        ca2 = model.findCAatom(self.siteB.chainid, self.siteB.rnum)
        #ca1 = model.biopdbstruct[0][self.siteA.chainid][self.siteA.rnum]['CA']
        #ca2 = model.biopdbstruct[0][self.siteB.chainid][self.siteB.rnum]['CA']
        #return ca1-ca2
        return np.linalg.norm(ca1.coord - ca2.coord)
    
    def fiftypercent(self):
        cutoffs = {'BS3/DSS':21, 'DSBSO':21, 'PhoX':16}
        if self.siteA.linker in cutoffs:        
            return cutoffs[self.siteA.linker]  
        else:
            print ('No information about linker. Using distance cutoff for BS3/DSS')
            return cutoffs['BS3/DSS']
         
    def score(self, model):
        viol = False
        dep1 = self.siteA.depth(model)
        dep2 = self.siteB.depth(model)
        mp1 = self.siteA.probability(dep1)
        mp2 = self.siteB.probability(dep2)
        dist = self.eudist(model)
        distp = self.probability(dist)
        score = mp1*mp2*distp
        
        if dep1 >= self.siteA.cutoff():
            score = -dep1/(4*model.maxdepth)
        if dep2 >= self.siteB.cutoff():
            score = -dep2/(4*model.maxdepth)
        if dist > self.cutoff():
            score = -dist/(2*model.maxCAdist)
            viol = True
        score *= self.weight
        return score, dist, viol
        
class Monolink:
    def __init__(self, chainid, rnum, linker='BS3/DSS', weight=1.0):
        self.chainid = chainid
        self.rnum = int(rnum)
        self.linker = linker
        self.weight = float(weight)
    
    def linkdetails(self):
        print (self.chainid, self.rnum, self.linker, self.weight)
            
    def probability(self, depth):
        # Parameters of piecewise survival function
        bs3gamma = [0.3377483292430505, 4.398636019682727, 2.495116107776707]
        dsbsogamma = [0.21213344564414685, 4.474530089224358, 3.5476553332085365]
        phoxgamma = [0.21409971979884468, 4.4665730308471785, 4.786179948808256]
        bs3linear = [-0.2375, 2]
        dsbsolinear = [-0.2375, 2]
        phoxlinear = [-0.1727, 1.734]
        
        if depth <= 4.25:
            return 1 
        if self.linker == 'BS3/DSS':
            tagcoefs = np.array([1.20875756e+03, 5.31961163e+00, 6.43465155e-04])
            lyscoefs = np.array([4.44470936e+02, 4.65135510e+00, 1.69863402e-03])
            if func(depth, *lyscoefs) > 0:
                return func(depth, *tagcoefs)/func(depth, *lyscoefs)
            else:
                return 0
#            if depth <= 8.25:
#                return linear(depth, *bs3linear)
#            else:
#                return gammasf(depth, *bs3gamma)
        elif self.linker == 'DSBSO':
            if depth <= 8.25:
                return linear(depth, *dsbsolinear)
            else:
                return gammasf(depth, *dsbsogamma)
        elif self.linker == 'PhoX':
            if depth <= 9.75:
                return linear(depth, *phoxlinear)
            else:
                return gammasf(depth, *phoxgamma)
            

    def cutoff(self):
        cutoffs = {'BS3/DSS':15, 'DSBSO':15, 'PhoX':16}
        if self.linker in cutoffs:        
            return cutoffs[self.linker]  
        else:
            print ('No information about linker. Using depth cutoff for BS3/DSS')
            return cutoffs['BS3/DSS']
        
    def depth(self, model):
        return model.residuedepths[f'{self.chainid}:{self.rnum}']
    
    def color(self, model):
        depth = self.depth(model)
        color = 'blue'
        
        if self.linker == 'BS3/DSS':
            if depth > 6.25:
                color = 'red'
        elif self.linker == 'DSBSO':
            if depth > 6.25:
                color = 'red'
        elif self.linker == 'PhoX':
            if depth > 6.25:
                color = 'red'
        else:
            if depth > 6.25:
                color = 'red'            
        return color
        
    def score(self, model):
        viol = False
        depth = self.depth(model) 
        if depth >= self.cutoff():
            score = -(depth/model.maxdepth)
            viol = True
        else:
            score = self.probability(depth)
        score *= self.weight
        return score, depth, viol
        
def getxlmslist(xlmslist, linker='BS3/DSS'):
    xllist = []
    unique = []
    with open(xlmslist, 'r') as f:
        for ln in f:
            link, linktuple = parsexlmsline(ln.strip(), linker=linker)
            if linktuple not in unique:
                unique.append(linktuple)
                xllist.append(link)
    return xllist

def parsexlmsline(line, linker='BS3/DSS', weight=1.0):
    tmp = line.split()
    if len(tmp) > 1:    #if there's a score
        weight = float(tmp[1])
        buf = tmp[0].split('|')
    else:
        buf = line.split('|')
        
    if len(buf) == 2:   # if monolink
        res1 = int(buf[0])
        ch1 = buf[1]
        site1 = Monolink(ch1, res1, linker=linker, weight=weight)
        return site1, (ch1, res1)
        
    elif len(buf) == 4:   # if crosslink
        res1 = int(buf[0])
        ch1 = buf[1]
        site1 = Monolink(ch1, res1, linker=linker)
        res2 = int(buf[2])
        ch2 = buf[3]
        site2 = Monolink(ch2, res2, linker=linker)
        if (ch1, res1) <= (ch2, res2):
            return Crosslink(site1, site2, weight=weight), (ch1, res1, ch2, res2)
        else:
            return Crosslink(site2, site1, weight=weight), (ch2, res2, ch1, res1)

def linkmetrics(structure, linktuple, depths, linkweight=1.0, linker='BS3/DSS'):
    # initialize structure model
    model = StructModel(structure, depths=depths)
    
    # initialize crosslink or monolink
    if len(linktuple) == 2:  #if a monolink
        link = Monolink(linktuple[1], linktuple[0], linker=linker, weight=linkweight)
    else:   #if a crosslink
        ml1 = Monolink(linktuple[1], linktuple[0], linker=linker)
        ml2 = Monolink(linktuple[3], linktuple[2], linker=linker)
        link = Crosslink(ml1, ml2, weight=linkweight)
    
    # compute score and depth/distance
    if model.inmodel(link): # link found in model
        score, d, viol = link.score(model)
        return score, d
    else:   # link not found
        print ("Link coordinates not found in model")
        return None, None
            
def gammasf(x, s, loc, scale): # gamma
    return scipy.stats.gamma.sf(x, s, loc=loc, scale=scale)

def logistic_function(x, k, x0, a):
    return (1+np.exp(k * (x - x0)))**-a

def linear(x, m, b):
    return (m*x)+b

def func(x, a, b, c):
    return (a * (x**-b)) + c


