# **Logic Optimization Research Framework**

This repository provides a research-oriented framework for studying and evaluating logic synthesis optimization sequences, with a primary focus on FPGA mapping and future extensions to standard-cell (ASIC) flows.
The project is built as the experimental backbone for a graduate thesis on algorithmic and adaptive synthesis sequence optimization.
The emphasis is on:
- Infrastructure correctness
- Reproducibility
- Clear separation between infrastructure and algorithms
This is not a production tool. It is an experimental platform.

## What This Repository Does
At a high level, the repository allows you to:
- Define logic optimization actions and sequences
- Execute these sequences on benchmark circuits using ABC
- Collect QoR metrics (LUT count, logic depth)
- Store results in a strict, reproducible directory hierarchy
- Later plug in search / learning algorithms without touching the core infrastructure

## Repository Structure
<img width="723" height="585" alt="image" src="https://github.com/user-attachments/assets/01332e85-a541-4093-b282-dfc6da9420b5" />

## Folder-by-Folder Explanation
### common/ — Core Infrastructure
This is the most important folder. Everything here is designed to be stable and reusable.
#### common/action_space/
- Defines the search space for optimization:
- Primitive synthesis actions (e.g. balance, rewrite, refactor)
- Action objects and abstractions
- Built-in sequences (e.g. init, resyn, resyn2)
- No execution logic lives here — only definitions.
#### common/execution/
Responsible for running synthesis and measuring QoR.
Key responsibilities:
- Build ABC scripts
- Run ABC (FPGA mapping with if -K)
- Parse metrics (LUTs, levels)
- Measure execution time
This layer does not care whether actions come from:
- Built-in scripts
- Hand-written sequences
- Learning algorithms
#### common/storage/
Handles result storage and filesystem layout.
Responsibilities:
- Define canonical result paths
- Write results to disk (json, pkl)
- Enforce deterministic directory hierarchy
All results follow the structure:
      results/refs/<script>/<option>/<design>/
Example:
      results/refs/resyn2/fpga-6/adder/result.json

### refs/ — Reference (Baseline) Runs
This folder contains scripts that generate baseline results.
These are:
- Deterministic
- Algorithm-independent
- Used as ground truth for comparison
Example use:
    Run resyn2 on all EPFL benchmarks
Store LUT and depth results
    Later compare algorithms against these baselines

### algorithms/
This folder is reserved for:
- Greedy search
- Adaptive greedy
- Reinforcement learning
- Bayesian optimization
- Any custom sequence-generation logic
Algorithms must consume the infrastructure in common/, not reimplement it.
(Currently empty or partially populated — intentional.)

### benchmarks/
Contains benchmark circuits.
Currently uses EPFL combinational benchmarks (.blif)
Structure allows adding other benchmark suites later

### experiments/
Reserved for higher-level experiment orchestration:
- Running multiple algorithms
- Sweeping hyperparameters
- Aggregating results
(Not yet active, by design.)

### results/
- Auto-generated results.
- Never manually edited
- Typically excluded from version control
- Used for post-processing and analysis

### test/
- Lightweight tests to verify:
- Execution correctness
- Action sequences
- Storage paths
These are sanity checks, not full unit tests.

## How to Use This Repository
### 1. Environment Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements/requirements.txt

Ensure abc is available in your PATH.

### 2. Run a Single Reference Evaluation
python -m refs.run_fpga_refs \
  --design_file benchmarks/epfl/adder.blif \
  --script resyn2 \
  --lut_k 6

This will:
- Run ABC with FPGA mapping (if -K 6)
- Apply the resyn2 sequence
- Store results under results/refs/

### 3. Run References on All Benchmarks
Use the provided bash script (or similar):
    bash run_all_fpga_refs.sh
Features:
- Iterates over all .blif designs
- Skips designs with existing results
- Safe to stop and resume
- Stored Metrics
- For reference runs, only essential metrics are stored:
    {
      "lut": 257,
      "levels": 51
    }

#### Optional pickle (result.pkl) is also written for:
- Faster loading
- Heavy numerical analysis later
- Execution logs are not stored by default to avoid unnecessary clutter.

## Design Philosophy
- Infrastructure first, algorithms second
- Deterministic baselines before optimization
- Explicit filesystem structure over implicit conventions
- No hidden state, no magic
If something looks “minimal”, it is intentional.

## Current Status
✅ Core infrastructure (common/) completed
✅ FPGA reference execution implemented
✅ Built-in sequences validated
⏳ Algorithm integration (next phase)

##Intended Audience
This repository is intended for:
- Graduate-level research
- Experimental algorithm development
- Reproducible synthesis studies
- It is not intended for end-user synthesis workflows.

##Final Note
All future complexity belongs in:
- algorithms/
- experiments/
The infrastructure should remain boring, predictable, and stable.
That is the point.
