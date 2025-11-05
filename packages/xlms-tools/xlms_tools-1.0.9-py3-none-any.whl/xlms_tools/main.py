# This file is part of the xlms-tools package
#
# Copyright (c) 2023 - Topf Lab, Leibniz-Institut für Virologie
# and Center for Data and Computing in Natural Sciences, Universität Hamburg
# Hamburg, Germany.
#
# This module was developed by:
#   Karen Manalastas-Cantos    <karen.manalastas-cantos AT cssb-hamburg.de>

import argparse
import os.path
import os
import time
from xlms_tools.score import *
from xlms_tools.printing import *
from xlms_tools.visualization import *
from xlms_tools.simulate import outputSASDs

def main():
    parser = argparse.ArgumentParser(description='Score protein structures by their concordance with crosslinking mass spectrometry (XL-MS) data')
    parser.add_argument('pdb', metavar='PDB', type=str, nargs='+',
                    help='PDB file/s of protein: PDB or mmCIF format')
    parser.add_argument('-m', '--mode', type=str, choices=['score', 'depth', 'sim'], default='score',
                    help='score: compute model score with respect to XL-MS data; depth: compute residue depths; sim: simulate crosslinks and monolinks')
    parser.add_argument('-s','--score', type=str, choices=['old', 'new'], default='new',
                    help='old: use Total Residue Depth (RD) for monolinks; Matched and      Nonaccessible Crosslinks (MNXL) for crosslinks; \nnew: use Monolink Probability (MP) for monolinks, Crosslink Probability (XLP) for crosslinks')
    parser.add_argument('-l', '--list', type=str,
                    help='[score mode only] list of crosslinks and monolinks')
    parser.add_argument('-r', '--recov', type=str,
                    help='[sim mode only] recovery rate for crosslink/monolink simulation')
    parser.add_argument('--linker', type=str, choices=['BS3/DSS', 'DSBSO', 'PhoX'], 
                    default='BS3/DSS',
                    help='Crosslinking reagent used')
    parser.add_argument('--name', type=str, default='',
                    help='Run name. Output files will use this as a base filename')
    parser.add_argument('--color', type=str, default='lightgray',
                    help='color name or hexcode recognizable by ChimeraX, to color the protein in visualization')
    parser.add_argument('-q', '--quiet', action='store_true',
                    help='run with minimal stdout and output files (scores only, no visualization)')

    args = parser.parse_args()
    verbose = not args.quiet

    printsoftwareheader()

    if args.mode == 'score':
        print ('Scoring models...')
        start = time.time()
        
        # parse xl-ms file
        xllist = getxlmslist(args.list, args.linker)

        # set run name
        if len(args.name) > 0:
            visdir = args.name
        else:
            visdir = os.path.basename(args.list)[:-4]

        # if verbose, set up ChimeraX visulization
        if verbose:
            if not os.path.exists(visdir):
                os.mkdir(visdir)
            cxcptr = printcxc(args.pdb, visdir=visdir, color=args.color)

        # score each structure model
        bestmodel = ""
        bestscore = -1000
        for i,model in enumerate(args.pdb):
            struct = StructModel(model, verbose=verbose)
            struct.scoremodel(xllist, verbose=verbose)
            
            # open score output file
            if i == 0:
                f = openscorefile(struct, outname=visdir+"_scores")
                
            struct.printscores(f)
            struct.printindivscores(prefix=visdir)
            if verbose:
                struct.printchimeraxfiles(visdir, cxcptr, xllist, i+1)

            # get best scoring model
            iscore = struct.avexlscore
            if iscore == 0:
                iscore = struct.avemlscore
            if iscore > bestscore:
                bestscore = iscore
                bestmodel = model
                
        f.close()   # close score output file
        
    
        print ("\n***\n\nBEST SCORING MODEL:", bestmodel)
        print (f"XLP/MP scores are in {visdir}_scores.tsv")
        if verbose:
            print (f"Open {visdir}.cxc with ChimeraX to visualize the models with crosslinks")
        print (f"Total time elapsed: {time.time()-start:.3f}s\n")    

    elif args.mode == 'depth':
        for i in args.pdb:
            struct = StructModel(i, verbose=verbose)
            struct.outputdepth()
        
    elif args.mode == 'sim':
        for i in args.pdb:
            outputSASDs(i, linker=args.linker)

    else:
        print("Mode '", args.mode, "' not yet supported")

    print("\nIf you use xlms-tools, please cite:")
    print("Manalastas-Cantos, K., Adoni, K. R., Pfeifer, M., Märtens, B., Grünewald, K., Thalassinos, K., & Topf, M. (2024). Modeling flexible protein structure with AlphaFold2 and cross-linking mass spectrometry. Molecular & Cellular Proteomics. https://doi.org/10.1016/j.mcpro.2024.100724\n")

if __name__ == '__main__':
    main()