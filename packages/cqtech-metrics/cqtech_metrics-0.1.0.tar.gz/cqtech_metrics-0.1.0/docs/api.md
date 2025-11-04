# CQTech Metrics API 文档

本文档整理了诚勤指标中枢平台 OpenAPI 接口（共 12 个），每个接口包含中文和英文名称、用途简述、请求 URL 与方法、请求头和请求体参数表、示例请求、返回字段说明和返回示例等信息。字段说明使用 Markdown 表格展示，中英文并列对照，便于 AI 生成代码与接口对接。

---

## 1. 获取 APP 令牌 (Get APP Token)

### 用途
该接口用于鉴权认证，调用任何业务接口前需调用此接口获取 access_token（令牌具有时效性，失效后需重新获取）。

### URL & 方法
`POST /open-api/system/oauth2-openapi/token`

### 请求头参数

| 字段名 (Field Name) | 类型 (Type) | 必填 (Required) | 描述 (Description) | 示例 (Example) |
|---------------------|-------------|-----------------|---------------------|----------------|
| appkey (应用编号) | 字符串 (String) | 是 | 应用编号（在指标中枢平台 "第三方应用开放 → 应用管理" 中获取） | ZNZSCS |
| nonce (10位随机数) | 整型 (Integer) | 是 | 随机生成 10 位数字 | 1768277523 |
| curtime (当前时间戳) | 整型 (Integer) | 是 | 当前时间戳，单位秒 | 1761042060 |
| username (登录人工号) | 字符串 (String) | 是 | 当前登录人工号 | 19950174 |
| checksum (校验码) | 字符串 (String) | 是 | 签名（使用 username、secret、nonce、curtime 通过 SHA1 加密生成） | 自动生成 |

### 响应参数

| 字段名 | 类型 | 描述 (Description) |
|--------|------|---------------------|
| access_token (认证 token) | 字符串 (String) | 调用业务接口时用于身份认证的令牌，通过请求头 Authorization: Bearer <access_token> 传递 |
| refresh_token (刷新 token) | 字符串 (String) | 刷新令牌（当前未提供刷新功能，可忽略） |
| token_type (token 类型) | 字符串 (String) | 令牌类型，固定为 bearer |
| expires_in (有效期) | 整型 (Integer) | 令牌有效期，单位秒（示例：1800 秒） |

### 请求示例
```bash
appKey="ZNZSCS"
secret="xxxxxxxxxxxxxxxxxxxxxxx"
username="19950174"
nonce=$(shuf -i 1000000000-9999999999 -n 1)
curTime=$(date +%s)
checkSumBuilder="${username}${secret}${nonce}${curTime}"
checkSum=$(echo -n "$checkSumBuilder" | sha1sum | awk '{print $1}')

curl 'https://指标中枢域名/open-api/system/oauth2-openapi/token' \
  -X 'POST' \
  -H "appkey: $appKey" \
  -H "checksum: $checkSum" \
  -H "curtime: $curTime" \
  -H "nonce: $nonce" \
  -H "username: $username"
```

### 返回示例
```json
{
    "code": 0,
    "data": {
        "scope": null,
        "access_token": "c72c783a23f84bd4a52aa955dfaf2985",
        "refresh_token": "a3a8c4803d0d4a4d8a3b825968d6582f",
        "token_type": "bearer",
        "expires_in": 1799
    },
    "msg": ""
}
```

---

## 2. 查询应用下所有场景版本列表 (Query All Scene Versions under Application)

### 用途
该接口用于查询某应用下可访问的所有场景版本（不受当前登录用户权限限制），一般用于第三方应用管理端配置场景版本。

### URL & 方法
`POST /open-api/metric/scene/versions`

### 请求头参数

| 字段名 | 类型 (Type) | 必填 | 描述 (Description) | 示例 |
|--------|-------------|------|---------------------|------|
| Authorization (认证 token) | 字符串 (String) | 是 | 调用获取 APP 令牌接口获取的 access_token，通过请求头传参 | Bearer 9c37206336fb4fd38b9e09783e41a2a2 |

### 请求体参数

| 字段名 | 类型 (Type) | 必填 | 描述 (Description) | 示例 |
|--------|-------------|------|---------------------|------|
| name (场景版本名称) | 字符串 (String) | 否 | 场景版本名称模糊查询 (用于按名称筛选) | "学生" |
| sceneVersionStatus (场景版本状态) | 整型 (Integer) | 否 | 场景版本状态筛选：0 下线，1 上线，不传查所有 | 1 |
| pageNum (分页页数) | 整型 (Integer) | 是 | 当前查询页数 | 1 |
| pageSize (每页条数) | 整型 (Integer) | 是 | 每页查询条目数 | 2 |

### 响应参数

| 字段名 | 类型 | 描述 (Description) |
|--------|------|---------------------|
| list (场景版本列表) | 数组 (Array) | 场景版本对象列表 |
| total (场景版本总数) | 整型 (Integer) | 满足条件的场景版本总数 |

### list 数组中对象字段说明

