PUBLIC_API_URL = "https://api.sipametrics.com"
URLS = {
    "_check_permissions": f"{PUBLIC_API_URL}/iam-service/v1.1/permissions/resources",
    "metrics": f"{PUBLIC_API_URL}/data-service/v2/queries/metrics",
    "infra_equity_comparable": f"{PUBLIC_API_URL}/compute-service/v2/pi-comparables/average/by/profiles",
    "infra_debt_comparable": f"{PUBLIC_API_URL}/compute-service/v2/pi-comparables/average/by/profiles",
    "private_equity_comparable": f"{PUBLIC_API_URL}/compute-service/v2/pe-comparables/average/by/profiles",
    "private_equity_comparable_boundaries": f"{PUBLIC_API_URL}/compute-service/v2/pe-comparables/boundaries/by/profiles",
    "term_structure": f"{PUBLIC_API_URL}/data-service/v2/yields",
    "indices_catalogue": f"{PUBLIC_API_URL}/data-service/v2/lists/indices",
    "metrics_catalogue": f"{PUBLIC_API_URL}/data-service/v2/lists/types/{{app}}",
    "taxonomies": f"{PUBLIC_API_URL}/data-service/v2/lists/taxonomy/{{taxonomy}}",
    "private_infra_custom_benchmarks": f"{PUBLIC_API_URL}/compute-service/v2.1/pi-custom-index/metrics",
    "private_equity_custom_benchmarks": f"{PUBLIC_API_URL}/compute-service/v2.1/pe-custom-index/metrics",
    "private_equity_region_tree": f"{PUBLIC_API_URL}/compute-service/v2/pe-comparables/region-tree",
    "direct_alpha": f"{PUBLIC_API_URL}/compute-service/v1/alpha/compute"
}
VERSION = "v2"
SOURCE = "privateMetrics-python-sdk"