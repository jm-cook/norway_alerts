# Varsom Alerts - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

A Home Assistant custom integration that provides landslide and flood warnings from NVE (Norwegian Water Resources and Energy Directorate) via the Varsom.no API.

## Features

- **Single sensor per county** - Clean, modern design with all alerts in attributes
- **Landslide and flood warnings** - Choose one or both warning types
- **County-based alerts** - Select your Norwegian county
- **Activity levels** - Green (1), Yellow (2), Orange (3), Red (4)
- **Rich alert data** - Includes warning text, advice, consequences, municipalities, and more
- **Direct links** - Each alert includes a link to Varsom.no with an interactive map
- **Bilingual** - Support for Norwegian and English
- **Official Yr.no icons** - Embedded warning icons (no setup required)
- **Municipality filtering** - Optional filtering for specific municipalities within a county

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
   - Add repository URL: `https://github.com/jm-cook/varsom`
   - Category: Integration
   - Click "Add"

2. **Install Integration**
   - Search for "Varsom Alerts" in HACS
   - Click "Download"
   - Restart Home Assistant

3. **Add Integration**
   - Go to **Settings** → **Devices & Services**
   - Click **"+ Add Integration"**
   - Search for "Varsom Alerts"
   - Follow the configuration steps below

### Method 2: Manual Installation

1. **Copy Files**
   - Download the latest release
   - Copy the `custom_components/varsom` folder to your Home Assistant `config/custom_components/` directory
   - The final path should be: `/config/custom_components/varsom/`

2. **Restart Home Assistant**
   - Go to **Settings** → **System** → **Restart**

3. **Add Integration**
   - Go to **Settings** → **Devices & Services**
   - Click **"+ Add Integration"**
   - Search for "Varsom Alerts"

---

## Configuration

### Initial Setup

When adding the integration, you'll be prompted for:

#### 1. County (Required)
Select your Norwegian county from the dropdown:
- Oslo (03)
- Rogaland (11)
- Møre og Romsdal (15)
- Nordland (18)
- Viken (30)
- Innlandet (34)
- Vestfold og Telemark (38)
- Agder (42)
- Vestland (46)
- Trøndelag (50)
- Troms og Finnmark (54)

#### 2. Warning Type (Required)
Choose which warnings to monitor:
- **Landslide**: Monitor landslide warnings only
- **Flood**: Monitor flood warnings only
- **Both**: Monitor both types (combined sensor)

#### 3. Language (Optional, Default: English)
Select the language for alert text and Varsom.no links:
- **English** (en)
- **Norwegian** (no)

#### 4. Municipality Filter (Optional)
Filter alerts to specific municipalities within the county:
- Leave empty to see all alerts in the county
- Enter municipality name(s) separated by commas
- Example: `Bergen, Stord` (only shows alerts affecting these municipalities)
- Creates a second filtered sensor alongside the main sensor

#### 5. Test Mode (Optional, Default: Off)
Enable test mode to inject fake alerts for testing dashboards and automations when there are no active warnings.

### Example Configurations

**Basic - Vestland County Landslide Warnings**
- County: `Vestland`
- Warning Type: `Landslide`
- Language: `English`
- Creates: `sensor.varsom_landslide_vestland`

**With Municipality Filter - Bergen Area Only**
- County: `Vestland`
- Warning Type: `Both`
- Municipality Filter: `Bergen, Askøy, Fjell`
- Creates: 
  - `sensor.varsom_both_vestland` (all alerts)
  - `sensor.varsom_both_vestland_filtered` (Bergen area only)

### Multiple Configurations

You can add multiple instances for different counties or warning types. Each instance polls independently every 30 minutes.

**Example setup:**
- `sensor.varsom_landslide_vestland`
- `sensor.varsom_landslide_rogaland`
- `sensor.varsom_flood_vestland`
- `sensor.varsom_both_oslo`

### Reconfiguring

To change settings after initial setup:
1. Go to **Settings** → **Devices & Services**
2. Find **Varsom Alerts**
3. Click the three dots (⋮) → **Configure**
4. Update your settings and click **Submit**

---

## Sensor Data

### State

The sensor state represents the **highest activity level** (1-4) from all active warnings:

| State | Level | Color | Description |
|-------|-------|-------|-------------|
| `1` | Green | 🟢 | No warnings / Low danger |
| `2` | Yellow | 🟡 | Moderate danger |
| `3` | Orange | 🟠 | Considerable danger |
| `4` | Red | 🔴 | High/Extreme danger |

### Attributes

```yaml
active_alerts: 2
highest_level: "yellow"
highest_level_numeric: 2
county_name: "Vestland"
county_id: "46"
municipality_filter: null  # or "Bergen, Stord" if filtered
alerts:
  - id: "584731"
    master_id: "123456"
    level: 2
    level_name: "yellow"
    danger_type: "Jord- og flomskredfare"
    warning_type: "landslide"
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

| Warning Type | Yellow (2) | Orange (3) | Red (4) |
|-------------|-----------|-----------|---------|
| **Landslide** | 🟡 Landslide | 🟠 Severe Landslide | 🔴 Extreme Landslide |
| **Flood** | 🟡 Flood | 🟠 Severe Flood | 🔴 Extreme Flood |

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

## Dashboard Examples

For comprehensive dashboard card examples, see our dedicated guides:

### 📊 [COMPLETE_DASHBOARD_EXAMPLE.md](COMPLETE_DASHBOARD_EXAMPLE.md)
Complete dashboard layouts with:
- Multi-card layouts
- Vertical stacks
- Conditional displays
- Color-coded severity
- Mobile-optimized views

### 🎨 [FRONTEND_EXAMPLES.md](FRONTEND_EXAMPLES.md)
Advanced frontend examples with:
- Custom card configurations
- Template sensors
- Styling examples
- Integration with maps
- Notification setups

---

## Usage Examples

### Quick Start Examples

#### Basic Entity Card

```yaml
type: entities
title: Landslide Warnings
entities:
  - entity: sensor.varsom_landslide_vestland
    name: Vestland Alert Level
