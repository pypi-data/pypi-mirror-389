"""Metric models for CQTech Metrics SDK"""
from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Union
from .base import BaseResponse


class MetricDefinitionConfig(BaseModel):
    """Configuration for metric definition - Part of API endpoint 5: 根据单一场景版本uid查询指标实例定义信息，以及依赖指标定义信息"""
    # For atomic metrics
    aggFunc: Optional[str] = None  # e.g., "SUM"
    columns: Optional[List[str]] = None  # e.g., ["交易金额"]
    dataModel: Optional[str] = None  # e.g., "三十天消费记录"
    
    # For derived metrics
    hdim: Optional[List[Dict[str, Any]]] = None  # e.g., [{"column": "学号", "type": 1}]
    atomMetricUuid: Optional[str] = None  # e.g., "b9835a2d64374a58a6727524b2d8e914"
    
    # Additional fields from @class
    classInfo: Optional[str] = None  # e.g., "@class": "cn.iocoder.yudao.module..."
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )


class MetricDefinition(BaseModel):
    """Model for metric definition - Part of API endpoint 5: 根据单一场景版本uid查询指标实例定义信息，以及依赖指标定义信息"""
    id: Optional[int] = None
    name: Optional[str] = None
    uuid: Optional[str] = None  # Using uuid instead of uid to match API example
    type: Optional[int] = None  # 1=atomic, 2=derived, 3=compound, 4=custom
    versionName: Optional[str] = None
    versionUuid: Optional[str] = None
    definitionConfig: Optional[MetricDefinitionConfig] = None
    metadata: Optional[Dict[str, Any]] = None  # e.g., metric_source, metric_paraphrase
    metricDomain: Optional[List[Dict[str, Any]]] = None  # e.g., [{"name": "消费组件", "id": 45, "parentId": 42}]
    tags: Optional[List[str]] = None
    departments: Optional[List[str]] = None
    relevantDeptIds: Optional[List[int]] = None
    logic: Optional[str] = None
    remark: Optional[str] = None
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )


class MetricRecalculate(BaseModel):
    """Model for metric recalculate - Part of API endpoint 5: 根据单一场景版本uid查询指标实例定义信息，以及依赖指标定义信息"""
    id: int
    metricInstanceId: int
    name: str
    code: str
    queryLanguage: str
    measureCol: str
    dimCols: List[str]
    isDefault: bool
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )


class MetricInstance(BaseModel):
    """Model for metric instance - API endpoint 5: 根据单一场景版本uid查询指标实例定义信息，以及依赖指标定义信息"""
    id: int
    parentId: Optional[int] = None
    name: str
    code: Optional[str] = None
    dims: List[str]
    definition: Optional[MetricDefinition] = None
    cronExpression: Optional[str] = None
    children: Optional[List['MetricInstance']] = None
    state: Optional[int] = None
    recalculateList: Optional[List[MetricRecalculate]] = None
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )


class GlobalFilter(BaseModel):
    """Global filter for metric queries - API endpoints 7 & 8: 根据多个指标实例标识/ID查询指标执行结果及评价"""
    dims: Optional[Dict[str, Any]] = None  # Dimension filters (范围为指标实例的维度和度量(measure))
    id: Optional[str] = None  # Optional ID for grouping
    recalculate: Optional[bool] = None  # Recalculate flag (为true时会使用指标实例默认的精算sql实时计算结果)
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )


class InstanceFilter(BaseModel):
    """Filter for individual instances - API endpoints 7 & 8: 根据多个指标实例标识/ID查询指标执行结果及评价"""
    instanceId: Optional[int] = None  # 用于确定查询的哪个指标实例，返回的指标实例执行结果会以该id为key
    instanceCode: Optional[str] = None  # 用于确定查询的哪个指标实例，返回的指标实例执行结果会以该标识为key
    dims: Optional[List[str]] = None  # 用于确定查哪些维度的执行结果
    id: Optional[str] = None  # 指标实例别名，适用于同一个指标实例，因参数不同需要查询多次执行结果
    recalculate: Optional[bool] = None  # 为true时会使用指标实例默认的精算sql实时计算结果
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )


class MetricQuery(BaseModel):
    """Query parameters for metric endpoints - API endpoints 7, 8, 9, 10: 查询指标执行结果、明细数据和去重"""
    sceneVersionUid: str  # 场景版本uid，用于确定查询的哪个场景版本下的指标实例
    sceneVersionUid: str  # 场景版本uid，用于确定查询的哪个场景版本下的指标实例
    instanceCodes: Optional[List[str]] = None  # 指标实例标识，用于过滤指标实例
    instanceIds: Optional[List[int]] = None  # 指标实例id，用于过滤指标实例
    recalculate: Optional[bool] = None  # 指标精算标志，为true时会使用指标实例默认的精算sql实时计算结果
    globalFilter: Optional[GlobalFilter] = None  # 全局筛选条件，所有指标实例用一种查询筛选条件
    instances: Optional[List[InstanceFilter]] = None  # 指标实例差异参数，针对指标实例差异化参数单独为每个指标实例定义维度、筛选条件等参数
    pageNum: Optional[int] = None  # 分页页数，当前查询的页数
    pageSize: Optional[int] = None  # 每页条数，每页查询数据条数
    instanceId: Optional[int] = None  # 指标实例id，用于确定查询的是哪个指标实例的明细
    instanceCode: Optional[str] = None  # 指标实例标识，用于确定查询的是哪个指标实例的明细
    filter: Optional[Dict[str, Any]] = None  # 明细数据筛选，用户需要看哪个维度的明细数据
    orderField: Optional[str] = None  # 排序字段，需要排序的字段，用于表格展示明细后
    orderType: Optional[str] = None  # 排序规则，asc正序,desc倒序
    columnAlias: Optional[str] = None  # 字段名，查询某个字段的选项值
    searchValue: Optional[str] = None  # 选项名，用户模糊查询选项内容


