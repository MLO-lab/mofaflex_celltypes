# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog][],
and this project adheres to [Semantic Versioning][].

[keep a changelog]: https://keepachangelog.com/en/1.1.0/
[semantic versioning]: https://semver.org/spec/v2.0.0.html

## [0.2.0] (Unreleased)

### Changed
- the `show_featurenames` argument to `pl.factor` is now called `show_samplenames` to better reflect what it actually does

### Removed
- The MOFA compatibility mode for saving a trained model

## [0.1.1] (Unreleased)

### Added
- `tl.factor_correlation` to calculate the correlation between factors

### Changed
- `pl.factor` now also accepts factor names for the `factor` argument.

### Deprecated
- The MOFA compatibility mode for saving a trained model.

## [0.1.0]

- Initial release

[0.2.0]: https://github.com/bioFAM/mofaflex/releases/tag/v0.2.0
[0.1.1]: https://github.com/bioFAM/mofaflex/releases/tag/v0.1.1
[0.1.0]: https://github.com/bioFAM/mofaflex/releases/tag/v0.1.0