| 字段名 | 类型 | 描述 (Description) |
|--------|------|---------------------|
| id (场景版本ID) | 整型 (Integer) | 场景版本 ID |
| name (场景名称) | 字符串 (String) | 场景名称 |
| versionName (场景版本名称) | 字符串 (String) | 场景版本名称 |
| uid (场景版本UID) | 字符串 (String) | 场景版本 UID，在后续接口调用中作为参数 |
| status (场景版本状态) | 整型 (Integer) | 场景版本状态：0 未上线，1 已上线 |
| cronExpression (定时任务Cron表达式) | 字符串 (String) | 场景版本的定时任务 Cron 表达式 |
| instanceCount (指标实例数量) | 整型 (Integer) | 该场景版本下的指标实例数量 |

### 请求示例
```bash
curl 'https://指标中枢域名/open-api/metric/scene/versions' \
  -X 'POST' \
  -H 'authorization: Bearer 9c37206336fb4fd38b9e09783e41a2a2' \
  -H 'content-type: application/json' \
  --data-raw '{
    "name": "学生",
    "sceneVersionStatus": 1,
    "pageNum": 1,
    "pageSize": 2
}'
```

### 返回示例
```json
{
    "code": 0,
    "data": {
        "list": [
            {
                "id": 159,                   // 场景版本ID
                "name": "s学生信息场景",         // 场景名称
                "versionName": "s精算场景全部",   // 场景版本名称
                "uid": "293d005d2ef24a62afb2a72aefed9ff1",   // 场景版本UID
                "status": 1,                 // 场景版本状态，0=未上线，1=已上线
                "cronExpression": "0 0 0 1 * ?",   // 场景版本定时任务 Cron 表达式
                "instanceCount": 110          // 指标实例数量
            },
            {
                "id": 156,
                "name": "s学生信息场景",
                "versionName": "s精算场景",
                "uid": "5c9f889223624dc79c5d2287ca3e6bb3",
                "status": 1,
                "cronExpression": "0 0 0 1 * ?",
                "instanceCount": 14
            }
        ],
        "total": 9
    },
    "msg": ""
}
```

---

## 3. 根据应用权限查询场景版本列表 (Query Scene Versions by App Permission)

### 用途
该接口用于查询某应用下当前登录用户有权限访问的场景版本列表，一般用于第三方用户端根据权限筛选可用场景版本。

### URL & 方法
`POST /open-api/metric/scene/versions/with-permission`

### 请求头参数

| 字段名 | 类型 (Type) | 必填 | 描述 (Description) | 示例 |
|--------|-------------|------|---------------------|------|
| Authorization (认证 token) | 字符串 (String) | 是 | 调用获取 APP 令牌接口获取的 access_token，通过请求头传参 | Bearer 9c37206336fb4fd38b9e09783e41a2a2 |

### 请求体参数

| 字段名 | 类型 (Type) | 必填 | 描述 (Description) | 示例 |
|--------|-------------|------|---------------------|------|
| name (场景版本名称) | 字符串 (String) | 否 | 场景版本名称模糊查询 (用于按名称筛选) | "学生" |
| sceneVersionStatus (场景版本状态) | 整型 (Integer) | 否 | 场景版本状态筛选：0 下线，1 上线，不传查所有 | 1 |
| pageNum (分页页数) | 整型 (Integer) | 是 | 当前查询页数 | 1 |
| pageSize (每页条数) | 整型 (Integer) | 是 | 每页查询条目数 | 2 |

### 响应参数

| 字段名 | 类型 | 描述 (Description) |
|--------|------|---------------------|
| list (场景版本列表) | 数组 (Array) | 场景版本对象列表 |
| total (场景版本总数) | 整型 (Integer) | 满足条件的场景版本总数 |

### list 数组中对象字段说明
list 数组中对象的字段与接口2相同（id、name、versionName、uid、status、cronExpression、instanceCount 等），详情见接口2。

### 请求示例
```bash
curl 'https://指标中枢域名/open-api/metric/scene/versions/with-permission' \
  -X 'POST' \
  -H 'authorization: Bearer 9c37206336fb4fd38b9e09783e41a2a2' \
  -H 'content-type: application/json' \
  --data-raw '{
    "name": "学生",
    "sceneVersionStatus": 1,
    "pageNum": 1,
    "pageSize": 2
}'
```

### 返回示例
```json
{
    "code": 0,
    "data": {
        "list": [
            {
                "id": 159,
                "name": "s学生信息场景",
                "versionName": "s精算场景全部",
                "uid": "293d005d2ef24a62afb2a72aefed9ff1",
                "status": 1,
                "cronExpression": "0 0 0 1 * ?",
                "instanceCount": 110
            },
            {
                "id": 156,
                "name": "s学生信息场景",
                "versionName": "s精算场景",
                "uid": "5c9f889223624dc79c5d2287ca3e6bb3",
                "status": 1,
                "cronExpression": "0 0 0 1 * ?",
                "instanceCount": 14
            }
        ],
        "total": 9
    },
    "msg": ""
}
```

---

## 4. 根据单一场景版本 UID 查询指标实例定义及依赖信息 (Query Metric Instances and Dependencies by Scene Version UID)

