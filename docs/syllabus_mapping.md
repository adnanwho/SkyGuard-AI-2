# SkyGuard AI — Classical AI Syllabus Mapping

Status legend: `PLANNED` → `DESIGNED` → `IMPLEMENTED` → `TESTED` → `INTEGRATED`.
Nothing is marked past `PLANNED` until the corresponding code exists and
runs; nothing is marked `TESTED` until it has actually been executed and
verified. See `docs/repository_audit.md` §14 for the audit that produced
this table (2026-09-16): no syllabus code exists yet.

| AI Topic | SkyGuard Concept | Implementation File | Demonstration | Test/Evidence | Status |
|---|---|---|---|---|---|
| Problem formulation | Fault-hypothesis state space over stations | `src/skyguard/search/problem.py` | — | — | PLANNED |
| BFS / DFS / IDS | Diagnostic traversal of the station neighbor graph | `src/skyguard/search/{bfs,dfs,ids}.py` | — | — | PLANNED |
| Bidirectional search | Fault-to-symptom meet-in-the-middle search | `src/skyguard/search/bidirectional.py` | — | — | PLANNED |
| Heuristics / Greedy / A* | Least-cost diagnostic path to root cause | `src/skyguard/search/{heuristic,greedy,astar}.py` | — | — | PLANNED |
| AO* | Decomposable (AND/OR) fault diagnosis | `src/skyguard/search/aostar.py` | — | — | PLANNED |
| CSP | Maintenance visit scheduling under technician/travel constraints | `src/skyguard/search/csp.py` | — | — | PLANNED |
| Minimax | Detector vs. worst-case evasive fault pattern | `src/skyguard/adversarial/minimax.py` | — | — | PLANNED |
| Alpha-beta pruning | Same, pruned | `src/skyguard/adversarial/alpha_beta.py` | — | — | PLANNED |
| Propositional logic | Declarative re-expression of existing QC rules | `src/skyguard/knowledge/propositional.py` | — | — | PLANNED |
| First-order logic | Station/sensor facts and rules with variables | `src/skyguard/knowledge/first_order.py` | — | — | PLANNED |
| Semantic networks | Station/sensor/region relationship graph | `src/skyguard/knowledge/semantic_network.py` | — | — | PLANNED |
| Frames | Structured station/sensor templates | `src/skyguard/knowledge/frames.py` | — | — | PLANNED |
| Inference (forward/backward chaining) | Diagnosis rule engine | `src/skyguard/knowledge/inference.py` | — | — | PLANNED |
| Bayesian probability | Confidence scoring for diagnoses | `src/skyguard/reasoning/bayes.py` | — | — | PLANNED |
| Bayesian networks | Joint reasoning over QC/ensemble/context evidence | `src/skyguard/reasoning/bayesian_network.py` | — | — | PLANNED |
| Certainty factors | MYCIN-style diagnosis confidence combination | `src/skyguard/reasoning/certainty_factor.py` | — | — | PLANNED |
| Dempster-Shafer theory | Combining four disagreeing detectors (IF/ECOD/COPOD/HBOS) | `src/skyguard/reasoning/dempster_shafer.py` | — | — | PLANNED |
| Fuzzy logic | Fuzzy severity membership (LOW/MEDIUM/HIGH) | `src/skyguard/reasoning/fuzzy.py` | — | — | PLANNED |

## Important distinction

The existing anomaly-detection stack — Isolation Forest, ECOD, COPOD, HBOS,
and their ensemble combination — is **unsupervised machine learning**, not
classical AI syllabus material. It is the application's working foundation
and must be preserved, but it should not be presented as syllabus coverage.
The modules in this table are additive academic work layered on top of that
foundation, using it as a real application context rather than inventing
toy examples.

## Structural prerequisite

`src/skyguard/__init__.py` currently imports `SkyGuardEngine` eagerly, which
pulls in `pyod`, `scikit-learn`, and `shap` as a side effect of importing
the package at all. The search/adversarial/knowledge/reasoning modules
should not inherit that dependency — a BFS demo should not require the ML
stack to be installed. Fix the eager import before starting Module 1.
