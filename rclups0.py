#!/usr/bin/env python
desc="""Report distance matrix between proteins. 

Dependencies:
- Biopython, numpy & scipy
"""
epilog="""Author: l.p.pryszcz@gmail.com
Bratislava, 28/04/2016
"""

import os, sys, gzip
import numpy as np
from datetime import datetime
from Bio import SeqIO
from multiprocessing import Pool
from scipy.cluster import hierarchy
import matplotlib.pyplot as plt

aa2i = {'A': 0, 'R': 1, 'N': 2, 'D': 3, 'C': 4, 'Q': 5, 'E': 6, 'G': 7, 'H': 8, 'I': 9, 'L': 10, 'K': 11, 'M': 12, 'F': 13, 'P': 14, 'S': 15, 'T': 16, 'W': 17, 'Y': 18, 'V': 19}
dna2i = {'A': 0, 'C': 1, 'G': 2, 'T': 3, 'a': 0, 'c': 1, 'g': 2, 't': 3}
a2i = dna2i
bases = len(set(a2i.values()))

# Grantham R (1974) Science 185:862-864.
Polarity = {'A': 8.1, 'R': 10.5, 'N': 11.6, 'D': 13.0, 'C': 5.5, 'Q': 10.5, 'E': 12.3, 'G': 9.0, 'H': 10.4, 'I': 5.2, 'L': 4.9, 'K': 11.3, 'M': 5.7, 'F': 5.2, 'P': 8.0, 'S': 9.2, 'T': 8.6, 'W': 5.4, 'Y': 6.2, 'V': 5.9}
Volume   = {'A': 31.0, 'R': 124.0, 'N': 56.0, 'D': 54.0, 'C': 55.0, 'Q': 85.0, 'E': 83.0, 'G': 3.0, 'H': 96.0, 'I': 111.0, 'L': 111.0, 'K': 119.0, 'M': 105.0, 'F': 132.0, 'P': 32.5, 'S': 32.0, 'T': 61.0, 'W': 170.0, 'Y': 136.0, 'V': 84.0}
# Zhao, G., London E (2006) Protein Sci. 15:1987-2001.
Transmembrane = {'A': 0.38, 'R': -2.57, 'N': -1.62, 'D': -3.27, 'C': -0.3, 'Q': -1.84, 'E': -2.9, 'G': -0.19, 'H': -1.44, 'I': 1.97, 'L': 1.82, 'K': -3.46, 'M': 1.4, 'F': 1.98, 'P': -1.44, 'S': -0.53, 'T': -0.32, 'W': 1.53, 'Y': 0.49, 'V': 1.46}

polarity = {aa: (v-np.mean(Polarity.values()))/np.std(Polarity.values()) for aa, v in Polarity.iteritems()}
volume   = {aa: (v-np.mean(Volume.values()))/np.std(Volume.values())     for aa, v in Volume.iteritems()}
transmembrane = {aa: (v-np.mean(Transmembrane.values()))/np.std(Transmembrane.values()) for aa, v in Transmembrane.iteritems()}

def get_power_spectrum(seq, features):
    """Return power spectrum for given feature.
    
    Consider normalisation by seq length.
    """
    # DFT - here I'm looking only at first dimension
    A = np.fft.fft([features[aa] for aa in seq if aa in features])
    # PS
    ## Get the first half of the transform (since it's symmetric) - make sure it's good
    PS = np.abs(A[1:(len(seq)+1)/2])**2
    #PS = np.sum(PS) #/len(seq)
    PS = [len(seq)*np.sum(PS**j)/len(seq)**j for j in range(1,4)]
    return PS

def get_coords0(arg):
    """Return x, y coordinates for given sequence"""
    name, seq = arg
    x = get_power_spectrum(seq, polarity)
    y = get_power_spectrum(seq, volume)
    z = get_power_spectrum(seq, transmembrane)
    return name, x + y + z

