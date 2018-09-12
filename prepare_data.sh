#!/bin/bash

set -o pipefail

# python2 prepare_kb_to_stats_and_metrics.py < KB_cs.all | python2 check_columns_in_kb.py --cat | python2 wiki_stats_to_KB.py > KBstats.all &&
# python2 metrics_to_KB.py -k KBstats.all | sed '/^\s*$/d' > KBstatsMetrics.all &&
echo -n "VERSION=" | cat - VERSION HEAD-KB KBstatsMetrics.all > KB-HEAD.all
exit_status=$?

#rm KBstats.all wiki_stats

exit $exit_status

