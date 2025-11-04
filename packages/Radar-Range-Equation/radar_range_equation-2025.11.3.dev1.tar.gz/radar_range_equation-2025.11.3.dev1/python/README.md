2025.10.27

Main updates include support for theta_B and calculations for spheres, RCS and radius from RCS.

## Radar Range Equation

A compact toolbox for deriving and evaluating radar range equations. It exposes a small programmatic API for setting physical variables, performing common radar-related calculations, and converting units.

## Install

pip install radar-range-equation
```

## Quick start

```python
import radar_range_equation as RRE

# Set common variables
RRE.vars.c = 3.0e8        # speed of light (m/s)
RRE.vars.f = 430e6        # frequency (Hz)
RRE.vars.eta = 0.6        # antenna efficiency (unitless)

# Because `lambda` is a reserved word in Python, access it with getattr/setattr
setattr(RRE.vars, 'lambda', RRE.vars.c / RRE.vars.f)
print('wavelength (m):', getattr(RRE.vars, 'lambda'))

# Compute effective aperture (circular antenna example)
RRE.vars.D = RRE.convert_ft_to_m(60)  # antenna diameter in meters
RRE.vars.A_e = RRE.solve.A_e_circ()
print('A_e (m^2):', RRE.vars.A_e)
```

## Public API (short)

- `vars` — namespace-like container of variables (speed of light `c`, frequency `f`, wavelength `lambda`, gains, power, sigma, etc.). Use `getattr`/`setattr` for `lambda`.
- `solve` — helper functions for computing aperture, gain, R_max, P_t and other routine expressions (e.g., `solve.wavelength()`, `solve.G_t()`).
- `equations` — symbolic SymPy expressions representing the radar equations used by `solve`.
- `redefine_variable(name, value)` — convenience to set attributes on the `vars` namespace.
- `convert_to_db`, `convert_to_degrees`, `convert_m_to_mi`, `convert_w_to_kw`, `convert_ft_to_m` — small conversion helpers.

## Testing

After installing the package you can run the included smoke test:

```powershell
python python/test_package.py
```

The test script checks basic import and example calculations.

## Notes and gotchas

- `lambda` is a reserved Python keyword; use `getattr(vars, 'lambda')` and `setattr(vars, 'lambda', value)` when reading/writing the wavelength variable.
- The package mixes symbolic (SymPy) and numeric (NumPy/Scipy) approaches. The `equations` module provides symbolic forms while `solve` returns numeric results based on values in `vars`.

## Contributing

Small, focused improvements (tests, docs, type hints) are welcome. The repository uses Hatch in CI for packaging; see `.github/workflows/python-package.yml` for the build/test flow.

## License

See the repository `LICENSE` file for licensing details.

# Radar Range Equation
A basic toolbox for solving radar range equations

## Testing

After building and installing the package, you can run the test script to verify functionality:

```bash
python python/test_package.py
```

This test script verifies that:
- The package can be imported successfully
- Variables can be set dynamically (e.g., `c`, `f`, `lambda`)
- The `redefine_variable` function works correctly
- Calculations work as expected (e.g., `lambda = c/f`)

### Example Usage

```python
import radar_range_equation as RRE

# Set the speed of light (m/s)
RRE.vars.c = 3.00 * 10**8

# Set the frequency (Hz)
RRE.vars.f = 10

# Calculate and set wavelength (m)
# Note: 'lambda' is a reserved keyword in Python, so use setattr/getattr
setattr(RRE.vars, 'lambda', RRE.vars.c / RRE.vars.f)

# Print the wavelength
print(getattr(RRE.vars, 'lambda'))  # Output: 30000000.0
```
