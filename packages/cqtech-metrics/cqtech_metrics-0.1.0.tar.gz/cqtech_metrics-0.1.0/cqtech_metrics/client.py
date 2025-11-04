"""Main client for CQTech Metrics SDK"""
import time
import requests
from typing import Optional, Dict, Any, List
from .models.auth import TokenResponse, TokenResponseData, TokenRequest
from .models.scenes import (
    SceneVersionQuery, SceneVersionWithPermissionQuery, 
    SceneVersionMetricInstancesQuery, SceneVersionMetricInstancesWithVersionsQuery,
    SceneVersionResponse, SceneVersionWithPermissionResponse, 
    SceneVersionMetricInstancesResponse, SceneVersionMetricInstanceLineageResponse,
    SceneVersionMetricInstancesWithVersionsResponse
)
from .models.metrics import (
    MetricQuery, MetricResultsByCodeResponse, MetricDetailResponse, 
    MetricTagsResponse, MetricDistinctFieldResponse,
    MetricResultsByIdResponse
)
from .models.scenes import SceneVersionMetricInstanceLineage
from .utils import generate_checksum, generate_nonce, format_auth_header
from .exceptions import AuthenticationError, APIError

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv is optional, so if it's not installed, just continue
    pass


class CQTechClient:
    """Main client for interacting with CQTech Metrics API"""
    
    def __init__(self, base_url: Optional[str] = None, app_key: Optional[str] = None, 
                 secret: Optional[str] = None, username: Optional[str] = None, 
                 verify_ssl: bool = True, timeout: int = 30):
        """
        Initialize the client
        
        Args:
            base_url: The base URL of the CQTech Metrics API (e.g., https://api.example.com).
                     If not provided, will attempt to read from CQTECH_BASE_URL environment variable.
            app_key: Your application key. If not provided, will attempt to read from 
                     CQTECH_APP_KEY environment variable.
            secret: Your application secret. If not provided, will attempt to read from 
                    CQTECH_SECRET environment variable.
            username: Your username. If not provided, will attempt to read from 
                      CQTECH_USERNAME environment variable.
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
        """
        import os
        
        # Get values from parameters or environment variables
        self.base_url = (base_url or os.getenv('CQTECH_BASE_URL', '')).rstrip('/')
        self.app_key = app_key or os.getenv('CQTECH_APP_KEY', '')
        self.secret = secret or os.getenv('CQTECH_SECRET', '')
        self.username = username or os.getenv('CQTECH_USERNAME', '')
        
        # Validate required parameters are provided
        if not self.base_url:
            raise ValueError("base_url must be provided either as parameter or CQTECH_BASE_URL environment variable")
        if not self.app_key:
            raise ValueError("app_key must be provided either as parameter or CQTECH_APP_KEY environment variable")
        if not self.secret:
            raise ValueError("secret must be provided either as parameter or CQTECH_SECRET environment variable")
        if not self.username:
            raise ValueError("username must be provided either as parameter or CQTECH_USERNAME environment variable")
        
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        
        # Session for connection pooling
        self.session = requests.Session()
        
        # Token cache
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[int] = None
    
    def _ensure_valid_token(self):
        """Ensure we have a valid access token, refresh if needed"""
        if (self._access_token is None or 
            self._token_expires_at is None or 
            time.time() >= self._token_expires_at - 60):  # Refresh 1 minute before expiration
            # Import here to avoid circular import
            from .auth import CQTechAuthClient
            auth_client = CQTechAuthClient(self)
            auth_client.authenticate()
    
    def _make_request(self, method: str, endpoint: str, headers: Optional[Dict] = None, 
                     json_data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make an authenticated request to the API"""
        # Ensure we have a valid token
        self._ensure_valid_token()
        
        # Prepare headers
        if headers is None:
            headers = {}
        
        # Add authentication header
        if self._access_token:
            headers.update(format_auth_header(self._access_token))
        
        # Only set content-type if we're sending JSON
        if json_data is not None and 'content-type' not in headers:
            headers['content-type'] = 'application/json'
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=json_data,
                params=params,
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            
            # Parse response
            response_data = response.json()
            
            # Check for API errors
            if response.status_code >= 400 or (isinstance(response_data, dict) and response_data.get('code') != 0):
                error_code = response_data.get('code', response.status_code)
                error_msg = response_data.get('msg', 'Unknown error')
                raise APIError(error_code, error_msg)
            
            return response_data
            
        except requests.exceptions.RequestException as e:
            raise APIError(500, f"Request failed: {str(e)}")
        except ValueError as e:  # JSON decode error
            raise APIError(500, f"Invalid JSON response: {str(e)}")

    # Authentication Endpoint
    def get_app_token(self, username: str, app_key: str, secret: str) -> TokenResponse:
        """
        Get APP token for authentication (API endpoint 1)
        
        This interface is used for authentication. You need to call this interface
        before calling any other interfaces to obtain a token, and the token has
        an expiration time. When it expires, you need to call this interface again
        to get a new access_token.
        
        URL: POST /open-api/system/oauth2-openapi/token
        
        Header parameters:
        - appkey (str, required): Application number (found in the metric center platform 
          -> Third-party Application Open -> Application Management)
        - nonce (int, required): 10-digit random number
        - curtime (int, required): Current timestamp in seconds (not milliseconds)
        - username (str, required): Current login user number
        - checksum (str, required): Signature using SHA1 encryption of username, 
          secret, nonce, and curtime
        
        Returns:
            TokenResponse: Response containing access_token, refresh_token, token_type, 
            and expires_in fields
            
        Example:
            response = client.get_app_token(
                username="19950174",
                app_key="ZNZSCS",
                secret="xxxxxxxxxxxxxxxxxxxxxxx"
            )
            # Use response.data.access_token for subsequent API calls
        """
        import time
        from .utils import generate_checksum, generate_nonce
        
        nonce = generate_nonce()
        curtime = int(time.time())
        checksum = generate_checksum(username, secret, nonce, curtime)
        
        headers = {
            "appkey": app_key,
            "checksum": checksum,
            "curtime": str(curtime),
            "nonce": str(nonce),
            "username": username
        }
        
        response_data = self.session.post(
            f"{self.base_url}/open-api/system/oauth2-openapi/token",
            headers=headers,
            verify=self.verify_ssl,
            timeout=self.timeout
        ).json()
        
        return TokenResponse(**response_data)

    # Scene Version Endpoints
    def query_all_scene_versions(self, query: SceneVersionQuery) -> SceneVersionResponse:
        """
        Query all scene versions under application (API endpoint 2)
        
        This interface is suitable for third-party application management end to configure
        scene versions. It can query all scene versions accessible under the application,
        regardless of the login user's permissions.
        
        URL: POST /open-api/metric/scene/versions
        
        Header parameters:
        - Authorization (str, required): Authentication token obtained through the
          get_app_token interface, passed via request header: 
          "authorization": "Bearer ${access_token}"
        
        Request body parameters:
        - name (str, optional): Scene version name for fuzzy query
        - sceneVersionStatus (int, optional): Scene version status (0: offline, 
          1: online). If not passed, queries all statuses
        - pageNum (int, required): Current page number for pagination
        - pageSize (int, required): Number of items per page for pagination
        
        Returns:
            SceneVersionResponse: Response containing a list of scene versions and total count
            
        Example:
            query = SceneVersionQuery(
                name="学生",
                sceneVersionStatus=1,
                pageNum=1,
                pageSize=10
            )
            response = client.query_all_scene_versions(query)
        """
        response_data = self._make_request(
            method="POST",
            endpoint="/open-api/metric/scene/versions",
            json_data=query.model_dump(exclude_none=True)
        )
        return SceneVersionResponse(**response_data)

    def query_scene_versions_with_permission(self, query: SceneVersionWithPermissionQuery) -> SceneVersionWithPermissionResponse:
        """
        Query scene versions by app permission (API endpoint 3)
        
        This interface is suitable for third-party application user end to configure
        scene versions. It can query scene versions that the current user has access
        permissions for under the application.
        
        URL: POST /open-api/metric/scene/versions/with-permission
        
        Header parameters:
        - Authorization (str, required): Authentication token obtained through the
          get_app_token interface, passed via request header: 
          "authorization": "Bearer ${access_token}"
        
        Request body parameters:
        - name (str, optional): Scene version name for fuzzy query
        - sceneVersionStatus (int, optional): Scene version status (0: offline, 
          1: online). If not passed, queries all statuses
        - pageNum (int, required): Current page number for pagination
        - pageSize (int, required): Number of items per page for pagination
        
        Returns:
            SceneVersionWithPermissionResponse: Response containing a list of scene versions 
            that the user has permission to access, and total count
            
        Example:
            query = SceneVersionWithPermissionQuery(
                name="学生",
                sceneVersionStatus=1,
                pageNum=1,
                pageSize=10
            )
            response = client.query_scene_versions_with_permission(query)
        """
        response_data = self._make_request(
            method="POST",
            endpoint="/open-api/metric/scene/versions/with-permission",
            json_data=query.model_dump(exclude_none=True)
        )
        return SceneVersionWithPermissionResponse(**response_data)

    # Metric Instance Endpoints
    def query_metric_instances_by_scene_version(self, query: SceneVersionMetricInstancesQuery) -> SceneVersionMetricInstancesResponse:
        """
        Query metric instances and dependencies by scene version UID (API endpoint 4)
        
        This interface can query metric instance information, definition information,
        and the definition information of dependent metrics based on a specific scene
        version for which the logged-in user has permissions.
        
        URL: POST /open-api/metric/scene/version/metric-instances
        
        Header parameters:
        - Authorization (str, required): Authentication token obtained through the
          get_app_token interface, passed via request header: 
          "authorization": "Bearer ${access_token}"
        
        Request body parameters:
        - sceneVersionUid (str, required): Scene version UID to determine which scene
          version's metric instances to query
        - instanceCodes (List[str], optional): Metric instance codes for filtering.
          If not passed, queries all metric instances the user has permission to access
        - metricInstanceName (str, optional): Metric instance name for fuzzy query
        - tags (List[str], optional): Metric tags for filtering metric instances
        - state (int, optional): Metric instance state (0: offline, 1: online).
          If not passed, queries all states
        - pageNum (int, required): Current page number for pagination
        - pageSize (int, required): Number of items per page for pagination
        
        Returns:
            SceneVersionMetricInstancesResponse: Response containing a list of metric 
            instances with their definitions and dependencies, and total count
            
        Example:
            query = SceneVersionMetricInstancesQuery(
                sceneVersionUid="7dda43b03da04ef79ca935ac14a1ca60",
                instanceCodes=["byxf"],
                metricInstanceName="消费",
                tags=["校园卡组件"],
                state=1,
                pageNum=1,
                pageSize=10
            )
            response = client.query_metric_instances_by_scene_version(query)
        """
        response_data = self._make_request(
            method="POST",
            endpoint="/open-api/metric/scene/version/metric-instances",
            json_data=query.model_dump(exclude_none=True)
        )
        return SceneVersionMetricInstancesResponse(**response_data)

    def query_metric_instance_lineage(self, query: SceneVersionMetricInstancesQuery) -> SceneVersionMetricInstanceLineageResponse:
        """
        Query metric lineage by scene version UID including data models (API endpoint 5)
        
        This interface can query metric instance lineage information based on a specific
        scene version for which the logged-in user has permissions. This includes 
        dependent metrics, data models, data sources, and data tables.
        
        URL: POST /open-api/metric/scene/version/metric-instance/lineage
        
        Header parameters:
        - Authorization (str, required): Authentication token obtained through the
          get_app_token interface, passed via request header: 
          "authorization": "Bearer ${access_token}"
        
        Request body parameters:
        - sceneVersionUid (str, required): Scene version UID to determine which scene
          version's metric instances to query
        - instanceCodes (List[str], optional): Metric instance codes for filtering.
          If not passed, queries all metric instances the user has permission to access
        
        Response fields:
        - id (int): Metric instance ID
        - name (str): Metric instance name
        - code (str): Metric instance code
        - type (int): Data type (1: metric, 2: data model, 3: data source, 4: data table)
        - state (int): Metric instance state
        - definition (dict): Metric definition information
        - children (list): Dependent data including dependent metric instances, 
          data models, data sources, data tables
        
        Returns:
            SceneVersionMetricInstanceLineageResponse: Response containing lineage 
            information of metric instances
            
        Example:
            query = SceneVersionMetricInstancesQuery(
                sceneVersionUid="7dda43b03da04ef79ca935ac14a1ca60",
                instanceCodes=["byxf"]
            )
            response = client.query_metric_instance_lineage(query)
        """
        response_data = self._make_request(
            method="POST",
            endpoint="/open-api/metric/scene/version/metric-instance/lineage",
            json_data=query.model_dump(exclude_none=True)
        )
        return SceneVersionMetricInstanceLineageResponse(**response_data)

    # Metric Result Endpoints
    def query_metric_results_by_codes(self, query: MetricQuery) -> MetricResultsByCodeResponse:
        """
        Query metric results and assessments by multiple instance codes (API endpoint 6)
        
        This interface can query metric instance execution results and assessment information,
        including real-time metric recalculation results based on metric instance execution
        results, and scenarios where the same metric instance needs to query 2 different
        parameter sets of results simultaneously.
        
        URL: POST /open-api/metric/instance/codes/measure
        
        Header parameters:
        - Authorization (str, required): Authentication token obtained through the
          get_app_token interface, passed via request header: 
          "authorization": "Bearer ${access_token}"
        
        Request body parameters:
        - sceneVersionUid (str, required): Scene version UID to determine which scene
          version's metric instances to query
        - recalculate (bool, optional): Metric recalculation flag. If true, uses the 
          metric instance's default recalculation SQL for real-time calculation results.
          If there is no default recalculation SQL, returns the original metric instance
          calculation results
        - instanceCodes (List[str], optional): Metric instance codes for filtering.
          If not passed, queries all metric instances the user has permission to access
        - globalFilter (dict, optional): Global filter conditions for all metric instances
        - instances (list, optional): Per-metric-instance parameter differences to define
          dimensions, filter conditions, etc. for each metric instance individually
        
        The globalFilter structure includes:
        - op (str): Logical operation (AND, OR)
        - exprs (list): Filter items
        - querys (list): Nested filters
        
        Returns:
            MetricResultsByCodeResponse: Response containing metric results and assessments
            with dynamic keys based on instance codes or IDs
            
        Example:
            query = MetricQuery(
                sceneVersionUid="7dda43b03da04ef79ca935ac14a1ca60",
                instanceCodes=["byxf"],
                instances=[
                    {
                        "instanceCode": "byxf",
                        "dims": ["商户名称"],
                        "id": "byxf_max",
                        "recalculate": True
                    }
                ]
            )
            response = client.query_metric_results_by_codes(query)
        """
        response_data = self._make_request(
            method="POST",
            endpoint="/open-api/metric/instance/codes/measure",
            json_data=query.model_dump(exclude_none=True)
        )
        return MetricResultsByCodeResponse(**response_data)

    def query_metric_results_by_ids(self, query: MetricQuery) -> MetricResultsByIdResponse:
        """
        Query metric results and assessments by multiple instance IDs (API endpoint 7)
        
        This interface can query metric instance execution results and assessment information,
        including real-time metric recalculation results based on metric instance execution
        results, and scenarios where the same metric instance needs to query 2 different
        parameter sets of results simultaneously. This is similar to endpoint 6 but uses
        metric instance IDs instead of codes.
        
        URL: POST /open-api/metric/instance/ids/measure
        
        Header parameters:
        - Authorization (str, required): Authentication token obtained through the
          get_app_token interface, passed via request header: 
          "authorization": "Bearer ${access_token}"
        
        Request body parameters:
        - sceneVersionUid (str, required): Scene version UID to determine which scene
          version's metric instances to query
        - recalculate (bool, optional): Metric recalculation flag. If true, uses the 
          metric instance's default recalculation SQL for real-time calculation results.
          If there is no default recalculation SQL, returns the original metric instance
          calculation results
        - instanceIds (List[int], optional): Metric instance IDs for filtering.
          If not passed, queries all metric instances the user has permission to access
        - globalFilter (dict, optional): Global filter conditions for all metric instances
        - instances (list, optional): Per-metric-instance parameter differences to define
          dimensions, filter conditions, etc. for each metric instance individually
        
        The instances items structure includes:
        - instanceId (int): Metric instance ID to determine which metric instance to query,
          metric instance execution results will use this ID as key
        - dims (List[str]): Dimensions to determine which dimensional execution results to query
        - filter (dict): Filter conditions for the current metric instance that will not 
          follow globalFilter
        - id (str): Metric instance alias suitable for the same metric instance, if different
          parameters are needed to query multiple execution results, different IDs can be
          passed, and the returned metric instance execution results will use this ID as key
        - recalculate (bool): Metric recalculation flag
        - recalculateCode (str): Recalculation code used when recalculate is true, instead
          of the default recalculation SQL
        
        Returns:
            MetricResultsByIdResponse: Response containing metric results and assessments
            with dynamic keys based on instance IDs
            
        Example:
            query = MetricQuery(
                sceneVersionUid="7dda43b03da04ef79ca935ac14a1ca60",
                instanceIds=[4021],
                instances=[
                    {
                        "instanceId": 4021,
                        "dims": ["商户名称"],
                        "id": "byxf_max",
                        "recalculate": True
                    }
                ]
            )
            response = client.query_metric_results_by_ids(query)
        """
        response_data = self._make_request(
            method="POST",
            endpoint="/open-api/metric/instance/ids/measure",
            json_data=query.model_dump(exclude_none=True)
        )
        return MetricResultsByIdResponse(**response_data)

    # Detail Data Endpoints
    def query_metric_instance_detail(self, query: MetricQuery) -> MetricDetailResponse:
        """
        Query metric instance detail data (API endpoint 8)
        
        This interface can query detailed (underlying) data based on metric instance
        execution statistics results, generally used for drilling down from statistics
        to details.
        
        URL: POST /open-api/metric/instance/detail
        
        Header parameters:
        - Authorization (str, required): Authentication token obtained through the
          get_app_token interface, passed via request header: 
          "authorization": "Bearer ${access_token}"
        
        Request body parameters:
        - sceneVersionUid (str, required): Scene version UID to determine which scene
          version to query
        - instanceId (int, required): Metric instance ID (higher priority than instanceCode;
          if both are provided, takes instanceId). Used to determine which metric 
          instance's details to query
        - instanceCode (str, optional): Metric instance code (lower priority than instanceId)
        - filter (dict, optional): Detail data filter conditions, structure same as globalFilter
        - orderField (str, optional): Field name for sorting (used for table display details)
        - orderType (str, optional): Sort direction: asc (ascending) or desc (descending)
        - pageNum (int, required): Current page number for pagination
        - pageSize (int, required): Number of items per page for pagination
        
        Returns:
            MetricDetailResponse: Response containing detailed data, columns, and total count
            - list: Detailed records list, each item is an object
            - columns: Detail fields list for building table headers, each with alias and type
            - total: Total number of detailed records
            
        Example:
            query = MetricQuery(
                sceneVersionUid="7dda43b03da04ef79ca935ac14a1ca60",
                instanceId=4021,
                pageNum=1,
                pageSize=10
            )
            response = client.query_metric_instance_detail(query)
        """
        # Only include required fields for this endpoint
        detail_query = {
            k: v for k, v in query.model_dump(exclude_none=True).items() 
            if k in ['sceneVersionUid', 'instanceId', 'instanceCode', 'filter', 
                     'orderField', 'orderType', 'pageNum', 'pageSize']
        }
        response_data = self._make_request(
            method="POST",
            endpoint="/open-api/metric/instance/detail",
            json_data=detail_query
        )
        return MetricDetailResponse(**response_data)

    def query_distinct_field_values(self, query: MetricQuery) -> MetricDistinctFieldResponse:
        """
        Query distinct values of a field in detail data (API endpoint 9)
        
        Used to query all possible values for a specific field in the detailed data
        (for building dropdown filter options for that field). After getting detailed
        data, this interface can be called based on a field to get all different options.
        
        URL: POST /open-api/metric/instance/detail-distinct-field
        
        Header parameters:
        - Authorization (str, required): Authentication token obtained through the
          get_app_token interface, passed via request header: 
          "authorization": "Bearer ${access_token}"
        
        Request body parameters:
        - sceneVersionUid (str, required): Scene version UID to determine which scene
          version to query under
        - instanceId (int, required): Metric instance ID to determine which metric 
          instance's details to query. Higher priority than instanceCode.
        - instanceCode (str, optional): Metric instance code (lower priority than instanceId)
        - filter (dict, optional): Detail data filter conditions, structure same as globalFilter
        - columnAlias (str, required): Field alias to query distinct values for
        - searchValue (str, optional): Fuzzy search keyword for filtering option names
        - pageNum (int, required): Current page number for pagination
        - pageSize (int, required): Number of items per page for pagination
        
        Returns:
            MetricDistinctFieldResponse: Response containing a list of distinct field values
            after deduplication
            
        Example:
            query = MetricQuery(
                sceneVersionUid="7dda43b03da04ef79ca935ac14a1ca60",
                instanceId=4021,
                columnAlias="商户名称",
                pageNum=1,
                pageSize=10
            )
            response = client.query_distinct_field_values(query)
        """
        # Only include required fields for this endpoint
        distinct_query = {
            k: v for k, v in query.model_dump(exclude_none=True).items() 
            if k in ['sceneVersionUid', 'instanceId', 'instanceCode', 'filter',
                     'columnAlias', 'searchValue', 'pageNum', 'pageSize']
        }
        response_data = self._make_request(
            method="POST",
            endpoint="/open-api/metric/instance/detail-distinct-field",
            json_data=distinct_query
        )
        return MetricDistinctFieldResponse(**response_data)

    # Multiple Scene Versions Endpoints
    def query_metric_instances_with_versions(
        self, 
        query: SceneVersionMetricInstancesWithVersionsQuery
    ) -> SceneVersionMetricInstancesWithVersionsResponse:
        """
        Query metric instances by multiple scene version UIDs (API endpoint 11)
        
        This interface is suitable for scenarios that need to query metric instances
        based on multiple scene versions. It allows querying user-permissioned metric 
        instances from multiple scene versions in a single request.
        
        URL: POST /open-api/metric/scene/version/metric-instances-withVersions
        
        Header parameters:
        - Authorization (str, required): Authentication token obtained through the
          get_app_token interface, passed via request header: 
          "authorization": "Bearer ${access_token}"
        
        Request body parameters:
        - sceneVersionUids (List[str], required): Scene version UIDs to determine 
          which scene versions' metric instances to query
        - tags (List[str], optional): Metric tags for filtering metric instances,
          allowing tag-based search of metric instances
        
        Returns:
            SceneVersionMetricInstancesWithVersionsResponse: Response containing 
            a list of metric instances with their scene version UID, including:
            - sceneVersionUid (str): Scene version UID associated with the metric instance
            - id (int): Metric instance ID
            - name (str): Metric instance name
            - code (str): Metric instance code
            - state (int): Metric instance state (0: offline, 1: online)
            - definition (dict): Metric definition information
            - recalculateList (list): List of metric instance recalculations
            
        Definition object includes:
        - id (int): Metric definition ID
        - name (str): Metric definition name
        - uid (str): Metric definition UID
        - type (int): Metric type (1: atomic, 2: derived, 3: composite, 4: custom)
        - versionName (str): Metric version name
        - versionUuid (str): Metric version UID
        - metadata (dict): Metric metadata with pre-defined meanings: 
          metric_source (metric source), metric_paraphrase (metric explanation),
          metric_data_source (data source)
        - metricDomain (dict): Metric domain
        - tags (list): Tags
        - departments (list): Responsible departments
        - logic (str): Calculation rules
        - remark (str): Metric summary
        
        RecalculateList object includes:
        - id (int): Metric recalculation ID
        - metricInstanceId (int): Metric instance ID
        - name (str): Metric recalculation name
        - code (str): Metric recalculation code
        - queryLanguage (str): Metric recalculation SQL statement
        - measureCol (str): Measure field
        - dimCols (list): Dimension fields (dimension_desc represents dimension value
          descriptions, may be empty)
        - isDefault (bool): Whether is default (true: default, false: not default)
        
        Example:
            query = SceneVersionMetricInstancesWithVersionsQuery(
                sceneVersionUids=["7dda43b03da04ef79ca935ac14a1ca60"],
                tags=["校园卡组件"]
            )
            response = client.query_metric_instances_with_versions(query)
        """
        response_data = self._make_request(
            method="POST",
            endpoint="/open-api/metric/scene/version/metric-instances-withVersions",
            json_data=query.model_dump(exclude_none=True)
        )
        return SceneVersionMetricInstancesWithVersionsResponse(**response_data)

    def get_metric_tags(self) -> MetricTagsResponse:
        """
        Get list of tags defined in metric management (API endpoint 12)
        
        This interface can query metric tag options, used for tag-based searching
        of metric instances in interfaces 4 and 11.
        
        URL: POST /open-api/metric/metricmgt/tags/list
        
        Header parameters:
        - Authorization (str, required): Authentication token obtained through the
          get_app_token interface, passed via request header: 
          "authorization": "Bearer ${access_token}"
        
        Returns:
            MetricTagsResponse: Response containing a list of available tags with:
            - id (int): Tag ID
            - labelValue (str): Tag name that can be passed to interfaces 4 and 11
              tags parameter to query metric instances
            - createTime (int): Creation time timestamp (optional)
            
        Example:
            response = client.get_metric_tags()
            # Use response.data to access the list of tags
            for tag in response.data:
                print(f"Tag ID: {tag.id}, Tag Name: {tag.label_value}")
        """
        response_data = self._make_request(
            method="POST",
            endpoint="/open-api/metric/metricmgt/tags/list"
        )
        return MetricTagsResponse(**response_data)

    def close(self):
        """Close the client session"""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        """Enter the runtime context for the client."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the runtime context for the client."""
        self.close()
    
    async def __aenter__(self):
        """Async enter the runtime context for the client."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async exit the runtime context for the client."""
        self.close()