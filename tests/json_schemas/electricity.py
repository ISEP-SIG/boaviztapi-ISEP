available_countries_schema = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Generated schema for Root",
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "zone_code": {
        "type": "string"
      },
      "name": {
        "type": "string"
      },
      "subdivision_name": {
        "type": "string"
      },
      "EIC_code": {
        "type": "string"
      },
      "alpha_3": {
        "type": "string"
      }
    },
    "required": [
      "zone_code",
      "name",
      "subdivision_name",
      "EIC_code",
      "alpha_3"
    ]
  }
}