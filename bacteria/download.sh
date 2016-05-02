#!/bin/bash

accessions="AE005674.1|Shi-fle-2a
CP001383.1|Shi-fle-17
CP001671.1|Ecoil-ABU
CP000468.1|Ecoil-APEC
AE009952.1|Yer-KIM
AL590842.1|Yer-CO92
CP001593.1|Yer-Z176003
CP001585.1|Yer-D106004
AM295250.1|Sta-car
AE015929.1|Sta-epi-AT
AP006716.1|Sta-hae
CP001837.1|Sta-lug
CP001151.1|Rho-KD131
CP000578.1|Rho-ATCC
AM260480.1|Ral-H16
CP000091.1|Ral-JMP
CP001598.1|Bac-A0248
AE016879.1|Bac-Ames
CP001215.1|Bac-CDC
AE017225.1|Bac-Stern
CP000048.1|Bor-hermsii
CP000976.1|Bor-dut
CP000049.1|Bor-tur
CP000993.1|Bor-recu
CP000246.1|Clo-per-ATCC
CP000312.1|Clo-per-SM101
BA000016.3|Clo-per-13
CP000527.1|Des-vul-DP4
CP002297.1|Des-vul-RCH1
AE017285.1|Des-vul-Hild"

www="http://www.ebi.ac.uk/ena/data/view/display=fasta&download=fasta&"
for e in $accessions; do acc=`echo $e | cut -f1 -d'|'`; name=`echo $e | cut -f2 -d'|'`; echo `date` $acc $name; curl -s $www$acc | gzip > $name.fa.gz; done; date

