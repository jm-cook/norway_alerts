# Included Blueprints

The Norway Alerts integration includes blueprints to help you display alerts in your dashboard.

## CAP Alert Markdown Sensor

**Location**: `blueprints/template/cap_alert_markdown_sensor.yaml`

This blueprint creates a template sensor that formats your Norway Alerts (or any CAP-formatted alert sensor) into beautifully formatted markdown for display in a markdown card.

### Features

- **Status Indicators**: Shows if alerts are Expected (⏰), Ongoing (⚠️), or Ended (✅)
- **Alert Icons**: Displays warning icons specific to each alert type and severity
- **Formatted Dates**: Shows dates and times in a readable format
- **Multiple Alerts**: Handles and displays multiple active alerts
- **Map Support**: Displays alert maps when available (for MetAlerts)
- **Configurable**: Toggle icons, status, and maps on/off

### Installation

#### Method 1: Import from GitHub (Recommended)

1. Go to **Settings → Automations & Scenes → Blueprints** in Home Assistant
2. Click the **Import Blueprint** button (bottom right)
3. Enter this URL:
   ```
   https://github.com/jm-cook/norway_alerts/blob/main/blueprints/template/cap_alert_markdown_sensor.yaml
   ```
4. Click **Preview Blueprint** then **Import Blueprint**

#### Method 2: Manual Installation

1. Download [cap_alert_markdown_sensor.yaml](https://github.com/jm-cook/norway_alerts/blob/main/blueprints/template/cap_alert_markdown_sensor.yaml)
2. Copy it to your Home Assistant `config/blueprints/template/` folder
3. Restart Home Assistant (if needed)

### Usage

After importing the blueprint, add this to your `configuration.yaml`:

```yaml
template:
  - use_blueprint:
      path: jm-cook/cap_alert_markdown_sensor.yaml # relative to config/blueprints/template/
      input:
        alert_sensor: sensor.weather_alerts_home
        show_icon: true
        show_status: true
        show_map: true
    name: weather_alerts_home_formatted
    unique_id: weather_alerts_home_formatted
```

**Configuration options:**
- **alert_sensor**: Your Norway Alerts sensor entity ID (required)
- **show_icon**: Display warning icons next to titles (default: `true`)
- **show_status**: Show Expected/Ongoing/Ended status (default: `true`)
- **show_map**: Display alert maps when available (default: `true`)

After adding to `configuration.yaml`, **restart Home Assistant** to create the sensor.

### Usage in Dashboard

After creating the sensor, add a markdown card to your dashboard:

```yaml
type: markdown
content: |
  {{ state_attr('sensor.cap_alerts_formatted', 'formatted_content') }}
title: Active Weather Alerts
```

Replace `sensor.cap_alerts_formatted` with whatever name you chose in step 4.

### Example Output

The blueprint formats alerts like this:

```
### 🌀 Orange wind warning

**Status**: ⚠️ Ongoing

**Severity**: ORANGE

**Type**: orange; wind

**Valid Period**: January 13, 14:00 to January 14, 06:00

#### Description
Strong winds expected with gusts up to 25 m/s. This may cause damage to infrastructure and disrupt outdoor activities.

#### Instructions
Secure loose objects. Avoid unnecessary travel. Stay informed about weather updates.

#### Consequences
Damage to infrastructure possible. Travel disruptions expected. Outdoor activities hazardous.

**Area**: Vestland, Bergen

**Certainty**: Likely | **Severity**: Moderate

---
```

### Customization

The sensor's `formatted_content` attribute contains the full markdown. You can:

- Use conditional cards to only show when there are active alerts
- Combine multiple alert sensors in one card
- Style the markdown card with card-mod

### Requirements

- Home Assistant 2023.4 or later (for template sensor blueprints)
- Norway Alerts integration installed with CAP format enabled
- Or any other sensor providing CAP-formatted alerts

### Compatibility

This blueprint works with:
- Norway Alerts sensors (with `cap_format: true`)
- MetAlerts integration sensors
- Any custom integration following the CAP standard

The sensor must provide an `alerts` attribute containing a list of alert objects with these fields:
- `title`, `description`, `starttime`, `endtime`
- `severity`, `event_awareness_name`, `awareness_level_color`
- `certainty`, `entity_picture` (optional), `map_url` (optional)
