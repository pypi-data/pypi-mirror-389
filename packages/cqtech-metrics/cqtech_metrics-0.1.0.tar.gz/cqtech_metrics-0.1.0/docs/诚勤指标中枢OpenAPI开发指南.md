# 诚勤指标中枢OpenAPI开发指南

![图片 6](https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/res/yBRq1ZP1bjAo6Odv/img/f54374ea-231e-4e5b-9b53-f03b7374e9d1.png)

诚勤教育指标中枢OpenAPI开发指南

— 南京诚勤教育科技有限公司版权所有 —

## 目录

1. [通用响应字段说明](#1-通用响应字段说明)
2. [获取APP令牌](#2-获取app令牌)
3. [查询应用下所有场景版本列表（跟登录人权限无关）](#3-查询应用下所有场景版本列表跟登录人权限无关)
4. [根据应用权限查询场景版本列表](#4-根据应用权限查询场景版本列表)
5. [根据单一场景版本uid查询指标实例定义信息，以及依赖指标定义信息](#5-根据单一场景版本uid查询指标实例定义信息以及依赖指标定义信息)
6. [根据单一场景版本uid查询指标血缘，包含数据模型](#6-根据单一场景版本uid查询指标血缘包含数据模型)
7. [根据多个指标实例标识查询指标执行结果及评价](#7-根据多个指标实例标识查询指标执行结果及评价)
8. [根据多个指标实例id查询指标执行结果及评价](#8-根据多个指标实例id查询指标执行结果及评价)
9. [查询指标实例明细数据](#9-查询指标实例明细数据)
10. [查明细数据单字段去重](#10-查明细数据单字段去重)
11. [根据多个场景版本uuid查询用户有权限查看的指标实例列表](#11-根据多个场景版本uuid查询用户有权限查看的指标实例列表)
12. [获取指标管理定义的标签列表](#12-获取指标管理定义的标签列表)

本文档旨在为需要对接指标中枢平台的第三方应用提供完整、清晰、准确的接口说明，本文档共整理了11个接口，囊括了鉴权认证，场景版本和指标实例元数据，指标血缘，指标执行结果，指标明细数据以及其他辅助接口，基本涵盖了从查看指标，到分析结果，再到朔源明细等使用场景。接口包含了URL、Method、请求参数和返回响应，同时标注了参数和响应各个字段的说明、类型、是否必填、描述和示例，并提供了请求示例和返回示例作为参考。

## <a id="1-通用响应字段说明"></a>1 通用响应字段说明

| 字段名 | 说明 | 类型 | 描述 |
| --- | --- | --- | --- |
| code | 响应码 | 整型 | 0表示响应正常，401表示token过期，需重新调用第2个获取APP令牌接口获取access_token，500表示响应异常，需检查接口参数或指标配置是否正确 |
| data | 响应主体 |  | 以下接口返回响应字段介绍皆从data开始介绍 |
| msg | 异常描述 | 字符串 | 当code返回0是，表示响应正常，msg返回空字符串 |

## <a id="2-获取app令牌"></a>2 获取APP令牌

该接口用于鉴权认证，调用任何接口前都需要先调用该接口拿到token，且token具有时效性，失效后需重新获取。

### URL

| 方法 | 路径 |
| --- | --- |
| POST | `/open-api/system/oauth2-openapi/token` |

### 请求参数

**Header参数**

| 参数名 | 说明 | 类型 | 是否必填 | 描述 | 示例 |
| --- | --- | --- | --- | --- | --- |
| appkey | 应用编号 | 字符串 | 必填 | 在指标中枢平台->第三方应用开放->应用管理可以找到对应应用的编号 | ZNZSCS |
| nonce | 10位随机数 | 整型 | 必填 | 随机生成10位数字 | 1768277523 |
| curtime | 当前时间（秒） | 整型 | 必填 | 当前时间的时间戳，单位秒，不是毫秒 | 1761042060 |
| username | 登录人工号 | 字符串 | 必填 | 当前登录人工号 | 19950174 |
| checksum | 校验码 | 字符串 | 必填 | 通过username、secret（应用密钥，指标中枢平台->第三方应用开放->应用管理可以找到）、nonce、curtime再通过org.apache.commons.codec.digest.DigestUtils的静态方法sha1Hex生成不可逆的加密字符串，即签名。 |  |

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

### 返回响应

| 字段名 | 说明 | 类型 | 描述 |
| --- | --- | --- | --- |
| access_token | 认证token | 字符串 | 用于业务接口调用认证，通过请求头传参headers:{ "authorization": `Bearer ${access_token}`} |
| refresh_token | 刷新token | 字符串 | 暂未提供刷新token接口，该字段可忽略 |
| token_type | token类型 | 字符串 | token类型只有一种：bearer |
| expires_in | token有效期（秒） | 整型 | token有效期：1800秒，过期后需要重新调用该接口获取access_token |

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

## <a id="3-查询应用下所有场景版本列表跟登录人权限无关"></a>3 查询应用下所有场景版本列表（跟登录人权限无关）

该接口适用于第三方应用管理端配置场景版本，可查询应用下可访问的所有场景版本，与登录人权限无关。

### URL

| 方法 | 路径 |
| --- | --- |
| POST | `/open-api/metric/scene/versions` |

### 请求参数

**Header参数**

| 参数名 | 说明 | 类型 | 是否必填 | 描述 | 示例 |
| --- | --- | --- | --- | --- | --- |
| authorization | 认证token | 字符串 | 必填 | 通过调用获取APP令牌接口拿到access_token，通过请求头传参headers:{ "authorization": `Bearer ${access_token}`} | Bearer 784553cdccf745b38714b3f4552b42fe |

**Body参数**

| 参数名 | 说明 | 类型 | 是否必填 | 描述 | 示例 |
| --- | --- | --- | --- | --- | --- |
| name | 场景版本名称 | 字符串 | 不必填 | 用于场景名称模糊查询 | 第五轮学科评估 |
| sceneVersionStatus | 场景版本状态 | 整型 | 不必填 | 0下线，1上线，不传表示查所有状态 | 1 |
| pageNo | 分页页数 | 整型 | 必填 | 当前查询的页数 | 1 |
| pageSize | 每页条数 | 整型 | 必填 | 每页查询数据条数 | 10 |

### 请求示例

```bash
curl 'https://指标中枢域名/open-api/metric/scene/versions' \
  -X 'POST' \
  -H 'authorization: Bearer 9c37206336fb4fd38b9e09783e41a2a2' \
  -H 'content-type: application/json' \
  --data-raw '{
    "name": "学生",
    "sceneVersionStatus": 1,
    "pageNum":1,
    "pageSize":2
  }'
```

### 返回响应

| 字段名 | 说明 | 类型 | 描述 |
| --- | --- | --- | --- |
| list | 场景版本列表 | 数组 |  |
| total | 场景版本总数 | 整型 |  |

**list**

| 字段名 | 说明 | 类型 | 描述 |
| --- | --- | --- | --- |
| id | 场景版本id | 整型 |  |
| name | 场景名称 | 字符串 |  |
| versionName | 场景版本名称 | 字符串 |  |
| uid | 场景版本uid | 字符串 | 在后面接口中会用到uid作为接口参数 |
| status | 场景版本状态 | 整型 | 0未上线，1已上线 |
| cronExpression | 定时任务cron表达式 | 字符串 |  |
| instanceCount | 指标实例数量 | 整型 |  |

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
                "sourceVersion": null,
                "status": 1,
                "cronExpression": "0 0 0 1 * ?",
                "constructionCycle": "",
                "file": null,
                "remark": "",
                "instanceCount": 110,
                "taskId": 509,
                "fileId": null
            },
            {
                "id": 156,
                "name": "s学生信息场景",
                "versionName": "s精算场景",
                "uid": "5c9f889223624dc79c5d2287ca3e6bb3",
                "sourceVersion": null,
                "status": 1,
                "cronExpression": "0 0 0 1 * ?",
                "constructionCycle": "",
                "file": null,
                "remark": "",
                "instanceCount": 14,
                "taskId": 506,
                "fileId": null
            }
        ],
        "total": 9
    },
    "msg": ""
}
```

## <a id="4-根据应用权限查询场景版本列表"></a>4 根据应用权限查询场景版本列表

该接口适用于第三方应用用户端配置场景版本，可查询应用下登录人有权限访问的场景版本。

### URL

| 方法 | 路径 |
| --- | --- |
| POST | `/open-api/metric/scene/versions/with-permission` |

### 请求参数

**Header参数**

| 参数名 | 说明 | 类型 | 是否必填 | 描述 | 示例 |
| --- | --- | --- | --- | --- | --- |
| authorization | 认证token | 字符串 | 必填 | 通过调用获取APP令牌接口拿到access_token，通过请求头传参headers:{ "authorization": `Bearer ${access_token}`} | Bearer 784553cdccf745b38714b3f4552b42fe |

**Body参数**

| 参数名 | 说明 | 类型 | 是否必填 | 描述 | 示例 |
| --- | --- | --- | --- | --- | --- |
| name | 场景版本名称 | 字符串 | 不必填 | 用于场景版本名称模糊查询 | 第五轮学科评估 |
| sceneVersionStatus | 场景版本状态 | 整型 | 不必填 | 0下线，1上线，不传表示查所有状态 | 1 |
| pageNo | 分页页数 | 整型 | 必填 | 当前查询的页数 | 1 |
| pageSize | 每页条数 | 整型 | 必填 | 每页查询数据条数 | 10 |

### 请求示例

```bash
curl 'https://指标中枢域名/open-api/metric/scene/versions/with-permission' \
  -X 'POST' \
  -H 'authorization: Bearer 9c37206336fb4fd38b9e09783e41a2a2' \
  -H 'content-type: application/json' \
  --data-raw '{
    "name": "学生",
    "sceneVersionStatus": 1,
    "pageNum":1,
    "pageSize":2
  }'
```

### 返回响应

| 字段名 | 说明 | 类型 | 描述 |
| --- | --- | --- | --- |
| list | 场景版本列表 | 数组 |  |
| total | 场景版本总数 | 整型 |  |

**list**

| 字段名 | 说明 | 类型 | 描述 |
| --- | --- | --- | --- |
| id | 场景版本id | 整型 |  |
| name | 场景名称 | 字符串 |  |
| versionName | 场景版本名称 | 字符串 |  |
| uid | 场景版本uid | 字符串 | 在后面接口中会用到uid作为接口参数 |
| status | 场景版本状态 | 整型 | 0未上线，1已上线 |
| cronExpression | 定时任务cron表达式 | 字符串 |  |
| instanceCount | 指标实例数量 | 整型 |  |

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
                "sourceVersion": null,
                "status": 1,
                "cronExpression": "0 0 0 1 * ?",
                "constructionCycle": "",
                "file": null,
                "remark": "",
                "instanceCount": 110,
                "taskId": 509,
                "fileId": null
            },
            {
                "id": 156,
                "name": "s学生信息场景",
                "versionName": "s精算场景",
                "uid": "5c9f889223624dc79c5d2287ca3e6bb3",
                "sourceVersion": null,
                "status": 1,
                "cronExpression": "0 0 0 1 * ?",
                "constructionCycle": "",
                "file": null,
                "remark": "",
                "instanceCount": 14,
                "taskId": 506,
                "fileId": null
            }
        ],
        "total": 9
    },
    "msg": ""
}
```

## <a id="5-根据单一场景版本uid查询指标实例定义信息以及依赖指标定义信息"></a>5 根据单一场景版本uid查询指标实例定义信息，以及依赖指标定义信息

该接口可基于某一场景版本查询登录人有权限的指标实例信息、定义信息、以及其依赖指标的定义信息。

### URL

| 方法 | 路径 |
| --- | --- |
| POST | `/open-api/metric/scene/version/metric-instances` |

### 请求参数

**Header参数**

| 参数名 | 说明 | 类型 | 是否必填 | 描述 | 示例 |
| --- | --- | --- | --- | --- | --- |
| authorization | 认证token | 字符串 | 必填 | 通过调用获取APP令牌接口拿到access_token，通过请求头传参headers:{ "authorization": `Bearer ${access_token}`} | Bearer 784553cdccf745b38714b3f4552b42fe |

**Body参数**

| 参数名 | 说明 | 类型 | 是否必填 | 描述 | 示例 |
| --- | --- | --- | --- | --- | --- |
| sceneVersionUid | 场景版本uid | 字符串 | 必填 | 用于确定查询的哪个场景版本下的指标实例 | 784553cdccf745b38714b3f4552b42fe |
| instanceCodes | 指标实例标识 | 字符串数组 | 不必填 | 用于过滤指标实例，不传则查询登录人有权限的所有指标实例 | ['byxf'] |
| metricInstanceName | 指标实例名称 | 字符串 | 不必填 | 用于指标实例名称模糊查询 | 本月消费 |
| tags | 指标标签 | 字符串数组 | 不必填 | 用于根据标签筛选指标实例 | ['核心指标'] |
| state | 指标实例状态 | 整型 | 不必填 | 0未上线，1已上线，不传则查询登录人有权限的所有指标实例 | 1 |
| pageNo | 分页页数 | 整型 | 必填 | 当前查询的页数 | 1 |
| pageSize | 每页条数 | 整型 | 必填 | 每页查询数据条数 | 10 |

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
    "pageNum":1,
    "pageSize":2
  }'
```

### 返回响应

| 字段名 | 说明 | 类型 | 描述 |
| --- | --- | --- | --- |
| list | 指标实例列表 | 数组 |  |
| total | 指标实例总数 | 整型 |  |

**list**

| 字段名 | 说明 | 类型 | 描述 |
| --- | --- | --- | --- |
| id | 指标实例id | 整型 |  |
| name | 指标实例名称 | 字符串 |  |
| code | 指标实例标识 | 字符串 |  |
| dims | 维度 | 字符串数组 |  |
| state | 指标实例状态 | 整型 | 0未上线，1已上线 |
| definition | 指标定义信息 | 对象 |  |
| recalculateList | 指标实例精算列表 | 数组 |  |
| children | 依赖指标实例 | 数组 | 当前指标实例依赖的指标实例树，数据结构与list一致 |

**definition**

| 字段名 | 说明 | 类型 | 描述 |
| --- | --- | --- | --- |
| id | 指标定义id | 整型 |  |
| name | 指标定义名称 | 字符串 |  |
| uid | 指标定义uid | 字符串 |  |
| type | 指标类型 | 整型 | 1原子指标、2派生指标、3复合指标、4自定义指标 |
| versionName | 指标版本名称 | 字符串 |  |
| versionUuid | 指标版本uid | 字符串 |  |
| metadata | 指标元数据 | 对象 | 预设元素据含义：metric_source指标来源，metric_paraphrase指标释义，metric_data_source数据来源 |
| metricDomain | 指标域 | 对象 |  |
| tags | 标签 | 数组 |  |
| departments | 归口部门 | 数组 |  |
| logic | 计算规则 | 字符串 |  |
| remark | 指标简述 | 字符串 |  |

**recalculateList**

| 字段名 | 说明 | 类型 | 描述 |
| --- | --- | --- | --- |
| id | 指标精算id | 整型 |  |
| metricInstanceId | 指标实例id | 整型 |  |
| name | 指标精算名称 | 字符串 |  |
| code | 指标精算标识 | 字符串 |  |
| queryLanguage | 指标精算sql语句 | 字符串 |  |
| measureCol | 度量字段 | 字符串 |  |
| dimCols | 维度字段 | 数组 | 维度_desc代表维值描述，可能为空 |
| isDefault | 是否默认 | 布尔 | true默认，false非默认 |

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
                "dims": [
                    "学号",
                    "商户名称"
                ],
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
                            {
                                "column": "学号",
                                "type": 1
                            },
                            {
                                "column": "商户名称",
                                "type": 1
                            }
                        ],
                        "atomMetricUuid": "b9835a2d64374a58a6727524b2d8e914"
                    },
                    "metadata": {
                        "metric_source": "数据中台 -> metric_dwd.t_dwd_fact_a44_28029938",
                        "metric_paraphrase": "记录用户在本月1日至当前日期之间的消费总金额和总次数，用于月度行为分析、活跃度监控和短期营销效果评估，支持动态用户画像更新。",
                        "metric_data_source": ""
                    },
                    "metricDomain": [
                        {
                            "name": "消费组件",
                            "id": 45,
                            "parentId": 42
                        }
                    ],
                    "tags": [
                        "校园卡组件"
                    ],
                    "departments": [
                        "网信办",
                        "网络空间安全学院"
                    ],
                    "relevantDeptIds": [
                        101,
                        104
                    ],
                    "logic": "对【消费金额（原子）】进行SUM求和，通过派生指标，进行学号的维度设置，计算当前用户的总消费金额，再根据过滤条件 :[交易时间 小于等于 系统参数 后1天 即2025-10-18 00:00:00 且 交易时间 大于等于 系统参数 当月一号 即2025-10-01 00:00:00 且 交易类型 等于 消费] 取当前月的数据。",
                    "remark": "统计用户在当前自然月内的消费次数与金额，反映其近期活跃度与消费趋势。"
                },
                "metricDomain": [
                    {
                        "name": "消费组件",
                        "id": 45,
                        "parentId": 42
                    }
                ],
                "tags": [
                    "校园卡组件"
                ],
                "departments": null,
                "relevantDeptIds": [
                    101,
                    104
                ],
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
                                "columns": [
                                    "交易金额"
                                ],
                                "dataModel": "三十天消费记录"
                            },
                            "metadata": {
                                "metric_source": "",
                                "metric_paraphrase": "",
                                "metric_data_source": ""
                            },
                            "metricDomain": [
                                {
                                    "name": "消费组件",
                                    "id": 45,
                                    "parentId": 42
                                }
                            ],
                            "tags": [
                                "校园卡组件"
                            ],
                            "departments": null,
                            "relevantDeptIds": [],
                            "logic": "",
                            "remark": ""
                        },
                        "metricDomain": [
                            {
                                "name": "消费组件",
                                "id": 45,
                                "parentId": 42
                            }
                        ],
                        "tags": [
                            "校园卡组件"
                        ],
                        "departments": null,
                        "relevantDeptIds": [],
                        "children": [],
                        "state": 1,
                        "recalculateList": null
                    }
                ],
                "state": 1,
                "recalculateList": [
                    {
                        "id": 62,
                        "metricInstanceId": 4021,
                        "name": "最受欢迎的商户",
                        "code": "zshydsh",
                        "queryLanguage": "SELECT cast(sum(${sys_metric_measure}) as decimal(20,2)) AS measure, 商户名称, 商户名称_desc FROM ${sys_metric_resultset} where 商户名称 is not null GROUP BY 商户名称,商户名称_desc ORDER BY measure DESC limit 1",
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

## <a id="6-根据单一场景版本uid查询指标血缘包含数据模型"></a>6 根据单一场景版本uid查询指标血缘，包含数据模型

该接口可基于某一场景版本查询登录人有权限的指标实例血缘，包括依赖指标、数据模型、数据源、数据表。

### URL

| 方法 | 路径 |
| --- | --- |
| POST | `/open-api/metric/scene/version/metric-instance/lineage` |

### 请求参数

**Header参数**

| 参数名 | 说明 | 类型 | 是否必填 | 描述 | 示例 |
| --- | --- | --- | --- | --- | --- |
| Authorization | 认证token | 字符串 | 必填 | 通过调用获取APP令牌接口拿到access_token，通过请求头传参headers:{ "authorization": `Bearer ${access_token}`} | Bearer 784553cdccf745b38714b3f4552b42fe |

**Body参数**

| 参数名 | 说明 | 类型 | 是否必填 | 描述 | 示例 |
| --- | --- | --- | --- | --- | --- |
| sceneVersionUid | 场景版本uid | 字符串 | 必填 | 用于确定查询的哪个场景版本下的指标实例 | 784553cdccf745b38714b3f4552b42fe |
| instanceCodes | 指标实例标识 | 字符串数组 | 不必填 | 用于过滤指标实例，不传则查询登录人有权限的所有指标实例 | ['byxf'] |

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

### 返回响应

| 字段名 | 说明 | 类型 | 描述 |
| --- | --- | --- | --- |
| id | 指标实例id | 整型 |  |
| name | 指标实例名称 | 字符串 |  |
| code | 指标实例标识 | 字符串 |  |
| type | 数据类型 | 整型 | 1指标，2数据模型，3数据源，4数据表 |
| state | 指标实例状态 | 整型 | 0未上线，1已上线 |
| definition | 指标定义信息 | 对象 |  |
| children | 依赖数据 | 数组 | 包括依赖指标实例、数据模型、数据源、数据表 |

**definition**

| 字段名 | 说明 | 类型 | 描述 |
| --- | --- | --- | --- |
| id | 指标定义id | 整型 |  |
| name | 指标定义名称 | 字符串 |  |
| uid | 指标定义uid | 字符串 |  |
| type | 指标类型 | 整型 | 1原子指标、2派生指标、3复合指标、4自定义指标 |
| versionName | 指标版本名称 | 字符串 |  |
| versionUuid | 指标版本uid | 字符串 |  |

**children数据模型**

| 字段名 | 说明 | 类型 | 描述 |
| --- | --- | --- | --- |
| id | 数据模型id | 整型 |  |
| name | 数据模型名称 | 整型 |  |
| type | 数据类型 | 整型 | 1指标，2数据模型，3数据源，4数据表 |

**children数据源（type=3）**

| 字段名 | 说明 | 类型 | 描述 |
| --- | --- | --- | --- |
| id | 数据源id | 整型 |  |
| name | 数据源名称 | 字符串 |  |
| type | 数据类型 | 整型 | 1指标，2数据模型，3数据源，4数据表 |

**children数据表（type=4）**

| 字段名 | 说明 | 类型 | 描述 |
| --- | --- | --- | --- |
| name | 数据表名称 | 字符串 |  |
| type | 数据类型 | 整型 | 1指标，2数据模型，3数据源，4数据表 |

### 返回示例

```json
{
    "code": 0,
    "data": [
        {
            "id": 4021,
            "name": "本月消费",
            "code": "byxf",
            "state": "1",
            "parentId": null,
            "type": 1,
            "definition": {
                "id": null,
                "name": "本月消费",
                "uuid": "4fbee76efa28475c9732ec032255b952",
                "type": 2,
                "versionName": "main",
                "versionUuid": "afbf45a3415b482fb8d11f7d3ab31b21",
                "definitionConfig": {
                    "@class": "cn.iocoder.yudao.module.metric.dal.dataobject.metricmgt.DerivedDefinitionConfigInfo",
                    "hdim": [
                        {
                            "column": "学号",
                            "type": 1
                        },
                        {
                            "column": "商户名称",
                            "type": 1
                        }
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
                            "columns": [
                                "交易金额"
                            ],
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
            ]
        }
    ],
    "msg": ""
}
```

## <a id="7-根据多个指标实例标识查询指标执行结果及评价"></a>7 根据多个指标实例标识查询指标执行结果及评价

该接口可查询指标实例执行结果及评价信息，包括针对指标实例执行结果进行指标实时精算结果，以及同一个指标实例需要同时查询不同参数的2种查询结果。

### URL

| 方法 | 路径 |
| --- | --- |
| POST | `/open-api/metric/instance/codes/measure` |

### 请求参数

**Header参数**

| 参数名 | 说明 | 类型 | 是否必填 | 描述 | 示例 |
| --- | --- | --- | --- | --- | --- |
| authorization | 认证token | 字符串 | 必填 | 通过调用获取APP令牌接口拿到access_token，通过请求头传参headers:{ "authorization": `Bearer ${access_token}`} | Bearer 784553cdccf745b38714b3f4552b42fe |

**Body参数**

| 参数名 | 说明 | 类型 | 是否必填 | 描述 | 示例 |
| --- | --- | --- | --- | --- | --- |
| sceneVersionUid | 场景版本uid | 字符串 | 必填 | 用于确定查询的哪个场景版本下的指标实例 | 784553cdccf745b38714b3f4552b42fe |
| recalculate | 指标精算标志 | 布尔 | 不必填 | 为true时会使用指标实例默认的精算sql实时计算结果，若没有默认精算sql则返回指标实例原始计算结果 | true |
| instanceCodes | 指标实例标识 | 字符串数组 | 不必填 | 用于过滤指标实例，不传则查询登录人有权限的所有指标实例 | ['byxf'] |
| globalFilter | 全局筛选条件 | 对象 | 不必填 | 所有指标实例用一种查询筛选条件 | 查看结构 |
| instances | 指标实例差异参数 | 数组 | 不必填 | 针对指标实例差异化参数单独为每个指标实例定义维度、筛选条件等参数 | 查看结构 |

**globalFilter查看示意**

| 参数名 | 说明 | 类型 | 是否必填 | 描述 | 示例 |
| --- | --- | --- | --- | --- | --- |
| op | 逻辑运算 | 字符串 | 必填 | AND、OR | AND |
| exprs | 筛选项 | 数组 | 必填 |  | 查看结构 |
| querys | 嵌套筛选 | 数组 | 不必填 | 为嵌套筛选条件，例如第一层是AND，第二次是OR。其数据结构为globalFilter[] |  |

**exprs**

| 参数名 | 说明 | 类型 | 是否必填 | 描述 | 示例 |
| --- | --- | --- | --- | --- | --- |
| field | 筛选字段 | 字符串 | 必填 | 范围为指标实例的维度和度量(measure) | 学院 |
| op | 运算符 | 字符串 | 必填 | EQ("=")、NE("!=")、IN("in")、 NOTIN("not in")、LIKE("like")、 NOTLIKE("not like")、ISNULL("is null")、 ISNOTNULL("is not null")、LT("<"), GT(">")、LTE("<=")、GTE(">=") | EQ |
| value | 筛选值 | 字符串、数字 | ISNULL和ISNOTNULL不必填，其他必填 |  | 矿业工程 |

**instances**

| 参数名 | 说明 | 类型 | 是否必填 | 描述 | 示例 |
| --- | --- | --- | --- | --- | --- |
| instanceCode | 指标实例标识 | 字符串 | 必填 | 用于确定查询的哪个指标实例，返回的指标实例执行结果会以该标识为key | sexcelpsmgzysyje |
| dims | 维度 | 字符串数组 | 不必填 | 用于确定查哪些维度的执行结果，若传空数组，则返回没有维度的执行数据，若传null，则返回执行后的所有数据 | ['学科','年度'] |
| filter | 当前指标实例的筛选条件 | 对象 | 不必填 | 针对当前指标实例定义的筛选条件，不会沿用globalFilter。<br>参数结构与globalFilter相同 | 查看结构 |
| id | 指标实例别名 | 字符串 | 不必填 | 适用于同一个指标实例，因参数不同需要查询多次执行结果，可传入不同id，返回的指标实例执行结果会以该id为key | Sexcelpsmgzysyje_subject |
| recalculate | 指标精算标志 | 布尔 | 不必填 | 为true时会使用指标实例默认的精算sql实时计算结果，若没有默认精算sql则返回指标实例原始计算结果 | true |
| recalculateCode | 精算标识 | 字符串 | 不必填 | 当recalculate为true时，传入该参数，则不会使用默认精算sql，而是使用该参数的精算sql，若该精算sql不存在，则该指标实例计算结果会返回异常 | dateFilter |

**globalFilter结构示例**

```json
{
    "op": "AND",
    "exprs": [
        {
            "field": "专业名称",
            "op": "LIKE",
            "value": "类"
        },
        {
            "field": "学籍状态",
            "op": "EQ",
            "value": "在籍"
        }
    ],
    "querys": [
        {
            "op": "OR",
            "exprs": [
                {
                    "field": "是否交流交换",
                    "op": "NE",
                    "value": "留学生"
                },
                {
                    "field": "是否交流交换",
                    "op": "ISNULL",
                    "value": ""
                }
            ]
        },
        {
            "op": "OR",
            "exprs": [
                {
                    "field": "学制",
                    "op": "EQ",
                    "value": "4"
                },
                {
                    "field": "学制",
                    "op": "EQ",
                    "value": "5"
                }
            ]
        }
    ]
}
```

**该示例表示：**

专业名称 like '%类%' AND 学籍状态 = '在籍' AND (是否交流交换 != '留学生' OR 是否交流交换 is null) AND (学制 = 4 OR 学制 = 5)

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

### 返回响应

| 字段名 | 说明 | 类型 | 描述 |
| --- | --- | --- | --- |
| byxf_max | 指标实例标识或id，根据传参变化 | 数组 | 在参数中若同一个指标示例需要查询多次，可传不同的id，则该字段为id，否则改字段为指标实例标识 |

**byxf_max**

| 字段名 | 说明 | 类型 | 描述 |
| --- | --- | --- | --- |
| dims | 维度：维值 | 对象 |  |
| dimsDesc | 维度：维值描述 | 对象 | 可能为空 |
| measureType | 统计值类型 | 整型 | 1数字，2字符串 |
| measure | 统计值 | 字符串 |  |
| assessments | 评价信息 | 数组 | 支持多组评价，recalculate为true（指标精算）时，assessments为null |

**assessments**

| 字段名 | 说明 | 类型 | 描述 |
| --- | --- | --- | --- |
| name | 评价名称 | 字符串 |  |
| ruleResults | 评价结果 | 对象 | name：评价结果，calDesc：评价规则描述 |

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
                            {
                                "name": "达标",
                                "calDesc": "大于等于250"
                            }
                        ]
                    },
                    {
                        "name": "校标",
                        "ruleResults": [
                            {
                                "name": "未达标",
                                "calDesc": "大于等于300"
                            }
                        ]
                    }
                ]
            }
        ]
    },
    "msg": ""
}
```

## <a id="8-根据多个指标实例id查询指标执行结果及评价"></a>8 根据多个指标实例id查询指标执行结果及评价

该接口可查询指标实例执行结果及评价信息，包括针对指标实例执行结果进行指标实时精算结果，以及同一个指标实例需要同时查询不同参数的2种查询结果。

### URL

| 方法 | 路径 |
| --- | --- |
| POST | `/open-api/metric/instance/ids/measure` |

### 请求参数

**Header参数**

| 参数名 | 说明 | 类型 | 是否必填 | 描述 | 示例 |
| --- | --- | --- | --- | --- | --- |
| Authorization | 认证token | 字符串 | 必填 | 通过调用获取APP令牌接口拿到access_token，通过请求头传参headers:{ "authorization": `Bearer ${access_token}`} | Bearer 784553cdccf745b38714b3f4552b42fe |

**Body参数**（参数结构与第7个接口参数类似，只是将指标实例标识换成了指标实例id）

| 参数名 | 说明 | 类型 | 是否必填 | 描述 | 示例 |
| --- | --- | --- | --- | --- | --- |
| sceneVersionUid | 场景版本uid | 字符串 | 必填 | 用于确定查询的哪个场景版本下的指标实例 | 784553cdccf745b38714b3f4552b42fe |
| recalculate | 指标精算标志 | 布尔 | 不必填 | 为true时会使用指标实例默认的精算sql实时计算结果，若没有默认精算sql则返回指标实例原始计算结果 | true |
| instanceIds | 指标实例id | 字符串数组 | 不必填 | 用于过滤指标实例，不传则查询登录人有权限的所有指标实例 | [2] |
| globalFilter | 全局筛选条件 | 对象 | 不必填 | 所有指标实例用一种查询筛选条件 | 查看结构 |
| instances | 指标实例差异参数 | 数组 | 不必填 | 针对指标实例差异化参数单独为每个指标实例定义维度、筛选条件等参数 | 查看结构 |

**globalFilter查看示意**

| 参数名 | 说明 | 类型 | 是否必填 | 描述 | 示例 |
| --- | --- | --- | --- | --- | --- |
| op | 逻辑运算 | 字符串 | 必填 | AND、OR | AND |
| exprs | 筛选项 | 数组 | 必填 |  | 查看结构 |
| querys | 嵌套筛选 | 数组 | 不必填 | 为嵌套筛选条件，例如第一层是AND，第二次是OR。其数据结构为globalFilter[] |  |

**exprs**

| 参数名 | 说明 | 类型 | 是否必填 | 描述 | 示例 |
| --- | --- | --- | --- | --- | --- |
| field | 筛选字段 | 字符串 | 必填 | 范围为指标实例的维度和度量(measure) | 学院 |
| op | 运算符 | 字符串 | 必填 | EQ("=")、NE("!=")、IN("in")、 NOTIN("not in")、LIKE("like")、 NOTLIKE("not like")、ISNULL("is null")、 ISNOTNULL("is not null")、LT("<"), GT(">")、LTE("<=")、GTE(">=") | EQ |
| value | 筛选值 | 字符串、数字 | ISNULL和ISNOTNULL不必填，其他必填 |  | 矿业工程 |

**instances->ITEMS**

| 参数名 | 说明 | 类型 | 是否必填 | 描述 | 示例 |
| --- | --- | --- | --- | --- | --- |
| instanceId | 指标实例id | 整型 | 必填 | 用于确定查询的哪个指标实例，返回的指标实例执行结果会以该id为key | 2 |
| dims | 维度 | 字符串数组 | 不必填 | 用于确定查哪些维度的执行结果 | ['学科','年度'] |
| filter | 当前指标实例的筛选条件 | 对象 | 不必填 | 针对当前指标实例定义的筛选条件，不会沿用globalFilter。<br>参数结构与globalFilter相同 | 查看结构 |
| id | 指标实例别名 | 字符串 | 不必填 | 适用于同一个指标实例，因参数不同需要查询多次执行结果，可传入不同id，返回的指标实例执行结果会以该id为key | Sexcelpsmgzysyje_subject |
| recalculate | 指标精算标志 | 布尔 | 不必填 | 为true时会使用指标实例默认的精算sql实时计算结果，若没有默认精算sql则返回指标实例原始计算结果 | true |
| recalculateCode | 精算标识 | 字符串 | 不必填 | 当recalculate为true时，传入该参数，则不会使用默认精算sql，而是使用该参数的精算sql，若该精算sql不存在，则该指标实例计算结果会返回异常 | dateFilter |

**globalFilter结构示意**

```json
{
    "op": "AND",
    "exprs": [
        {
            "field": "专业名称",
            "op": "LIKE",
            "value": "类"
        },
        {
            "field": "学籍状态",
            "op": "EQ",
            "value": "在籍"
        }
    ],
    "querys": [
        {
            "op": "OR",
            "exprs": [
                {
                    "field": "是否交流交换",
                    "op": "NE",
                    "value": "留学生"
                },
                {
                    "field": "是否交流交换",
                    "op": "ISNULL",
                    "value": ""
                }
            ]
        },
        {
            "op": "OR",
            "exprs": [
                {
                    "field": "学制",
                    "op": "EQ",
                    "value": "4"
                },
                {
                    "field": "学制",
                    "op": "EQ",
                    "value": "5"
                }
            ]
        }
    ]
}
```

该示意表示：

1. 专业名称 like '%类%' AND 学籍状态 = '在籍' AND (是否交流交换 != '留学生' OR 是否交流交换 is null) AND (学制 = 4 OR 学制 = 5)

### 请求示例

```bash
curl 'https://指标中枢域名/open-api/metric/instance/codes/measure' \
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

### 返回响应

| 字段名 | 说明 | 类型 | 描述 |
| --- | --- | --- | --- |
| byxf_max | 指标实例标识或id，根据传参变化 | 数组 | 在参数中若同一个指标示例需要查询多次，可传不同的id，则该字段为id，否则改字段为指标实例标识 |

**byxf_max**

| 字段名 | 说明 | 类型 | 描述 |
| --- | --- | --- | --- |
| dims | 维度：维值 | 对象 |  |
| dimsDesc | 维度：维值描述 | 对象 | 可能为空 |
| measureType | 统计值类型 | 整型 | 1数字，2字符串 |
| measure | 统计值 | 字符串 |  |
| assessments | 评价信息 | 数组 | 支持多组评价，recalculate为true（指标精算）时，assessments为null |

**assessments**

| 字段名 | 说明 | 类型 | 描述 |
| --- | --- | --- | --- |
| name | 评价名称 | 字符串 |  |
| ruleResults | 评价结果 | 对象 | name：评价结果，calDesc：评价规则描述 |

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
                            {
                                "name": "达标",
                                "calDesc": "大于等于250"
                            }
                        ]
                    },
                    {
                        "name": "校标",
                        "ruleResults": [
                            {
                                "name": "未达标",
                                "calDesc": "大于等于300"
                            }
                        ]
                    }
                ]
            }
        ]
    },
    "msg": ""
}
```

## <a id="9-查询指标实例明细数据"></a>9 查询指标实例明细数据

该接口可基于指标实例执行统计结果查询明细数据。

### URL

| 方法 | 路径 |
| --- | --- |
| POST | `/open-api/metric/instance/detail` |

### 请求参数

**Header参数**

| 参数名 | 说明 | 类型 | 是否必填 | 描述 | 示例 |
| --- | --- | --- | --- | --- | --- |
| Authorization | 认证token | 字符串 | 必填 | 通过调用获取APP令牌接口拿到access_token，通过请求头传参headers:{ "authorization": `Bearer ${access_token}`} | Bearer 784553cdccf745b38714b3f4552b42fe |

**Body参数**

| 参数名 | 说明 | 类型 | 是否必填 | 描述 | 示例 |
| --- | --- | --- | --- | --- | --- |
| sceneVersionUid | 场景版本uid | 字符串 | 必填 | 用于确定查询的哪个场景版本下的指标实例 | 784553cdccf745b38714b3f4552b42fe |
| instanceId | 指标实例id | 整型 | instanceId和instanceCode需必填一个 | 用于确定查询的是哪个指标实例的明细，比instanceCode优先级高，若instanceId和instanceCode都传值，则取instanceId | 2 |
| instanceCode | 指标实例标识 | 字符串 | instanceId和instanceCode需必填一个 | 用于确定查询的是哪个指标实例的明细，比instanceId优先级高， | byxf' |
| filter | 明细数据筛选 | 对象 | 不必填 | 用于筛选明细数据，用户需要看哪个维度的明细数据，也需要构建filter参数，其数据结构与globalFilter一致 | 查看结构 |
| orderField | 排序字段 | 字符串 | 不必填 | 需要排序的字段，用于表格展示明细后，用户选择字段排序 | 立项日期 |
| orderType | 排序规则 | 字符串 | 不必填 | asc正序,desc倒序 | asc |
| pageNo | 分页页数 | 整型 | 必填 | 当前查询的页数 | 1 |
| pageSize | 每页条数 | 整型 | 必填 | 每页查询数据条数 | 10 |

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

### 返回响应

| 字段名 | 说明 | 类型 | 描述 |
| --- | --- | --- | --- |
| list | 明细数据 | 数组 |  |
| columns | 明细字段 | 数组 | 用于构建表头，alias：字段名，type：字段类型 |
| total | 明细总数 | 整型 |  |

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
            {
                "alias": "交易时间段",
                "type": "VARCHAR"
            },
            {
                "alias": "交易日期",
                "type": "DATETIME"
            },
            {
                "alias": "学生当前状态",
                "type": "VARCHAR"
            }
        ]
    },
    "msg": ""
}
```

## <a id="10-查明细数据单字段去重"></a>10 查明细数据单字段去重

当拿到明细数据构建表格后，用户需要基于明细数据二次过滤，该接口可查询某字段有哪些值，可用于构架目字段下拉选择框的选项。

### URL

| 方法 | 路径 |
| --- | --- |
| POST | `/open-api/metric/instance/detail-distinct-field` |

### 请求参数

**Header参数**

| 参数名 | 说明 | 类型 | 是否必填 | 描述 | 示例 |
| --- | --- | --- | --- | --- | --- |
| Authorization | 认证token | 字符串 | 必填 | 通过调用获取APP令牌接口拿到access_token，通过请求头传参headers:{ "authorization": `Bearer ${access_token}`} | Bearer 784553cdccf745b38714b3f4552b42fe |

**Body参数**

| 参数名 | 说明 | 类型 | 是否必填 | 描述 | 示例 |
| --- | --- | --- | --- | --- | --- |
| sceneVersionUid | 场景版本uid | 字符串 | 必填 | 用于确定查询的哪个场景版本下的指标实例 | 784553cdccf745b38714b3f4552b42fe |
| instanceId | 指标实例id | 整型 | instanceId和instanceCode需必填一个 | 用于确定查询的是哪个指标实例的明细，比instanceCode优先级高，若instanceId和instanceCode都传值，则取instanceId | 2 |
| instanceCode | 指标实例标识 | 字符串 | instanceId和instanceCode需必填一个 | 用于确定查询的是哪个指标实例的明细，比instanceId优先级高， | byxf' |
| filter | 明细数据筛选 | 对象 | 不必填 | 用于筛选明细数据，用户需要看哪个维度的明细数据，也需要构建filter参数，其数据结构与globalFilter一致 | 查看结构 |
| columnAlias | 字段名 | 字符串 | 必填 | 查询某个字段的选项值 | 学生当前状态 |
| searchValue | 选项名 | 字符串 | 不必填 | 用户模糊查询选项内容 | 在读 |
| pageNo | 分页页数 | 整型 | 必填 | 当前查询的页数 | 1 |
| pageSize | 每页条数 | 整型 | 必填 | 每页查询数据条数 | 10 |

### 请求示例

```bash
curl 'https://指标中枢域名/open-api/metric/instance/detail-distinct-field' \
  -X 'POST' \
  -H 'authorization: Bearer bd48ef7ff4684cacb0b8cea2da56a94e' \
  -H 'content-type: application/json' \
  --data-raw '{
    "sceneVersionUid": "7dda43b03da04ef79ca935ac14a1ca60",
    "instanceId": 4021,
    "columnAlias": "商户名称"
    "pageNum": 1,
    "pageSize": 2
  }'
```

### 返回响应

| 字段名 | 说明 | 类型 | 描述 |
| --- | --- | --- | --- |
| data | 字段内容 | 数组 | 返回该字段所有选项并去重 |

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

## <a id="11-根据多个场景版本uuid查询用户有权限查看的指标实例列表"></a>11 根据多个场景版本uuid查询用户有权限查看的指标实例列表

该接口适用于需要基于多个场景版本查询指标实例的情况。

### URL

| 方法 | 路径 |
| --- | --- |
| POST | `/open-api/metric/scene/version/metric-instances-withVersions` |

### 请求参数

**Header参数**

| 参数名 | 说明 | 类型 | 是否必填 | 描述 | 示例 |
| --- | --- | --- | --- | --- | --- |
| Authorization | 认证token | 字符串 | 必填 | 通过调用获取APP令牌接口拿到access_token，通过请求头传参headers:{ "authorization": `Bearer ${access_token}`} | Bearer 784553cdccf745b38714b3f4552b42fe |

**Body参数**

| 参数名 | 说明 | 类型 | 是否必填 | 描述 | 示例 |
| --- | --- | --- | --- | --- | --- |
| sceneVersionUids | 场景版本uid | 字符串数组 | 必填 | 用于确定查询的哪些场景版本下的指标实例 | 784553cdccf745b38714b3f4552b42fe |
| tags | 标签 | 字符串数组 | 不必填 | 指标实例可根据标签搜索 |  |

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

### 返回响应

| 字段名 | 说明 | 类型 | 描述 |
| --- | --- | --- | --- |
| sceneVersionUid | 场景版本uid |  |  |
| id | 指标实例id | 整型 |  |
| name | 指标实例名称 | 字符串 |  |
| code | 指标实例标识 | 字符串 |  |
| state | 指标实例状态 | 整型 | 0未上线，1已上线 |
| definition | 指标定义信息 | 对象 |  |
| recalculateList | 指标实例精算列表 | 数组 |  |

**definition**

| 字段名 | 说明 | 类型 | 描述 |
| --- | --- | --- | --- |
| id | 指标定义id | 整型 |  |
| name | 指标定义名称 | 字符串 |  |
| uid | 指标定义uid | 字符串 |  |
| type | 指标类型 | 整型 | 1原子指标、2派生指标、3复合指标、4自定义指标 |
| versionName | 指标版本名称 | 字符串 |  |
| versionUuid | 指标版本uid | 字符串 |  |
| metadata | 指标元数据 | 对象 | 预设元素据含义：metric_source指标来源，metric_paraphrase指标释义，metric_data_source数据来源 |
| metricDomain | 指标域 | 对象 |  |
| tags | 标签 | 数组 |  |
| departments | 归口部门 | 数组 |  |
| logic | 计算规则 | 字符串 |  |
| remark | 指标简述 | 字符串 |  |

**recalculateList**

| 字段名 | 说明 | 类型 | 描述 |
| --- | --- | --- | --- |
| id | 指标精算id | 整型 |  |
| metricInstanceId | 指标实例id | 整型 |  |
| name | 指标精算名称 | 字符串 |  |
| code | 指标精算标识 | 字符串 |  |
| queryLanguage | 指标精算sql语句 | 字符串 |  |
| measureCol | 度量字段 | 字符串 |  |
| dimCols | 维度字段 | 数组 | 维度_desc代表维值描述，可能为空 |
| isDefault | 是否默认 | 布尔 | true默认，false非默认 |

### 返回示例

```json
{
    "code": 0,
    "data": [
        {
            "sceneVersionUid": "7dda43b03da04ef79ca935ac14a1ca60",
            "id": 4057,
            "parentId": null,
            "name": "最近消费（派生）",
            "code": "zjxfps",
            "state": 1,
            "definition": {
                "id": 472,
                "name": "最近消费（派生）",
                "uuid": "01c456daf0644977877c104c96094fae",
                "type": 2,
                "versionName": "main",
                "versionUuid": "e099fe4c5bf04e1cb7ccff5f33e60341",
                "definitionConfig": {
                    "@class": "cn.iocoder.yudao.module.metric.dal.dataobject.metricmgt.DerivedDefinitionConfigInfo",
                    "hdim": [
                        {
                            "column": "学号",
                            "type": 1
                        },
                        {
                            "column": "性别",
                            "type": 1
                        }
                    ],
                    "vdim": {
                        "column": "交易时间",
                        "type": 1,
                        "dimModel": "day"
                    },
                    "atomMetricUuid": "c0af896a7ce1424791e97c8b1e32235a"
                },
                "metadata": null,
                "metricDomain": null,
                "tags": null,
                "departments": null,
                "relevantDeptIds": null,
                "logic": "",
                "remark": ""
            },
            "recalculateList": [
                {
                    "id": 45,
                    "metricInstanceId": 4057,
                    "name": "过滤空数据",
                    "code": "hlksj",
                    "queryLanguage": "SELECT ${sys_metric_measure} AS measure, 学号, 学号_desc, 交易时间, 交易时间_desc, 性别, 性别_desc FROM ${sys_metric_resultset} WHERE 学号 is NOT null AND 交易时间 is NOT null AND 性别 is NOT null",
                    "measureCol": "measure",
                    "dimCols": null,
                    "isDefault": false
                }
            ]
        }
    ],
    "msg": ""
}
```

## <a id="12-获取指标管理定义的标签列表"></a>12 获取指标管理定义的标签列表

该接口可查询指标标签选项，用于第4、10接口标签搜索指标实例。

### URL

| 方法 | 路径 |
| --- | --- |
| POST | `/open-api/metric/metricmgt/tags/list` |

### 请求参数

**Header参数**

| 参数名 | 说明 | 类型 | 是否必填 | 描述 | 示例 |
| --- | --- | --- | --- | --- | --- |
| Authorization | 认证token | 字符串 | 必填 | 通过调用获取APP令牌接口拿到access_token，通过请求头传参headers:{ "authorization": `Bearer ${access_token}`} | Bearer 784553cdccf745b38714b3f4552b42fe |

### 请求示例

```bash
curl 'https://指标中枢域名/open-api/metric/metricmgt/tags/list' \
  -X 'POST' \
  -H 'authorization: Bearer bd48ef7ff4684cacb0b8cea2da56a94e' \
  -H 'content-type: application/json'
```

### 返回响应

| 字段名 | 说明 | 类型 | 描述 |
| --- | --- | --- | --- |
| id | 标签id | 整型 |  |
| labelValue | 标签名称 | 字符串 | 传递给第5、11接口tags参数，查询指标实例 |

### 返回示例

```json
{
    "code": 0,
    "data": [
        {
            "id": 1,
            "labelValue": "核心指标",
            "createTime": 1753326015000
        },
        {
            "id": 2,
            "labelValue": "教学",
            "createTime": 1753326257000
        }
    ],
    "msg": ""
}
``````