```

#### Markdown Card with Alert Details

```yaml
type: markdown
content: |
  {% set alerts = state_attr('sensor.varsom_landslide_vestland', 'alerts') or [] %}
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
  - alias: "Varsom Yellow Alert Notification"
    trigger:
      - platform: numeric_state
        entity_id: sensor.varsom_landslide_vestland
        above: 1
    action:
      - service: notify.mobile_app
        data:
          title: "Landslide Warning - {{ state_attr('sensor.varsom_landslide_vestland', 'highest_level') | upper }}"
          message: >
            {{ state_attr('sensor.varsom_landslide_vestland', 'alerts')[0].main_text }}
          data:
            url: "{{ state_attr('sensor.varsom_landslide_vestland', 'alerts')[0].url }}"
            tag: "varsom_alert"
            importance: high
```

#### Red Alert Emergency

```yaml
automation:
  - alias: "Varsom Red Alert - Emergency"
    trigger:
      - platform: numeric_state
        entity_id: sensor.varsom_landslide_vestland
        above: 3  # Red level
    action:
      - service: notify.notify
        data:
          title: "🚨 EXTREME WEATHER WARNING 🚨"
          message: >
            {{ state_attr('sensor.varsom_landslide_vestland', 'alerts')[0].main_text }}
            
            {{ state_attr('sensor.varsom_landslide_vestland', 'alerts')[0].advice_text }}
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
          {% set alerts = state_attr('sensor.varsom_landslide_vestland', 'alerts') or [] %}
          {% set bergen_alerts = alerts | selectattr('municipalities', 'search', 'Bergen') | list %}
          {{ bergen_alerts[0].level_name if bergen_alerts else 'green' }}
        attributes:
          alert_count: >
            {% set alerts = state_attr('sensor.varsom_landslide_vestland', 'alerts') or [] %}
            {% set bergen_alerts = alerts | selectattr('municipalities', 'search', 'Bergen') | list %}
            {{ bergen_alerts | length }}
          main_text: >
            {% set alerts = state_attr('sensor.varsom_landslide_vestland', 'alerts') or [] %}
            {% set bergen_alerts = alerts | selectattr('municipalities', 'search', 'Bergen') | list %}
            {{ bergen_alerts[0].main_text if bergen_alerts else 'No alerts' }}
```

#### Combined Alert Status

```yaml
template:
  - sensor:
      - name: "All Varsom Alerts"
        state: >
          {% set landslide = states('sensor.varsom_landslide_vestland') | int %}
          {% set flood = states('sensor.varsom_flood_vestland') | int %}
          {{ max(landslide, flood) }}
        attributes:
          highest_level: >
            {% set landslide = states('sensor.varsom_landslide_vestland') | int %}
            {% set flood = states('sensor.varsom_flood_vestland') | int %}
            {% set level = max(landslide, flood) %}
            {{ ['green', 'yellow', 'orange', 'red'][level - 1] if level > 0 else 'green' }}
```

---

## Troubleshooting

### Integration Not Found

**Problem**: "Varsom Alerts" doesn't appear in the integration list

**Solutions**:
1. Ensure files are in `/config/custom_components/varsom/`
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
   - Search for `sensor.varsom`
   - Should see your configured sensor(s)

2. **View Attributes**
   - Click on the sensor
   - Verify attributes: `active_alerts`, `county_name`, `alerts` array

3. **Check Logs**
   - Go to **Settings** → **System** → **Logs**
   - Filter for "varsom"
   - Should see successful API fetch messages

4. **Verify Icon**
   - Add sensor to dashboard
   - Icon should appear automatically when alerts are active
   - Enable Test Mode if no real alerts exist

---

## API Information

### Endpoints Used

This integration uses the official NVE API:

- **Landslide API**: `https://api01.nve.no/hydrology/forecast/landslide/v1.0.10/api`
- **Flood API**: `https://api01.nve.no/hydrology/forecast/flood/v1.0.10/api`
- **Update Interval**: 30 minutes
- **Documentation**: https://api.nve.no/doc/

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
- **Data Source**: NVE (Norwegian Water Resources and Energy Directorate)
- **Website**: https://www.varsom.no/
- **Warning Icons**: Yr warning icons © 2015 by Yr/NRK, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

### Acknowledgments

- Based on patterns from the Met Alerts integration
- Icons from the official Yr.no warning icon set
- API documentation from NVE
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

- [DEV_SUMMARY.md](DEV_SUMMARY.md) - Technical development notes and architecture
- [CHANGELOG.md](CHANGELOG.md) - Version history and changes

---

## License

This integration is provided as-is under the MIT License.

The warning icons are licensed under CC BY 4.0 by Yr/NRK.

---

## Support

- **Issues**: https://github.com/jm-cook/varsom/issues
- **Discussions**: https://github.com/jm-cook/varsom/discussions
- **Documentation**: This README and linked guides

---

**Note**: This integration is not affiliated with NVE or Varsom.no. It provides an interface to their public API for use in Home Assistant.

**Last Updated**: December 2025  
**Integration Version**: 1.0.0  
**Minimum HA Version**: 2024.1.0
