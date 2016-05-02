#!/bin/bash

accessions="AF285261.1|CANAL
AJ511533.1|CANGA
AY962591.1|CANME
AY962590.1|CANOR
X74411.6|CANPA
GU126492.1|CANSU
KR260476|SACCE"

www="http://www.ebi.ac.uk/ena/data/view/display=fasta&download=fasta&"
for e in $accessions; do acc=`echo $e | cut -f1 -d'|'`; name=`echo $e | cut -f2 -d'|'`; echo `date` $acc $name; curl -s $www$acc | gzip > $name.fa.gz; done; date

