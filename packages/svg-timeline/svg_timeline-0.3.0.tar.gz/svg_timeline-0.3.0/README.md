# svg-timeline

A pure python library to create timeline plots.

## Documentation
At the current time (`0.2.2`), this library is still in an early development state.
Because I still expect the API to undergo larger changes until version `1.0`,
there is no extensive user documentation yet.

- For a rough usage overview, please take a look at the example below.
- For more technical information, you can read the [ADRs](https://github.com/TiDreyer/svg-timeline/tree/main/ADRs).

### Example
This is the result of running the script [`examples/emmy_noether.py`](https://github.com/TiDreyer/svg-timeline/blob/main/examples/emmy_noether.py):

![a timeline of Emmy Noether's life](https://github.com/TiDreyer/svg-timeline/raw/main/examples/emmy_noether.svg)

## Allowed Version Number Tags
[Semantic versioning](https://semver.org/) and [PEP 440](https://peps.python.org/pep-0440/#public-version-identifier)
have different requirements on version numbers.
This project aims to use version numbers that are valid according to both standards.
Effectively this allows version tags of the following form:

```
N.N.N[-(a|b|rc)N][-postN][-devN]
```

Where:
- `N` is a shorthand for a positive integer
- `(x|y)` symbolize two allowed variants `x` and `y`
- `[]` denote optional parts
- (the other symbols are literal characters)
