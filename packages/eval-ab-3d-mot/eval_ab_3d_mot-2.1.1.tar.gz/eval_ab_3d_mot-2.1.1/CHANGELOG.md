# 2.1.0

  - Add script `run-ab-3d-mot-with-clavia` to run the tracker consuming KITTI annotations.
  - Use `pure-ab-3d-mot==2.1.0`.
  - Update third-party development dependencies.

# 2.0.0

  - Use the AssociationQuality class from the package `association-quality-clavia`.

# 1.0.0

  - Added the module `association_quality` with an implementation of the classifier.


# 0.1.0

  - Creation.
  - Split the module `evaluation.py` into smaller modules.
  - Unit test the function `box_overlap` (originally `boxoverlap`).
  - Unit test the class `Stat` (originally `stat`).
  - Unit test the class `TrackData` (originally `tData`).
  - Capitalize the constant `num_sample_points` --> `NUM_SAMPLE_POINTS = 41.0`.
  - Remove the `dump` (text file stream) from the class `Stat`.
  - Rename `Stat.print_summary` to `Stat.get_summary`.
  - Remove plot functions from `Stat`.
  - Add the magic `TrackData.__repr__`.
  - Merge `loadGroundTruth` and `loadTracking` into `load_data`.
  - Abstain from loading data from text file (`scripts/KITTI/evaluate_tracking.seqmap.val`).
  - Make `TrackingEvaluation.getThresholds` a standalone function (`thresholds.get_thresholds`).
  - Simplify arguments of the `TrackingEvaluation.load_data`.
  - Test `TrackingEvaluation.reset()`.
  - Start testing `TrackingEvaluation.compute_3d_party_metrics`.
  - Tested all, many by defining smaller functions.
  - Added an argparse-based CLI.
  - Added rich-argparse raw-text formatter in CLI.
  - Added a script `run-ab-3d-mot` to run the AB3DMOT tracker (from `pure-ab-3d-mot` package).
  - Added a script `eval-ab-3d-mot-single-seq` to run the evaluator on results produced by `run-ab-3d-mot`.
  - Script `batch-run-ab-3d-mot` to run the AB3DMOT tracker for a set of detection sequences.
  - Using the progress bar from the `rich` package in `batch-run-ab-3d-mot`.
  - Added the `batch-eval-ab-3d-mot`.
  - Fixed the tracking output by adding more time stamps to the detection generator.


