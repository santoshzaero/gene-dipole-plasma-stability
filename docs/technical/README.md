# Technical guide

## Start here

The simulations follow a small disturbance in a plasma confined by a ring-shaped magnet. Two measurements summarize its early behavior. The growth rate tells you how fast its size changes. The real frequency tells you how fast it oscillates. The [beginner guide](../beginner_guide/README.md) explains the physics and shows how to read the plots.

## Model, diagnostics, and validation

The calculations use a linear electrostatic gyrokinetic model. Start with geometry and normalization to connect the GENE inputs to the physics, then use the diagnostics sections to interpret growth, frequency, and unresolved cases.

- [Linear model and dipole geometry](theoretical_background.md)
- [Numerical methodology and diagnostics](numerical_methodology.md)
- [Normalization and species definitions](normalization.md)
- [Convergence and free-energy fits](convergence.md)
- [Field-line mode envelopes](mode_structure.md)
- [Adiabatic-electron theory benchmark](adiabatic_validation.md)
- [Sources and local verification points](../references.md)
