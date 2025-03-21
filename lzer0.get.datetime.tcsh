#!/bin/tcsh
# created  by DZ (5 Apr 2024)
# recovers date and time from LZER0 data stream 
# tsch does not support error redirecting and socat causse a broken pipe at the 1st exit status
#
#********************  DEFAULTS ********************
#
set JOB = `basename $0`
set CURDIR = `pwd`

set LOGFILE = $HOME/log/$JOB.log
set lzer0Date = `socat tcp:localhost:2222 - | grep --line-buffered -a GNRMC | gawk 'BEGIN{FS="GNRMC"}; {print $2;exit}' | gawk 'BEGIN{FS=","} {print "20"substr($10,5,2)"/"substr($10,3,2)"/"substr($10,1,2)}'`
set lzer0Time = `socat tcp:localhost:2222 - | grep --line-buffered -a GNGGA | gawk 'BEGIN{FS=","}; {print substr($2,1,2)":"substr($2,3,2)":"substr($2,5,5);exit}'`
echo $lzer0Date $lzer0Time
