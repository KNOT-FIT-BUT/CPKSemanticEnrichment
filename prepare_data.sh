#!/bin/bash

python2 wiki_stats_to_KB.py > KBstats.all
python2 metrics_to_KB.py -k KBstats.all | sed '/^\s*$/d' > KBstatsMetrics.all


#echo -n "VERSION=" | cat - VERSION HEAD-KB KBstatsMetrics.all > KB-HEAD.all

rm KBstats.all wiki_stats
