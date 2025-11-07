"""
增強推薦引擎 (EnhancedRecommendationEngine)
整合性能追蹤、可參考價值評估、混合推薦策略
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
import logging
import json
import time
from datetime import datetime

from src.models.ml_recommender import MLRecommender
from src.models.reason_generator import ReasonGenerator
from src.models.reference_value_evaluator import ReferenceValueEvaluator
from src.models.collaborative_filtering import CollaborativeFilteringModel
from src.utils.performance_tracker import PerformanceTracker
from src.utils.degradation_strategy import DegradationStrategy
from src.models.data_models import (
    MemberInfo, Recommendation, RecommendationSource, Product
)
from src.models.enhanced_data_models import (
    PerformanceMetrics, ReferenceValueScore, MemberHistory,
    QualityLevel, RecommendationStage
)
from src.config import settings

logger = logging.getLogger(__name__)


class EnhancedRecommendationResponse:
    """增強版推薦回應"""
    
    def __init__(
        self,
        member_code: str,
        recommendations: List[Recommendation],
        reference_value_score: ReferenceValueScore,
        performance_metrics: PerformanceMetrics,
        total_count: int,
        strategy_used: str,
        model_version: str,
        quality_level: QualityLevel,
        is_degraded: bool = False
    ):
        self.member_code = member_code
        self.recommendations = recommendations
        self.reference_value_score = reference_value_score
        self.performance_metrics = performance_metrics
        self.total_count = total_count
        self.strategy_used = strategy_used
        self.model_version = model_version
        self.timestamp = datetime.now()
        self.quality_level = quality_level
        self.is_degraded = is_degraded
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'member_code': self.member_code,
            'recommendations': [
                {
                    'product_id': rec.product_id,
                    'product_name': rec.product_name,
                    'confidence_score': rec.confidence_score,
                    'explanation': rec.explanation,
                    'rank': rec.rank,
                    'source': rec.source.value
                }
                for rec in self.recommendations
            ],
            'reference_value_score': {
                'overall_score': self.reference_value_score.overall_score,
                'relevance_score': self.reference_value_score.relevance_score,
                'novelty_score': self.reference_value_score.novelty_score,
                'explainability_score': self.reference_value_score.explainability_score,
                'diversity_score': self.reference_value_score.diversity_score,
                'score_breakdown': self.reference_value_score.score_breakdown
            },
            'performance_metrics': {
                'request_id': self.performance_metrics.request_id,
                'total_time_ms': self.performance_metrics.total_time_ms,
                'stage_times': self.performance_metrics.stage_times,
                'is_slow_query': self.performance_metrics.is_slow_query
            },
            'total_count': self.total_count,
            'strategy_used': self.strategy_used,
            'model_version': self.model_version,
            'timestamp': self.timestamp.isoformat(),
            'quality_level': self.quality_level.value,
            'is_degraded': self.is_degraded
        }


class EnhancedRecommendationEngine:
    """增強版推薦引擎"""
    
    # 策略權重配置
    STRATEGY_WEIGHTS = {
        'collaborative_filtering': 0.00,  # 協同過濾 0% (暫時禁用，因為沒有 cf_model)
        'content_based': 1.00,           # 內容推薦 100% (使用 ML 模型)
        'popularity': 0.00,              # 熱門推薦 0%
        'diversity': 0.00                # 多樣性推薦 0%
    }
    
    def __init__(self, model_path: Optional[Path] = None):
        """
        初始化增強推薦引擎
        
        Args:
            model_path: 模型目錄路徑，None 表示使用當前版本
        """
        if model_path is None:
            model_path = settings.MODELS_DIR / settings.MODEL_VERSION
        
        self.model_path = Path(model_path)
        
        logger.info("增強推薦引擎初始化...")
        logger.info(f"  模型路徑: {self.model_path}")
        
        # 初始化組件
        self.performance_tracker = PerformanceTracker()
        self.value_evaluator = ReferenceValueEvaluator()
        self.degradation_strategy = None  # 稍後初始化
        
        # 載入模型和特徵
        self.ml_model = None
        self.cf_model = None
        self.member_features = None
        self.product_features = None
        self.metadata = None
        self.reason_generator = None
        
        # 性能優化：快取
        self._product_name_cache = {}  # 產品名稱快取
        self._member_history_cache = {}  # 會員歷史快取（有限大小）
        self._cache_max_size = 1000  # 快取最大大小
        
        self._load_models()
        self._load_features()
        self._load_metadata()
        self._initialize_reason_generator()
        self._initialize_degradation_strategy()
        self._build_product_name_cache()  # 預先建立產品名稱快取
        
        logger.info("✓ 增強推薦引擎初始化完成")
    
    def _load_models(self):
        """載入模型"""
        # 載入 ML 模型
        ml_model_file = self.model_path / 'model.pkl'
        if ml_model_file.exists():
            logger.info("載入 ML 模型...")
            self.ml_model = MLRecommender.load(ml_model_file)
            logger.info("✓ ML 模型載入完成")
        else:
            logger.warning("ML 模型檔案不存在")
        
        # 載入協同過濾模型（如果存在）
        cf_model_file = self.model_path / 'cf_model.pkl'
        if cf_model_file.exists():
            logger.info("載入協同過濾模型...")
            try:
                self.cf_model = CollaborativeFilteringModel.load(cf_model_file)
                logger.info("✓ 協同過濾模型載入完成")
            except Exception as e:
                logger.warning(f"協同過濾模型載入失敗: {e}")
                self.cf_model = None
        else:
            logger.info("協同過濾模型檔案不存在，將跳過協同過濾推薦")
    
    def _load_features(self):
        """載入特徵"""
        member_features_file = self.model_path / 'member_features.parquet'
        product_features_file = self.model_path / 'product_features.parquet'
        
        if member_features_file.exists():
            logger.info("載入會員特徵...")
            self.member_features = pd.read_parquet(member_features_file)
            logger.info(f"✓ 會員特徵載入完成: {len(self.member_features)} 個會員")
        else:
            logger.warning("會員特徵檔案不存在")
        
        if product_features_file.exists():
            logger.info("載入產品特徵...")
            self.product_features = pd.read_parquet(product_features_file)
            logger.info(f"✓ 產品特徵載入完成: {len(self.product_features)} 個產品")
        else:
            logger.warning("產品特徵檔案不存在")
    
    def _load_metadata(self):
        """載入元資料"""
        metadata_file = self.model_path / 'metadata.json'
        
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            logger.info("✓ 元資料載入完成")
        else:
            logger.warning("元資料檔案不存在")
            self.metadata = {'version': 'unknown'}
    
    def _initialize_reason_generator(self):
        """初始化推薦理由生成器"""
        logger.info("初始化推薦理由生成器...")
        self.reason_generator = ReasonGenerator(
            product_features=self.product_features,
            member_features=self.member_features
        )
        logger.info("✓ 推薦理由生成器初始化完成")
    
    def _initialize_degradation_strategy(self):
        """初始化降級策略"""
        logger.info("初始化降級策略...")
        self.degradation_strategy = DegradationStrategy(
            product_features=self.product_features
        )
        logger.info("✓ 降級策略初始化完成")
    
    def _build_product_name_cache(self):
        """性能優化：預先建立產品名稱快取"""
        if self.product_features is not None:
            logger.info("建立產品名稱快取...")
            for _, row in self.product_features.iterrows():
                product_id = row['stock_id']
                product_name = row.get('stock_description', product_id)
                self._product_name_cache[product_id] = product_name
            logger.info(f"✓ 產品名稱快取建立完成: {len(self._product_name_cache)} 個產品")

    
    def recommend(
        self,
        member_info: MemberInfo,
        n: Optional[int] = None,
        strategy: str = 'hybrid'
    ) -> EnhancedRecommendationResponse:
        """
        生成增強版推薦
        
        Args:
            member_info: 會員資訊
            n: 推薦數量
            strategy: 推薦策略 ('hybrid', 'ml_only', 'cf_only')
            
        Returns:
            EnhancedRecommendationResponse: 增強版推薦回應
        """
        n = n or settings.TOP_K_RECOMMENDATIONS
        request_id = f"req_{member_info.member_code}_{int(time.time() * 1000)}"
        
        logger.info(f"為會員 {member_info.member_code} 生成增強推薦...")
        
        # 子任務 5.1: 啟動性能追蹤
        self.performance_tracker.start_tracking(request_id)
        
        try:
            # 階段 1: 特徵載入
            self.performance_tracker.track_stage(request_id, RecommendationStage.FEATURE_LOADING.value)
            member_history = self._build_member_history(member_info)
            products_info = self._build_products_info()
            
            # 階段 2: 模型推理 - 生成推薦
            self.performance_tracker.track_stage(request_id, RecommendationStage.MODEL_INFERENCE.value)
            
            if strategy == 'hybrid':
                recommendations = self._generate_hybrid_recommendations(member_info, n)
            elif strategy == 'ml_only':
                recommendations = self._generate_ml_recommendations(member_info, n)
            elif strategy == 'cf_only':
                recommendations = self._generate_cf_recommendations(member_info, n)
            else:
                raise ValueError(f"不支援的策略: {strategy}")
            
            # 階段 3: 推薦合併（已在混合推薦中完成）
            self.performance_tracker.track_stage(request_id, RecommendationStage.RECOMMENDATION_MERGING.value)
            
            # 階段 4: 理由生成
            self.performance_tracker.track_stage(request_id, RecommendationStage.REASON_GENERATION.value)
            recommendations = self._enhance_recommendations_with_reasons(
                recommendations, member_info, member_history
            )
            
            # 子任務 5.2: 品質評估
            self.performance_tracker.track_stage(request_id, RecommendationStage.QUALITY_EVALUATION.value)
            reference_value_score = self.value_evaluator.evaluate(
                recommendations=recommendations,
                member_info=member_info,
                member_history=member_history,
                products_info=products_info
            )
            
            # 結束性能追蹤
            performance_metrics = self.performance_tracker.end_tracking(request_id)
            
            # 子任務 7.3: 檢查是否需要降級
            is_degraded = False
            if self.degradation_strategy and self.degradation_strategy.should_degrade(
                value_score=reference_value_score,
                performance_metrics=performance_metrics
            ):
                logger.warning(f"品質或性能不達標，執行降級策略")
                
                # 執行降級推薦
                degraded_recommendations = self.degradation_strategy.execute_degradation(
                    member_info=member_info,
                    n=n
                )
                
                # 如果降級推薦成功，使用降級推薦
                if degraded_recommendations:
                    recommendations = degraded_recommendations
                    is_degraded = True
                    
                    # 重新評估降級推薦的品質
                    reference_value_score = self.value_evaluator.evaluate(
                        recommendations=recommendations,
                        member_info=member_info,
                        member_history=member_history,
                        products_info=products_info
                    )
                    
                    logger.info(f"✓ 降級推薦完成，新的可參考價值分數: {reference_value_score.overall_score:.2f}")
            
            # 子任務 5.4: 確定品質等級
            quality_level = self._determine_quality_level(reference_value_score)
            
            # 創建增強回應
            response = EnhancedRecommendationResponse(
                member_code=member_info.member_code,
                recommendations=recommendations,
                reference_value_score=reference_value_score,
                performance_metrics=performance_metrics,
                total_count=len(recommendations),
                strategy_used=strategy if not is_degraded else 'degraded',
                model_version=self.metadata.get('version', 'unknown'),
                quality_level=quality_level,
                is_degraded=is_degraded
            )
            
            logger.info(f"✓ 增強推薦生成完成")
            logger.info(f"  推薦數量: {len(recommendations)}")
            logger.info(f"  可參考價值分數: {reference_value_score.overall_score:.2f}")
            logger.info(f"  總耗時: {performance_metrics.total_time_ms:.2f} ms")
            logger.info(f"  品質等級: {quality_level.value}")
            
            return response
            
        except Exception as e:
            logger.error(f"增強推薦生成失敗: {e}")
            import traceback
            traceback.print_exc()
            
            # 嘗試結束追蹤
            try:
                performance_metrics = self.performance_tracker.end_tracking(request_id)
            except:
                performance_metrics = PerformanceMetrics(
                    request_id=request_id,
                    total_time_ms=0.0,
                    stage_times={},
                    is_slow_query=False,
                    timestamp=datetime.now()
                )
            
            # 返回空推薦
            return EnhancedRecommendationResponse(
                member_code=member_info.member_code,
                recommendations=[],
                reference_value_score=ReferenceValueScore(
                    overall_score=0.0,
                    relevance_score=0.0,
                    novelty_score=0.0,
                    explainability_score=0.0,
                    diversity_score=0.0,
                    score_breakdown={},
                    timestamp=datetime.now()
                ),
                performance_metrics=performance_metrics,
                total_count=0,
                strategy_used=strategy,
                model_version=self.metadata.get('version', 'unknown'),
                quality_level=QualityLevel.POOR,
                is_degraded=True
            )
    
    def _build_member_history(self, member_info: MemberInfo) -> MemberHistory:
        """
        構建會員歷史資料（使用快取優化）
        
        性能優化：使用 LRU 快取避免重複計算相同會員的歷史資料
        
        Args:
            member_info: 會員資訊
            
        Returns:
            MemberHistory: 會員歷史資料
        """
        # 檢查快取
        cache_key = f"{member_info.member_code}_{len(member_info.recent_purchases or [])}"
        if cache_key in self._member_history_cache:
            return self._member_history_cache[cache_key]
        
        # 從會員特徵中提取歷史資料
        purchased_products = member_info.recent_purchases or []
        
        # 性能優化：批次查詢產品資訊，避免逐個查詢
        purchased_categories = []
        purchased_brands = []
        prices = []
        
        if self.product_features is not None and purchased_products:
            # 批次查詢所有購買的產品
            products_df = self.product_features[
                self.product_features['stock_id'].isin(purchased_products)
            ]
            
            # 提取類別
            if 'category' in products_df.columns:
                categories = products_df['category'].dropna().tolist()
                purchased_categories = categories
            
            # 提取品牌（從描述）
            if 'stock_description' in products_df.columns:
                for desc in products_df['stock_description'].dropna():
                    brand = desc.split()[0] if desc else None
                    if brand:
                        purchased_brands.append(brand)
            
            # 提取價格
            if 'avg_price' in products_df.columns:
                prices = products_df['avg_price'].dropna()
                prices = [p for p in prices if p > 0]
        
        # 計算平均購買價格和標準差
        avg_price = float(np.mean(prices)) if prices else 0.0
        price_std = float(np.std(prices)) if len(prices) > 1 else (avg_price * 0.3 if avg_price > 0 else 0.0)
        
        member_history = MemberHistory(
            member_code=member_info.member_code,
            purchased_products=purchased_products,
            purchased_categories=list(set(purchased_categories)),
            purchased_brands=list(set(purchased_brands)),
            avg_purchase_price=avg_price,
            price_std=price_std,
            browsed_products=[]  # 暫時沒有瀏覽資料
        )
        
        # 更新快取（LRU策略）
        if len(self._member_history_cache) >= self._cache_max_size:
            # 移除最舊的項目
            oldest_key = next(iter(self._member_history_cache))
            del self._member_history_cache[oldest_key]
        
        self._member_history_cache[cache_key] = member_history
        
        return member_history
    
    def _build_products_info(self) -> Dict[str, Product]:
        """
        構建產品資訊字典
        
        Returns:
            Dict[str, Product]: 產品資訊字典
        """
        products_info = {}
        
        if self.product_features is not None:
            for _, row in self.product_features.iterrows():
                product = Product(
                    stock_id=row['stock_id'],
                    stock_description=row.get('stock_description', ''),
                    avg_price=row.get('avg_price', 0.0),
                    category=row.get('category', None)
                )
                products_info[product.stock_id] = product
        
        return products_info

    
    def _generate_hybrid_recommendations(
        self,
        member_info: MemberInfo,
        n: int
    ) -> List[Recommendation]:
        """
        子任務 5.3: 生成混合推薦
        整合協同過濾、內容推薦、熱門推薦、多樣性推薦
        
        Args:
            member_info: 會員資訊
            n: 推薦數量
            
        Returns:
            List[Recommendation]: 推薦列表
        """
        all_recommendations = []
        
        # 1. 協同過濾推薦 (40%)
        cf_count = int(n * self.STRATEGY_WEIGHTS['collaborative_filtering'])
        if self.cf_model is not None and cf_count > 0:
            cf_recs = self._generate_cf_recommendations(member_info, cf_count)
            all_recommendations.extend(cf_recs)
        
        # 2. 內容推薦 (30%) - 使用 ML 模型
        content_count = int(n * self.STRATEGY_WEIGHTS['content_based'])
        if content_count > 0:
            content_recs = self._generate_ml_recommendations(member_info, content_count)
            all_recommendations.extend(content_recs)
        
        # 3. 熱門推薦 (20%)
        popular_count = int(n * self.STRATEGY_WEIGHTS['popularity'])
        if popular_count > 0:
            popular_recs = self._generate_popularity_recommendations(member_info, popular_count)
            all_recommendations.extend(popular_recs)
        
        # 4. 多樣性推薦 (10%)
        diversity_count = int(n * self.STRATEGY_WEIGHTS['diversity'])
        if diversity_count > 0:
            diversity_recs = self._generate_diversity_recommendations(member_info, diversity_count)
            all_recommendations.extend(diversity_recs)
        
        # 5. 去重和排序
        unique_recs = self._deduplicate_recommendations(all_recommendations)
        sorted_recs = self._sort_recommendations(unique_recs)
        
        # 6. 取前 n 個
        final_recs = sorted_recs[:n]
        
        # 7. 重新分配排名
        for rank, rec in enumerate(final_recs, 1):
            rec.rank = rank
        
        return final_recs
    
    def _generate_ml_recommendations(
        self,
        member_info: MemberInfo,
        n: int
    ) -> List[Recommendation]:
        """
        使用 ML 模型生成推薦
        
        Args:
            member_info: 會員資訊
            n: 推薦數量
            
        Returns:
            List[Recommendation]: 推薦列表
        """
        if self.ml_model is None:
            return []
        
        try:
            # 獲取候選產品
            candidate_products = self._get_candidate_products(member_info, n * 3)
            
            if not candidate_products:
                return []
            
            # 使用模型預測
            predictions = self.ml_model.recommend(
                member_id=member_info.member_code,
                product_ids=candidate_products,
                member_features_df=self.member_features,
                product_features_df=self.product_features,
                n=n
            )
            
            # 轉換為 Recommendation 物件
            recommendations = []
            for rank, (product_id, score) in enumerate(predictions, 1):
                product_name = self._get_product_name(product_id)
                confidence_score = min(100, max(0, score * 100))
                
                rec = Recommendation(
                    product_id=product_id,
                    product_name=product_name,
                    confidence_score=confidence_score,
                    explanation="",  # 稍後生成
                    rank=rank,
                    source=RecommendationSource.ML_MODEL,
                    raw_score=score
                )
                recommendations.append(rec)
            
            return recommendations
            
        except Exception as e:
            logger.warning(f"ML 推薦生成失敗: {e}")
            return []
    
    def _generate_cf_recommendations(
        self,
        member_info: MemberInfo,
        n: int
    ) -> List[Recommendation]:
        """
        使用協同過濾生成推薦
        
        Args:
            member_info: 會員資訊
            n: 推薦數量
            
        Returns:
            List[Recommendation]: 推薦列表
        """
        if self.cf_model is None:
            return []
        
        try:
            # 使用協同過濾推薦
            cf_predictions = self.cf_model.recommend(
                member_id=member_info.member_code,
                n=n,
                exclude_known=True,
                known_products=member_info.recent_purchases
            )
            
            # 轉換為 Recommendation 物件
            recommendations = []
            for rank, (product_id, score) in enumerate(cf_predictions, 1):
                product_name = self._get_product_name(product_id)
                confidence_score = min(100, max(0, score * 10))  # 調整分數範圍
                
                rec = Recommendation(
                    product_id=product_id,
                    product_name=product_name,
                    confidence_score=confidence_score,
                    explanation="",  # 稍後生成
                    rank=rank,
                    source=RecommendationSource.COLLABORATIVE_FILTERING,
                    raw_score=score
                )
                recommendations.append(rec)
            
            return recommendations
            
        except Exception as e:
            logger.warning(f"協同過濾推薦生成失敗: {e}")
            return []
    
    def _generate_popularity_recommendations(
        self,
        member_info: MemberInfo,
        n: int
    ) -> List[Recommendation]:
        """
        生成熱門產品推薦
        
        Args:
            member_info: 會員資訊
            n: 推薦數量
            
        Returns:
            List[Recommendation]: 推薦列表
        """
        if self.product_features is None:
            return []
        
        try:
            # 排除已購買產品
            available_products = self.product_features.copy()
            if member_info.recent_purchases:
                available_products = available_products[
                    ~available_products['stock_id'].isin(member_info.recent_purchases)
                ]
            
            # 按熱門度排序
            if 'popularity_score' in available_products.columns:
                top_products = available_products.nlargest(n, 'popularity_score')
            else:
                # 如果沒有熱門度分數，隨機選擇
                top_products = available_products.sample(min(n, len(available_products)))
            
            # 轉換為 Recommendation 物件
            recommendations = []
            for rank, (_, row) in enumerate(top_products.iterrows(), 1):
                product_id = row['stock_id']
                product_name = row.get('stock_description', product_id)
                popularity_score = row.get('popularity_score', 50.0)
                
                rec = Recommendation(
                    product_id=product_id,
                    product_name=product_name,
                    confidence_score=min(100, max(0, popularity_score)),
                    explanation="",  # 稍後生成
                    rank=rank,
                    source=RecommendationSource.POPULARITY,
                    raw_score=popularity_score
                )
                recommendations.append(rec)
            
            return recommendations
            
        except Exception as e:
            logger.warning(f"熱門推薦生成失敗: {e}")
            return []
    
    def _generate_diversity_recommendations(
        self,
        member_info: MemberInfo,
        n: int
    ) -> List[Recommendation]:
        """
        生成多樣性推薦（探索新類別）
        
        Args:
            member_info: 會員資訊
            n: 推薦數量
            
        Returns:
            List[Recommendation]: 推薦列表
        """
        if self.product_features is None:
            return []
        
        try:
            # 獲取會員已購買的類別
            purchased_categories = set()
            if member_info.recent_purchases:
                for product_id in member_info.recent_purchases:
                    product = self.product_features[
                        self.product_features['stock_id'] == product_id
                    ]
                    if not product.empty and 'category' in product.columns:
                        category = product.iloc[0]['category']
                        if pd.notna(category):
                            purchased_categories.add(category)
            
            # 選擇新類別的產品
            available_products = self.product_features.copy()
            
            # 排除已購買產品
            if member_info.recent_purchases:
                available_products = available_products[
                    ~available_products['stock_id'].isin(member_info.recent_purchases)
                ]
            
            # 優先選擇新類別
            if 'category' in available_products.columns and purchased_categories:
                new_category_products = available_products[
                    ~available_products['category'].isin(purchased_categories)
                ]
                
                if len(new_category_products) >= n:
                    available_products = new_category_products
            
            # 隨機選擇以增加多樣性
            selected_products = available_products.sample(min(n, len(available_products)))
            
            # 轉換為 Recommendation 物件
            recommendations = []
            for rank, (_, row) in enumerate(selected_products.iterrows(), 1):
                product_id = row['stock_id']
                product_name = row.get('stock_description', product_id)
                
                rec = Recommendation(
                    product_id=product_id,
                    product_name=product_name,
                    confidence_score=60.0,  # 中等信心分數
                    explanation="",  # 稍後生成
                    rank=rank,
                    source=RecommendationSource.DIVERSITY,
                    raw_score=0.6
                )
                recommendations.append(rec)
            
            return recommendations
            
        except Exception as e:
            logger.warning(f"多樣性推薦生成失敗: {e}")
            return []
    
    def _deduplicate_recommendations(
        self,
        recommendations: List[Recommendation]
    ) -> List[Recommendation]:
        """
        去除重複推薦（優化版本）
        
        性能優化：使用字典保留最高分數的推薦
        
        Args:
            recommendations: 推薦列表
            
        Returns:
            List[Recommendation]: 去重後的推薦列表
        """
        # 使用字典保留每個產品的最高分數推薦
        product_recs = {}
        
        for rec in recommendations:
            if rec.product_id not in product_recs:
                product_recs[rec.product_id] = rec
            else:
                # 保留信心分數更高的推薦
                if rec.confidence_score > product_recs[rec.product_id].confidence_score:
                    product_recs[rec.product_id] = rec
        
        return list(product_recs.values())
    
    def _sort_recommendations(
        self,
        recommendations: List[Recommendation]
    ) -> List[Recommendation]:
        """
        按信心分數排序推薦
        
        Args:
            recommendations: 推薦列表
            
        Returns:
            List[Recommendation]: 排序後的推薦列表
        """
        return sorted(recommendations, key=lambda x: x.confidence_score, reverse=True)

    
    def _enhance_recommendations_with_reasons(
        self,
        recommendations: List[Recommendation],
        member_info: MemberInfo,
        member_history: MemberHistory
    ) -> List[Recommendation]:
        """
        為推薦添加理由
        
        Args:
            recommendations: 推薦列表
            member_info: 會員資訊
            member_history: 會員歷史
            
        Returns:
            List[Recommendation]: 添加理由後的推薦列表
        """
        # 重置理由生成器的已使用理由追蹤
        self.reason_generator.reset_used_reasons()
        
        for rec in recommendations:
            reason = self.reason_generator.generate_reason(
                member_info=member_info,
                product_id=rec.product_id,
                confidence_score=rec.confidence_score,
                member_history=member_history,
                source=rec.source,
                max_reasons=2
            )
            rec.explanation = reason
        
        return recommendations
    
    def _determine_quality_level(
        self,
        reference_value_score: ReferenceValueScore
    ) -> QualityLevel:
        """
        確定品質等級
        
        Args:
            reference_value_score: 可參考價值分數
            
        Returns:
            QualityLevel: 品質等級
        """
        score = reference_value_score.overall_score
        
        if score >= 80:
            return QualityLevel.EXCELLENT
        elif score >= 60:
            return QualityLevel.GOOD
        elif score >= 40:
            return QualityLevel.ACCEPTABLE
        else:
            return QualityLevel.POOR
    
    def _get_candidate_products(
        self,
        member_info: MemberInfo,
        max_candidates: int = 100
    ) -> List[str]:
        """
        獲取候選產品列表
        
        Args:
            member_info: 會員資訊
            max_candidates: 最大候選數量
            
        Returns:
            List[str]: 產品 ID 列表
        """
        if self.product_features is None:
            return []
        
        # 獲取所有產品
        all_products = self.product_features['stock_id'].tolist()
        
        # 排除已購買產品
        if member_info.recent_purchases:
            all_products = [
                p for p in all_products 
                if p not in member_info.recent_purchases
            ]
        
        # 限制候選數量
        if len(all_products) > max_candidates:
            if 'popularity_score' in self.product_features.columns:
                top_products = self.product_features.nlargest(
                    max_candidates, 'popularity_score'
                )
                all_products = top_products['stock_id'].tolist()
            else:
                all_products = all_products[:max_candidates]
        
        return all_products
    
    def _get_product_name(self, product_id: str) -> str:
        """
        獲取產品名稱（使用快取優化）
        
        性能優化：使用預先建立的快取，避免重複查詢 DataFrame
        """
        # 優先使用快取
        if product_id in self._product_name_cache:
            return self._product_name_cache[product_id]
        
        # 快取未命中，查詢 DataFrame
        if self.product_features is None:
            return product_id
        
        product = self.product_features[
            self.product_features['stock_id'] == product_id
        ]
        
        if not product.empty and 'stock_description' in product.columns:
            product_name = product.iloc[0]['stock_description']
            # 更新快取
            self._product_name_cache[product_id] = product_name
            return product_name
        
        return product_id
    
    def get_model_info(self) -> Dict[str, Any]:
        """獲取模型資訊"""
        return {
            'model_version': self.metadata.get('version', 'unknown'),
            'model_type': self.metadata.get('model_type', 'unknown'),
            'trained_at': self.metadata.get('trained_at', 'unknown'),
            'metrics': self.metadata.get('metrics', {}),
            'total_products': len(self.product_features) if self.product_features is not None else 0,
            'total_members': len(self.member_features) if self.member_features is not None else 0,
            'cf_model_available': self.cf_model is not None,
            'strategy_weights': self.STRATEGY_WEIGHTS
        }
    
    def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        return {
            'status': 'healthy' if self.ml_model is not None else 'unhealthy',
            'ml_model_loaded': self.ml_model is not None,
            'cf_model_loaded': self.cf_model is not None,
            'member_features_loaded': self.member_features is not None,
            'product_features_loaded': self.product_features is not None,
            'metadata_loaded': self.metadata is not None,
            'performance_tracker_active': True,
            'value_evaluator_active': True,
            'reason_generator_active': self.reason_generator is not None,
            'degradation_strategy_active': self.degradation_strategy is not None
        }
    
    def get_degradation_thresholds(self) -> Dict[str, Any]:
        """
        獲取降級閾值配置
        
        Returns:
            Dict[str, Any]: 降級閾值配置
        """
        if self.degradation_strategy:
            return self.degradation_strategy.get_degradation_thresholds()
        return {}
    
    def update_degradation_thresholds(
        self,
        min_quality_score: Optional[float] = None,
        max_response_time_ms: Optional[float] = None
    ) -> None:
        """
        更新降級閾值配置
        
        Args:
            min_quality_score: 最低品質分數閾值
            max_response_time_ms: 最大反應時間閾值
        """
        if self.degradation_strategy:
            self.degradation_strategy.update_degradation_thresholds(
                min_quality_score=min_quality_score,
                max_response_time_ms=max_response_time_ms
            )
            logger.info("降級閾值已更新")


def main():
    """測試增強推薦引擎"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("測試增強推薦引擎")
    print("=" * 60)
    
    try:
        # 建立增強推薦引擎
        print("\n建立增強推薦引擎...")
        engine = EnhancedRecommendationEngine()
        
        # 健康檢查
        print("\n健康檢查...")
        health = engine.health_check()
        for key, value in health.items():
            status = "✓" if value else "✗"
            print(f"  {status} {key}: {value}")
        
        # 獲取模型資訊
        print("\n模型資訊...")
        info = engine.get_model_info()
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        # 測試推薦
        print("\n測試增強推薦...")
        member_info = MemberInfo(
            member_code="CU000001",
            phone="0937024682",
            total_consumption=17400.0,
            accumulated_bonus=500.0,
            recent_purchases=["30463", "31033"]
        )
        
        response = engine.recommend(member_info, n=5, strategy='hybrid')
        
        print(f"\n為會員 {response.member_code} 的增強推薦:")
        print(f"策略: {response.strategy_used}")
        print(f"品質等級: {response.quality_level.value}")
        print(f"總耗時: {response.performance_metrics.total_time_ms:.2f} ms")
        print(f"\n可參考價值分數:")
        print(f"  綜合分數: {response.reference_value_score.overall_score:.2f}")
        print(f"  相關性: {response.reference_value_score.relevance_score:.2f}")
        print(f"  新穎性: {response.reference_value_score.novelty_score:.2f}")
        print(f"  可解釋性: {response.reference_value_score.explainability_score:.2f}")
        print(f"  多樣性: {response.reference_value_score.diversity_score:.2f}")
        
        print(f"\n推薦列表:")
        for rec in response.recommendations:
            print(f"  {rec.rank}. {rec.product_name}")
            print(f"     來源: {rec.source.value}")
            print(f"     信心分數: {rec.confidence_score:.2f}")
            print(f"     推薦理由: {rec.explanation}")
        
        print(f"\n性能指標:")
        for stage, time_ms in response.performance_metrics.stage_times.items():
            print(f"  {stage}: {time_ms:.2f} ms")
        
        print("\n" + "=" * 60)
        print("✓ 增強推薦引擎測試完成！")
        print("=" * 60)
        
    except FileNotFoundError as e:
        print(f"\n✗ 錯誤: {e}")
        print("請先執行訓練: python src/train.py")
    except Exception as e:
        print(f"\n✗ 錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
