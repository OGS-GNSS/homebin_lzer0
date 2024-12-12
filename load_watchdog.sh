!/bin/bash
LOAD=`uptime |awk '{print $NF}'`
LOADCOMP=`echo $LOAD \> 10 |bc -l`
if [ $LOADCOMP -eq 1 ]
then shutdown -r 0
fi
