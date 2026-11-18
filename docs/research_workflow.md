# Research session workflow

1. Check the run index and input hashes for existing usable results. Write the scientific question, expected comparison, physical controls, and acceptance criteria before creating cases.
2. Confirm charge neutrality, normalization, grid and branch coverage for the chosen model. Use one-variable pilot runs and compare with an existing baseline when the executable, settings, and diagnostics match.
3. Run each new case in a unique scratch directory. Record the exact input, build, output precision, ranks, threads, actual wall time, timestep range, final normalized time, exit code, GENE convergence message, growth rate, and real frequency. Update records after each completed case. Treat anomalies, solver uncertainty and energy estimates as distinct review outcomes. Retain enough field and energy samples for future checks.
4. Update the tables and figures incrementally. Inspect outliers against raw logs and time histories. Explain uncertainties and which comparisons the results support, then record the next decision in the [roadmap](research_roadmap.md).
5. Run the offline reproduction command and inspect changes and file provenance. Stage only reviewed research files. Use a message such as `Document deuterium parallel-grid sensitivity` or `Add shared benchmark replication results`. A commit should capture a real research change and the date the change was made.
6. Commit and push approved changes. Keep raw local outputs in the original or scratch locations, with a documented path reference or portable subset for evidence.

## Initial GitHub publication plan

The proposed remote name is `gene-dipole-plasma-stability`. Review author attribution, report sharing, the research-material license, repository visibility, and the GENE modification disclosures before publication. The repository currently uses a rights-reserved notice for review and the archived report's group credit in `CITATION.cff`. Replace the citation credit with confirmed individual or group attribution and add a release date, version, and repository URL when they exist.

GitHub CLI authentication could not be established in the current shell. The `gh` on PATH is an unrelated Python browser helper whose interpreter fails with a CPU architecture error on this Mac. No working official GitHub CLI was found. Check `gh auth status` using a working ARM64 GitHub CLI before an approved publication. After explicit approval, create a GitHub repository with the agreed visibility, configure its remote, and push the reviewed history. Verify the README images, GitHub-rendered links, data downloads, citation panel, and repo permissions after publication.