def get_coords(arg):
    """Alternative approach
    
    Hoang (2015) A new method to cluster DNA sequences using Fourier power spectrum
    """
    name, seq = arg
    a = np.zeros((bases, len(seq)), dtype=int)
    c = np.zeros(bases)
    for i, aa in enumerate(seq):
        if aa not in a2i:
            continue
        # update
        a[a2i[aa]][i] = 1
        c[a2i[aa]]   += 1
    # DFT
    A = [np.fft.fft(_a) for _a in a]
    # PS: only the first half : 
    PS = [np.abs(_A[1:(len(seq))/2])**2 for _A in A] #; print PS.shape
    # normalised moments
    MV = []
    for i, ps in enumerate(PS):
        for j in range(1, 4):
            mv = c[i]*(len(seq)-c[i])*np.sum(ps**j)/(c[i]**j*((len(seq)-c[i])**j))
            MV.append(mv)
    return name, MV
    
def fasta_generator(files, verbose):
    """Return entry id and sequence"""
    for i, handle in enumerate(files, 1):
        if verbose:
            sys.stderr.write(' %s %s    \n'%(i, handle.name))
        name = ".".join(handle.name.split('.')[:-1])
        if handle.name.endswith('.gz'):
            handle = gzip.open(handle.name)
            name = ".".join(handle.name.split('.')[:-2])
        seqs = []
        for r in SeqIO.parse(handle, 'fasta'):
            #yield r.description, str(r.seq)
            seqs.append(str(r.seq))
        seq = "".join(seqs)
        name += "_%s"%len(seq)
        yield name, seq
        
def fasta2clusters(files, out, nproc, dendrogram, verbose):
    """Report clusters"""
    if verbose:
        sys.stderr.write('Parsing %s input(s)...\n'%len(files))
    # get iterator
    iterator = fasta_generator(files, verbose)
    # start pool of processes
    p = Pool(nproc)
    ytdist, labels = [], []
    for i, (name, coords) in enumerate(p.imap(get_coords, iterator), 1):
        #if verbose and not i%1000:
        sys.stderr.write(' %s %s       \n'%(i, name))
        #fields = name.split()
        #name = " ".join((fields[0].split('_')[-1], fields[1].split(':')[-1], fields[4].split(':')[-1]))
        # store
        labels.append(name)
        ytdist.append(coords)
        # report
        out.write("%s\t%s\n"%(name, "\t".join(map(str, coords))))

    # report distances
    dists = np.zeros((i,i))
    for i1 in range(i-1):
        v1 = np.array(ytdist[i1])#; print len(v1)
        for i2 in range(i1, i):
            v2 = np.array(ytdist[i2])
            d = np.linalg.norm(v1-v2)
            dists[i1][i2] = d
            dists[i2][i1] = d
    np.savetxt('out.txt', dists, delimiter='\t', header='\t'.join(labels))
            
    if verbose:
        sys.stderr.write('%s entries processed!\n'%i)

    if dendrogram:
        # UPGMA http://docs.scipy.org/doc/scipy-0.17.0/reference/generated/scipy.cluster.hierarchy.linkage.html
        Z = hierarchy.linkage(ytdist, method='average', metric='euclidean') 
        plt.figure()
        dn = hierarchy.dendrogram(Z, labels=labels, orientation='right')
        plt.show()
        
def main():
    import argparse
    usage   = "%(prog)s -v" #usage=usage, 
    parser  = argparse.ArgumentParser(description=desc, epilog=epilog, \
                                      formatter_class=argparse.RawTextHelpFormatter)
  
    parser.add_argument('--version', action='version', version='1.0b')   
    parser.add_argument("-v", "--verbose", default=False, action="store_true",
                        help="verbose")    
    parser.add_argument("-i", "--input", nargs="+", type=file, default=[sys.stdin,], 
                        help="input stream [stdin]")
    parser.add_argument("-o", "--output",    default=sys.stdout, type=argparse.FileType('w'), 
                        help="output stream   [stdout]")
    parser.add_argument("-d", "--dendrogram", action='store_true', default=False, 
                        help="plot dendrogram")
    parser.add_argument("-n", "--nproc", default=1, type=int, 
                        help="no. of processed to run [%(default)s]")
    
    o = parser.parse_args()
    if o.verbose:
        sys.stderr.write("Options: %s\n"%str(o))
        
    fasta2clusters(o.input, o.output, o.nproc, o.dendrogram, o.verbose)

