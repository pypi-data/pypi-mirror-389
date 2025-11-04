"""

Configuration schema and metadata definitions

"""



from typing import Dict, List, Optional, Any

from dataclasses import dataclass, field

from enum import Enum





class DataType(str, Enum):

    """Data type for expected extraction results"""

    SINGLE_VALUE = "single_value"  # Single string/number

    LIST = "list"  # List of items

    OBJECT = "object"  # Dictionary/object

    NESTED_LIST = "nested_list"  # List of objects





class ResourceType(str, Enum):

    """Type of resource"""

    API_JSON = "api_json"

    API_GRAPHQL = "api_graphql"

    HTML_STATIC = "html_static"

    HTML_RENDERED = "html_rendered"

    HTML_CAPTCHA = "html_captcha"

    CUSTOM_METHOD = "custom_method"





@dataclass

class ConfigMetadata:

    """Metadata for configuration"""

    data_type: DataType

    expected_format: str  # Description of expected format

    sample_value: Optional[Any] = None

    update_frequency: str = "daily"  # daily, hourly, realtime

    requires_auth: bool = False

    is_paginated: bool = False

    version: str = "1.0"

    created_at: Optional[str] = None

    updated_at: Optional[str] = None

    tags: List[str] = field(default_factory=list)





@dataclass

class ResourceConfig:

    """Configuration for a single resource"""

    url: str

    resource_type: ResourceType



    # API-specific

    api_path: Optional[str] = None

    method: str = "get"

    headers: Dict[str, str] = field(default_factory=dict)

    request_data: Optional[Dict] = None



    # HTML-specific

    xpath: Optional[str] = None

    path: Optional[List[Dict]] = None

    is_render_required: bool = False

    is_captcha_based: bool = False

    sleep_time: int = 5

    locator_click: Optional[str] = None



    # Processing

    pre_actions_methods: List[str] = field(default_factory=list)

    actions_methods: List[str] = field(default_factory=list)

    extra_method: Optional[str] = None

    extra_method_kwargs: Dict = field(default_factory=dict)



    # Advanced

    use_proxy: bool = False

    timeout: int = 30
    value : Optional[Any] = None
    retries: int = 3





@dataclass

class MetricConfig:

    """Configuration for a single metric within an entity"""

    name: str  # Metric name (e.g., "energy_consumption", "transaction_count")

    resources: List[ResourceConfig]  # List of resources to try for this metric



    def to_dict(self) -> Dict:

        """Convert to dictionary"""

        return {

            "name": self.name,

            "resources": [

                {

                    "url": r.url,

                    "resource_type": r.resource_type.value,

                    "api_path": r.api_path,

                    "method": r.method,

                    "headers": r.headers,

                    "request_data": r.request_data,

                    "xpath": r.xpath,

                    "path": r.path,

                    "is_render_required": r.is_render_required,

                    "is_captcha_based": r.is_captcha_based,

                    "sleep_time": r.sleep_time,

                    "locator_click": r.locator_click,

                    "pre_actions_methods": r.pre_actions_methods,

                    "actions_methods": r.actions_methods,

                    "extra_method": r.extra_method,

                    "extra_method_kwargs": r.extra_method_kwargs,

                    "use_proxy": r.use_proxy,

                    "timeout": r.timeout,

                    "retries": r.retries

                }

                for r in self.resources

            ]

        }





@dataclass

class ScraperConfig:

    """

    Complete scraper configuration file.



    Structure:

    {

        "metadata": {...},

        "entities": {

            "bitcoin": [{metric_config}, {metric_config}],

            "ethereum": [{metric_config}]

        }

    }



    Output format: List[{name, metric, value, date, config_name}]

    """

    config_name: str  # File name (e.g., "energy_consumption")

    metadata: ConfigMetadata

    entities: Dict[str, List[MetricConfig]]  # entity_name -> list of metrics



    def to_dict(self) -> Dict:

        """Convert to dictionary for JSON serialization"""

        return {

            "metadata": {

                "data_type": self.metadata.data_type.value,

                "expected_format": self.metadata.expected_format,

                "sample_value": self.metadata.sample_value,

                "update_frequency": self.metadata.update_frequency,

                "requires_auth": self.metadata.requires_auth,

                "is_paginated": self.metadata.is_paginated,

                "version": self.metadata.version,

                "created_at": self.metadata.created_at,

                "updated_at": self.metadata.updated_at,

                "capture_date": self.metadata.created_at,  # For compatibility

                "tags": self.metadata.tags

            },

            "entities": {

                entity_name: [metric.to_dict() for metric in metrics]

                for entity_name, metrics in self.entities.items()

            }

        }



    @classmethod

    def from_dict(cls, config_name: str, data: Dict) -> 'ScraperConfig':

        """Create from dictionary"""

        metadata = ConfigMetadata(

            data_type=DataType(data["metadata"]["data_type"]),

            expected_format=data["metadata"]["expected_format"],

            sample_value=data["metadata"].get("sample_value"),

            update_frequency=data["metadata"].get("update_frequency", "daily"),

            requires_auth=data["metadata"].get("requires_auth", False),

            is_paginated=data["metadata"].get("is_paginated", False),

            version=data["metadata"].get("version", "1.0"),

            created_at=data["metadata"].get("created_at"),

            updated_at=data["metadata"].get("updated_at"),

            tags=data["metadata"].get("tags", [])

        )



        # Parse entities

        entities = {}

        for entity_name, metrics_data in data.get("entities", {}).items():

            metrics = []

            for metric_data in metrics_data:

                resources = [

                    ResourceConfig(

                        url=r["url"],

                        resource_type=ResourceType(r["resource_type"]),

                        api_path=r.get("api_path"),

                        method=r.get("method", "get"),

                        headers=r.get("headers", {}),

                        request_data=r.get("request_data"),

                        xpath=r.get("xpath"),

                        path=r.get("path"),

                        is_render_required=r.get("is_render_required", False),

                        is_captcha_based=r.get("is_captcha_based", False),

                        sleep_time=r.get("sleep_time", 5),

                        locator_click=r.get("locator_click"),

                        pre_actions_methods=r.get("pre_actions_methods", []),

                        actions_methods=r.get("actions_methods", []),

                        extra_method=r.get("extra_method"),

                        extra_method_kwargs=r.get("extra_method_kwargs", {}),

                        use_proxy=r.get("use_proxy", False),

                        timeout=r.get("timeout", 30),

                        retries=r.get("retries", 3)

                    )

                    for r in metric_data["resources"]

                ]

                metrics.append(MetricConfig(

                    name=metric_data["name"],

                    resources=resources

                ))

            entities[entity_name] = metrics



        return cls(

            config_name=config_name,

            metadata=metadata,

            entities=entities

        )
