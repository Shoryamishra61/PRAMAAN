# FECL-v4 TEST freeze contract

This file defines the process; it is not evidence that a freeze or TEST run already occurred.

1. Generate and validate all five splits.
2. Run TRAIN/DEV only and select architecture/hyperparameters.
3. Fit calibration, CRC and OOD references on CALIBRATION only.
4. Generate the DEV/CALIBRATION tournament artifact.
5. Hash every protocol, code, dataset, model, schema and calibration input into an immutable freeze.
6. Verify TEST/OOD hashes without parsing their case contents in the training process.
7. Run TEST once with explicit `--confirm-final-test`.
8. Atomically write the result and a separate append-only receipt containing start/end time, freeze
   digest, result digest, process outcome and `test_execution_index: 1`.
9. Refuse if either the TEST result or receipt already exists.

The freeze counter is not mutated after TEST. Receipt existence and digest prove which local artifact
was produced; they do not prove independent execution, source authenticity, or production validity.

