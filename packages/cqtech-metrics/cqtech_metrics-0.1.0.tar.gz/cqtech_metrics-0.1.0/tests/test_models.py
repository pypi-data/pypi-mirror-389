"""Test suite for CQTech Metrics SDK models"""
import unittest
from cqtech_metrics.models.auth import TokenResponse, TokenResponseData
from cqtech_metrics.models.scenes import SceneVersion, SceneVersionQuery
from cqtech_metrics.models.metrics import MetricInstance, MetricDefinition, MetricRecalculate


class TestAuthModels(unittest.TestCase):
    """Test cases for authentication models"""
    
    def test_token_response_model(self):
        """Test TokenResponse model"""
        data = {
            'code': 0,
            'data': {
                'scope': None,
                'access_token': 'test_token',
                'refresh_token': 'refresh_token',
                'token_type': 'bearer',
                'expires_in': 1800
            },
            'msg': 'Success'
        }
        
        token_response = TokenResponse(**data)
        
        self.assertEqual(token_response.code, 0)
        self.assertEqual(token_response.data.access_token, 'test_token')
        self.assertEqual(token_response.data.token_type, 'bearer')
        self.assertEqual(token_response.data.expires_in, 1800)
        self.assertEqual(token_response.msg, 'Success')
    
    def test_token_response_optional_fields(self):
        """Test TokenResponse model with optional fields"""
        data = {
            'code': 0,
            'data': {
                'scope': None,
                'access_token': 'test_token',
                'refresh_token': None,
                'token_type': 'bearer',
                'expires_in': 1800
            }
        }
        
        token_response = TokenResponse(**data)
        
        self.assertEqual(token_response.code, 0)
        self.assertIsNone(token_response.data.refresh_token)
        self.assertIsNone(token_response.msg)


class TestSceneModels(unittest.TestCase):
    """Test cases for scene models"""
    
    def test_scene_version_model(self):
        """Test SceneVersion model"""
        scene_data = {
            'id': 123,
            'name': 'Test Scene',
            'version_name': 'v1.0',
            'uid': 'test-uid-123',
            'status': 1,
            'cron_expression': '0 0 * * *',
            'instance_count': 5
        }
        
        scene = SceneVersion(**scene_data)
        
        self.assertEqual(scene.id, 123)
        self.assertEqual(scene.name, 'Test Scene')
        self.assertEqual(scene.version_name, 'v1.0')
        self.assertEqual(scene.uid, 'test-uid-123')
        self.assertEqual(scene.status, 1)
        self.assertEqual(scene.cron_expression, '0 0 * * *')
        self.assertEqual(scene.instance_count, 5)
    
    def test_scene_version_query_model(self):
        """Test SceneVersionQuery model"""
        query_data = {
            'name': 'Test Scene',
            'scene_version_status': 1,
            'page_num': 1,
            'page_size': 10
        }
        
        query = SceneVersionQuery(**query_data)
        
        self.assertEqual(query.name, 'Test Scene')
        self.assertEqual(query.scene_version_status, 1)
        self.assertEqual(query.page_num, 1)
        self.assertEqual(query.page_size, 10)


class TestMetricModels(unittest.TestCase):
    """Test cases for metric models"""
    
    def test_metric_definition_model(self):
        """Test MetricDefinition model"""
        from cqtech_metrics.models.metrics import MetricDefinitionConfig
        
        definition_data = {
            'id': 1,
            'name': 'Test Metric',
            'uuid': 'test-metric-uuid',  # Changed from 'uid' to 'uuid' to match API
            'type': 2,
            'version_name': 'main',
            'version_uuid': 'test-version-uuid',
            'definition_config': {'hdim': [{'column': 'test', 'type': 1}]},
            'metadata': {'source': 'test'},
            'metric_domain': [{'name': 'Test Domain', 'id': 1, 'parentId': 0}],
            'tags': ['test-tag'],
            'departments': ['Test Dept'],
            'relevant_dept_ids': [100],
            'logic': 'test logic',
            'remark': 'test remark'
        }
        
        definition = MetricDefinition(**definition_data)
        
        self.assertEqual(definition.id, 1)
        self.assertEqual(definition.name, 'Test Metric')
        self.assertEqual(definition.uuid, 'test-metric-uuid')
        self.assertEqual(definition.type, 2)
        self.assertEqual(definition.version_name, 'main')
        # The definition_config would be a MetricDefinitionConfig object
        # So we need to handle this differently
        self.assertIsNotNone(definition.definition_config)
    
    def test_metric_recalculate_model(self):
        """Test MetricRecalculate model"""
        recalc_data = {
            'id': 1,
            'metric_instance_id': 123,
            'name': 'Test Recalculate',
            'code': 'test_code',
            'query_language': 'SELECT * FROM test',
            'measure_col': 'measure',
            'dim_cols': ['dim1', 'dim2'],
            'is_default': True
        }
        
        recalc = MetricRecalculate(**recalc_data)
        
        self.assertEqual(recalc.id, 1)
        self.assertEqual(recalc.metric_instance_id, 123)
        self.assertEqual(recalc.name, 'Test Recalculate')
        self.assertEqual(recalc.code, 'test_code')
        self.assertEqual(recalc.query_language, 'SELECT * FROM test')
        self.assertEqual(recalc.measure_col, 'measure')
        self.assertEqual(recalc.dim_cols, ['dim1', 'dim2'])
        self.assertTrue(recalc.is_default)
    
    def test_metric_instance_model(self):
        """Test MetricInstance model"""
        instance_data = {
            'id': 123,
            'parent_id': 100,
            'name': 'Test Instance',
            'code': 'test_code',
            'dims': ['dim1', 'dim2'],
            'state': 1,
            'cron_expression': '0 0 * * *'
        }
        
        instance = MetricInstance(**instance_data)
        
        self.assertEqual(instance.id, 123)
        self.assertEqual(instance.parent_id, 100)
        self.assertEqual(instance.name, 'Test Instance')
        self.assertEqual(instance.code, 'test_code')
        self.assertEqual(instance.dims, ['dim1', 'dim2'])
        self.assertEqual(instance.state, 1)
        self.assertEqual(instance.cron_expression, '0 0 * * *')
        self.assertIsNone(instance.definition)
        self.assertIsNone(instance.children)
        self.assertIsNone(instance.recalculate_list)


if __name__ == '__main__':
    unittest.main()