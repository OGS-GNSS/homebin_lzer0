#!/usr/bin/env bash
# Script to start post processing elebaoration using rnx2rtkp
# created  by DZ (Jan. 2019)
# modified by DZ (Aug. 2022)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lzer0.config.sh"
#******************** Definizione delle variabili principali ********************
PATH="$PATH:/usr/sbin:/sbin:/usr/local/bin:/usr/bin:/bin:${LZERO_BIN_DIR}:." #fundamental to run  scripts inside cron without full path commands
#
# MAIN JOB VALUES
StarTime="$(date +%s)"
JOB="$(basename "$0")"
#
#********************  TUNING VARIABLES BEGIN ********************
STORAGE=${LZERO_STORAGE_MOUNT}
DUMPDIR=${LZERO_GNSS_DIR}
BINDIR=${LZERO_BIN_DIR}
TMPDIR=${LZERO_TMP_DIR}
RTKCFGFILE=${LZERO_RNX2RTKP_CONFIG} 	# it includes all the post-processing elaboration options
CRDFILE=${LZERO_STATION_POS_FILE}		# it includes apriori coordinates of different GNSS sites (ROVER inluded)
CFGFILE=${LZERO_SITE_CONFIG}			# it includes ROVER and MASTER GNSS site names to be used in the elaboration
#********************  TUNING VARIABLES END  ********************
#
# DEFAULT PARAMS
SITE="" # ROVER GNSS SITE NAME (default empty string)
REFV="" # ROVER GNSS SITE NAME (default empty string)
YEAR="$(date +%Y)"
DOY="$(date +%j)"
HOUR="$(date +%H)"
RATE=30 	#sampling rate
FORCE="N" 	# do not overwrite existing results
FIXLIM=0.10 	# to be used for statistic check
if [[ -e "$CFGFILE" ]]; then
	SITE="$(grep -v "#" "$CFGFILE" | gawk 'BEGIN{FS=":"} {if ($1=="rover name") {print $2}}' | tr -d " " | tr "a-z" "A-Z")"
	if [[ "$SITE" == "" ]]; then
		SITE="UNKN" # ROVER site name
	fi
	REFV="$(grep -v "#" "$CFGFILE" | gawk 'BEGIN{FS=":"} {if ($1=="master name") {print $2}}' | tr -d " " | tr "a-z" "A-Z")"
fi
#
# To avoid problems with the last session X for Hour 00
if [[ "$HOUR" == "00" || "$HOUR" == "0" ]]; then
        HOUR=24
        if (( 10#$DOY == 1 )); then
                # it happens the 1st of Jannuary at midnight
                decDoys=-1
        else
                # it happens in all other cases
                decDoys=$((10#$DOY - 2))
        fi
        DOY="$(date -d "$decDoys days ${YEAR}-01-01" +%j)"
        YEAR="$(date -d "$decDoys days ${YEAR}-01-01" +%Y)"
else
	:
fi
#
# check command line params. First one is used to set the site name, second one for brand
while [[ $# -gt 0 ]]; do
        case "$1" in
                "-r")
                        # Rover site name
                        shift
                        SITE="$(echo "$1" | tr 'a-z' 'A-Z')"
                        ;;
                "-m")
                        # Master site name
                        shift
                        REFV="$(echo "$1" | tr 'a-z' 'A-Z')"
                        ;;
                "-sr")
                        # Sampling rate
                        shift
                        RATE="$1"
                        ;;
                "-y")
                        # Year
                        shift
                        YEAR="$1"
                        ;;
                "-d")
                        # DOY
                        shift
                        DOY="$1"
                        ;;
		"-h")
                        # HOUR OF DAY
                        shift
                        HOUR="$1"
                        ;;
                "-w")
                        #  overwrite old file
                        FORCE="Y"
                        ;;
                *)
                        shift
                        ;;
        esac
        shift