### 用途
该接口可基于某一场景版本，查询当前登录用户有权限查看的指标实例信息及定义信息，以及其依赖指标的定义信息。

### URL & 方法
`POST /open-api/metric/scene/version/metric-instances`

### 请求头参数

| 字段名 | 类型 (Type) | 必填 | 描述 (Description) | 示例 |
|--------|-------------|------|---------------------|------|
| Authorization (认证 token) | 字符串 (String) | 是 | 调用获取 APP 令牌接口获取的 access_token，通过请求头传参 | Bearer bd48ef7ff4684cacb0b8cea2da56a94e |

### 请求体参数

| 字段名 | 类型 (Type) | 必填 | 描述 (Description) | 示例 |
|--------|-------------|------|---------------------|------|
| sceneVersionUid (场景版本 UID) | 字符串 (String) | 是 | 场景版本 UID (确定查询哪个场景版本的指标实例) | "784553cdccf74..." |
| instanceCodes (指标实例标识) | 字符串数组 (Array of String) | 否 | 指标实例标识列表 (用于过滤指定实例，不传则查询所有可见实例) | ["byxf"] |
| metricInstanceName (指标实例名称) | 字符串 (String) | 否 | 指标实例名称模糊查询 | "消费" |
| tags (指标标签) | 字符串数组 (Array of String) | 否 | 指标标签筛选 | ["校园卡组件"] |
| state (指标实例状态) | 整型 (Integer) | 否 | 指标实例状态：0 未上线，1 已上线，不传则查询所有 | 1 |
| pageNum (分页页数) | 整型 (Integer) | 是 | 当前查询页数 | 1 |
| pageSize (每页条数) | 整型 (Integer) | 是 | 每页查询条目数 | 2 |

### 响应参数

| 字段名 | 类型 | 描述 (Description) |
|--------|------|---------------------|
| list (指标实例列表) | 数组 (Array) | 指标实例对象列表 |
| total (指标实例总数) | 整型 (Integer) | 满足条件的指标实例总数 |

### list 数组中对象字段说明

| 字段名 | 类型 | 描述 (Description) |
|--------|------|---------------------|
| id (指标实例ID) | 整型 (Integer) | 指标实例 ID |
| parentId (父级ID) | 整型 (Integer) | 父指标实例 ID |
| name (指标实例名称) | 字符串 (String) | 指标实例名称 |
| code (指标实例标识) | 字符串 (String) | 指标实例标识 |
| dims (维度) | 字符串数组 (Array) | 指标实例的维度列表 |
| state (指标实例状态) | 整型 (Integer) | 指标实例状态：0 未上线，1 已上线 |
| definition (指标定义信息) | 对象 (Object) | 指标定义信息 |
| recalculateList (指标精算列表) | 数组 (Array) | 指标实例的精算列表 |
| children (依赖指标) | 数组 (Array) | 当前指标实例依赖的其他指标实例树 |

### definition 对象字段说明

| 字段名 | 类型 | 描述 (Description) |
|--------|------|---------------------|
| id (指标定义ID) | 整型 (Integer) | 指标定义 ID |
| name (指标定义名称) | 字符串 (String) | 指标定义名称 |
| uid (指标定义UID) | 字符串 (String) | 指标定义 UID |
| type (指标类型) | 整型 (Integer) | 指标类型：1 原子、2 派生、3 复合、4 自定义 |
| versionName (指标版本名称) | 字符串 (String) | 指标版本名称 |
| versionUuid (指标版本UID) | 字符串 (String) | 指标版本 UID |
| metadata (指标元数据) | 对象 (Object) | 指标元数据 (Preset meta-data, e.g., metric_source, metric_paraphrase, metric_data_source) |
| metricDomain (指标域) | 数组 (Array) | 指标域列表 |
| tags (标签) | 数组 (Array) | 指标标签列表 |
| departments (归口部门) | 数组 (Array) | 指标归口部门列表 |
| logic (计算规则) | 字符串 (String) | 指标的计算逻辑描述 |
| remark (指标简述) | 字符串 (String) | 指标简要说明 |

### recalculateList 数组中每个对象字段说明

| 字段名 | 类型 | 描述 (Description) |
|--------|------|---------------------|
| id (指标精算ID) | 整型 (Integer) | 指标精算 ID |
| metricInstanceId (指标实例ID) | 整型 (Integer) | 指标实例 ID |
| name (指标精算名称) | 字符串 (String) | 指标精算名称 |
| code (指标精算标识) | 字符串 (String) | 指标精算标识 |
| queryLanguage (SQL语句) | 字符串 (String) | 指标精算 SQL 语句 |
| measureCol (度量字段) | 字符串 (String) | 计算结果的度量字段 |
| dimCols (维度字段) | 数组 (Array) | 计算结果的维度字段列表 |
| isDefault (是否默认) | 布尔 (Boolean) | 是否默认精算 (true=default, false=non-default) |

### 请求示例
```bash
curl 'https://指标中枢域名/open-api/metric/scene/version/metric-instances' \
  -X 'POST' \
  -H 'authorization: Bearer bd48ef7ff4684cacb0b8cea2da56a94e' \
  -H 'content-type: application/json' \
  --data-raw '{
    "sceneVersionUid": "7dda43b03da04ef79ca935ac14a1ca60",
    "instanceCodes": ["byxf"],
    "metricInstanceName": "消费",
    "tags": ["校园卡组件"],
    "state": 1,
    "pageNum": 1,
    "pageSize": 2
}'
```

