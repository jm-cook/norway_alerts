# Changelog

All notable changes to the Norway Alerts integration will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2026-01-23

### Added
- **Formatted Content Attribute** - Automatic markdown formatting for CAP-formatted alerts
  - Available for CAP sensors: Weather alerts (always) and NVE warnings with CAP enabled
  - Generated using Jinja2 template engine
  - Ready-to-use display format for markdown cards without custom templates
  - Configurable display options: show_icon, show_status, show_map
  - Includes alert status (Expected/Ongoing/Ended), severity, descriptions, instructions, consequences
  - No template logic required in dashboard cards

## [2.1.0] - 2026-01-13

### Breaking Changes
- **Sensor state changed**: State now represents the count of active alerts
  - Previous: State was highest activity level (1-5) or text string "1" for no alerts
  - Current: State is integer count (0 = no alerts, 1 = one alert, 2 = two alerts, etc.)
  - Severity information still available in `highest_level` and `highest_level_numeric` attributes
  - **Impact**: Automations or templates using `states('sensor.norway_alerts_*')` for severity level need updating

### Added
- **CAP format conversion** - Optional conversion of NVE warnings to CAP (Common Alerting Protocol) format
  - Enabled by default for new sensors
  - Existing sensors preserve their original format for backward compatibility
  - Allows unified display of NVE and Met.no alerts using the same template
  - Only available for NVE warnings (landslide, flood, avalanche) - Met.no alerts are always CAP
- **Template blueprint** - Pre-built template sensor blueprint for displaying CAP-formatted alerts
  - Available in `blueprints/template/cap_alert_markdown_sensor.yaml`
  - Import from GitHub for easy setup
  - Configurable display options (icons, status, maps)
  - Creates formatted markdown sensor for use in markdown cards

### Changed
- CAP format option hidden for Met.no weather alerts (always CAP format)

## [2.0.0] - 2026-01-09

### Breaking Changes
- **Integration renamed**: `varsom` → `norway_alerts`
  - Domain changed to better reflect all warning types (geohazards + weather)
  - Custom component directory: `/custom_components/norway_alerts/`
  - Sensors now prefixed with `sensor.norway_alerts_*`
  - Requires removal of old integration and re-adding with new name

### Added
- **Met.no MetAlerts API integration** - Weather warnings from Norwegian Meteorological Institute
  - Support for all meteorological warning types (wind, rain, snow, thunderstorms, etc.)
  - Latitude/longitude-based location configuration
  - CAP (Common Alerting Protocol) format support
- **Avalanche warnings** - Full support for NVE avalanche warnings
  - 5-level severity scale (green, yellow, orange, red, black)
  - Avalanche-specific attributes and data
- **Two-step configuration flow** - Improved setup process
  - Step 1: Select warning type and general settings
  - Step 2: Conditional location fields (county OR coordinates)
- **Persistent notifications** - Optional notification system
  - Configurable severity thresholds
  - Notifications for new or changed alerts
  - Severity filter options (all, yellow+, orange+, red only)
- **Test mode** - Generate fake alerts for testing dashboards and automations

### Changed
- **Architecture**: One sensor per warning type (cleaner separation)
  - Each configuration creates a single dedicated sensor
  - Users add integration multiple times for different types
  - Better attribute organization per warning type
- **Location handling**: Conditional fields based on warning type
  - NVE warnings (landslide/flood/avalanche): County-based with municipality filter
  - Met.no weather alerts: Latitude/longitude coordinates
  - Default coordinates from Home Assistant location (editable)
- **API Factory pattern**: Unified API client architecture
  - BaseWarningAPI abstract class
  - Separate API classes for each warning source
  - Consistent data format across all warning types

### Technical Details
- Based on MIT-licensed code from @kutern84 and @svenove (met_alerts)
- Proper attribution maintained in source code
- Updated WarningAPIFactory to support latitude/longitude parameters
- Enhanced error handling for different location types
- Backward compatibility for existing configurations

### Documentation
- **Consolidated README.md** - All documentation in one place
  - MetAlerts configuration and usage
  - Avalanche warnings documentation
  - Updated examples for all warning types
  - Architecture explanation
- **Removed obsolete files**:
  - NOTIFICATION_EXAMPLES.md
  - REFACTORING_SUMMARY.md
  - FRONTEND_EXAMPLES.md
  - DEV_SUMMARY.md
  - COMPLETE_DASHBOARD_EXAMPLE.md
  - AVALANCHE_FILTERING_GUIDE.md
  - AVALANCHE_DISPLAY_EXAMPLES.md
  - AVALANCHE_ATTRIBUTES_UPDATE.md
  - notes/ directory

### Credits
- Met.no MetAlerts integration code: @kutern84 and @svenove
- Original met_alerts repository: https://github.com/kurtern84/met_alerts

## [1.0.0] - 2025-12-15

### Added
- Initial release of Varsom Alerts integration
- Single sensor per county with all alerts in attributes
- Support for landslide warnings from NVE API
- Support for flood warnings from NVE API
- Option to monitor both warning types simultaneously
- County selection from all Norwegian counties
- Bilingual support (Norwegian and English)
- Config flow for easy setup through UI
- Rich alert data including:
  - Activity levels (1-4: green, yellow, orange, red)
  - Danger types and warning text
  - Affected municipalities
  - Valid from/to timestamps
  - Advice and consequence information
  - Direct links to Varsom.no with interactive maps
- Automatic icon updates based on alert level
- 30-minute update interval for fresh data

### Technical Details
- Uses DataUpdateCoordinator pattern for efficient API polling
- Implements modern Home Assistant best practices
- Single sensor design (not multiple _2, _3, _4 sensors like older integrations)
- All alerts accessible via structured attributes array
- Proper error handling and logging

### Documentation
- Comprehensive README with usage examples
- Template sensor examples for municipality filtering
- Automation examples for notifications
- Lovelace card configuration examples

[1.0.0]: https://github.com/jm-cook/varsom/releases/tag/v1.0.0
