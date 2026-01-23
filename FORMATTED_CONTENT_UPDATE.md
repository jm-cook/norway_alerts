# Formatted Content Feature - Implementation Summary

## Overview
Added `formatted_content` attribute to norway_alerts sensors, providing pre-formatted markdown display content without requiring external blueprints or template sensors.

## Changes Made

### 1. Constants Added (const.py)
```python
CONF_SHOW_ICON = "show_icon"
CONF_SHOW_STATUS = "show_status"
CONF_SHOW_MAP = "show_map"
```

### 2. Config Flow Updated (config_flow.py)
- Imported new formatting constants
- Added three boolean options to the options flow:
  - `show_icon`: Include warning icons (default: True)
  - `show_status`: Show alert status (Expected/Ongoing/Ended) (default: True)
  - `show_map`: Include map images (default: True)

### 3. Sensor Implementation (sensor.py)
- Imported new constants
- Added `_generate_formatted_content()` method that:
  - Takes list of alerts as input
  - Generates markdown with HTML table formatting
  - Includes icons, status, descriptions, instructions, consequences, time periods
  - Respects user's display preferences from config
  - Returns "No active alerts" when no alerts present
- Modified `extra_state_attributes` property to include `formatted_content` in the result dict

### 4. Documentation (README.md)
- Added **Display Content** section explaining:
  - What formatted_content is
  - Configuration options (show_icon, show_status, show_map)
  - Simple usage example: `{{ state_attr('sensor.norway_alerts_xxx', 'formatted_content') }}`
- Added **Recorder Configuration** section with:
  - Explanation of why to exclude large attributes
  - Complete configuration.yaml example
  - Notes about what gets excluded vs retained

## Usage

### Basic Display
```yaml
type: markdown
content: >
  {{ state_attr('sensor.norway_alerts_landslide_vestland', 'formatted_content') }}
```

### Configure Display Options
1. Go to **Settings** → **Devices & Services**
2. Find your Norway Alerts integration
3. Click **Configure**
4. Toggle options:
   - Show Icon
   - Show Status
   - Show Map

### Exclude from Recorder (Recommended)
Add to `configuration.yaml`:
```yaml
recorder:
  exclude:
    entity_globs:
      - sensor.norway_alerts_*
    entities:
      - sensor.norway_alerts_landslide_vestland
  include:
    entity_globs:
      - sensor.norway_alerts_*
    entities:
      - sensor.norway_alerts_landslide_vestland
  exclude_attributes:
    entity_globs:
      - sensor.norway_alerts_*
    entities:
      - sensor.norway_alerts_landslide_vestland
    attributes:
      - alerts
      - formatted_content
```

## Benefits
1. **No Blueprint Required**: Users no longer need to import and configure blueprints
2. **No configuration.yaml Edits**: No need to add template sensors
3. **Simpler Setup**: Just add the integration and display the content
4. **Configurable**: Users can customize what's included via integration options
5. **Database Friendly**: Documentation guides users to exclude large attributes

## Breaking Changes
**None** - This is a fully backward-compatible addition:
- Existing attributes remain unchanged
- `formatted_content` is a new optional attribute
- Users can continue using blueprints if they prefer
- No changes to sensor state or core attributes

## Testing Checklist
- [ ] Verify new constants are accessible
- [ ] Confirm options appear in configuration flow
- [ ] Test `formatted_content` generation with active alerts
- [ ] Test with no active alerts (should return "No active alerts")
- [ ] Verify show_icon=false removes icons
- [ ] Verify show_status=false removes status headers
- [ ] Verify show_map=false removes map images
- [ ] Test in markdown card
- [ ] Verify recorder exclusion works as documented

## Next Steps
1. Test with real alerts or test mode
2. Update version number in manifest.json
3. Update CHANGELOG.md
4. Consider deprecating blueprint in future version (after users migrate)
