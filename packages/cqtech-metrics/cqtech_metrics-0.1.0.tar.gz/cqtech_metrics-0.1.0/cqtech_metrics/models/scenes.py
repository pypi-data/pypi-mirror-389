"""Scene models for CQTech Metrics SDK"""
from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from .base import BaseResponse
from .metrics import MetricInstance


class SceneVersion(BaseModel):
    """Model for scene version - API endpoint 3: 查询应用下所有场景版本列表（跟登录人权限无关）"""
    id: int
    name: str
    versionName: str
    uid: str
    sourceVersion: Optional[str] = None
    status: int  # 0=offline, 1=online
    cronExpression: Optional[str] = None
    constructionCycle: Optional[str] = None
    file: Optional[str] = None
    remark: Optional[str] = None
    instanceCount: int
    taskId: Optional[int] = None
    fileId: Optional[int] = None
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )


class SceneVersionQuery(BaseModel):
    """Query parameters for scene version endpoints - API endpoints 3 & 4"""
    name: Optional[str] = None  # Scene version name for fuzzy query
    sceneVersionStatus: Optional[int] = None  # 0=offline, 1=online
    pageNum: int  # Current page number for pagination
    pageSize: int  # Number of items per page for pagination
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )


class SceneVersionResponseData(BaseModel):
    """Response data for scene version list - API endpoints 3 & 4"""
    list: List[SceneVersion]  # List of scene versions
    total: int  # Total number of scene versions
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )


class SceneVersionResponse(BaseModel):
    """Response model for scene version list - API endpoints 3 & 4"""
    code: int  # Response code: 0=success, 401=token expired, 500=error
    data: SceneVersionResponseData  # Response data containing list and total
    msg: Optional[str] = None  # Error message if code != 0, empty string otherwise
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )


class SceneVersionWithPermissionQuery(SceneVersionQuery):
    """Query parameters for scene version with permission endpoint - API endpoint 4: 根据应用权限查询场景版本列表"""
    pass  # Same as SceneVersionQuery


class SceneVersionWithPermissionResponse(SceneVersionResponse):
    """Response model for scene version with permission - API endpoint 4: 根据应用权限查询场景版本列表"""
    pass  # Same structure as SceneVersionResponse


class SceneVersionMetricInstancesQuery(BaseModel):
    """Query parameters for scene version metric instances - API endpoint 5: 根据单一场景版本uid查询指标实例定义信息，以及依赖指标定义信息"""
    sceneVersionUid: str  # Scene version UID to query metric instances from
    instanceCodes: Optional[List[str]] = None  # Metric instance codes for filtering
    metricInstanceName: Optional[str] = None  # Metric instance name for fuzzy query
    tags: Optional[List[str]] = None  # Metric tags for filtering
    state: Optional[int] = None  # Metric instance state (0=offline, 1=online)
    pageNum: int  # Current page number for pagination
    pageSize: int  # Number of items per page for pagination
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )


class SceneVersionMetricInstancesResponseData(BaseModel):
    """Response data for scene version metric instances - API endpoint 5: 根据单一场景版本uid查询指标实例定义信息，以及依赖指标定义信息"""
    list: List[MetricInstance]  # List of metric instances with their definitions and dependencies
    total: int  # Total number of metric instances
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )


class SceneVersionMetricInstancesResponse(BaseModel):
    """Response model for scene version metric instances - API endpoint 5: 根据单一场景版本uid查询指标实例定义信息，以及依赖指标定义信息"""
    code: int  # Response code: 0=success, 401=token expired, 500=error
    data: SceneVersionMetricInstancesResponseData  # Response data containing list and total
    msg: Optional[str] = None  # Error message if code != 0, empty string otherwise
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )


class SceneVersionMetricInstanceLineage(BaseModel):
    """Model for scene version metric instance lineage - API endpoint 6: 根据单一场景版本uid查询指标血缘，包含数据模型"""
    id: int  # Metric instance ID
    name: str  # Metric instance name
    code: Optional[str] = None  # Metric instance code
    type: int  # Data type (1=metric, 2=data model, 3=data source, 4=data table)
    state: Optional[str] = None  # Metric instance state
    parentId: Optional[int] = None  # Parent metric instance ID
    definition: Optional[Dict[str, Any]] = None  # Metric definition information
    cronExpression: Optional[str] = None  # Cron expression
    children: List['SceneVersionMetricInstanceLineage']  # Dependent data including dependent metric instances, data models, data sources, data tables
    recalculateList: Optional[List[Dict[str, Any]]] = None  # Metric recalculation list
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )


class SceneVersionMetricInstanceLineageResponse(BaseModel):
    """Response model for scene version metric instance lineage - API endpoint 6: 根据单一场景版本uid查询指标血缘，包含数据模型"""
    code: int  # Response code: 0=success, 401=token expired, 500=error
    data: List[SceneVersionMetricInstanceLineage]  # List of lineage information of metric instances
    msg: Optional[str] = None  # Error message if code != 0, empty string otherwise
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )


class SceneVersionMetricInstancesWithVersionsQuery(BaseModel):
    """Query parameters for scene version metric instances with multiple versions - API endpoint 11: 根据多个场景版本uuid查询用户有权限查看的指标实例列表
    
    This query model allows filtering metric instances across multiple scene versions.
    """
    sceneVersionUids: List[str]  # List of scene version UIDs to query metric instances from (required)
    tags: Optional[List[str]] = None  # Metric tags for filtering metric instances (optional)
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )


class MetricInstanceWithSceneVersion(MetricInstance):
    """Metric instance extended with scene version UID for interface 11
    
    This model extends the base MetricInstance model by adding the scene version UID
    to identify which scene version the metric instance belongs to.
    """
    sceneVersionUid: str  # The UID of the scene version this metric instance belongs to
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )


class SceneVersionMetricInstancesWithVersionsResponse(BaseModel):
    """Response model for scene version metric instances with versions - API endpoint 11: 根据多个场景版本uuid查询用户有权限查看的指标实例列表"""
    code: int  # Response code: 0=success, 401=token expired, 500=error
    data: List[MetricInstanceWithSceneVersion]  # List of metric instances, each containing the scene version UID they belong to
    msg: Optional[str] = None  # Error message if code != 0, empty string otherwise
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )