"""
VoiceGuard AI - 학습 강화 보이스피싱 분석기
기존 시스템에 점진적 학습 기능 추가
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
        
        # 1. 기본 분석 수행
        base_result = await super().analyze_text(text, context)
        
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
        
        # 6. 성능 추적 업데이트
        self.performance_tracker["total_analyses"] += 1
        
        processing_time = time.time() - start_time
        logger.info(f"🧠 학습 강화 분석 완료: {processing_time:.3f}초")
        
        return integrated_result
    
    async def _apply_few_shot_learning(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Few-shot Learning 적용"""
        
        # 관련성 높은 예시 선별
        relevant_examples = self._select_relevant_examples(text)
        
        if not relevant_examples:
            return {"confidence": 0, "examples_used": 0}
        
        # Few-shot 프롬프트 구성
        prompt = self._build_few_shot_prompt(text, relevant_examples)
        
        try:
            # LLM 호출
            result = await self.llm_manager.analyze_scam_risk(
                text=prompt,
                context={**context, "analysis_type": "few_shot_learning"}
            )
            
            # 결과 파싱
            parsed_result = self._parse_few_shot_response(result.content)
            parsed_result["examples_used"] = len(relevant_examples)
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"Few-shot 학습 실패: {e}")
            return {"confidence": 0, "examples_used": 0, "error": str(e)}
    
    def _select_relevant_examples(self, text: str, max_examples: int = None) -> List[Dict]:
        """관련성 높은 예시 선별"""
        
        max_examples = max_examples or self.config["max_few_shot_examples"]
        relevant_examples = []
        
        # 키워드 기반 관련성 계산
        text_words = set(text.lower().split())
        
        for category, examples in self.few_shot_pool.items():
            for example in examples:
                example_words = set(example["text"].lower().split())
                
                # 공통 단어 비율 계산
                common_words = text_words & example_words
                relevance_score = len(common_words) / max(len(text_words), len(example_words))
                
                if relevance_score > 0.1:  # 최소 관련성 임계값
                    example_with_score = example.copy()
                    example_with_score["relevance_score"] = relevance_score
                    relevant_examples.append(example_with_score)
        
        # 관련성 점수로 정렬하고 상위 N개 선택
        relevant_examples.sort(key=lambda x: x["relevance_score"], reverse=True)
        return relevant_examples[:max_examples]
    
    def _build_few_shot_prompt(self, text: str, examples: List[Dict]) -> str:
        """Few-shot 프롬프트 구성"""
        
        prompt = """당신은 한국 보이스피싱 탐지 전문가입니다.
다음 학습된 예시들을 참고하여 새로운 텍스트를 분석하세요.

## 학습 예시들:
"""
        
        for i, example in enumerate(examples, 1):
            prompt += f"""
예시 {i}:
텍스트: "{example['text']}"
판정: {example['label']}
신뢰도: {example['confidence']:.2f}
근거: {example['reasoning']}
---
"""
        
        prompt += f"""

## 분석할 텍스트:
"{text}"

## 지시사항:
위 학습 예시들의 패턴을 참고하여 분석하고, 다음 JSON 형식으로 응답하세요:
{{
    "risk_score": 0.0-1.0,
    "classification": "scam" 또는 "legitimate",
    "confidence": 0.0-1.0,
    "reasoning": "판단 근거 (학습 예시와의 유사점 언급)",
    "similar_examples": ["유사한 예시 번호들"],
    "key_patterns": ["탐지된 주요 패턴들"]
}}
"""
        
        return prompt
    
    def _parse_few_shot_response(self, response: str) -> Dict[str, Any]:
        """Few-shot 응답 파싱"""
        
        try:
            # JSON 파싱 시도
            import json
            parsed = json.loads(response)
            
            return {
                "confidence": parsed.get("confidence", 0.5),
                "risk_score": parsed.get("risk_score", 0.5),
                "classification": parsed.get("classification", "uncertain"),
                "reasoning": parsed.get("reasoning", ""),
                "similar_examples": parsed.get("similar_examples", []),
                "key_patterns": parsed.get("key_patterns", [])
            }
            
        except json.JSONDecodeError:
            # JSON 파싱 실패시 텍스트에서 정보 추출
            logger.warning("Few-shot 응답 JSON 파싱 실패, 텍스트 분석 시도")
            
            confidence = 0.5
            risk_score = 0.5
            
            # 간단한 텍스트 분석
            if "scam" in response.lower():
                classification = "scam"
                risk_score = 0.7
            elif "legitimate" in response.lower():
                classification = "legitimate"
                risk_score = 0.3
            else:
                classification = "uncertain"
            
            return {
                "confidence": confidence,
                "risk_score": risk_score,
                "classification": classification,
                "reasoning": "응답 파싱 부분 실패",
                "similar_examples": [],
                "key_patterns": []
            }
    
    def _apply_adaptive_patterns(self, text: str) -> Dict[str, Any]:
        """적응형 패턴 매칭"""
        
        matched_patterns = []
        total_confidence = 0
        
        for pattern_id, pattern in self.adaptive_patterns.items():
            # 키워드 매칭
            keyword_matches = sum(1 for keyword in pattern.keywords if keyword in text.lower())
            
            if keyword_matches > 0:
                match_score = (keyword_matches / len(pattern.keywords)) * pattern.success_rate
                
                matched_patterns.append({
                    "pattern_id": pattern_id,
                    "match_score": match_score,
                    "keywords_matched": keyword_matches,
                    "pattern_success_rate": pattern.success_rate,
                    "usage_count": pattern.usage_count
                })
                
                total_confidence += match_score
        
        # 최고 매칭 패턴
        best_pattern = max(matched_patterns, key=lambda x: x["match_score"]) if matched_patterns else None
        
        return {
            "confidence": min(total_confidence, 1.0),
            "matched_patterns": matched_patterns,
            "best_pattern": best_pattern,
            "total_patterns_checked": len(self.adaptive_patterns)
        }
    
    def _integrate_analysis_results(self, base_result: Dict, few_shot_result: Dict, pattern_result: Dict) -> Dict[str, Any]:
        """분석 결과 통합"""
        
        # 가중 평균으로 최종 위험도 계산
        weights = {
            "base": 0.4,
            "few_shot": 0.4, 
            "pattern": 0.2
        }
        
        # 각 분석의 위험도 점수
        base_score = base_result.get("risk_score", 0.5)
        few_shot_score = few_shot_result.get("risk_score", 0.5)
        pattern_score = pattern_result.get("confidence", 0.5)
        
        final_risk_score = (
            base_score * weights["base"] +
            few_shot_score * weights["few_shot"] +
            pattern_score * weights["pattern"]
        )
        
        # 신뢰도 계산
        confidences = [
            base_result.get("confidence", 0.5),
            few_shot_result.get("confidence", 0.5),
            pattern_result.get("confidence", 0.5)
        ]
        
        final_confidence = sum(confidences) / len(confidences)
        
        # 위험 레벨 결정
        if final_risk_score >= 0.8:
            risk_level = "critical"
        elif final_risk_score >= 0.6:
            risk_level = "high"
        elif final_risk_score >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # 통합 결과
        return {
            "final_risk_score": final_risk_score,
            "risk_level": risk_level,
            "confidence": final_confidence,
            "scam_type": base_result.get("scam_type", "unknown"),
            "key_indicators": base_result.get("key_indicators", []),
            "reasoning": self._create_integrated_reasoning(base_result, few_shot_result, pattern_result),
            "recommendation": base_result.get("recommendation", "신중하게 대응하세요"),
            "analysis_breakdown": {
                "base_analysis": {"score": base_score, "confidence": base_result.get("confidence", 0.5)},
                "few_shot_learning": {"score": few_shot_score, "confidence": few_shot_result.get("confidence", 0.5)},
                "pattern_matching": {"score": pattern_score, "confidence": pattern_result.get("confidence", 0.5)}
            }
        }
    
    def _create_integrated_reasoning(self, base_result: Dict, few_shot_result: Dict, pattern_result: Dict) -> str:
        """통합 추론 결과 생성"""
        
        reasoning_parts = []
        
        # 기본 분석 추론
        if base_result.get("reasoning"):
            reasoning_parts.append(f"기본 분석: {base_result['reasoning']}")
        
        # Few-shot 학습 추론
        if few_shot_result.get("reasoning") and few_shot_result.get("examples_used", 0) > 0:
            reasoning_parts.append(f"학습 기반 분석: {few_shot_result['reasoning']}")
        
        # 패턴 매칭 결과
        if pattern_result.get("best_pattern"):
            best_pattern = pattern_result["best_pattern"]
            reasoning_parts.append(f"패턴 매칭: {best_pattern['pattern_id']} 패턴과 {best_pattern['match_score']:.2f} 일치")
        
        return " | ".join(reasoning_parts) if reasoning_parts else "종합 분석 완료"
    
    async def learn_from_feedback(self, analysis_id: str, actual_label: str, user_feedback: str, user_id: str = None):
        """사용자 피드백으로부터 학습"""
        
        # 분석 결과 찾기 (실제로는 세션 저장소에서 조회)
        # 여기서는 간단화하여 새로운 학습 예시로 처리
        
        learning_example = LearningExample(
            text="", # 실제로는 원본 텍스트 저장
            actual_label=actual_label,
            predicted_label="", # 실제로는 예측 결과 저장
            confidence=0.0, # 실제로는 예측 신뢰도 저장
            user_feedback=user_feedback,
            cultural_markers=[],
            timestamp=datetime.now(),
            user_id=user_id
        )
        
        self.learning_examples.append(learning_example)
        self.performance_tracker["user_feedback_count"] += 1
        
        logger.info(f"📝 사용자 피드백 학습: {user_feedback} (총 {len(self.learning_examples)}개)")
        
        # 충분한 피드백이 쌓이면 학습 수행
        if len(self.learning_examples) >= self.config["learning_threshold"]:
            await self._perform_learning_cycle()
    
    async def _perform_learning_cycle(self):
        """학습 사이클 수행"""
        
        logger.info("🔄 학습 사이클 시작...")
        
        try:
            # 1. 잘못 분류된 사례들 분석
            incorrect_examples = [
                ex for ex in self.learning_examples 
                if ex.user_feedback == "wrong"
            ]
            
            # 2. 새로운 패턴 발견
            await self._discover_new_patterns(incorrect_examples)
            
            # 3. Few-shot 예시 풀 업데이트
            self._update_few_shot_pool()
            
            # 4. 성능 메트릭 계산
            self._calculate_performance_metrics()
            
            # 5. 학습 데이터 저장
            self._save_learning_data()
            
            self.performance_tracker["learning_cycles"] += 1
            
            logger.info(f"✅ 학습 사이클 완료 (#{self.performance_tracker['learning_cycles']})")
            
        except Exception as e:
            logger.error(f"❌ 학습 사이클 실패: {e}")
    
    async def _discover_new_patterns(self, incorrect_examples: List[LearningExample]):
        """새로운 패턴 발견"""
        
        if len(incorrect_examples) < self.config["min_examples_for_pattern"]:
            return
        
        # 공통 키워드 추출
        scam_examples = [ex for ex in incorrect_examples if ex.actual_label == "scam"]
        
        if len(scam_examples) >= 3:
            # 키워드 빈도 분석
            all_words = []
            for example in scam_examples:
                all_words.extend(example.text.lower().split())
            
            from collections import Counter
            word_freq = Counter(all_words)
            
            # 자주 나타나는 키워드들로 새 패턴 생성
            common_keywords = [word for word, freq in word_freq.most_common(10) if freq >= 2]
            
            if common_keywords:
                pattern_id = f"learned_pattern_{len(self.adaptive_patterns) + 1}_{datetime.now().strftime('%Y%m%d')}"
                
                new_pattern = AdaptivePattern(
                    pattern_id=pattern_id,
                    keywords=common_keywords,
                    cultural_context=[],  # 추후 확장
                    success_rate=0.7,  # 초기값
                    usage_count=0,
                    last_updated=datetime.now(),
                    examples=[ex.text for ex in scam_examples[:3]]
                )
                
                self.adaptive_patterns[pattern_id] = new_pattern
                
                logger.info(f"🆕 새 패턴 발견: {pattern_id} - 키워드: {common_keywords[:5]}")
    
    def _update_few_shot_pool(self):
        """Few-shot 예시 풀 업데이트"""
        
        # 높은 신뢰도의 올바른 예측 사례들을 Few-shot 풀에 추가
        high_quality_examples = [
            ex for ex in self.learning_examples 
            if ex.user_feedback == "correct" and ex.confidence > 0.8
        ]
        
        for example in high_quality_examples[:5]:  # 최대 5개만 추가
            category = self._categorize_example(example)
            
            if category and len(self.few_shot_pool[category]) < 10:  # 카테고리당 최대 10개
                new_example = {
                    "text": example.text,
                    "label": example.actual_label,
                    "reasoning": "사용자 검증된 실제 사례",
                    "confidence": example.confidence
                }
                
                self.few_shot_pool[category].append(new_example)
                logger.info(f"📚 Few-shot 예시 추가: {category}")
    
    def _categorize_example(self, example: LearningExample) -> Optional[str]:
        """예시를 카테고리로 분류"""
        
        text = example.text.lower()
        
        if any(keyword in text for keyword in ["금융감독원", "검찰", "경찰", "국세청"]):
            return "government_scam"
        elif any(keyword in text for keyword in ["어머니", "아들", "딸", "사고", "응급실"]):
            return "family_emergency" 
        elif example.actual_label == "legitimate":
            return "legitimate_calls"
        
        return None
    
    def _calculate_performance_metrics(self):
        """성능 메트릭 계산"""
        
        if not self.learning_examples:
            return
        
        # 정확도 계산
        correct_predictions = sum(1 for ex in self.learning_examples if ex.user_feedback == "correct")
        total_predictions = len(self.learning_examples)
        
        current_accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
        
        self.performance_tracker["accuracy_trend"].append({
            "timestamp": datetime.now().isoformat(),
            "accuracy": current_accuracy,
            "total_examples": total_predictions
        })
        
        # 최근 10개 기록만 유지
        if len(self.performance_tracker["accuracy_trend"]) > 10:
            self.performance_tracker["accuracy_trend"] = self.performance_tracker["accuracy_trend"][-10:]
        
        logger.info(f"📊 현재 정확도: {current_accuracy:.3f} ({correct_predictions}/{total_predictions})")
    
    def _generate_analysis_id(self, text: str) -> str:
        """분석 고유 ID 생성"""
        return hashlib.md5(f"{text}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
    
    def _save_learning_data(self):
        """학습 데이터 저장"""
        
        try:
            self.config["data_persistence_path"].parent.mkdir(parents=True, exist_ok=True)
            
            save_data = {
                "timestamp": datetime.now().isoformat(),
                "adaptive_patterns": {
                    pid: asdict(pattern) for pid, pattern in self.adaptive_patterns.items()
                },
                "few_shot_pool": self.few_shot_pool,
                "performance_tracker": self.performance_tracker,
                "learning_examples_count": len(self.learning_examples)
            }
            
            with open(self.config["data_persistence_path"], 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"💾 학습 데이터 저장 완료: {self.config['data_persistence_path']}")
            
        except Exception as e:
            logger.error(f"💾 학습 데이터 저장 실패: {e}")
    
    def _load_existing_data(self):
        """기존 학습 데이터 로드"""
        
        try:
            if self.config["data_persistence_path"].exists():
                with open(self.config["data_persistence_path"], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 적응형 패턴 복원
                for pid, pattern_data in data.get("adaptive_patterns", {}).items():
                    pattern_data["last_updated"] = datetime.fromisoformat(pattern_data["last_updated"])
                    self.adaptive_patterns[pid] = AdaptivePattern(**pattern_data)
                
                # Few-shot 풀 업데이트
                if "few_shot_pool" in data:
                    for category, examples in data["few_shot_pool"].items():
                        if category in self.few_shot_pool:
                            self.few_shot_pool[category].extend(examples)
                
                # 성능 추적 데이터 복원
                if "performance_tracker" in data:
                    self.performance_tracker.update(data["performance_tracker"])
                
                logger.info(f"📚 기존 학습 데이터 로드: 패턴 {len(self.adaptive_patterns)}개")
                
        except Exception as e:
            logger.warning(f"📚 기존 데이터 로드 실패 (신규 시작): {e}")
    
    def get_learning_status(self) -> Dict[str, Any]:
        """학습 상태 조회"""
        
        return {
            "total_analyses": self.performance_tracker["total_analyses"],
            "learning_examples": len(self.learning_examples),
            "adaptive_patterns": len(self.adaptive_patterns),
            "few_shot_pool_size": {
                category: len(examples) 
                for category, examples in self.few_shot_pool.items()
            },
            "learning_cycles": self.performance_tracker["learning_cycles"],
            "current_accuracy": self.performance_tracker["accuracy_trend"][-1]["accuracy"] if self.performance_tracker["accuracy_trend"] else 0,
            "ready_for_learning": len(self.learning_examples) >= self.config["learning_threshold"]
        }

# 기존 analyzer를 학습 강화 버전으로 업그레이드
def create_learning_enhanced_analyzer():
    """학습 강화 분석기 생성"""
    return LearningEnhancedAnalyzer(llm_manager)

# 사용 예제
async def demo_learning_system():
    """학습 시스템 데모"""
    
    analyzer = create_learning_enhanced_analyzer()
    
    # 분석 수행
    test_text = "안녕하십니까. 금융감독원에서 연락드렸습니다. 계좌 점검이 필요합니다."
    result = await analyzer.analyze_with_learning(test_text)
    
    print("🔍 분석 결과:")
    print(f"  위험도: {result['final_risk_score']:.2f}")
    print(f"  신뢰도: {result['confidence']:.2f}")
    print(f"  Few-shot 적용: {result['few_shot_applied']}")
    print(f"  패턴 매칭: {result['patterns_matched']}개")
    
    # 사용자 피드백 시뮬레이션
    await analyzer.learn_from_feedback(
        analysis_id=result["analysis_id"],
        actual_label="scam",
        user_feedback="correct",
        user_id="demo_user"
    )
    
    # 학습 상태 확인
    status = analyzer.get_learning_status()
    print("\n📊 학습 상태:")
    print(f"  총 분석: {status['total_analyses']}")
    print(f"  학습 예시: {status['learning_examples']}")
    print(f"  적응형 패턴: {status['adaptive_patterns']}")
    print(f"  현재 정확도: {status['current_accuracy']:.3f}")

if __name__ == "__main__":
    asyncio.run(demo_learning_system())