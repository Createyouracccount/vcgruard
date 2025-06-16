"""
VoiceGuard AI - 학습 강화 보이스피싱 분석기 (순환 import 해결 버전)
기존 시스템에 점진적 학습 기능 추가

파일 위치: core/learning_enhanced_analyzer.py
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

from collections import defaultdict, Counter

# 순환 import 방지 - analyzer는 동적 로딩
from core.llm_manager import llm_manager
from config.settings import detection_thresholds

logger = logging.getLogger(__name__)

@dataclass
class LearningExample:
    """학습 예시 데이터"""
    text: str
    actual_label: str  # "scam" or "legitimate"
    predicted_label: str
    confidence: float
    user_feedback: str  # "correct", "wrong", "uncertain"
    cultural_markers: List[str]
    timestamp: datetime
    user_id: Optional[str] = None

@dataclass
class AdaptivePattern:
    """적응형 패턴"""
    pattern_id: str
    keywords: List[str]
    cultural_context: List[str]
    success_rate: float
    usage_count: int
    last_updated: datetime
    examples: List[str]

class LearningEnhancedAnalyzer:
    """학습 기능이 강화된 분석기"""
    
    def __init__(self, llm_manager):
        self.llm_manager = llm_manager
        
        # 기본 분석 기능 (analyzer.py에서 복사)
        self.stats = {
            'total_analyses': 0,
            'high_risk_detections': 0,
            'avg_analysis_time': 0.0,
            'pattern_matches': {}
        }
        
        # 기본 키워드 패턴
        self.quick_patterns = self._build_quick_patterns()
        
        # 학습 데이터 저장소
        self.learning_examples: List[LearningExample] = []
        self.adaptive_patterns: Dict[str, AdaptivePattern] = {}
        
        # Few-shot 예시 풀
        self.few_shot_pool = self._initialize_few_shot_pool()
        
        # 성능 추적
        self.performance_tracker = {
            "total_analyses": 0,
            "user_feedback_count": 0,
            "accuracy_trend": [],
            "pattern_evolution": [],
            "learning_cycles": 0
        }
        
        # 설정
        self.config = {
            "min_examples_for_pattern": 3,
            "max_few_shot_examples": 5,
            "learning_threshold": 10,  # 10개 피드백마다 학습
            "pattern_confidence_threshold": 0.7,
            "data_persistence_path": Path("data/learning_data.json")
        }
        
        # 기존 학습 데이터 로드
        self._load_existing_data()
        
        logger.info("🧠 학습 강화 분석기 초기화 완료")
    
    def _build_quick_patterns(self) -> Dict[str, Any]:
        """기본 키워드 패턴 (analyzer.py와 동일)"""
        
        patterns = {
            'critical_keywords': [
                '납치', '유괴', '죽는다', '체포영장', '계좌동결', '응급실'
            ],
            'high_risk_keywords': [
                '금융감독원', '검찰청', '경찰서', '수사', '조사', '범죄', '피의자'
            ],
            'medium_risk_keywords': [
                '대출', '저금리', '정부지원금', '환급', '당첨', '만나서', '직접'
            ],
            'financial_keywords': [
                '계좌번호', '비밀번호', '송금', '이체', '현금', '카드번호'
            ],
            'app_keywords': [
                '앱설치', '다운로드', '권한', '허용', '업데이트', '인증'
            ]
        }
        
        return patterns
    
    def _initialize_few_shot_pool(self) -> Dict[str, List[Dict]]:
        """Few-shot 예시 풀 초기화"""
        
        return {
            "government_scam": [
                {
                    "text": "안녕하십니까. 금융감독원 전자금융과에서 연락드렸습니다. 고객님의 계좌가 범죄에 연루되어 즉시 조치가 필요합니다.",
                    "label": "scam",
                    "reasoning": "금융감독원은 개인에게 직접 전화하여 계좌 관련 조치를 요구하지 않음",
                    "confidence": 0.95
                },
                {
                    "text": "검찰청 수사관입니다. 귀하와 관련된 사건으로 출석하셔야 합니다.",
                    "label": "scam", 
                    "reasoning": "검찰청 출석은 공문으로 통지하며 전화로 개인 연락하지 않음",
                    "confidence": 0.93
                }
            ],
            
            "family_emergency": [
                {
                    "text": "어머니, 저 아들이에요. 교통사고 나서 응급실에 있는데 수술비가 급해요.",
                    "label": "scam",
                    "reasoning": "가족 확인 없이 급한 금전 요구, 실제 응급상황시 병원에서 공식 연락",
                    "confidence": 0.88
                },
                {
                    "text": "할아버지, 손자예요. 사채업자들한테 잡혀서 돈이 급해요.",
                    "label": "scam",
                    "reasoning": "가족 관계 이용한 감정 조작, 불법 상황 언급으로 신고 회피 유도",
                    "confidence": 0.91
                }
            ],
            
            "legitimate_calls": [
                {
                    "text": "안녕하세요. 고객님께서 신청하신 대출 심사 결과를 안내드리려고 연락드렸습니다.",
                    "label": "legitimate",
                    "reasoning": "고객이 사전 신청한 서비스에 대한 결과 안내",
                    "confidence": 0.85
                },
                {
                    "text": "배송 예정이던 택배가 주소 문제로 배송이 어려워 연락드렸습니다.",
                    "label": "legitimate",
                    "reasoning": "구체적인 배송 관련 문의, 개인정보 요구 없음",
                    "confidence": 0.80
                }
            ]
        }
    
    async def analyze_text(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """기본 analyze_text 메서드 (하위 호환성)"""
        
        # 학습 강화 분석 수행
        enhanced_result = await self.analyze_with_learning(text, context)
        
        # 기존 형식으로 변환 (하위 호환성)
        legacy_result = {
            "risk_score": enhanced_result["final_risk_score"],
            "risk_level": enhanced_result["risk_level"],
            "scam_type": enhanced_result["scam_type"],
            "confidence": enhanced_result["confidence"],
            "key_indicators": enhanced_result["key_indicators"],
            "immediate_action": enhanced_result["final_risk_score"] >= 0.8,
            "reasoning": enhanced_result["reasoning"],
            "recommendation": enhanced_result["recommendation"],
            
            # 새로운 학습 정보 추가
            "learning_enhanced": True,
            "analysis_id": enhanced_result["analysis_id"],
            "few_shot_applied": enhanced_result["few_shot_applied"],
            "patterns_matched": enhanced_result["patterns_matched"]
        }
        
        return legacy_result
    
    async def analyze_with_learning(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """학습 기능이 통합된 분석"""
        
        start_time = time.time()
        context = context or {}
        
        # 1. 기본 분석 수행 (키워드 + LLM)
        base_result = await self._basic_analysis(text, context)
        
        # 2. Few-shot Learning 적용
        few_shot_result = await self._apply_few_shot_learning(text, context)
        
        # 3. 적응형 패턴 매칭
        pattern_result = self._apply_adaptive_patterns(text)
        
        # 4. 결과 통합 및 신뢰도 조정
        integrated_result = self._integrate_analysis_results(
            base_result, few_shot_result, pattern_result
        )
        
        # 5. 학습을 위한 메타데이터 추가
        integrated_result.update({
            "analysis_id": self._generate_analysis_id(text),
            "few_shot_applied": few_shot_result.get("examples_used", 0) > 0,
            "patterns_matched": len(pattern_result.get("matched_patterns", [])),
            "learning_data": {
                "base_confidence": base_result.get("confidence", 0),
                "few_shot_confidence": few_shot_result.get("confidence", 0),
                "pattern_confidence": pattern_result.get("confidence", 0)
            }
        })