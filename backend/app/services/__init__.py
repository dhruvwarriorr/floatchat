"""Domain service boundaries used by the API routes.

For anomaly requests the target order is data retrieval, QC filtering,
QC-passed aggregation/anomaly scoring, evidence grading, then provenance-panel
composition.  Structural modules do not imply scientific implementation.
"""
