First workflow attempt interrupted because evaluator's refresh helper incorrectly
waited for the notice to become hidden after refreshing. The application leaves
“Refreshing project…” visible after Refresh re-enables. The initial failed-check
screenshots remain here; the corrected helper waits for the control to re-enable.
Subsequent results are saved in workflow-rerun. No product code changed.
