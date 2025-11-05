# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-05

### Added
- Production-ready release
- Bulk image upload from multiple URLs
- SSRF protection and security features
- Custom Wagtail admin integration with custom button
- Real-time upload status feedback with visual indicators
- Support for JPEG, PNG, GIF, BMP, and WEBP formats
- File size validation (10 MB max per image)
- Content-Type validation
- Image format verification with Pillow
- Comprehensive documentation and README
- Complete test suite with pytest
- Modern, responsive UI following Wagtail design patterns
- Makefile with build, test, and publish targets
- GitHub Actions workflow for automated PyPI publishing

### Fixed
- PyPI packaging metadata issues resolved
- setuptools version pinned to ensure compatibility
- Proper dependency management (requests, Pillow)

### Security
- Protection against SSRF attacks
- Private IP address blocking
- File size validation (10 MB limit)
- Content-Type validation
- Timeout protection (10 seconds)

## [0.1.0] - 2025-10-20 [DEPRECATED]

### Added
- Initial beta release
- Basic image upload from URLs functionality

## [Unreleased]

### Planned
- Collection selection in upload form
- Image preview before import
- CSV import for bulk URLs
- Progress bar for batch uploads
- Image metadata extraction
- Custom error handling improvements
- Support for additional image formats

