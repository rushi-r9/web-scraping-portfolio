"""Field definitions for the local HTML-fixture demonstrations."""
SCHEMAS = {
    "products": {"required": ["sku", "name", "price", "url"], "fields": ["sku", "name", "price", "currency", "category", "availability", "rating", "description", "url"], "id_field": "sku"},
    "properties": {"required": ["listing_id", "title", "price", "location", "url"], "fields": ["listing_id", "title", "price", "currency", "location", "property_type", "bedrooms", "area_sqft", "description", "url"], "id_field": "listing_id"},
    "jobs": {"required": ["job_id", "title", "company", "location", "url"], "fields": ["job_id", "title", "company", "location", "salary", "employment_type", "experience", "description", "url"], "id_field": "job_id"},
    "businesses": {"required": ["business_id", "name", "category", "location", "source_url"], "fields": ["business_id", "name", "category", "website", "phone", "location", "source_url"], "id_field": "business_id"},
}
