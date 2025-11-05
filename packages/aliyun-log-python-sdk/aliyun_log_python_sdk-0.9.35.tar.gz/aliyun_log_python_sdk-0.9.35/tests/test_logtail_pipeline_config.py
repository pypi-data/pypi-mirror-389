#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) Alibaba Cloud Computing
# All rights reserved.

"""
Unit tests for Logtail Pipeline Config API

This test file validates the LogtailPipelineConfigDetail class
and its JSON serialization/deserialization.
"""

from __future__ import print_function
import unittest
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aliyun.log.logtail_pipeline_config_detail import LogtailPipelineConfigDetail


class TestLogtailPipelineConfigDetail(unittest.TestCase):
    """Test cases for LogtailPipelineConfigDetail"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config_name = "test-pipeline-config"
        self.inputs = [
            {
                "Type": "input_file",
                "FilePaths": ["/var/log/*.log"]
            }
        ]
        self.flushers = [
            {
                "Type": "flusher_sls",
                "Logstore": "test-logstore"
            }
        ]
        self.processors = [
            {
                "Type": "processor_parse_json_native",
                "SourceKey": "content"
            }
        ]
        self.log_sample = '{"level": "INFO", "message": "test"}'
    
    def test_basic_init(self):
        """Test basic initialization with required fields only"""
        config = LogtailPipelineConfigDetail(
            config_name=self.config_name,
            inputs=self.inputs,
            flushers=self.flushers
        )
        
        self.assertEqual(config.config_name, self.config_name)
        self.assertEqual(config.inputs, self.inputs)
        self.assertEqual(config.flushers, self.flushers)
        self.assertIsNone(config.log_sample)
        self.assertEqual(config.global_config, {})
        self.assertEqual(config.processors, [])
        self.assertEqual(config.aggregators, [])
    
    def test_full_init(self):
        """Test initialization with all fields"""
        global_config = {"TopicType": "filepath"}
        aggregators = [{"Type": "aggregator_context"}]
        
        config = LogtailPipelineConfigDetail(
            config_name=self.config_name,
            inputs=self.inputs,
            flushers=self.flushers,
            log_sample=self.log_sample,
            global_config=global_config,
            processors=self.processors,
            aggregators=aggregators
        )
        
        self.assertEqual(config.config_name, self.config_name)
        self.assertEqual(config.log_sample, self.log_sample)
        self.assertEqual(config.global_config, global_config)
        self.assertEqual(config.processors, self.processors)
        self.assertEqual(config.aggregators, aggregators)
    
    def test_to_json_basic(self):
        """Test to_json with basic configuration"""
        config = LogtailPipelineConfigDetail(
            config_name=self.config_name,
            inputs=self.inputs,
            flushers=self.flushers
        )
        
        json_dict = config.to_json()
        
        self.assertIn("configName", json_dict)
        self.assertIn("inputs", json_dict)
        self.assertIn("flushers", json_dict)
        self.assertEqual(json_dict["configName"], self.config_name)
        self.assertEqual(json_dict["inputs"], self.inputs)
        self.assertEqual(json_dict["flushers"], self.flushers)
        # Optional fields should not be present if not set
        self.assertNotIn("logSample", json_dict)
    
    def test_to_json_full(self):
        """Test to_json with all fields"""
        global_config = {"TopicType": "filepath"}
        aggregators = [{"Type": "aggregator_context"}]
        
        config = LogtailPipelineConfigDetail(
            config_name=self.config_name,
            inputs=self.inputs,
            flushers=self.flushers,
            log_sample=self.log_sample,
            global_config=global_config,
            processors=self.processors,
            aggregators=aggregators
        )
        
        json_dict = config.to_json()
        
        self.assertIn("configName", json_dict)
        self.assertIn("logSample", json_dict)
        self.assertIn("global", json_dict)
        self.assertIn("inputs", json_dict)
        self.assertIn("processors", json_dict)
        self.assertIn("aggregators", json_dict)
        self.assertIn("flushers", json_dict)
        
        self.assertEqual(json_dict["configName"], self.config_name)
        self.assertEqual(json_dict["logSample"], self.log_sample)
        self.assertEqual(json_dict["global"], global_config)
        self.assertEqual(json_dict["processors"], self.processors)
        self.assertEqual(json_dict["aggregators"], aggregators)
    
    def test_from_json_basic(self):
        """Test from_json with basic configuration"""
        json_dict = {
            "configName": self.config_name,
            "inputs": self.inputs,
            "flushers": self.flushers
        }
        
        config = LogtailPipelineConfigDetail.from_json(json_dict)
        
        self.assertEqual(config.config_name, self.config_name)
        self.assertEqual(config.inputs, self.inputs)
        self.assertEqual(config.flushers, self.flushers)
        self.assertIsNone(config.log_sample)
        self.assertIsNone(config.global_config)
        self.assertEqual(config.processors, [])
    
    def test_from_json_full(self):
        """Test from_json with all fields"""
        global_config = {"TopicType": "filepath"}
        aggregators = [{"Type": "aggregator_context"}]
        
        json_dict = {
            "configName": self.config_name,
            "logSample": self.log_sample,
            "global": global_config,
            "inputs": self.inputs,
            "processors": self.processors,
            "aggregators": aggregators,
            "flushers": self.flushers
        }
        
        config = LogtailPipelineConfigDetail.from_json(json_dict)
        
        self.assertEqual(config.config_name, self.config_name)
        self.assertEqual(config.log_sample, self.log_sample)
        self.assertEqual(config.global_config, global_config)
        self.assertEqual(config.inputs, self.inputs)
        self.assertEqual(config.processors, self.processors)
        self.assertEqual(config.aggregators, aggregators)
        self.assertEqual(config.flushers, self.flushers)
    
    def test_json_roundtrip(self):
        """Test JSON serialization and deserialization roundtrip"""
        global_config = {"TopicType": "filepath", "EnableRawLog": True}
        aggregators = [{"Type": "aggregator_context", "MaxLogGroupCount": 100}]
        
        original = LogtailPipelineConfigDetail(
            config_name=self.config_name,
            inputs=self.inputs,
            flushers=self.flushers,
            log_sample=self.log_sample,
            global_config=global_config,
            processors=self.processors,
            aggregators=aggregators
        )
        
        # Serialize to JSON
        json_dict = original.to_json()
        json_str = json.dumps(json_dict)
        
        # Deserialize from JSON
        parsed_dict = json.loads(json_str)
        restored = LogtailPipelineConfigDetail.from_json(parsed_dict)
        
        # Verify roundtrip
        self.assertEqual(restored.config_name, original.config_name)
        self.assertEqual(restored.log_sample, original.log_sample)
        self.assertEqual(restored.global_config, original.global_config)
        self.assertEqual(restored.inputs, original.inputs)
        self.assertEqual(restored.processors, original.processors)
        self.assertEqual(restored.aggregators, original.aggregators)
        self.assertEqual(restored.flushers, original.flushers)
    
    def test_str_representation(self):
        """Test __str__ method"""
        config = LogtailPipelineConfigDetail(
            config_name=self.config_name,
            inputs=self.inputs,
            flushers=self.flushers
        )
        
        str_repr = str(config)
        self.assertIsInstance(str_repr, str)
        # Should be valid JSON
        parsed = json.loads(str_repr)
        self.assertEqual(parsed["configName"], self.config_name)
    
    def test_repr_representation(self):
        """Test __repr__ method"""
        config = LogtailPipelineConfigDetail(
            config_name=self.config_name,
            inputs=self.inputs,
            flushers=self.flushers
        )
        
        repr_str = repr(config)
        self.assertIn("LogtailPipelineConfigDetail", repr_str)
        self.assertIn(self.config_name, repr_str)
    
    def test_multiple_processors(self):
        """Test configuration with multiple processors"""
        processors = [
            {
                "Type": "processor_parse_json_native",
                "SourceKey": "content"
            },
            {
                "Type": "processor_filter_regex",
                "Include": {
                    "level": "ERROR|WARN"
                }
            },
            {
                "Type": "processor_desensitize",
                "SourceKey": "message",
                "Method": "const",
                "Match": r"\d{11}",
                "ReplaceString": "***"
            }
        ]
        
        config = LogtailPipelineConfigDetail(
            config_name=self.config_name,
            inputs=self.inputs,
            flushers=self.flushers,
            processors=processors
        )
        
        json_dict = config.to_json()
        self.assertEqual(len(json_dict["processors"]), 3)
        
        # Test roundtrip
        restored = LogtailPipelineConfigDetail.from_json(json_dict)
        self.assertEqual(len(restored.processors), 3)
        self.assertEqual(restored.processors[0]["Type"], "processor_parse_json_native")
        self.assertEqual(restored.processors[1]["Type"], "processor_filter_regex")
        self.assertEqual(restored.processors[2]["Type"], "processor_desensitize")


class TestLogtailPipelineConfigResponse(unittest.TestCase):
    """Test cases for response classes"""
    
    def test_import_response_classes(self):
        """Test that response classes can be imported"""
        try:
            from aliyun.log.logtail_pipeline_config_response import (
                CreateLogtailPipelineConfigResponse,
                UpdateLogtailPipelineConfigResponse,
                DeleteLogtailPipelineConfigResponse,
                GetLogtailPipelineConfigResponse,
                ListLogtailPipelineConfigResponse
            )
            # If we get here, imports are successful
            self.assertTrue(True)
        except ImportError as e:
            self.fail("Failed to import response classes: %s" % str(e))
    
    def test_get_response_with_config(self):
        """Test GetLogtailPipelineConfigResponse with config detail"""
        from aliyun.log.logtail_pipeline_config_response import GetLogtailPipelineConfigResponse
        
        resp_body = {
            "configName": "test-config",
            "inputs": [{"Type": "input_file"}],
            "flushers": [{"Type": "flusher_sls", "Logstore": "test"}]
        }
        
        headers = {"x-log-requestid": "test-request-id"}
        
        response = GetLogtailPipelineConfigResponse(resp_body, headers)
        config = response.get_pipeline_config()
        
        self.assertIsNotNone(config)
        self.assertEqual(config.config_name, "test-config")
    
    def test_list_response_properties(self):
        """Test ListLogtailPipelineConfigResponse properties
        
        Note: List API returns config names (strings) only, not full config objects
        """
        from aliyun.log.logtail_pipeline_config_response import ListLogtailPipelineConfigResponse
        
        resp_body = {
            "count": 2,
            "total": 10,
            "configs": ["config1", "config2"]  # Config names only, not full objects
        }
        
        headers = {"x-log-requestid": "test-request-id"}
        
        response = ListLogtailPipelineConfigResponse(resp_body, headers)
        
        self.assertEqual(response.get_count(), 2)
        self.assertEqual(response.get_total(), 10)
        self.assertEqual(len(response.get_configs()), 2)
        # Verify it returns config names as strings
        self.assertEqual(response.get_configs()[0], "config1")
        self.assertEqual(response.get_configs()[1], "config2")
        self.assertIsInstance(response.get_configs()[0], str)
    
    def test_list_response_merge(self):
        """Test ListLogtailPipelineConfigResponse merge for pagination"""
        from aliyun.log.logtail_pipeline_config_response import ListLogtailPipelineConfigResponse
        
        # First page
        resp_body1 = {
            "count": 2,
            "total": 5,
            "configs": ["config1", "config2"]
        }
        headers1 = {"x-log-requestid": "test-request-id-1"}
        response1 = ListLogtailPipelineConfigResponse(resp_body1, headers1)
        
        # Second page
        resp_body2 = {
            "count": 2,
            "total": 5,
            "configs": ["config3", "config4"]
        }
        headers2 = {"x-log-requestid": "test-request-id-2"}
        response2 = ListLogtailPipelineConfigResponse(resp_body2, headers2)
        
        # Merge
        response1.merge(response2)
        
        # Verify merged result
        self.assertEqual(response1.get_count(), 4)  # 2 + 2
        self.assertEqual(response1.get_total(), 5)  # Use latest total
        self.assertEqual(len(response1.get_configs()), 4)
        self.assertEqual(response1.get_configs(), ["config1", "config2", "config3", "config4"])


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestLogtailPipelineConfigDetail))
    suite.addTests(loader.loadTestsFromTestCase(TestLogtailPipelineConfigResponse))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

