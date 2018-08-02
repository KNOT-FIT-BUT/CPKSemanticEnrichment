#!/bin/bash

python2 prepare_kb_to_stats_and_metrics.py < KB_cs.all | python2 wiki_stats_to_KB.py > KBstats.all
python2 metrics_to_KB.py -k KBstats.all | sed '/^\s*$/d' > KBstatsMetrics.all


echo -n "VERSION=" | cat - VERSION HEAD-KB KBstatsMetrics.all > KB-HEAD.all

#rm KBstats.all wiki_stats