if __name__=='__main__': 
    t0 = datetime.now()
    try:
        main()
    except KeyboardInterrupt:
        sys.stderr.write("\nCtrl-C pressed!      \n")
    except IOError as e:
        sys.stderr.write("I/O error({0}): {1}\n".format(e.errno, e.strerror))
    dt = datetime.now()-t0
    sys.stderr.write("#Time elapsed: %s\n"%dt)


""" 
% Tung Hoang a , Changchuan Yin a , Hui Zheng a , Chenglong Yu b,c , Rong Lucy He d ,Stephen S.-T. Yau (2015) A new method to cluster DNA sequences using Fourier power spectrum

function [v] = GetMomentVectorPS(seq)
%UNTITLED2 Summary of this function goes here
%   Detailed explanation goes here

n=length(seq);

%Binary indicator sequences of A, C, G, T (each value will be either 1 or 0
%; 1 if that nucleotide appears in that position and 0 otherwise)
uA=zeros(1, n);
uC=zeros(1, n);
uG=zeros(1, n);
uT=zeros(1, n);

%Sequences' length (of A, C, G, T respectively)
nA=0;
nC=0;
nG=0;
nT=0;

%Get the binary indicator sequences and their lengths
for i=1:n
    nu=seq(i);
   switch upper(nu)
      case {'A'}
           uA(i)=1;
           uC(i)=0;
           uG(i)=0;
           uT(i)=0;
           nA=nA+1;
      case {'C'}
           uC(i)=1;
           uA(i)=0;
           uG(i)=0;
           uT(i)=0;
           nC=nC+1;     
      case {'G'}
           uG(i)=1;
           uA(i)=0;
           uC(i)=0;
           uT(i)=0;
           nG=nG+1;
      case {'T'}
           uT(i)=1;
           uA(i)=0;
           uC(i)=0;
           uG(i)=0;
           nT=nT+1;
   end
end

%Discrete Fourier Transforms
UA=fft(uA);   
UC=fft(uC);
UG=fft(uG);
UT=fft(uT);

%Exclude the first term
UA(1)=[];
UC(1)=[];
UG(1)=[];
UT(1)=[];

% Get the first half of the transform (since it's symmetric)
m=floor((n-1)/2);
UA1=UA(1:m);
UC1=UC(1:m);
UG1=UG(1:m);
UT1=UT(1:m);

%Power spectrums
PSA=abs(UA).^2;     
PSC=abs(UC).^2;     
PSG=abs(UG).^2;     
PST=abs(UT).^2;     

%Normalized moments
MA=zeros(1,3);   
MC=zeros(1,3);
MG=zeros(1,3);
MT=zeros(1,3);

%Moment vector
for j=1:3
   MA(j)=(nA*(n-nA))*sum(PSA.^j)/(nA^(j)*(n-nA)^(j)); 
   MC(j)=(nC*(n-nC))*sum(PSC.^j)/(nC^(j)*(n-nC)^(j)); 
   MG(j)=(nG*(n-nG))*sum(PSG.^j)/(nG^(j)*(n-nG)^(j)); 
   MT(j)=(nT*(n-nT))*sum(PST.^j)/(nT^(j)*(n-nT)^(j)); 
end


v=[MA(1), MC(1), MG(1), MT(1), MA(2), MC(2), MG(2), MT(2), MA(3), MC(3), MG(3), MT(3)];


end
"""