### 返回示例
```json
{
    "code": 0,
    "data": {
        "list": [
            {
                "id": 4021,
                "parentId": null,
                "name": "本月消费",
                "code": "byxf",
                "dims": ["学号", "商户名称"],
                "definition": {
                    "id": 462,
                    "name": "本月消费",
                    "uuid": "4fbee76efa28475c9732ec032255b952",
                    "type": 2,
                    "versionName": "main",
                    "versionUuid": "afbf45a3415b482fb8d11f7d3ab31b21",
                    "definitionConfig": {
                        "@class": "cn.iocoder.yudao.module.metric.dal.dataobject.metricmgt.DerivedDefinitionConfigInfo",
                        "hdim": [
                            { "column": "学号", "type": 1 },
                            { "column": "商户名称", "type": 1 }
                        ],
                        "atomMetricUuid": "b9835a2d64374a58a6727524b2d8e914"
                    },
                    "metadata": {
                        "metric_source": "数据中台 -> metric_dwd.t_dwd_fact_a44_28029938",
                        "metric_paraphrase": "记录用户在本月 1日至当前日期之间的消费总金额和总次数...",
                        "metric_data_source": ""
                    },
                    "metricDomain": [{ "name": "消费组件", "id": 45, "parentId": 42 }],
                    "tags": ["校园卡组件"],
                    "departments": ["网信办", "网络空间安全学院"],
                    "relevantDeptIds": [101, 104],
                    "logic": "对消费金额（原子）进行 SUM 求和，通过派生指标进行学号维度设置...",
                    "remark": "统计用户在当前自然月内的消费次数与金额，反映其近期活跃度与消费趋势。"
                },
                "cronExpression": null,
                "children": [
                    {
                        "id": 4022,
                        "parentId": 4021,
                        "name": "消费金额（原子）_main",
                        "code": "byxf",
                        "dims": [],
                        "definition": {
                            "id": 459,
                            "name": "消费金额（原子）_SUM",
                            "uuid": "b9835a2d64374a58a6727524b2d8e914",
                            "type": 1,
                            "versionName": "main",
                            "versionUuid": "87e400d85a664b6d8c06dffb41ed5184",
                            "definitionConfig": {
                                "@class": "cn.iocoder.yudao.module.metric.dal.dataobject.metricmgt.AtomicDefinitionConfigInfo",
                                "aggFunc": "SUM",
                                "columns": ["交易金额"],
                                "dataModel": "三十天消费记录"
                            },
                            "metadata": null
                        },
                        "cronExpression": null,
                        "children": [
                            {
                                "id": 402,
                                "name": "三十天消费记录",
                                "code": null,
                                "state": null,
                                "parentId": null,
                                "type": 2,
                                "definition": null,
                                "cronExpression": null,
                                "children": []
                            }
                        ]
                    }
                ],
                "state": 1,
                "recalculateList": [
                    {
                        "id": 62,
                        "metricInstanceId": 4021,
                        "name": "最受欢迎的商户",
                        "code": "zshydsh",
                        "queryLanguage": "SELECT cast(sum(${sys_metric_measure}) as decimal(20,2)) AS measure, 商户名称, 商户名称_desc FROM ${sys_metric_resultset} ...",
                        "measureCol": "measure",
                        "dimCols": ["商户名称", "商户名称_desc"],
                        "isDefault": true
                    }
                ]
            }
        ],
        "total": 1
    },
    "msg": ""
}
```

---

## 5. 根据单一场景版本 UID 查询指标血缘 (包含数据模型) (Query Metric Lineage by Scene Version UID, including Data Models)

### 用途
该接口可基于某一场景版本，查询当前登录用户有权限的指标实例血缘信息，包括依赖指标、数据模型、数据源、数据表等关联信息。

### URL & 方法
`POST /open-api/metric/scene/version/metric-instance/lineage`

### 请求头参数

| 字段名 | 类型 (Type) | 必填 | 描述 (Description) | 示例 |
|--------|-------------|------|---------------------|------|
| Authorization (认证 token) | 字符串 (String) | 是 | 调用获取 APP 令牌接口获取的 access_token，通过请求头传参 | Bearer bd48ef7ff4684cacb0b8cea2da56a94e |

### 请求体参数

| 字段名 | 类型 (Type) | 必填 | 描述 (Description) | 示例 |
|--------|-------------|------|---------------------|------|
| sceneVersionUid (场景版本 UID) | 字符串 (String) | 是 | 场景版本 UID (确定查询哪个场景版本) | "7dda43b03da04ef79ca935ac14a1ca60" |
| instanceCodes (指标实例标识) | 字符串数组 (Array of String) | 否 | 指标实例标识列表 (用于过滤指定实例，不传则查询所有可见实例) | ["byxf"] |

### 响应参数
本接口返回指标实例血缘信息，主要字段说明如下：

