# rclups


## testing
```bash
cd mito
./download.sh

../rclups0.py -vd -n 3 -i *.fa.gz
```


rm Bacteria.fa; for f in *.fa.gz; do s=`echo $f | cut -f1 -d'.'`; echo $f $s; echo ">$s" >> Bacteria.fasta; zgrep -v ">" $f >> Bacteria.fasta; done