class MetricResultDimValue(BaseModel):
    """Dimension value in metric result - API endpoints 7 & 8: 根据多个指标实例标识/ID查询指标执行结果及评价"""
    dims: Dict[str, Any]  # 维度：维值，e.g., {"商户名称": "校园超市"}
    dimsDesc: Optional[Dict[str, Any]] = None  # 维度：维值描述，可能为空，e.g., {"商户名称": null}
    measureType: Optional[int] = None  # 统计值类型，1数字,2字符串
    measure: str  # 统计值
    assessments: Optional[List[Dict[str, Any]]] = None  # 评价信息，支持多组评价，recalculate为true（指标精算）时，assessments为null
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )


class MetricResultAssessment(BaseModel):
    """Assessment result in metric evaluation - API endpoints 7 & 8: 根据多个指标实例标识/ID查询指标执行结果及评价"""
    name: str  # 评价名称，e.g., "政策文件"
    ruleResults: List[Dict[str, str]]  # 评价结果，name：评价结果，calDesc：评价规则描述


class MetricResultsByCodeResponseData(BaseModel):
    """Response data for metric results by code - API endpoint 7: 根据多个指标实例标识查询指标执行结果及评价"""
    # Contains instance ID or code as key, with list of results as value
    pass  # This is a dynamic structure where each key is an instance ID/code


class MetricResultsByCodeResponse(BaseModel):
    """Response model for metric results by codes - API endpoint 7: 根据多个指标实例标识查询指标执行结果及评价"""
    code: int  # 响应码，0表示响应正常，401表示token过期，500表示响应异常
    data: Dict[str, List[MetricResultDimValue]]  # Dynamic key-value where key is instance code
    msg: Optional[str] = None  # 异常描述，当code返回0是，表示响应正常，msg返回空字符串
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )


class MetricResultsByIdResponse(MetricResultsByCodeResponse):
    """Response model for metric results by IDs - API endpoint 8: 根据多个指标实例id查询指标执行结果及评价"""
    pass  # Same structure as MetricResultsByCodeResponse


class MetricDetailColumn(BaseModel):
    """Column definition in metric detail data - API endpoint 9: 查询指标实例明细数据"""
    alias: str  # 字段名，如"交易时间段"
    type: str  # 字段类型，如"VARCHAR"
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )


class MetricDetailDataResponse(BaseModel):
    """Response data for metric detail - API endpoint 9: 查询指标实例明细数据"""
    total: int  # 明细总数
    list: List[Dict[str, Any]]  # 明细数据，每项为一个对象
    columns: List[MetricDetailColumn]  # 明细字段，用于构建表头，alias：字段名，type：字段类型
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )


class MetricDetailResponse(BaseModel):
    """Response model for metric detail data - API endpoint 9: 查询指标实例明细数据"""
    code: int  # 响应码，0表示响应正常，401表示token过期，500表示响应异常
    data: MetricDetailDataResponse  # 响应主体，包含明细数据、列定义和总数
    msg: Optional[str] = None  # 异常描述，当code返回0是，表示响应正常，msg返回空字符串
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )


class MetricDistinctFieldResponse(BaseModel):
    """Response model for distinct field values - API endpoint 10: 查明细数据单字段去重"""
    code: int  # 响应码，0表示响应正常，401表示token过期，500表示响应异常
    data: List[str]  # 字段内容，返回该字段所有选项并去重
    msg: Optional[str] = None  # 异常描述，当code返回0是，表示响应正常，msg返回空字符串
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )


class MetricTagsItem(BaseModel):
    """Model for a single metric tag - API endpoint 12: 获取指标管理定义的标签列表"""
    id: int  # 标签id
    labelValue: str  # 标签名称
    createTime: Optional[int] = None  # 创建时间戳
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )


class MetricTagsResponse(BaseModel):
    """Response model for metric tags - API endpoint 12: 获取指标管理定义的标签列表"""
    code: int  # 响应码，0表示响应正常，401表示token过期，500表示响应异常
    data: List[MetricTagsItem]  # 响应主体，标签列表
    msg: Optional[str] = None  # 异常描述，当code返回0是，表示响应正常，msg返回空字符串
    
    model_config = ConfigDict(
        populate_by_name=True  # Allow both camelCase and snake_case field names
    )


# Update forward references
MetricInstance.update_forward_refs()