done
site="$(echo "$SITE" | tr 'A-Z' 'a-z')"
refv="$(echo "$REFV" | tr 'A-Z' 'a-z')"
SES="$(echo "$HOUR" | hr2ses)"
ses="$(echo "$SES" | tr 'A-Z' 'a-z')"
HOURONDISK="$(echo "$HOUR" | awk ' {if (length($0) <=1) print 0$0; else print $0}')"
DOYONDISK="$(echo "$DOY" | awk '{if (length($0) == 1) print "00"$0} {if (length($0) == 2) print "0"$0} {if (length($0) == 3) print $0}')"
YR="$(echo "$YEAR" | awk '{print substr($0,3,2)}')"
#
# Building full date
tempDOY=$((10#$DOY - 1))
FULLDATE="$(date -d "$tempDOY days ${YEAR}-01-01" +"%Y.%m.%d")"
#
# Check TMPDIR
if [[ ! -e "${TMPDIR}" ]]; then
	mkdir -p "${TMPDIR}"
fi
rm -fR "${TMPDIR}"/* &> /dev/null # Cleaning tmp dir at the beginning
#
# Preparing filenames and dirs
finalDir=${DUMPDIR}/${YEAR}/${DOYONDISK}/1Hpp
pfixObs=${DOYONDISK}${ses}.${YR}o # RINEX observations	(e.g. 342a.18o)
pfixNav=${DOYONDISK}${ses}.${YR}n # GPS RINEX NAV		(e.g. 342a.18n)
pfixGlo=${DOYONDISK}${ses}.${YR}g # GLONASS RINEX NAV		(e.g. 342a.18g)
pfixHna=${DOYONDISK}${ses}.${YR}h # HNAV			(e.g. 342a.18h)
pfixQna=${DOYONDISK}${ses}.${YR}q # QNAV			(e.g. 342a.18q)
pfixLna=${DOYONDISK}${ses}.${YR}l # LNAV			(e.g. 342a.18l)
pfixSbs=${DOYONDISK}${ses}.${YR}s # SBAS messages		(e.g. 342a.18s)
tgtPos=${SITE}.${FULLDATE}.${DOYONDISK}.${ses}.pp.pos	# POS	(e.g. BRU1.2019.01.11.011.a.pp.pos)
tgtPosM=${SITE}.${FULLDATE}.${DOYONDISK}.${ses}.pp.mean.pos	# POS  (e.g. BRU1.2019.01.11.011.a.pp.mean.pos)
#
# Check finalDir
if [[ ! -e "${finalDir}" ]]; then
	mkdir -p "${finalDir}"
fi

run_processing() {
	echo "Recovering ${SITE} and ${REFV} data into ${TMPDIR}..."
	echo "lzer0.get.hourlygnss -s ${SITE} -d ${DOY} -h ${HOUR} -sr $RATE"
	lzer0.get.hourlygnss -s "${SITE}" -d "${DOY}" -h "${HOUR}" -sr "$RATE"
	echo "lzer0.get.hourlygnss -s ${REFV} -d ${DOY} -h ${HOUR} -sr $RATE -p"
	lzer0.get.hourlygnss -s "${REFV}" -d "${DOY}" -h "${HOUR}" -sr "$RATE" -p
	#
	# elaboration and  moving result to add
	cd "${TMPDIR}" || exit 1
	echo "Doing rnx2rtkp elaboration..."
	# rnx2rtkp command option syntax is  -k for config file and then
	# rover obs, master obs,  rover gps, rover glo, master gps, master glo
	echo "rnx2rtkp -k $RTKCFGFILE ${site}${pfixObs} ${refv}${pfixObs} ${site}${pfixNav} ${site}${pfixGlo} > ${tgtPos}"
	rnx2rtkp -k "$RTKCFGFILE" "${site}${pfixObs}" "${refv}${pfixObs}" \
		"${site}${pfixNav}" "${site}${pfixGlo}" > "${tgtPos}"
	echo "Copying results to ${finalDir}..."
	echo "cp ${tgtPos} ${finalDir}"
	cp "${tgtPos}" "${finalDir}"
	#
	# doing mean values
	echo "Doing mean values..."
	echo "lzer0.get.posavg -f ${finalDir}/${tgtPos} -s ${SITE} > ${finalDir}/${tgtPosM}"
	lzer0.get.posavg -f "${finalDir}/${tgtPos}" -s "${SITE}" > "${finalDir}/${tgtPosM}"
	#
	# doing some statistics
	echo "Doing some statistics..."
	echo "DATE O/E% OTH% STD% FLT% FIX% FFIX%" | gawk '{printf "%-10s %6s %6s %6s %6s %6s %6s\n",$1,$2,$3,$4,$5,$6,$7}' > "${finalDir}/${tgtPos}.stat"
	echo "lzer0.get.posstat -f ${finalDir}/${tgtPos} -s ${SITE} -t $FIXLIM > ${finalDir}/${tgtPos}.stat"
	lzer0.get.posstat -f "${finalDir}/${tgtPos}" -s "${SITE}" -c "$CRDFILE" -t "$FIXLIM" > "${finalDir}/${tgtPos}.stat"
	exit
}

#
# Check il results pos file in post processing mode is already there
if [[ ! -e "${finalDir}/${tgtPos}" ]]; then
	run_processing
else
	sizeTgt="$(stat -c %s "${finalDir}/${tgtPos}")"
	if [[ "${FORCE}" == "Y" || "$sizeTgt" == 0 ]]; then
		run_processing
	else
		echo "File already present. Use -w option to update it."
		exit
	fi
fi
