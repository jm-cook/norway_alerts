# Formatted Content Template

The `formatted_content` attribute is automatically generated for **CAP-formatted alerts only** using the Jinja2 template located in:
`custom_components/norway_alerts/templates/formatted_content.j2`

This applies to:
- **Weather alerts** (Met.no) - always in CAP format
- **NVE warnings** (landslide, flood, avalanche) - only when "Enable CAP format" is checked in configuration

> **Note**: Non-CAP NVE sensors will not have a `formatted_content` attribute. Use the blueprint template sensor for custom formatting in those cases.

## Customization

You can customize the display format by editing the template file directly. The template has access to:

### Variables
- `alerts` - List of enriched alert dictionaries
- `show_icon` - Boolean flag for icon display (from config)
- `show_status` - Boolean flag for status display (from config)
- `show_map` - Boolean flag for map display (from config)
- `now_timestamp` - Current timestamp for comparison

### Alert Fields
Each alert in the `alerts` list contains:
- `title` - Alert title
- `description` - Alert description
- `instruction` - Safety instructions
- `consequences` - Potential consequences
- `area` - Affected area (auto-generated from municipalities if not present)
- `entity_picture` - URL to alert icon
- `map_url` - URL to alert map
- `awareness_level_color` - Severity color name
- `event_awareness_name` - Event type name
- `certainty` - Certainty level
- `severity` - Severity level
- `starttime_timestamp` - Start time as Unix timestamp
- `endtime_timestamp` - End time as Unix timestamp
- `start_formatted` - Formatted start time string
- `end_formatted` - Formatted end time string

## Example

To change the time format, modify lines like:
```jinja2
🔵 {{ alert.start_formatted }} - increasing danger
```

To add new fields, access them from the alert dictionary:
```jinja2
{% if alert.get('some_new_field') %}
**New Field**: {{ alert.some_new_field }}
{% endif %}
```
