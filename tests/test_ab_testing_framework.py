"""
A/B 測試框架單元測試
測試分組邏輯、測試執行流程和結果分析功能
"""
import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime
from src.utils.ab_testing_framework import (
    ABTestingFramework,
    TestGroupConfig,
    TestRecord,
    GroupStatistics
)


class TestABTestingFramework:
    """測試 ABTestingFramework 類別"""
    
    @pytest.fixture
    def temp_paths(self):
        """創建臨時檔案路徑"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "ab_test_config.json"
            data_path = Path(tmpdir) / "ab_test_data.json"
            yield config_path, data_path
    
    @pytest.fixture
    def test_groups(self):
        """創建測試組配置"""
        return [
            TestGroupConfig(
                group_id="control",
                group_name="對照組",
                strategy_config={'weight': 0.5},
                traffic_ratio=0.5,
                description="對照組"
            ),
            TestGroupConfig(
                group_id="test_a",
                group_name="測試組 A",
                strategy_config={'weight': 0.6},
                traffic_ratio=0.5,
                description="測試組 A"
            )
        ]
    
    def test_create_test(self, temp_paths, test_groups):
        """測試創建 A/B 測試"""
        config_path, data_path = temp_paths
        framework = ABTestingFramework(
            config_path=str(config_path),
            data_path=str(data_path)
        )
        
        # 創建測試
        success = framework.create_test(
            test_name="測試 1",
            test_groups=test_groups
        )
        
        assert success is True
        assert framework.test_enabled is True
        assert framework.test_name == "測試 1"
        assert len(framework.test_groups) == 2
        assert framework.start_time is not None
    
    def test_create_test_invalid_ratio(self, temp_paths):
        """測試創建測試時流量比例不正確應失敗"""
        config_path, data_path = temp_paths
        framework = ABTestingFramework(
            config_path=str(config_path),
            data_path=str(data_path)
        )
        
        # 流量比例總和不為 1
        invalid_groups = [
            TestGroupConfig(
                group_id="control",
                group_name="對照組",
                strategy_config={},
                traffic_ratio=0.3,
                description=""
            ),
            TestGroupConfig(
                group_id="test_a",
                group_name="測試組 A",
                strategy_config={},
                traffic_ratio=0.5,
                description=""
            )
        ]
        
        success = framework.create_test(
            test_name="無效測試",
            test_groups=invalid_groups
        )
        
        assert success is False
    
    def test_assign_group_consistency(self, temp_paths, test_groups):
        """測試分組邏輯的一致性（同一會員始終分配到同一組）"""
        config_path, data_path = temp_paths
        framework = ABTestingFramework(
            config_path=str(config_path),
            data_path=str(data_path)
        )
        
        framework.create_test("測試", test_groups)
        
        # 同一會員多次分配應得到相同結果
        member_code = "M0001"
        group_1 = framework.assign_group(member_code)
        group_2 = framework.assign_group(member_code)
        group_3 = framework.assign_group(member_code)
        
        assert group_1 == group_2 == group_3
        assert group_1 in ["control", "test_a"]
    
    def test_assign_group_distribution(self, temp_paths, test_groups):
        """測試分組分布接近配置的流量比例"""
        config_path, data_path = temp_paths
        framework = ABTestingFramework(
            config_path=str(config_path),
            data_path=str(data_path)
        )
        
        framework.create_test("測試", test_groups)
        
        # 分配 1000 個會員
        assignments = {}
        for i in range(1000):
            member_code = f"M{i:04d}"
            group_id = framework.assign_group(member_code)
            assignments[group_id] = assignments.get(group_id, 0) + 1
        
        # 驗證分布接近 50:50
        control_ratio = assignments.get("control", 0) / 1000
        test_a_ratio = assignments.get("test_a", 0) / 1000
        
        # 允許 5% 的誤差
        assert abs(control_ratio - 0.5) < 0.05
        assert abs(test_a_ratio - 0.5) < 0.05
    
    def test_assign_group_when_disabled(self, temp_paths):
        """測試測試未啟用時分組應返回 None"""
        config_path, data_path = temp_paths
        framework = ABTestingFramework(
            config_path=str(config_path),
            data_path=str(data_path)
        )
        
        # 未啟用測試
        group_id = framework.assign_group("M0001")
        
        assert group_id is None
    
    def test_get_group_config(self, temp_paths, test_groups):
        """測試獲取測試組配置"""
        config_path, data_path = temp_paths
        framework = ABTestingFramework(
            config_path=str(config_path),
            data_path=str(data_path)
        )
        
        framework.create_test("測試", test_groups)
        
        # 獲取配置
        config = framework.get_group_config("control")
        
        assert config is not None
        assert config.group_id == "control"
        assert config.group_name == "對照組"
        assert config.traffic_ratio == 0.5
    
    def test_record_test_result(self, temp_paths, test_groups):
        """測試記錄測試結果"""
        config_path, data_path = temp_paths
        framework = ABTestingFramework(
            config_path=str(config_path),
            data_path=str(data_path)
        )
        
        framework.create_test("測試", test_groups)
        
        # 記錄結果
        framework.record_test_result(
            member_code="M0001",
            group_id="control",
            overall_score=65.5,
            relevance_score=70.0,
            novelty_score=30.0,
            explainability_score=80.0,
            diversity_score=60.0,
            response_time_ms=200.0,
            recommendation_count=5,
            strategy_used="hybrid"
        )
        
        assert len(framework.test_records) == 1
        
        record = framework.test_records[0]
        assert record.member_code == "M0001"
        assert record.group_id == "control"
        assert record.overall_score == 65.5
        assert record.response_time_ms == 200.0
    
    def test_calculate_group_statistics(self, temp_paths, test_groups):
        """測試計算組別統計數據"""
        config_path, data_path = temp_paths
        framework = ABTestingFramework(
            config_path=str(config_path),
            data_path=str(data_path)
        )
        
        framework.create_test("測試", test_groups)
        
        # 記錄多個結果
        for i in range(10):
            framework.record_test_result(
                member_code=f"M{i:04d}",
                group_id="control",
                overall_score=60.0 + i,
                relevance_score=70.0,
                novelty_score=30.0,
                explainability_score=80.0,
                diversity_score=60.0,
                response_time_ms=200.0 + i * 10,
                recommendation_count=5,
                strategy_used="hybrid"
            )
        
        # 計算統計
        stats = framework.calculate_group_statistics("control")
        
        assert stats is not None
        assert stats.total_records == 10
        assert stats.avg_overall_score == 64.5  # (60+61+...+69) / 10
        assert stats.avg_response_time_ms == 245.0  # (200+210+...+290) / 10
        assert len(stats.overall_scores) == 10
        assert len(stats.response_times) == 10
    
    def test_calculate_group_statistics_empty(self, temp_paths, test_groups):
        """測試計算空組別的統計數據"""
        config_path, data_path = temp_paths
        framework = ABTestingFramework(
            config_path=str(config_path),
            data_path=str(data_path)
        )
        
        framework.create_test("測試", test_groups)
        
        # 計算空組別統計
        stats = framework.calculate_group_statistics("control")
        
        assert stats is not None
        assert stats.total_records == 0
        assert stats.avg_overall_score == 0.0
    
    def test_perform_statistical_test(self, temp_paths, test_groups):
        """測試執行統計顯著性檢驗"""
        config_path, data_path = temp_paths
        framework = ABTestingFramework(
            config_path=str(config_path),
            data_path=str(data_path)
        )
        
        framework.create_test("測試", test_groups)
        
        # 為兩組記錄數據
        # 對照組：平均分數 60
        for i in range(50):
            framework.record_test_result(
                member_code=f"M{i:04d}",
                group_id="control",
                overall_score=60.0 + (i % 10) - 5,  # 55-65 之間
                relevance_score=70.0,
                novelty_score=30.0,
                explainability_score=80.0,
                diversity_score=60.0,
                response_time_ms=200.0,
                recommendation_count=5,
                strategy_used="hybrid"
            )
        
        # 測試組：平均分數 70（顯著更高）
        for i in range(50):
            framework.record_test_result(
                member_code=f"M{i+50:04d}",
                group_id="test_a",
                overall_score=70.0 + (i % 10) - 5,  # 65-75 之間
                relevance_score=75.0,
                novelty_score=35.0,
                explainability_score=85.0,
                diversity_score=65.0,
                response_time_ms=190.0,
                recommendation_count=5,
                strategy_used="hybrid"
            )
        
        # 執行統計檢驗
        result = framework.perform_statistical_test("control", "test_a")
        
        assert 'error' not in result
        assert result['group_a']['id'] == "control"
        assert result['group_b']['id'] == "test_a"
        assert result['test_results']['mean_difference'] > 0  # test_a 更好
        assert 't_statistic' in result['test_results']
        assert 'p_value' in result['test_results']
        assert 'is_significant' in result['test_results']
        assert 'interpretation' in result
    
    def test_perform_statistical_test_insufficient_samples(self, temp_paths, test_groups):
        """測試樣本數不足時的統計檢驗"""
        config_path, data_path = temp_paths
        framework = ABTestingFramework(
            config_path=str(config_path),
            data_path=str(data_path)
        )
        
        framework.create_test("測試", test_groups)
        
        # 只記錄少量數據
        for i in range(10):
            framework.record_test_result(
                member_code=f"M{i:04d}",
                group_id="control",
                overall_score=60.0,
                relevance_score=70.0,
                novelty_score=30.0,
                explainability_score=80.0,
                diversity_score=60.0,
                response_time_ms=200.0,
                recommendation_count=5,
                strategy_used="hybrid"
            )
        
        # 執行統計檢驗
        result = framework.perform_statistical_test("control", "test_a")
        
        assert 'error' in result
        assert '樣本數不足' in result['error']
    
    def test_generate_comparison_report(self, temp_paths, test_groups):
        """測試生成對比報告"""
        config_path, data_path = temp_paths
        framework = ABTestingFramework(
            config_path=str(config_path),
            data_path=str(data_path)
        )
        
        framework.create_test("測試", test_groups)
        
        # 記錄測試數據（添加一些變異性）
        for i in range(50):
            framework.record_test_result(
                member_code=f"M{i:04d}",
                group_id="control",
                overall_score=60.0 + (i % 10) - 5,  # 55-65 之間
                relevance_score=70.0 + (i % 8) - 4,
                novelty_score=30.0 + (i % 6) - 3,
                explainability_score=80.0 + (i % 10) - 5,
                diversity_score=60.0 + (i % 8) - 4,
                response_time_ms=200.0 + (i % 20) - 10,
                recommendation_count=5,
                strategy_used="hybrid"
            )
            
            framework.record_test_result(
                member_code=f"M{i+50:04d}",
                group_id="test_a",
                overall_score=70.0 + (i % 10) - 5,  # 65-75 之間
                relevance_score=75.0 + (i % 8) - 4,
                novelty_score=35.0 + (i % 6) - 3,
                explainability_score=85.0 + (i % 10) - 5,
                diversity_score=65.0 + (i % 8) - 4,
                response_time_ms=190.0 + (i % 20) - 10,
                recommendation_count=5,
                strategy_used="hybrid"
            )
        
        # 停止測試
        framework.stop_test()
        
        # 生成報告
        report = framework.generate_comparison_report()
        
        assert 'error' not in report
        assert 'test_info' in report
        assert report['test_info']['test_name'] == "測試"
        assert report['test_info']['total_records'] == 100
        assert 'groups' in report
        assert 'control' in report['groups']
        assert 'test_a' in report['groups']
        assert 'comparisons' in report
        # 現在應該有比較結果了（因為添加了變異性）
        assert len(report['comparisons']) > 0
        assert 'recommendation' in report
        assert report['recommendation']['best_group_id'] in ["control", "test_a"]
    
    def test_stop_test(self, temp_paths, test_groups):
        """測試停止測試"""
        config_path, data_path = temp_paths
        framework = ABTestingFramework(
            config_path=str(config_path),
            data_path=str(data_path)
        )
        
        framework.create_test("測試", test_groups)
        assert framework.test_enabled is True
        
        # 停止測試
        framework.stop_test()
        
        assert framework.test_enabled is False
        assert framework.end_time is not None
    
    def test_export_raw_data(self, temp_paths, test_groups):
        """測試匯出原始數據"""
        config_path, data_path = temp_paths
        framework = ABTestingFramework(
            config_path=str(config_path),
            data_path=str(data_path)
        )
        
        framework.create_test("測試", test_groups)
        
        # 記錄數據
        framework.record_test_result(
            member_code="M0001",
            group_id="control",
            overall_score=65.5,
            relevance_score=70.0,
            novelty_score=30.0,
            explainability_score=80.0,
            diversity_score=60.0,
            response_time_ms=200.0,
            recommendation_count=5,
            strategy_used="hybrid"
        )
        
        # 匯出數據
        raw_data = framework.export_raw_data()
        
        assert len(raw_data) == 1
        assert raw_data[0]['member_code'] == "M0001"
        assert raw_data[0]['group_id'] == "control"
        assert raw_data[0]['overall_score'] == 65.5
    
    def test_persistence(self, temp_paths, test_groups):
        """測試配置和數據的持久化"""
        config_path, data_path = temp_paths
        
        # 創建第一個實例
        framework1 = ABTestingFramework(
            config_path=str(config_path),
            data_path=str(data_path)
        )
        
        framework1.create_test("測試", test_groups)
        framework1.record_test_result(
            member_code="M0001",
            group_id="control",
            overall_score=65.5,
            relevance_score=70.0,
            novelty_score=30.0,
            explainability_score=80.0,
            diversity_score=60.0,
            response_time_ms=200.0,
            recommendation_count=5,
            strategy_used="hybrid"
        )
        
        # 創建第二個實例（應載入之前的配置和數據）
        framework2 = ABTestingFramework(
            config_path=str(config_path),
            data_path=str(data_path)
        )
        
        assert framework2.test_enabled is True
        assert framework2.test_name == "測試"
        assert len(framework2.test_groups) == 2
        assert len(framework2.test_records) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
