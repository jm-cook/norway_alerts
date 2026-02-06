# Norway Alerts - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/DTekNO/norway_alerts)
[![Validate with HACS](https://github.com/DTekNO/norway_alerts/actions/workflows/validate.yaml/badge.svg)](https://github.com/DTekNO/norway_alerts/actions/workflows/validate.yaml)
[![Hassfest](https://github.com/DTekNO/norway_alerts/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/DTekNO/norway_alerts/actions/workflows/hassfest.yaml)
[![GitHub Release](https://img.shields.io/github/release/DTekNO/norway_alerts.svg)](https://github.com/DTekNO/norway_alerts/releases)
![Project Maintenance](https://img.shields.io/maintenance/yes/2026.svg)

A comprehensive Home Assistant custom integration that provides Norwegian weather and geohazard warnings from multiple official sources:
- **Landslide, Flood, and Avalanche warnings** from NVE (Norwegian Water Resources and Energy Directorate)
- **Weather alerts** from Met.no (Norwegian Meteorological Institute)

All warnings unified in a clean, modern Home Assistant interface with automatic icon display and rich alert data.

## Features

### Warning Types
- **Landslide warnings** (NVE/Varsom.no) - Jord- og flomskredfare
- **Flood warnings** (NVE/Varsom.no) - Flomvarsling  
- **Avalanche warnings** (NVE/Varsom.no) - Snøskredvarsling
- **Weather alerts** (Met.no) - Meteorological warnings (wind, rain, snow, etc.)

### Key Features
- **Flexible configuration** - One sensor per warning type for clean separation
- **Multiple location types** - County-based (NVE) or coordinates-based (Met.no)
- **Activity levels** - Green (1), Yellow (2), Orange (3), Red (4), Black (5 for avalanche)
- **Included blueprints** - Pre-built templates for displaying alerts (see [BLUEPRINTS.md](BLUEPRINTS.md))
- **CAP format support** - Optional conversion of NVE warnings to CAP standard for unified display
- **Rich alert data** - Warning text, advice, consequences, affected areas, validity periods
- **Direct links** - Each alert links to detailed maps and information
- **Bilingual** - Full Norwegian and English support
- **Official Yr.no icons** - Embedded warning icons (no setup required)
- **Municipality filtering** - Filter NVE alerts to specific municipalities
- **Test mode** - Generate fake alerts for testing dashboards and automations
- **Persistent notifications** - Optional notifications for new or changed alerts

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Sensor Data](#sensor-data)
- [Icons](#icons)
- [Dashboard Examples](#dashboard-examples)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)
- [API Information](#api-information)
- [Credits](#credits)

---

## Installation

### Prerequisites
- Home Assistant 2024.1.0 or newer
- Internet connection to access NVE API

### Method 1: HACS (Recommended)

1. **Add Custom Repository**
   - Open HACS in Home Assistant
   - Click the three dots (⋮) in the top right
   - Select "Custom repositories"
   - Add repository URL: `https://github.com/DTekNO/norway_alerts`
   - Category: Integration
   - Click "Add"

2. **Install Integration**
   - Search for "Norway Alerts" in HACS
   - Click "Download"
   - Restart Home Assistant

3. **Add Integration**
   - Go to **Settings** → **Devices & Services**
   - Click **"+ Add Integration"**
   - Search for "Norway Alerts"
   - Follow the configuration steps below

### Method 2: Manual Installation

1. **Copy Files**
   - Download the latest release
   - Copy the `custom_components/norway_alerts` folder to your Home Assistant `config/custom_components/` directory
   - The final path should be: `/config/custom_components/norway_alerts/`

2. **Restart Home Assistant**
   - Go to **Settings** → **System** → **Restart**

3. **Add Integration**
   - Go to **Settings** → **Devices & Services**
   - Click **"+ Add Integration"**
   - Search for "Norway Alerts"

---

## Configuration

### Initial Setup

The integration uses a **two-step configuration flow**:

#### Step 1: Warning Type & Settings

**Warning Type** (Required) - Choose one per sensor:

*Geohazard Warnings (NVE via Varsom.no):*
- **Landslide** - Debris flows, rockslides, quick clay landslides
- **Flood** - River flooding, flash floods, groundwater flooding  
- **Avalanche** - Snow avalanche danger levels

*Weather Alerts (Met.no):*
- **Weather Alerts** - Wind, rain, snow, thunderstorms, coastal events, ice

**Language** (Optional, Default: English)
- **English** (en) or **Norwegian** (no)
- Controls alert text language and website links

**Test Mode** (Optional, Default: Off)
- Enable to inject fake alerts for testing
- Useful when there are no active warnings

**Enable Notifications** (Optional, Default: Off)
- Send persistent notifications for new/changed alerts
- Configure severity threshold for notifications

**Notification Severity** (Optional, Default: Yellow and above)
- **All warnings** - Notify for all severity levels
- **Yellow and above** - Skip green (no warning) notifications  
- **Orange and above** - Only moderate to extreme warnings
- **Red warnings only** - Only extreme warnings

#### Step 2: Location Configuration

The location fields shown depend on your selected warning type:

**For Geohazard Warnings** (Landslide, Flood, Avalanche):
- **County** (Required) - Select your Norwegian county:
  - Oslo (03), Rogaland (11), Møre og Romsdal (15), Nordland (18)
  - Østfold (31), Akershus (32), Buskerud (33), Innlandet (34)
  - Vestfold (39), Telemark (40), Agder (42), Vestland (46)
  - Trøndelag (50), Troms (55), Finnmark (56)
- **Municipality Filter** (Optional) - Filter to specific municipalities:
  - Leave empty for all alerts in the county
  - Enter names separated by commas: `Bergen, Stord`
  - Creates a second filtered sensor alongside the main sensor

**For Met.no Weather Alerts**:
- **Latitude** (Required, defaults to Home Assistant location)
- **Longitude** (Required, defaults to Home Assistant location)
- Can be edited to monitor any location in Norway

### Example Configurations

**Example 1: Vestland County Landslide Warnings**
- Warning Type: `Landslide`
- County: `Vestland`
- Language: `English`
- **Creates**: `sensor.norway_alerts_landslide_vestland`

**Example 2: Bergen Area Flood Warnings (Filtered)**
- Warning Type: `Flood`
- County: `Vestland`
- Municipality Filter: `Bergen, Askøy, Fjell`
- **Creates**: 
  - `sensor.norway_alerts_flood_vestland` (all county alerts)
  - `sensor.norway_alerts_flood_vestland_filtered` (Bergen area only)

**Example 3: Weather Alerts for Oslo**
- Warning Type: `Weather Alerts`
- Latitude: `59.9139`
- Longitude: `10.7522`
- **Creates**: `sensor.norway_alerts_weather_oslo`

**Example 4: Complete Monitoring Setup**

Add the integration **multiple times** to monitor different warning types and locations:
- `sensor.norway_alerts_landslide_vestland` - Geohazard: landslide warnings
- `sensor.norway_alerts_flood_vestland` - Geohazard: flood warnings  
- `sensor.norway_alerts_avalanche_vestland` - Geohazard: avalanche warnings
- `sensor.norway_alerts_weather_bergen` - Weather alerts for Bergen
- `sensor.norway_alerts_landslide_oslo` - Geohazard: Oslo landslides

> **Note**: Each configuration creates an independent sensor. This gives you clean separation between warning types with appropriate attributes for each.

### Reconfiguring

To change settings after initial setup:
1. Go to **Settings** → **Devices & Services**
2. Find **Norway Alerts**
3. Click the three dots (⋮) → **Configure**
4. Update your settings and click **Submit**

---

## Sensor Data

### State

The sensor state represents the **highest activity level** from all active warnings:

#### Geohazard Warnings - Landslide & Flood (NVE)
| State | Level | Color | Description |
|-------|-------|-------|-------------|
| `1` | Green | 🟢 | No warnings / Low danger |
| `2` | Yellow | 🟡 | Moderate danger |
| `3` | Orange | 🟠 | Considerable danger |
| `4` | Red | 🔴 | High/Extreme danger |

#### Geohazard Warnings - Avalanche (NVE)
| State | Level | Color | Description |
|-------|-------|-------|-------------|
| `1` | Green | 🟢 | Low danger |
| `2` | Yellow | 🟡 | Moderate danger |
| `3` | Orange | 🟠 | Considerable danger |
| `4` | Red | 🔴 | High danger |
| `5` | Black | ⚫ | Extreme danger |

#### Weather Alerts (Met.no)
| State | Level | Color | Description |
|-------|-------|-------|-------------|
| `1` | Green | 🟢 | No warnings |
| `2` | Yellow | 🟡 | Moderate weather event |
| `3` | Orange | 🟠 | Severe weather event |
| `4` | Red | 🔴 | Extreme weather event |

### Attributes

#### Common Attributes (All Warning Types)

All sensors provide the following core attributes:

```yaml
active_alerts: 2          # Number of active alerts
highest_level: "yellow"   # Color name of highest severity
highest_level_numeric: 2  # Numeric level (1-4 or 1-5 for avalanche)
formatted_content: "..."  # Formatted markdown for display (see Display Content section)
alerts: [...]             # Array of alert objects (see below)
```

> **⚠️ Recorder Exclusion Recommended**: The `alerts` and `formatted_content` attributes can be quite large and may cause database bloat and log warnings. It's recommended to exclude these from the recorder. See [Recorder Configuration](#recorder-configuration) below.

#### Geohazard Warnings (Landslide, Flood, Avalanche)

Additional attributes specific to NVE warnings:

```yaml
county_name: "Vestland"
county_id: "46"
municipality_filter: null  # or "Bergen, Stord" if filtered
alerts:
  - id: "584731"
    master_id: "123456"
    level: 2
    level_name: "yellow"
    danger_type: "Jord- og flomskredfare"
    warning_type: "landslide"  # or "flood" or "avalanche"
    municipalities:
      - "Tysnes"
      - "Bergen"
      - "Stord"
    valid_from: "2025-12-14T07:00:00"
    valid_to: "2025-12-15T06:59:00"
    danger_increases: "2025-12-14T16:00:00"
    danger_decreases: "2025-12-15T19:00:00"
    main_text: "Moderate avalanche danger..."
    warning_text: "Up to 150mm precipitation expected..."
    advice_text: "Stay informed about weather..."
    consequence_text: "Landslides may occur..."
    url: "https://www.varsom.no/en/flood-and-landslide-warning-service/forecastid/584731"
```

#### Met.no Weather Alerts

Additional attributes specific to Met.no alerts:

```yaml
latitude: 59.9139
longitude: 10.7522
alerts:
  - id: "2.49.0.1.578.0.20250109121500"  # Met.no CAP identifier
    level: 3
    level_name: "orange"
    danger_type: "Wind"  # or "Rain", "Snow", "Thunderstorm", etc.
    warning_type: "metalerts"
    event_type: "wind"
    municipalities: []  # Not applicable for Met.no alerts
    areas:
      - "Oslo"
      - "Akershus"
    valid_from: "2026-01-09T12:00:00+01:00"
    valid_to: "2026-01-10T06:00:00+01:00"
    main_text: "Orange wind warning"
    warning_text: "Strong winds expected with gusts up to 30 m/s..."
    instruction: "Secure loose objects. Avoid unnecessary travel..."
    consequences: "Damage to infrastructure possible..."
    certainty: "Likely"
    url: "https://www.met.no/vaer-og-klima/ekstremvaervarsler-og-andre-faremeldinger"
```

#### Alert Attributes Explained

- **id**: Unique forecast ID
- **master_id**: NVE master ID for the alert
- **level**: Numeric danger level (1-4)
- **level_name**: Color name (green, yellow, orange, red)
- **danger_type**: Type of danger (in selected language)
- **warning_type**: landslide, flood, or combined
- **municipalities**: List of affected municipalities
- **valid_from/valid_to**: Alert validity period
- **danger_increases/decreases**: When danger level changes
- **main_text**: Primary alert headline
- **warning_text**: Detailed warning description
- **advice_text**: What to do / safety instructions
- **consequence_text**: Potential impacts
- **url**: Direct link to Varsom.no map and details

---

## Icons

### Automatic Display (No Setup Required)

The integration **automatically displays warning icons** based on alert type and severity. Icons are embedded in the integration - no manual setup needed!

### Available Icons

| Warning Type | Yellow (2) | Orange (3) | Red (4) | Black (5) |
|-------------|-----------|-----------|---------|----------|
| **Landslide** | 🟡 Landslide | 🟠 Severe Landslide | 🔴 Extreme Landslide | - |
| **Flood** | 🟡 Flood | 🟠 Severe Flood | 🔴 Extreme Flood | - |
| **Avalanche** | 🟡 Avalanche | 🟠 Considerable Avalanche | 🔴 High Avalanche | ⚫ Extreme Avalanche |
| **Weather (Met.no)** | 🟡 Weather Alert | 🟠 Severe Weather | 🔴 Extreme Weather | - |

### Icon Source & License

- **Repository**: https://github.com/nrkno/yr-warning-icons
- **License**: CC BY 4.0 (Creative Commons Attribution 4.0 International)
- **Copyright**: Yr warning icons © 2015 by Yr/NRK
- **Format**: SVG embedded as base64 data URLs

The icons are embedded directly in the integration code, so they:
- ✅ Work immediately after installation
- ✅ Require no external files or www folder
- ✅ Display in all Home Assistant themes
- ✅ Update automatically based on alert level

### Using Custom Icons

To override with your own icons:
1. Go to **Settings** → **Devices & Services** → Click the entity
2. Click the gear icon (⚙️)
3. Set a custom icon (e.g., `mdi:alert-circle`) or entity picture URL

---

## Display Content

### Formatted Content Attribute

The integration automatically generates formatted markdown content in the `formatted_content` attribute using a built-in Jinja2 template, ready to display in markdown cards without any additional template logic.

> **Note**: The `formatted_content` attribute is only available for **CAP-formatted alerts**:
> - Weather alerts (Met.no) - always in CAP format
> - NVE warnings (landslide, flood, avalanche) - only when "Enable CAP format" is checked during configuration
> 
> Non-CAP NVE sensors will not have this attribute. Create your own template sensor for those cases, or enable CAP formatting.

#### Customization

The `formatted_content` attribute provides a ready-to-use display format. If you need different formatting, you can create your own template sensor using the `alerts` attribute - see the [Markdown Card with Custom Template](#markdown-card-with-custom-template) example below.

#### Configuration Options

You can customize what's included in the formatted content via **Settings** → **Devices & Services** → **Norway Alerts** → **Configure**:

- **Show Icon** (`show_icon`): Include warning icons in the formatted output (default: `true`)
- **Show Status** (`show_status`): Show "Expected", "Ongoing", or "Ended" status for each alert (default: `true`)
- **Show Map** (`show_map`): Include alert map images (default: `true`)

These options are passed to the template and control which elements appear in the output.

#### Usage Example

Display alerts directly in a markdown card:

```yaml
type: markdown
content: >
  {{ state_attr('sensor.norway_alerts_landslide_vestland', 'formatted_content') }}
```

That's it! No complex templates needed. The integration handles all the formatting, including:
- Alert status (Expected/Ongoing/Ended)
- Warning icons (if enabled)
- Severity levels with color codes
- Time periods with danger increase/decrease times
- Descriptions, instructions, and consequences
- Affected areas
- Map images (if enabled)

---

## Recorder Configuration

### Large Attributes Warning

The `alerts` and `formatted_content` attributes can be quite large (especially with multiple active alerts) and may cause:
- Database bloat
- Log warnings about entity size
- Slower recorder performance

Unfortunately, Home Assistant's recorder does not support excluding specific attributes - you can only exclude entire entities.

**Recommended approaches:**

1. **Exclude sensors from recorder** - Alert data is most valuable in real-time, not historically:
   ```yaml
   recorder:
     exclude:
       entity_globs:
         - sensor.norway_alerts_*
   ```
   **Pros**: Eliminates database bloat and log warnings entirely  
   **Cons**: No history graphs for alert levels (rarely needed for alerts)  
   **Note**: All real-time data, automations, and dashboards work perfectly

2. **Live with it** - Keep sensors in recorder despite large attributes:
   - The warnings are informational only
   - As long as you have disk space, no action needed
   - Useful if you want historical graphs of alert levels

3. **Shorter purge interval** - Keep sensors but limit history:
   ```yaml
   recorder:
     purge_keep_days: 3  # Instead of default 10
   ```
   Reduces database growth while maintaining some history

> **Note**: Excluding from recorder only affects historical storage. All attributes remain available in real-time via `state_attr()`, dashboard cards, and automations.

---

## Dashboard Examples

The integration works with all standard Home Assistant cards and custom cards from HACS.

### Compact View Toggle

The integration automatically creates a **Compact View** switch for each alert sensor. This allows you to toggle between:
- **Compact view** (switch ON): Shows all alert icons in a single row - perfect for dashboard overviews
- **Full view** (switch OFF - default): Shows complete alert details including descriptions, instructions, and maps

Both entities are linked in the same device, making them easy to find together.

**Finding Your Entity IDs:**
1. Go to Settings → Devices & Services → Norway Alerts
2. Click on your location/region device
3. Note both entity IDs (the sensor and the switch)

The sensor automatically detects if the switch is renamed and re-links without requiring a restart.

**Note:** Standard markdown cards do not support tap actions. To toggle the view, you'll need either a separate toggle control (shown below) or a custom card from HACS that adds tap action support.

#### Example: Entities Card with Toggle (Recommended)

Most compact approach using only standard cards:

```yaml
type: vertical-stack
cards:
  - type: entities
    entities:
      - entity: switch.vestland_weather_alerts_compact_view  # Your switch entity ID
        name: Compact View
  - type: markdown
    content: >
      {{ state_attr('sensor.norway_alerts_metalerts_vestland', 'formatted_content') }}
```

#### Example: Button Toggle

Alternative with a button control:

```yaml
type: vertical-stack
cards:
  - type: button
    entity: switch.vestland_weather_alerts_compact_view
    name: Toggle Alert View
    icon: mdi:view-compact
    tap_action:
      action: toggle
  - type: markdown
    content: >
      {{ state_attr('sensor.norway_alerts_metalerts_vestland', 'formatted_content') }}
```

#### Example: Custom Card with Tap Action (Advanced)

For tap-to-toggle on the markdown card itself, install the **Actions Card** from HACS:

**Requirements:** Install [actions-card](https://github.com/nutteloost/actions-card) from HACS

```yaml
type: custom:actions-card
entity: switch.vestland_weather_alerts_compact_view  # Your switch entity ID
tap_action:
  action: toggle
card:
  type: markdown
  content: >
    {{ state_attr('sensor.norway_alerts_metalerts_vestland', 'formatted_content') }}
```

This wraps the markdown card with tap action support, allowing you to tap anywhere to toggle between compact and full views.

---

## Usage Examples

### Quick Start Examples

#### Basic Entity Card

```yaml
type: entities
title: Landslide Warnings
entities:
  - entity: sensor.norway_alerts_landslide_vestland
    name: Vestland Alert Level
```

#### Markdown Card with Formatted Content

```yaml
type: markdown
content: >
  {{ state_attr('sensor.norway_alerts_landslide_vestland', 'formatted_content') }}
```

#### Markdown Card with Custom Template

If you want full control over the display, you can still use custom templates:

```yaml
type: markdown
content: |
  {% set alerts = state_attr('sensor.norway_alerts_landslide_vestland', 'alerts') or [] %}
  {% if alerts | count > 0 %}
  ## Active Warnings ({{ alerts | count }})
  {% for alert in alerts %}
  ### {{ alert.main_text }}
  **Level:** {{ alert.level_name | upper }}
  **Area:** {{ alert.municipalities | join(', ') }}
  **Valid:** {{ alert.valid_from }} to {{ alert.valid_to }}
  
  {{ alert.warning_text }}
  
  [View on Varsom.no]({{ alert.url }})
  {% endfor %}
  {% else %}
  No active warnings
  {% endif %}
```

### Automation Examples

#### Alert Notification

```yaml
automation:
  - alias: "Yellow Alert Notification"
    trigger:
      - platform: numeric_state
        entity_id: sensor.norway_alerts_landslide_vestland
        above: 1
    action:
      - service: notify.mobile_app
        data:
          title: "Landslide Warning - {{ state_attr('sensor.norway_alerts_landslide_vestland', 'highest_level') | upper }}"
          message: >
            {{ state_attr('sensor.norway_alerts_landslide_vestland', 'alerts')[0].main_text }}
          data:
            url: "{{ state_attr('sensor.norway_alerts_landslide_vestland', 'alerts')[0].url }}"
            tag: "norway_alert"
            importance: high
```

#### Red Alert Emergency

```yaml
automation:
  - alias: "Red Alert - Emergency"
    trigger:
      - platform: numeric_state
        entity_id: sensor.norway_alerts_landslide_vestland
        above: 3  # Red level
    action:
      - service: notify.notify
        data:
          title: "🚨 EXTREME WEATHER WARNING 🚨"
          message: >
            {{ state_attr('sensor.norway_alerts_landslide_vestland', 'alerts')[0].main_text }}
            
            {{ state_attr('sensor.norway_alerts_landslide_vestland', 'alerts')[0].advice_text }}
      - service: light.turn_on
        target:
          entity_id: light.living_room
        data:
          color_name: red
          brightness: 255
```

### Template Sensor Examples

#### Municipality-Specific Alert

```yaml
template:
  - sensor:
      - name: "Bergen Landslide Alert"
        state: >
          {% set alerts = state_attr('sensor.norway_alerts_landslide_vestland', 'alerts') or [] %}
          {% set bergen_alerts = alerts | selectattr('municipalities', 'search', 'Bergen') | list %}
          {{ bergen_alerts[0].level_name if bergen_alerts else 'green' }}
        attributes:
          alert_count: >
            {% set alerts = state_attr('sensor.norway_alerts_landslide_vestland', 'alerts') or [] %}
            {% set bergen_alerts = alerts | selectattr('municipalities', 'search', 'Bergen') | list %}
            {{ bergen_alerts | length }}
          main_text: >
            {% set alerts = state_attr('sensor.norway_alerts_landslide_vestland', 'alerts') or [] %}
            {% set bergen_alerts = alerts | selectattr('municipalities', 'search', 'Bergen') | list %}
            {{ bergen_alerts[0].main_text if bergen_alerts else 'No alerts' }}
```

#### Combined Alert Status

```yaml
template:
  - sensor:
      - name: "All Norway Alerts"
        state: >
          {% set landslide = states('sensor.norway_alerts_landslide_vestland') | int %}
          {% set flood = states('sensor.norway_alerts_flood_vestland') | int %}
          {{ max(landslide, flood) }}
        attributes:
          highest_level: >
            {% set landslide = states('sensor.norway_alerts_landslide_vestland') | int %}
            {% set flood = states('sensor.norway_alerts_flood_vestland') | int %}
            {% set level = max(landslide, flood) %}
            {{ ['green', 'yellow', 'orange', 'red'][level - 1] if level > 0 else 'green' }}
```

---

## Troubleshooting

### Integration Not Found

**Problem**: "Norway Alerts" doesn't appear in the integration list

**Solutions**:
1. Ensure files are in `/config/custom_components/norway_alerts/`
2. Check file permissions (readable by Home Assistant)
3. Restart Home Assistant completely
4. Check logs: **Settings** → **System** → **Logs**

### Cannot Connect Error

**Problem**: "Failed to connect to NVE/Varsom API"

**Solutions**:
1. Check internet connection
2. Verify NVE API is accessible: https://api01.nve.no/
3. Check Home Assistant logs for detailed error messages
4. Try different county or language setting
5. Wait a few minutes and try again (API might be temporarily down)

### No Alerts Showing

**Problem**: Sensor shows `1` (green) with no alerts

**Solutions**:
1. **This is normal if there are no active warnings!**
2. Verify on Varsom.no: https://www.varsom.no/
3. Try a different county that might have active warnings
4. Enable **Test Mode** in configuration to generate fake alerts for testing

### Sensor Not Updating

**Problem**: Data seems stale or not updating

**Solutions**:
1. Check Home Assistant logs for API errors
2. Manually trigger update: 
   - **Developer Tools** → **States** 
   - Find sensor → Click three dots → **Update**
3. Verify internet connection
4. Default update interval is **30 minutes** (this is normal)
5. Restart the integration

### Municipality Filter Not Working

**Problem**: Filtered sensor shows all alerts or no alerts

**Solutions**:
1. Check spelling of municipality names (case-insensitive but must match)
2. Use partial names (e.g., "Berg" will match "Bergen")
3. Check if municipality is actually in the selected county
4. Verify alerts exist for that municipality on Varsom.no
5. Try without filter first to see all available municipalities

### Icons Not Showing

**Problem**: Warning icons not displaying

**Solutions**:
1. Icons are embedded - no action needed
2. Refresh your browser (Ctrl+F5 or Cmd+Shift+R)
3. Clear Home Assistant frontend cache
4. Check entity card is using `entity_picture` (automatic)
5. If using custom cards, ensure they support `entity_picture`

### Testing the Installation

Run these checks to verify everything works:

1. **Check Sensor Exists**
   - Go to **Developer Tools** → **States**
   - Search for `sensor.norway_alerts`
   - Should see your configured sensor(s)

2. **View Attributes**
   - Click on the sensor
   - Verify attributes: `active_alerts`, `county_name`, `alerts` array

3. **Check Logs**
   - Go to **Settings** → **System** → **Logs**
   - Filter for "norway_alerts"
   - Should see successful API fetch messages

4. **Verify Icon**
   - Add sensor to dashboard
   - Icon should appear automatically when alerts are active
   - Enable Test Mode if no real alerts exist

---

## API Information

### Endpoints Used

This integration uses official Norwegian government APIs:

**NVE (Norwegian Water Resources and Energy Directorate)**:
- **Landslide API**: `https://api01.nve.no/hydrology/forecast/landslide/v1.0.10/api`
- **Flood API**: `https://api01.nve.no/hydrology/forecast/flood/v1.0.10/api`
- **Avalanche API**: `https://api01.nve.no/hydrology/forecast/avalanche/v6.3.0`
- **Documentation**: https://api.nve.no/doc/

**Met.no (Norwegian Meteorological Institute)**:
- **MetAlerts API**: `https://api.met.no/weatherapi/metalerts/2.0`
- **Documentation**: https://api.met.no/weatherapi/metalerts/2.0/documentation
- **Format**: CAP (Common Alerting Protocol) 1.2

**Update Interval**: 30 minutes for all sources

### Language Support

The language option controls:
- ✅ Alert text language (Norwegian or English from API)
- ✅ Varsom.no website link language

The API uses the `Språknøkkel` parameter:
- `1` = Norwegian (LangKey: 1 in response)
- `2` = English (LangKey: 2 in response)

### Data Freshness

- Alerts are fetched every **30 minutes**
- NVE typically updates warnings every 1-6 hours
- Critical updates may be more frequent

### API Limitations

- No authentication required (public API)
- No rate limiting currently enforced
- API availability depends on NVE infrastructure
- Historical data not available via this integration

---

## Credits

- **Author**: Jeremy Cook (@jm-cook)
- **Data Sources**: 
  - NVE (Norwegian Water Resources and Energy Directorate) - https://www.varsom.no/
  - Met.no (Norwegian Meteorological Institute) - https://www.met.no/
- **Warning Icons**: Yr warning icons © 2015 by Yr/NRK, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

### Acknowledgments

- Met.no MetAlerts API integration based on code by @kutern84 and @svenove from [met_alerts](https://github.com/kurtern84/met_alerts) (MIT License)
- Icons from the official Yr.no warning icon set  
- API documentation from NVE and Met.no
- Community feedback and contributions

---

## Development

### Technical Details

- Modern coordinator pattern for data fetching
- Config flow with validation
- Single sensor with attribute array architecture
- Embedded base64 SVG icons
- Bilingual support (Norwegian/English)
- Municipality filtering with client-side deduplication

### Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request with clear description

### See Also

- [CHANGELOG.md](CHANGELOG.md) - Version history and changes

---

## License

This integration is provided as-is under the MIT License.

The warning icons are licensed under CC BY 4.0 by Yr/NRK.

---

## Support

- **Issues**: https://github.com/DTekNO/norway_alerts/issues
- **Discussions**: https://github.com/DTekNO/norway_alerts/discussions
- **Documentation**: This README and linked guides

---

**Note**: This integration is not affiliated with NVE, Varsom.no, or Met.no. It provides an interface to their public APIs for use in Home Assistant.

**Last Updated**: January 2026  
**Integration Version**: 2.0.0  
**Minimum HA Version**: 2024.1.0
