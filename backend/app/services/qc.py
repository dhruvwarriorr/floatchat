"""ARGO quality-control service boundary.

The Rev. B architecture requires this stage to run after retrieval and before
anomaly scoring.  Filtering rules are intentionally not implemented until the
team freezes the accepted ARGO QC flags, adjusted-value precedence, data-mode
policy, and audit metadata against a reviewed dataset.
"""