| 字段名 | 类型 | 描述 (Description) |
|--------|------|---------------------|
| id (指标实例ID) | 整型 (Integer) | 指标实例ID |
| name (指标实例名称) | 字符串 (String) | 指标实例名称 |
| code (指标实例标识) | 字符串 (String) | 指标实例标识 |
| state (指标实例状态) | 字符串 (String) | 指标实例状态 |
| parentId (父级ID) | 整型 (Integer) | 父指标实例ID |
| type (类型) | 整型 (Integer) | 类型：1=指标，2=数据模型，3=数据源，4=数据表 |
| definition (指标定义信息) | 对象 (Object) | 指标定义信息 |
| cronExpression (定时任务Cron表达式) | 字符串 (String) | Cron表达式 |
| children (依赖数据) | 数组 (Array) | 依赖的数据列表（包括其他指标实例、数据模型、数据源、数据表） |
| recalculateList (指标精算列表) | 数组 (Array) | 指标精算列表 |

### 请求示例
```bash
curl 'https://指标中枢域名/open-api/metric/scene/version/metric-instance/lineage' \
  -X 'POST' \
  -H 'authorization: Bearer bd48ef7ff4684cacb0b8cea2da56a94e' \
  -H 'content-type: application/json' \
  --data-raw '{
    "sceneVersionUid": "7dda43b03da04ef79ca935ac14a1ca60",
    "instanceCodes": ["byxf"]
}'
```

### 返回示例
```json
{
    "code": 0,
    "data": [
        {
            "id": 4021,              // 指标实例ID
            "name": "本月消费",        // 指标实例名称
            "code": "byxf",          // 指标实例标识
            "state": "1",
            "parentId": null,
            "type": 1,               // 类型：1=指标，2=数据模型，3=数据源，4=数据表
            "definition": {
                "id": null,
                "name": "本月消费",         // 指标定义名称
                "uuid": "4fbee76efa28475c9732ec032255b952", // 指标定义UID
                "type": 2,               // 指标类型：2=派生指标
                "versionName": "main",   // 指标版本名称
                "versionUuid": "afbf45a3415b482fb8d11f7d3ab31b21", // 指标版本UID
                "definitionConfig": {
                    "@class": "cn.iocoder.yudao.module.metric.dal.dataobject.metricmgt.DerivedDefinitionConfigInfo",
                    "hdim": [
                        { "column": "学号", "type": 1 },
                        { "column": "商户名称", "type": 1 }
                    ],
                    "atomMetricUuid": "b9835a2d64374a58a6727524b2d8e914"
                },
                "metadata": null
            },
            "cronExpression": null,
            "children": [
                {
                    "id": 4022,
                    "name": "消费金额（原子）_main",
                    "code": "byxf",
                    "state": "1",
                    "parentId": 4021,
                    "type": 1,
                    "definition": {
                        "id": null,
                        "name": "消费金额（原子）_SUM",
                        "uuid": "b9835a2d64374a58a6727524b2d8e914",
                        "type": 1,
                        "versionName": "main",
                        "versionUuid": "87e400d85a664b6d8c06dffb41ed5184",
                        "definitionConfig": {
                            "@class": "cn.iocoder.yudao.module.metric.dal.dataobject.metricmgt.AtomicDefinitionConfigInfo",
                            "aggFunc": "SUM",
                            "columns": ["交易金额"],
                            "dataModel": "三十天消费记录"
                        },
                        "metadata": null
                    },
                    "cronExpression": null,
                    "children": [
                        {
                            "id": 402,
                            "name": "三十天消费记录",
                            "code": null,
                            "state": null,
                            "parentId": null,
                            "type": 2,
                            "definition": null,
                            "cronExpression": null,
                            "children": []
                        }
                    ]
                }
            ],
            "recalculateList": null
        }
    ],
    "msg": ""
}
```

---

## 6. 根据多个指标实例标识查询指标执行结果及评价 (Query Metric Results and Assessments by Multiple Instance Codes)

### 用途
该接口用于查询一个或多个指标实例的执行结果及评价信息。支持同时查询多个指标实例，并可使用默认精算 SQL 或不同的查询参数获取多组结果。

### URL & 方法
`POST /open-api/metric/instance/codes/measure`

### 请求头参数

| 字段名 | 类型 (Type) | 必填 | 描述 (Description) | 示例 |
|--------|-------------|------|---------------------|------|
| Authorization (认证 token) | 字符串 (String) | 是 | 调用获取 APP 令牌接口获取的 access_token，通过请求头传参 | Bearer bd48ef7ff4684cacb0b8cea2da56a94e |

### 请求体参数
说明：globalFilter、instances 为复杂对象，包含查询逻辑（示例结构如下）。instances 每项结构与 globalFilter 相似，区别在于 instances 针对单个指标实例的差异化筛选，可在请求体中按需提供。

### 响应参数

