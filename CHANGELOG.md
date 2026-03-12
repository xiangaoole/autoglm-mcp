# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-03-12

### Added
- Auto-convert 1000-based relative coordinates to pixel coordinates in tool response
- `get_screen_size()` to retrieve phone screen resolution via ADB
- `convert_coords_to_pixels()` supporting `[x,y]`, `[x1,y1,x2,y2]`, and dot-separated formats
- Local Development & Debugging guide in README (MCP Inspector, local server config)
- `requirements.txt` for local development setup

### Changed
- Tool response now returns pixel coordinates directly — no manual conversion needed
- Removed coordinate conversion note from `aiAsk` tool description
- Updated Development Status to Production/Stable

## [0.1.2] - 2026-03-12

### Changed
- Removed unused `width`/`height` from screenshot capture in MCP server
- Removed `pillow` dependency (no longer needed)

## [0.1.1] - 2026-01-29

### Changed
- Unified MCP config examples in README with all environment variables

## [0.1.0] - 2026-01-29

### Added
- Initial release
- `aiAsk` tool for Android screen analysis
- ADB integration for screenshot capture
- AutoGLM API integration for UI element recognition
- Relative coordinate system (0-1000 scale)
