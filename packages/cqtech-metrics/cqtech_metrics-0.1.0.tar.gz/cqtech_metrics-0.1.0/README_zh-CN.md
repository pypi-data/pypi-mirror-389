# 诚勤指标SDK

一个用于与诚勤指标中枢OpenAPI交互的Python SDK。

## 目录
- [概述](#概述)
- [安装](#安装)
- [快速开始](#快速开始)
- [API端点](#api端点)
- [使用示例](#使用示例)
- [数据模型](#数据模型)
- [认证](#认证)
- [测试](#测试)
- [贡献](#贡献)
- [许可证](#许可证)

## 概述

诚勤指标SDK提供了一个客户端，用于与诚勤指标中枢OpenAPI进行交互。此SDK使开发人员能够通过一组全面的接口进行身份验证、查询场景版本、指标实例等，这些接口与OpenAPI规范保持一致。

SDK包含12个API端点，涵盖：
- 认证和令牌管理
- 场景版本管理
- 指标实例定义和血缘关系
- 指标结果和评估
- 指标明细数据
- 标签管理
- 其他辅助接口

## 安装

```bash
pip install cqtech-metrics
```

## 快速开始

```python
from cqtech_metrics import CQTechClient
from cqtech_metrics.models.scenes import SceneVersionQuery
from cqtech_metrics.models.metrics import MetricQuery

# 初始化客户端（凭据从环境变量加载）
with CQTechClient() as client:
    # 查询所有场景版本
    query = SceneVersionQuery(
        name="学生",
        sceneVersionStatus=1,
        pageNum=1,
        pageSize=10
    )
    
    response = client.query_all_scene_versions(query)
    print(response)

    # 按代码查询指标结果
    metric_query = MetricQuery(
        sceneVersionUid=response.data.list[0].uid,
        instanceCodes=["byxf"]
    )
    results = client.query_metric_results_by_codes(metric_query)
    print(results)
```

使用环境变量方式：

```bash
# 设置环境变量
export CQTECH_BASE_URL="https://api.example.com"
export CQTECH_APP_KEY="your_app_key"
export CQTECH_SECRET="your_secret"
export CQTECH_USERNAME="your_username"
```

```python
from cqtech_metrics import CQTechClient
from cqtech_metrics.models.scenes import SceneVersionQuery

# 使用环境变量初始化客户端
client = CQTechClient()

# 查询有权限的场景版本
query = SceneVersionQuery(
    pageNum=1,
    pageSize=10
)
response = client.query_scene_versions_with_permission(query)
print(response)

client.close()
```

## API端点

SDK提供对12个主要API端点的访问：

1. **获取APP令牌** (`POST /open-api/system/oauth2-openapi/token`) - 认证并获取访问令牌
2. **查询所有场景版本** (`POST /open-api/metric/scene/versions`) - 查询应用下所有场景版本列表（与登录人权限无关）
3. **根据应用权限查询场景版本** (`POST /open-api/metric/scene/versions/with-permission`) - 根据应用权限查询场景版本列表
4. **根据场景版本查询指标实例** (`POST /open-api/metric/scene/version/metric-instances`) - 根据单一场景版本uid查询指标实例定义信息，以及依赖指标定义信息
5. **查询指标实例血缘** (`POST /open-api/metric/scene/version/metric-instance/lineage`) - 根据单一场景版本uid查询指标血缘，包含数据模型
6. **按代码查询指标结果** (`POST /open-api/metric/instance/codes/measure`) - 根据多个指标实例标识查询指标执行结果及评价
7. **按ID查询指标结果** (`POST /open-api/metric/instance/ids/measure`) - 根据多个指标实例id查询指标执行结果及评价
8. **查询指标实例明细** (`POST /open-api/metric/instance/detail`) - 查询指标实例明细数据
9. **查询单字段去重值** (`POST /open-api/metric/instance/detail-distinct-field`) - 查明细数据单字段去重
10. **根据多版本查询指标实例** (`POST /open-api/metric/scene/version/metric-instances-withVersions`) - 根据多个场景版本uuid查询用户有权限查看的指标实例列表
11. **获取指标标签** (`POST /open-api/metric/metricmgt/tags/list`) - 获取指标管理定义的标签列表

## 使用示例

### 认证

```python
from cqtech_metrics import CQTechClient

# SDK自动处理认证。令牌在需要时自动刷新。
client = CQTechClient(
    base_url="https://your-api-domain.com",
    app_key="your_app_key",
    secret="your_secret",
    username="your_username"
)
```

### 查询场景版本

```python
from cqtech_metrics.models.scenes import SceneVersionQuery

# 查询所有场景版本
query = SceneVersionQuery(
    name="学生",
    sceneVersionStatus=1,  # 0=下线, 1=上线
    pageNum=1,
    pageSize=10
)

response = client.query_all_scene_versions(query)
for scene in response.data.list:
    print(f"场景: {scene.name}, UID: {scene.uid}")
```

### 查询指标结果

```python
from cqtech_metrics.models.metrics import MetricQuery, GlobalFilter, InstanceFilter

# 按代码查询指标结果
query = MetricQuery(
    sceneVersionUid="7dda43b03da04ef79ca935ac14a1ca60",
    instanceCodes=["byxf", "xsl"],
    recalculate=False,
    globalFilter=GlobalFilter(
        dims={"学院": "计算机学院"},
        recalculate=False
    ),
    instances=[
        InstanceFilter(
            instanceCode="byxf",
            dims=["商户名称"],
            id="byxf_max",
            recalculate=True
        )
    ],
    pageNum=1,
    pageSize=10
)

results = client.query_metric_results_by_codes(query)
print(results)
```

### 查询指标明细数据

```python
# 查询详细指标数据
detail_query = MetricQuery(
    sceneVersionUid="7dda43b03da04ef79ca935ac14a1ca60",
    instanceId=4021,
    pageNum=1,
    pageSize=20
)

detail_response = client.query_metric_instance_detail(detail_query)
print(f"总记录数: {detail_response.data.total}")
for record in detail_response.data.list:
    print(record)
```

### 查询单字段去重值

```python
# 获取特定字段的唯一值
distinct_query = MetricQuery(
    sceneVersionUid="7dda43b03da04ef79ca935ac14a1ca60",
    instanceId=4021,
    columnAlias="商户名称",
    pageNum=1,
    pageSize=100
)

distinct_response = client.query_distinct_field_values(distinct_query)
print("可选商户:", distinct_response.data)
```

## 数据模型

SDK包含所有API响应的全面Pydantic模型：

### 认证模型
- `TokenResponse`: 认证端点的响应
- `TokenResponseData`: 令牌响应的数据部分
- `AuthHeader`: 认证头参数

### 场景模型
- `SceneVersion`: 场景版本信息
- `SceneVersionQuery`: 场景版本的查询参数
- `SceneVersionResponse`: 场景版本列表的响应

### 指标模型
- `MetricDefinition`: 指标的定义
- `MetricInstance`: 指标实例
- `MetricQuery`: 指标端点的查询参数
- `MetricResultDimValue`: 指标结果中的维度值
- `MetricDetailResponse`: 指标明细数据的响应

## 认证

SDK自动处理认证：
- 在进行API调用时自动获取令牌
- 在令牌到期前自动刷新
- 使用带校验和验证的OAuth2协议
- 令牌过期时自动刷新

认证流程：
1. 生成10位随机数
2. 获取当前时间戳（秒）
3. 使用用户名、密钥、随机数和时间戳的SHA1加密创建校验和
4. 向认证端点发送POST请求
5. 缓存令牌以供将来使用
6. 在需要时自动续订令牌

## 测试

运行测试：

```bash
pip install -r requirements-dev.txt
python -m pytest tests/
```

测试套件包括：
- 所有模型的单元测试
- API端点的集成测试
- 认证流程测试

## 贡献

1. Fork仓库
2. 创建功能分支 (`git checkout -b feature/awesome-feature`)
3. 提交更改 (`git commit -am 'Add awesome feature'`)
4. 推送到分支 (`git push origin feature/awesome-feature`)
5. 创建Pull Request

请确保适当更新测试并遵循现有代码风格。

## 许可证

该项目根据MIT许可证授权 - 有关详细信息，请参阅[LICENSE](LICENSE)文件。

## 支持

如需支持，请在GitHub仓库中提出问题或联系开发团队。