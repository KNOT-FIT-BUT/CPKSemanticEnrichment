#!/bin/bash
# Author: Volf Tomáš, ivolf@fit.vutbr.cz



####################     DEFAULTS      ####################
LANG="cs"

OUTDIR="$(dirname $0)/data"

UPLOAD_USER=$USER
UPLOAD_HOST=athena3.fit.vutbr.cz
UPLOAD_ROOTDIR=/mnt/knot/www/NAKI_CPK/CPKSemanticEnrichment

RUN_CREATE=false
RUN_UPLOAD=false



####################     FUNCTIONS     ####################
function help() {
  echo
  echo -e "Usage: ./$(basename ${0}) [<parameter> [<value>]] ..."
# TODO: few words about this tool
  echo -e "\t-h                         Print help"
  echo -e "\t-c                         Create knowledgebase"
  echo -e "\t-o <output dir>            Change output directory to <output dir>"
  echo -e "\t                           Default: ${OUTDIR}"
  echo -e "\t-u [<connection string>]   Upload output files to remote server via"
  echo -e "\t                           <connection string>. Default value is"
  echo -e "\t                           described below."
  echo
  echo "How to use <connection string>:"
  echo -e "\tBase form of connection string is <login>@<hostname>:<path to save>."
  echo -e "\tDefault value is: ${$UPLOAD_USER}@${UPLOAD_HOST}:${UPLOAD_ROOTDIR} ."
  echo -e "\tBecause any part of connection string can be omitted, following "
  echo -e "\tshortened variants of <connection string> are allowed:"
  echo -e "\t\t<login>"
  echo -e "\t\t@<hostname>"
  echo -e "\t\t:<path to save>"
  echo -e "\t\t<login>@<hostname>"
  echo -e "\t\t<login>:<path to save>"
  echo -e "\t\t@<hostname>:<path to save>"
}



function init() {
  LAUNCHDIR=$PWD
  
  cd `dirname $0`
  
  parseArgs "$@"

  mkdir -p "${OUTDIR}"
  
  F_HEAD="./data/in/KB-HEAD_${LANG}.tsv"
  F_OUT_VERSION="${OUTDIR}/KB-VERSION_${LANG}.info"
  F_OUT_KB="${OUTDIR}/KB_${LANG}.tsv"
}



function parseArgs() {
  local arg
  while getopts ":cho:u" arg
  do
    case ${arg} in
      h )
          help
          exit
        ;;

      c )
          RUN_CREATE=true
        ;;

      o )
          OUTDIR="${LAUNCHDIR}/${OPTARG}"
        ;;

      u )
          RUN_UPLOAD=true
          
          local TMP_OPTARG=${@:$OPTIND:1}
          if test "${TMP_OPTARG:0:1}" != "-"
          then
            OPTIND=$((OPTIND + 1))

            local TMP_USERHOST=${TMP_OPTARG%%:*}
            local TMP_USER=${TMP_USERHOST%%@*}
            local TMP_HOST=${TMP_USERHOST##*@}
            local TMP_ROOTDIR=${TMP_OPTARG#*:}

            if test "${TMP_USER}" != ""
            then
                UPLOAD_USER=$TMP_USER
            fi
            
            if test "${TMP_HOST}" != "${TMP_USER}"
            then
                UPLOAD_HOST=$TMP_HOST
            fi

            if test "${TMP_ROOTDIR}" != "${TMP_USERHOST}"
            then
                UPLOAD_ROOTDIR=$TMP_ROOTDIR
            fi
          fi
        ;;

      :)
          echo -e "ERROR: Missing argument for option \"-${OPTARG}\".\n" >&2
          help >&2
          exit 2
        ;;

      \? )
          echo -e "ERROR: Invalid option \"-${OPTARG}\".\n" >&2
          help >&2
          exit 1
        ;;
    esac
  done

  # no argument was given
  if test $OPTIND -eq 1
  then
    echo -e "ERROR: Missing some option - choose at least one.\n" >&2
    help >&2
    exit 1
  fi

  # remove args parsed by getopts
  shift $((OPTIND - 1))
}



function createKB() {
  if ! $RUN_CREATE
  then
    return
  fi
  
  mkdir -p "./data/in/" "./data/tmp"
  
  local INPUT_RESULTCODE=0
  wget -nv "http://knot.fit.vutbr.cz/NAKI_CPK/CPKSemanticEnrichment/tmp_base/KB-HEAD_${LANG}.tsv" -O "${F_HEAD}" || INPUT_RESULTCODE=$((INPUT_RESULTCODE + $?))
  wget -nv "http://knot.fit.vutbr.cz/NAKI_CPK/CPKSemanticEnrichment/tmp_base/KBbasic_${LANG}.tsv" -O "./data/in/KBbasic_${LANG}.tsv" || INPUT_RESULTCODE=$((INPUT_RESULTCODE + $?))
  wget -nv "http://knot.fit.vutbr.cz/NAKI_CPK/CPKSemanticEnrichment/tmp_base/wiki_stats_${LANG}.tsv" -O "./data/in/wiki_stats_${LANG}.tsv" || INPUT_RESULTCODE=$((INPUT_RESULTCODE + $?))
  
  if test $INPUT_RESULTCODE -ne 0
  then
    echo -e "\nERROR: At least one of input files could not be found." >&2
    exit 100
  fi
  
  local F_STATS="./data/tmp/KBstats_${LANG}.tsv"
  local F_STATSMETRICS="./data/tmp/KBstatsMetrics_${LANG}.tsv"
  
  eval python2 wiki_stats_to_KB.py > "${F_STATS}"
  python2 metrics_to_KB.py -k "${F_STATS}" | sed '/^\s*$/d' > "${F_STATSMETRICS}"

  date "+%s" >"${F_OUT_VERSION}"
  
  echo -n "VERSION=" | cat "${F_OUT_VERSION}" "${F_HEAD}" "${F_STATSMETRICS}" > "${F_OUT_KB}"
}



function checkSshError() {
  if test $? -ne 0
  then 
    echo "ERROR: while uploading KB to ${UPLOAD_HOST}." >&2
    exit 299
  fi
}



function uploadKB() {
  if ! $RUN_UPLOAD
  then
    return
  fi
  
  # check if output files exist
  if ! test -r "${F_OUT_VERSION}" || ! test -r "${F_OUT_KB}"
  then
    echo "ERROR: Could not find output files. Use argument \"-o\" to specify directory of output files or create knowledgebase by argument \"-c\"." >&2
    exit 200
  fi
  
  local SSH_CONNSTR="${UPLOAD_USER}@${UPLOAD_HOST}"
  echo $SSH_CONNSTR
  local VERSION=`cat ${F_OUT_VERSION}`
  
  local DIRNAME="${UPLOAD_ROOTDIR}/KB_${LANG}/KB_${LANG}_${VERSION}"
  echo "Creating directory for KB: ${DIRNAME}"
  ssh "${SSH_CONNSTR}" mkdir -p "${DIRNAME}"
  checkSshError
  
  echo "Copying KB"
  scp "${F_OUT_KB}" "${SSH_CONNSTR}:${DIRNAME}"
  checkSshError
  
  echo "Copying version info of KB"
  scp "${F_OUT_VERSION}" "${SSH_CONNSTR}:${UPLOAD_ROOTDIR}"
  checkSshError
}



####################     MAIN          ####################
init "$@"
createKB
uploadKB