| 字段名 (Field Name) | 类型 (Type) | 描述 (Description) |
|---------------------|-------------|---------------------|
| <instance> (指标实例标识或 ID) | 数组 (Array) | 指标实例的结果列表（若传入多个 id，则以 id 为字段名，否则以实例标识为字段名） |
| dims (维度：维值) | 对象 (Object) | 指标结果维度字段及其取值 |
| dimsDesc (维度：维值描述) | 对象 (Object) | 维度值描述，可能为 null |
| measureType (统计值类型) | 整型 (Integer) | 统计值类型 (1=数字, 2=字符串) |
| measure (统计值) | 字符串 (String) | 统计值 |
| assessments (评价信息) | 数组 (Array) | 评价结果列表（若 recalculate=true 时此字段为 null） |

### assessments 数组中每项字段说明

| 字段名 | 类型 | 描述 (Description) |
|--------|------|---------------------|
| name (评价名称) | 字符串 (String) | 评价名称 |
| ruleResults (评价结果) | 对象 (Object) | 评价结果对象，包含 name（结果）、calDesc（规则描述） |

### 请求示例
```bash
curl 'https://指标中枢域名/open-api/metric/instance/codes/measure' \
  -X 'POST' \
  -H 'authorization: Bearer bd48ef7ff4684cacb0b8cea2da56a94e' \
  -H 'content-type: application/json' \
  --data-raw '{
    "sceneVersionUid": "7dda43b03da04ef79ca935ac14a1ca60",
    "instanceCodes": ["byxf"],
    "instances": [
      {
        "instanceCode": "byxf",
        "dims": ["商户名称"],
        "id": "byxf_max",
        "recalculate": true
      }
    ]
  }'
```

### 返回示例
```json
{
    "code": 0,
    "data": {
        "byxf_max": [
            {
                "dims": {
                    "商户名称": "校园超市"
                },
                "dimsDesc": {
                    "商户名称": null
                },
                "measureType": null,
                "measure": "274.58",
                "assessments": [
                    {
                        "name": "政策文件",
                        "ruleResults": [
                            { "name": "达标", "calDesc": "大于等于 250" }
                        ]
                    },
                    {
                        "name": "校标",
                        "ruleResults": [
                            { "name": "未达标", "calDesc": "大于等于 300" }
                        ]
                    }
                ]
            }
        ]
    },
    "msg": ""
}
```

---

## 7. 根据多个指标实例 ID 查询指标执行结果及评价 (Query Metric Results and Assessments by Multiple Instance IDs)

### 用途
功能与接口6相同，不同之处在于本接口使用指标实例的 ID 作为过滤条件（替换 instanceCodes 为 instanceIds）。

### URL & 方法
`POST /open-api/metric/instance/ids/measure`

### 请求头参数
请求头参数说明与接口6相同（参见接口6）

### 请求体参数
请求体参数说明与接口6相似，只是将 instanceCodes 换为 instanceIds

### 响应参数
返回格式与接口6完全相同，示例如下（字段意义同接口6）：

### 请求示例
```bash
curl 'https://指标中枢域名/open-api/metric/instance/ids/measure' \
  -X 'POST' \
  -H 'authorization: Bearer bd48ef7ff4684cacb0b8cea2da56a94e' \
  -H 'content-type: application/json' \
  --data-raw '{
    "sceneVersionUid": "7dda43b03da04ef79ca935ac14a1ca60",
    "instanceIds": [4021],
    "instances": [
      {
        "instanceId": 4021,
        "dims": ["商户名称"],
        "id": "byxf_max",
        "recalculate": true
      }
    ]
}'
```

### 返回示例
```json
{
    "code": 0,
    "data": {
        "byxf_max": [
            {
                "dims": {
                    "商户名称": "校园超市"
                },
                "dimsDesc": {
                    "商户名称": null
                },
                "measureType": null,
                "measure": "274.58",
                "assessments": [
                    {
                        "name": "政策文件",
                        "ruleResults": [
                            { "name": "达标", "calDesc": "大于等于 250" }
                        ]
                    },
                    {
                        "name": "校标",
                        "ruleResults": [
                            { "name": "未达标", "calDesc": "大于等于 300" }
                        ]
                    }
                ]
            }
        ]
    },
    "msg": ""
}
```

---

## 8. 查询指标实例明细数据 (Query Metric Instance Detail Data)

### 用途
该接口用于查询指定指标实例的明细（底层数据）内容，一般用于统计结果向明细钻取。

### URL & 方法
`POST /open-api/metric/instance/detail`

### 请求头参数
请求头参数说明与接口6相同

### 请求体参数

| 字段名 | 类型 (Type) | 必填 | 描述 (Description) | 示例 |
|--------|-------------|------|---------------------|------|
| sceneVersionUid (场景版本 UID) | 字符串 (String) | 是 | 场景版本 UID (确定查询哪个场景版本) | "7dda43b03da04ef79ca935ac14a1ca60" |
| instanceId (指标实例ID) | 整型 (Integer) | 是 | 指标实例 ID (优先级高于 instanceCode；若都提供，以 ID 查询) | 4021 |
| instanceCode (指标实例标识) | 字符串 (String) | 是 | 指标实例标识 (若同时提供 instanceId，以 instanceId 优先) | "byxf" |
| filter (明细数据筛选) | 对象 (Object) | 否 | 明细数据筛选条件，与 globalFilter 结构相同 | 示例详见接口6 |
| orderField (排序字段) | 字符串 (String) | 否 | 用于排序的字段名 (字段排序用于明细展示) | "立项日期" |
| orderType (排序规则) | 字符串 (String) | 否 | 排序方向：asc 或 desc | asc |
| pageNum (分页页数) | 整型 (Integer) | 是 | 当前查询页数 | 1 |
| pageSize (每页条数) | 整型 (Integer) | 是 | 每页查询条目数 | 2 |

