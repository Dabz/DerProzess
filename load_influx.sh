#! /bin/sh
#
# load_influx.sh
# Copyright (C) 2019 gaspar_d </var/spool/mail/gaspar_d>
#
# Distributed under terms of the MIT license.
#

for file in `find results* -name '*annota*'`; do 
	curl -i -XPOST 'http://localhost:8086/write?db=prozess' --data-binary @$file; 
done

for file in `find results* -name '*influx*'`; do 
	curl -i -XPOST 'http://localhost:8086/write?db=prozess' --data-binary @$file; 
done
