# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]


## [0.2.0] - 2024-02-17
### Fixed
- `TextEmbed` widget placeholders ([#2]).

### Added
- Class attributes to `TextEmbed` to override codepoints used for widget placeholders ([#2]).
  - `.PLACEHOLDER_HEAD`
  - `.PLACEHOLDER_TAIL`
- More examples in the docs [#4].

### Changed
- `Hyperlink` now uses externally-applied display attributes ([#3]).
- Updated existing examples in the docs [#4].

[#2]: https://github.com/AnonymouX47/urwidgets/pull/2
[#3]: https://github.com/AnonymouX47/urwidgets/pull/3
[#4]: https://github.com/AnonymouX47/urwidgets/pull/4


## [0.1.1] - 2023-05-17
### Fixed
- `Hyperlink` text padding ([8b35012]).
- Validation of hyperlink text ([f9ee7d5]).

[8b35012]: https://github.com/AnonymouX47/urwidgets/commit/8b35012e45a0701c248633b94bc0767553c6073a
[f9ee7d5]: https://github.com/AnonymouX47/urwidgets/commit/f9ee7d57b5587789a630421aac3aaff005126b58


## [0.1.0] - 2023-05-14
### Added
- `TextEmbed` and `Hyperlink` widgets.
- `parse_text()` helper function.


[Unreleased]: https://github.com/AnonymouX47/urwidgets/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/AnonymouX47/urwidgets/compare/v0.1.0...v0.2.0
[0.1.1]: https://github.com/AnonymouX47/urwidgets/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/AnonymouX47/urwidgets/releases/tag/v0.1.0