### 响应参数

| 字段名 | 类型 | 描述 (Description) |
|--------|------|---------------------|
| list (明细数据) | 数组 (Array) | 明细记录列表，每项为一个对象 |
| columns (明细字段) | 数组 (Array) | 明细字段列表，用于构建表格表头，每项含 alias、type |
| total (明细总数) | 整型 (Integer) | 明细记录总数 |

### 请求示例
```bash
curl 'https://指标中枢域名/open-api/metric/instance/detail' \
  -X 'POST' \
  -H 'authorization: Bearer bd48ef7ff4684cacb0b8cea2da56a94e' \
  -H 'content-type: application/json' \
  --data-raw '{
    "sceneVersionUid": "7dda43b03da04ef79ca935ac14a1ca60",
    "instanceId": 4021,
    "pageNum": 1,
    "pageSize": 2
}'
```

### 返回示例
```json
{
    "code": 0,
    "data": {
        "total": 7392,
        "list": [
            {
                "交易时间段": "早上",
                "交易日期": "2023-01-02 00:00:00",
                "学生当前状态": "在读",
                "ID": "1"
            }
        ],
        "columns": [
            { "alias": "交易时间段", "type": "VARCHAR" },
            { "alias": "交易日期",   "type": "DATETIME" },
            { "alias": "学生当前状态", "type": "VARCHAR" }
        ]
    },
    "msg": ""
}
```

---

## 9. 查明细数据单字段去重 (Distinct Values of a Field in Detail Data)

### 用途
用于查询指定指标实例明细数据中某字段的所有可能取值（用于构建该字段的下拉筛选列表）。当获取明细数据后，可调用此接口根据某字段获取所有不同选项。

### URL & 方法
`POST /open-api/metric/instance/detail-distinct-field`

### 请求头参数
请求头参数说明与接口6相同

### 请求体参数

| 字段名 | 类型 (Type) | 必填 | 描述 (Description) | 示例 |
|--------|-------------|------|---------------------|------|
| sceneVersionUid (场景版本 UID) | 字符串 (String) | 是 | 场景版本 UID (确定在哪个场景版本下查询) | "7dda43b03da04ef79ca935ac14a1ca60" |
| instanceId (指标实例ID) | 整型 (Integer) | 是 | 指标实例 ID (用于确定查询哪个实例的明细) | 4021 |
| instanceCode (指标实例标识) | 字符串 (String) | 否 | 指标实例标识 (若同时提供，以 instanceId 优先) | "byxf" |
| filter (明细数据筛选) | 对象 (Object) | 否 | 明细数据筛选条件，与 globalFilter 结构相同 | 参考接口6 |
| columnAlias (字段名) | 字符串 (String) | 是 | 需要去重的字段别名 (要查询值的字段名称) | "商户名称" |
| searchValue (选项名) | 字符串 (String) | 否 | 模糊查询关键字 (用于筛选选项名称，可空) | "在读" |
| pageNum (分页页数) | 整型 (Integer) | 是 | 当前查询页数 | 1 |
| pageSize (每页条数) | 整型 (Integer) | 是 | 每页查询条目数 | 2 |

### 响应参数

| 字段名 | 类型 | 描述 (Description) |
|--------|------|---------------------|
| data (字段内容) | 数组 (Array) | 去重后的字段值列表 |

### 请求示例
```bash
curl 'https://指标中枢域名/open-api/metric/instance/detail-distinct-field' \
  -X 'POST' \
  -H 'authorization: Bearer bd48ef7ff4684cacb0b8cea2da56a94e' \
  -H 'content-type: application/json' \
  --data-raw '{
    "sceneVersionUid": "7dda43b03da04ef79ca935ac14a1ca60",
    "instanceId": 4021,
    "columnAlias": "商户名称",
    "pageNum": 1,
    "pageSize": 2
}'
```

### 返回示例
```json
{
    "code": 0,
    "data": [
        "在读"
    ],
    "msg": ""
}
```

---

## 10. 根据多个场景版本 UUID 查询用户有权限查看的指标实例列表 (Query Metric Instances by Multiple Scene Version UUIDs)

### 用途
该接口用于根据多个场景版本的 UUID 查询当前用户有权限查看的指标实例列表。适用于需要一次查询多个场景版本下实例的场景。

### URL & 方法
`POST /open-api/metric/scene/version/metric-instances-withVersions`

### 请求头参数
请求头参数说明与接口6相同

### 请求体参数

