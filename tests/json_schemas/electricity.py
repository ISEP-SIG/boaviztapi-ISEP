available_countries_schema = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Generated schema for Root",
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "EIC_code": {
        "type": "string"
      },
      "country_name": {
        "type": "string"
      },
      "alpha_3": {
        "type": "string"
      }
    },
    "required": [
      "EIC_code",
      "country_name",
      "alpha_3"
    ]
  }
}