| 字段名 | 类型 (Type) | 必填 | 描述 (Description) | 示例 |
|--------|-------------|------|---------------------|------|
| sceneVersionUids (场景版本 UID) | 字符串数组 (Array of String) | 是 | 场景版本 UID 列表 (指定需要查询的场景版本) | ["7dda43b03da04ef79ca935ac14a1ca60"] |
| tags (标签) | 字符串数组 (Array of String) | 否 | 指标标签筛选 (按标签查询实例) | ["校园卡组件"] |
| pageNum (分页页数) | 整型 (Integer) | 否 | 当前查询页数 | 1 |
| pageSize (每页条数) | 整型 (Integer) | 否 | 每页查询条目数 | 2 |

### 响应参数
返回结果为多个场景版本下的指标实例数组，每个对象包含以下字段：

| 字段名 | 类型 | 描述 (Description) |
|--------|------|---------------------|
| sceneVersionUid (场景版本 UID) | 字符串 (String) | 场景版本 UID (对应请求中的某个场景版本) |
| id (指标实例ID) | 整型 (Integer) | 指标实例 ID |
| parentId (父级ID) | 整型 (Integer) | 父指标实例 ID |
| name (指标实例名称) | 字符串 (String) | 指标实例名称 |
| code (指标实例标识) | 字符串 (String) | 指标实例标识 |
| state (指标实例状态) | 整型 (Integer) | 指标实例状态：0 未上线，1 已上线 |
| definition (指标定义信息) | 对象 (Object) | 指标定义信息 (Same structure as接口4的definition) |
| recalculateList (指标精算列表) | 数组 (Array) | 指标实例的精算列表 (Same structure as接口4的recalculateList) |

### 请求示例
```bash
curl 'https://指标中枢域名/open-api/metric/scene/version/metric-instances-withVersions' \
  -X 'POST' \
  -H 'authorization: Bearer bd48ef7ff4684cacb0b8cea2da56a94e' \
  -H 'content-type: application/json' \
  --data-raw '{
    "sceneVersionUids": ["7dda43b03da04ef79ca935ac14a1ca60"],
    "tags": ["校园卡组件"]
}'
```

### 返回示例
```json
{
    "code": 0,
    "data": [
        {
            "sceneVersionUid": "7dda43b03da04ef79ca935ac14a1ca60",
            "id": 4057,
            "parentId": null,
            "name": "本月消费",
            "code": "byxf",
            "dims": ["学号", "商户名称"],
            "definition": {
                "id": 462,
                "name": "本月消费",
                "uid": "4fbee76efa28475c9732ec032255b952",
                "type": 2,
                "versionName": "main",
                "versionUuid": "afbf45a3415b482fb8d11f7d3ab31b21",
                "metadata": {
                    "metric_source": "数据中台 -> metric_dwd.t_dwd_fact_a44_28029938",
                    "metric_paraphrase": "记录用户在本月 1日至当前日期之间的消费总金额...",
                    "metric_data_source": ""
                },
                "metricDomain": [{"name": "消费组件", "id": 45, "parentId": 42}],
                "tags": ["校园卡组件"],
                "departments": ["网信办", "网络空间安全学院"],
                "logic": "对消费金额（原子）进行 SUM 求和...",
                "remark": "统计用户在当前自然月内的消费次数与金额..."
            },
            "recalculateList": [
                {
                    "id": 62,
                    "metricInstanceId": 4021,
                    "name": "最受欢迎的商户",
                    "code": "zshydsh",
                    "queryLanguage": "SELECT cast(sum(${sys_metric_measure}) as decimal(20,2)) AS measure, 商户名称, 商户名称_desc FROM ${sys_metric_resultset} ...",
                    "measureCol": "measure",
                    "dimCols": ["商户名称", "商户名称_desc"],
                    "isDefault": true
                }
            ]
        }
    ],
    "msg": ""
}
```

---

## 11. 获取指标管理定义的标签列表 (Get List of Tags Defined in Metric Management)

### 用途
该接口用于获取指标管理模块中定义的所有标签列表，标签用于指标实例查询筛选（接口4、10 中的 tags 参数）。

### URL & 方法
`POST /open-api/metric/metricmgt/tags/list`
（不需要请求体，仅请求头携带 Authorization）

### 请求头参数

| 字段名 | 类型 (Type) | 必填 | 描述 (Description) | 示例 |
|--------|-------------|------|---------------------|------|
| Authorization (认证 token) | 字符串 (String) | 是 | 调用获取 APP 令牌接口获取的 access_token，通过请求头传参 | Bearer bd48ef7ff4684cacb0b8cea2da56a94e |

### 请求示例
```bash
curl 'https://指标中枢域名/open-api/metric/metricmgt/tags/list' \
  -X 'POST' \
  -H 'authorization: Bearer bd48ef7ff4684cacb0b8cea2da56a94e'
```

### 响应参数

| 字段名 | 类型 | 描述 (Description) |
|--------|------|---------------------|
| id (标签ID) | 整型 (Integer) | 标签 ID |
| labelValue (标签名称) | 字符串 (String) | 标签名称，传给接口4和10的 tags 参数 |

### 返回示例
```json
{
    "code": 0,
    "data": [
        { "id": 1, "labelValue": "核心指标", "createTime": 1753326015000 },
        { "id": 2, "labelValue": "教学",   "createTime": 1753326257000 }
    ],
    "msg": ""
}
```