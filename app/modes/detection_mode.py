"""
VoiceGuard AI - 실시간 탐지 모드 (학습 강화 버전)
의심스러운 통화 내용을 실시간으로 분석하고 경고
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .base_mode import BaseMode, ModeState

# 조건부 import
try:
    from services.simple_stt_service import SttService
except ImportError:
    try:
        from services.stt_service import SttService
    except ImportError:
        # 더미 STT 서비스
        class SttService:
            def __init__(self, *args, **kwargs):
                self.is_running = False
            def start(self):
                print("🎤 STT 서비스를 사용할 수 없습니다. 텍스트 입력으로 진행합니다.")
            def stop(self):
                pass

# 학습 강화 분석기 import
try:
    from core.learning_enhanced_analyzer import LearningEnhancedAnalyzer
    LEARNING_AVAILABLE = True
except ImportError:
    LEARNING_AVAILABLE = False
    # 기존 분석기 폴백
    try:
        from core.analyzer import VoicePhishingAnalyzer
    except ImportError:
        # 더미 분석기
        class VoicePhishingAnalyzer:
            def __init__(self, llm_manager):
                self.llm_manager = llm_manager
            async def analyze_text(self, text, context=None):
                return {
                    "risk_score": 0.3,
                    "risk_level": "낮음",
                    "scam_type": "테스트",
                    "key_indicators": ["테스트"],
                    "recommendation": "정상적인 테스트 결과입니다."
                }

try:
    from config.settings import settings
except ImportError:
    # 더미 설정
    class Settings:
        RETURNZERO_CLIENT_ID = "demo"
        RETURNZERO_CLIENT_SECRET = "demo"
    settings = Settings()

logger = logging.getLogger(__name__)

# 간단한 피드백 매니저 (core/learning_enhanced_analyzer.py가 없을 때 대비)
class SimpleFeedbackManager:
    """간단한 피드백 관리자"""
    
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.feedback_count = 0
        
    async def submit_feedback(self, analysis_id: str, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """피드백 제출 (간단 버전)"""
        try:
            if hasattr(self.analyzer, 'learn_from_feedback'):
                await self.analyzer.learn_from_feedback(
                    analysis_id=analysis_id,
                    actual_label=feedback_data.get("actual_label"),
                    user_feedback=feedback_data.get("user_feedback"),
                    user_id=feedback_data.get("user_id")
                )
            
            self.feedback_count += 1
            return {"success": True, "message": "피드백이 제출되었습니다"}
            
        except Exception as e:
            logger.error(f"피드백 처리 실패: {e}")
            return {"success": False, "error": str(e)}

class DetectionMode(BaseMode):
    """실시간 탐지 모드 (학습 강화)"""
    
    @property
    def mode_name(self) -> str:
        return "실시간 탐지"
    
    @property
    def mode_description(self) -> str:
        base_desc = "의심스러운 통화 내용을 실시간으로 분석하여 보이스피싱을 탐지합니다"
        if LEARNING_AVAILABLE:
            return f"{base_desc} (🧠 AI 학습 기능 포함)"
        return base_desc
    
    def _load_mode_config(self) -> Dict[str, Any]:
        """탐지 모드 설정"""
        return {
            'analysis_threshold': 0.3,
            'real_time_alerts': True,
            'auto_record': False,
            'sensitivity_level': 'medium',
            'max_analysis_length': 1000,
            'learning_enabled': LEARNING_AVAILABLE,  # 학습 기능 활성화 여부
            'feedback_enabled': True,  # 피드백 수집 여부
            'feedback_timeout': 10.0   # 피드백 입력 타임아웃
        }
    
    async def _initialize_mode(self) -> bool:
        """탐지 모드 초기화 (학습 기능 포함)"""
        
        try:
            # STT 서비스 초기화
            self.stt_service = SttService(
                client_id=settings.RETURNZERO_CLIENT_ID or "demo",
                client_secret=settings.RETURNZERO_CLIENT_SECRET or "demo",
                transcript_callback=self._on_speech_detected
            )
            
            # 분석 엔진 초기화 (학습 강화 또는 기본)
            if LEARNING_AVAILABLE:
                self.analyzer = LearningEnhancedAnalyzer(self.llm_manager)
                self.feedback_manager = SimpleFeedbackManager(self.analyzer)
                logger.info("🧠 학습 강화 분석기 초기화")
            else:
                self.analyzer = VoicePhishingAnalyzer(self.llm_manager)
                self.feedback_manager = SimpleFeedbackManager(self.analyzer)
                logger.warning("⚠️ 기본 분석기 사용 (학습 기능 비활성)")
            
            # 분석 큐 및 상태
            self.analysis_queue = asyncio.Queue(maxsize=10)
            self.current_conversation = []
            self.last_analysis_time = datetime.now()
            
            # 세션별 분석 결과 저장 (피드백용)
            self.session_results = {}
            
            logger.info("✅ 실시간 탐지 모드 초기화 완료")
            return True
            
        except Exception as e:
            logger.error(f"탐지 모드 초기화 실패: {e}")
            return False
    
    async def _run_mode_logic(self):
        """실시간 탐지 메인 로직"""
        
        print("🎤 실시간 보이스피싱 탐지 모드")
        if LEARNING_AVAILABLE:
            print("🧠 AI 학습 기능이 활성화되었습니다!")
        print("💡 의심스러운 통화 내용을 입력해주세요.")
        print("💡 '종료'를 입력하면 분석을 마칩니다.")
        print("-" * 50)
        
        # STT 서비스 시작 (사용 가능한 경우)
        try:
            self.stt_service.start()
        except:
            print("🎤 음성 인식 대신 텍스트 입력을 사용합니다.")
        
        # 분석 워커 시작
        analysis_task = asyncio.create_task(self._analysis_worker())
        
        try:
            # 메인 루프 - 텍스트 입력 받기
            while self.is_running:
                try:
                    # 비동기적으로 사용자 입력 받기
                    print("\n📝 분석할 내용을 입력하세요: ", end="", flush=True)
                    user_input = await asyncio.to_thread(input)
                    
                    if user_input.strip():
                        # 종료 명령 확인
                        if any(keyword in user_input.lower() for keyword in ['종료', '끝', '중단', '그만', 'exit', 'quit']):
                            print(f"\n🛑 종료 명령: '{user_input}'")
                            break
                        
                        # 분석 수행
                        await self._process_user_input(user_input.strip())
                
                except (EOFError, KeyboardInterrupt):
                    break
                except Exception as e:
                    logger.error(f"입력 처리 오류: {e}")
                    print(f"❌ 입력 오류: {e}")
            
        except Exception as e:
            logger.error(f"탐지 모드 실행 오류: {e}")
        finally:
            # 정리
            try:
                self.stt_service.stop()
            except:
                pass
            analysis_task.cancel()
            
            try:
                await analysis_task
            except asyncio.CancelledError:
                pass
    
    async def _process_user_input(self, text: str):
        """사용자 입력 직접 처리"""
        if not text or not text.strip():
            return
        
        timestamp = datetime.now()
        
        # 분석 큐에 추가
        try:
            self.analysis_queue.put_nowait({
                'text': text,
                'timestamp': timestamp
            })
            
            # 현재 대화에 추가
            self.current_conversation.append({
                'text': text,
                'timestamp': timestamp
            })
            
            # 대화 길이 제한
            if len(self.current_conversation) > 20:
                self.current_conversation.pop(0)
            
            print(f"\n👤 입력: {text}")
            
        except asyncio.QueueFull:
            logger.warning("분석 큐가 가득참 - 이전 분석 대기 중")
            print("⚠️ 분석 중입니다. 잠시 기다려주세요.")
    
    def _on_speech_detected(self, text: str):
        """STT 결과 콜백"""
        
        if not text or not text.strip():
            return
        
        text = text.strip()
        
        # 종료 명령 확인
        if any(keyword in text.lower() for keyword in ['종료', '끝', '중단', '그만']):
            print(f"\n🛑 종료 명령 감지: '{text}'")
            self.stop()
            return
        
        # 분석 큐에 추가
        try:
            timestamp = datetime.now()
            self.analysis_queue.put_nowait({
                'text': text,
                'timestamp': timestamp
            })
            
            # 현재 대화에 추가
            self.current_conversation.append({
                'text': text,
                'timestamp': timestamp
            })
            
            # 대화 길이 제한
            if len(self.current_conversation) > 20:
                self.current_conversation.pop(0)
            
            print(f"\n👤 음성 입력: {text}")
            
        except asyncio.QueueFull:
            logger.warning("분석 큐가 가득참 - 이전 분석 대기 중")
    
    async def _analysis_worker(self):
        """분석 워커 - 백그라운드에서 지속적으로 분석"""
        
        while self.is_running:
            try:
                # 분석할 데이터 대기
                speech_data = await asyncio.wait_for(
                    self.analysis_queue.get(),
                    timeout=1.0
                )
                
                # 분석 수행 (학습 강화 또는 기본)
                await self._analyze_speech(speech_data)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"분석 워커 오류: {e}")
                await asyncio.sleep(1)
    
    async def _analyze_speech(self, speech_data: Dict[str, Any]):
        """음성 데이터 분석 (학습 기능 통합)"""
        
        start_time = datetime.now()
        text = speech_data['text']
        
        try:
            if LEARNING_AVAILABLE:
                print(f"🧠 학습 강화 분석 중... ", end="", flush=True)
                
                # 학습 강화 분석 수행
                analysis_result = await self.analyzer.analyze_with_learning(
                    text=text,
                    context={
                        'conversation_history': self.current_conversation[-5:],
                        'session_id': self.session_id,
                        'timestamp': speech_data['timestamp'].isoformat()
                    }
                )
                
                # 기존 형식으로 변환 (호환성)
                analysis_result = self._convert_to_legacy_format(analysis_result)
                
            else:
                print(f"🔍 기본 분석 중... ", end="", flush=True)
                
                # 기본 분석
                analysis_result = await self.analyzer.analyze_text(
                    text=text,
                    context={
                        'conversation_history': self.current_conversation[-5:],
                        'session_id': self.session_id,
                        'timestamp': speech_data['timestamp'].isoformat()
                    }
                )
            
            # 분석 결과에 ID 추가 (피드백용)
            analysis_id = self._generate_analysis_id(text)
            analysis_result["analysis_id"] = analysis_id
            
            # 세션 결과 저장 (피드백용)
            self.session_results[analysis_id] = {
                "text": text,
                "result": analysis_result,
                "timestamp": start_time
            }
            
            # 분석 시간 계산
            analysis_time = (datetime.now() - start_time).total_seconds()
            print(f"완료 ({analysis_time:.2f}초)")
            
            # 결과 출력
            await self._display_analysis_result(analysis_result, text)
            
            # 사용자 피드백 요청 (학습 기능이 있을 때만)
            if LEARNING_AVAILABLE and self.config.get('feedback_enabled', True):
                await self._request_user_feedback(analysis_id)
            
            # 통계 업데이트
            self._update_stats(
                success=True,
                last_risk_score=analysis_result.get('risk_score', 0),
                analysis_time=analysis_time,
                learning_applied=analysis_result.get("few_shot_applied", False)
            )
            
        except Exception as e:
            logger.error(f"분석 실패: {e}")
            print(f"❌ 분석 실패: {e}")
            self._update_stats(success=False)
    
    def _convert_to_legacy_format(self, enhanced_result: Dict[str, Any]) -> Dict[str, Any]:
        """학습 강화 결과를 기존 형식으로 변환"""
        
        return {
            "risk_score": enhanced_result.get("final_risk_score", 0),
            "risk_level": enhanced_result.get("risk_level", "낮음"),
            "scam_type": enhanced_result.get("scam_type", "unknown"),
            "confidence": enhanced_result.get("confidence", 0),
            "key_indicators": enhanced_result.get("key_indicators", []),
            "immediate_action": enhanced_result.get("final_risk_score", 0) >= 0.8,
            "reasoning": enhanced_result.get("reasoning", ""),
            "recommendation": enhanced_result.get("recommendation", "신중하게 대응하세요"),
            
            # 학습 정보 추가
            "learning_enhanced": enhanced_result.get("few_shot_applied", False),
            "few_shot_applied": enhanced_result.get("few_shot_applied", False),
            "patterns_matched": enhanced_result.get("patterns_matched", 0)
        }
    
    async def _display_analysis_result(self, result: Dict[str, Any], original_text: str):
        """분석 결과 표시 (학습 정보 포함)"""
        
        risk_score = result.get('risk_score', 0)
        risk_level = result.get('risk_level', '낮음')
        scam_type = result.get('scam_type', '알 수 없음')
        
        # 위험도에 따른 아이콘 및 색상
        if risk_score >= 0.8:
            icon = "🚨"
            level_text = "매우 위험"
        elif risk_score >= 0.6:
            icon = "⚠️"
            level_text = "위험"
        elif risk_score >= 0.4:
            icon = "🔍"
            level_text = "주의 필요"
        else:
            icon = "✅"
            level_text = "안전"
        
        print(f"\n{icon} 분석 결과:")
        print(f"   위험도: {level_text} ({risk_score:.1%})")
        print(f"   추정 유형: {scam_type}")
        
        # 주요 지표 출력
        indicators = result.get('key_indicators', [])
        if indicators:
            print(f"   주요 지표: {', '.join(indicators[:3])}")
        
        # 권장사항
        recommendation = result.get('recommendation', '')
        if recommendation:
            print(f"   권장사항: {recommendation}")
        
        # 학습 정보 추가 표시 (학습 기능이 있을 때만)
        if LEARNING_AVAILABLE and result.get("learning_enhanced"):
            print(f"\n🧠 학습 정보:")
            print(f"   Few-shot 학습 적용: {'✅' if result.get('few_shot_applied') else '❌'}")
            print(f"   패턴 매칭: {result.get('patterns_matched', 0)}개")
            
            # 학습 상태 표시
            if hasattr(self.analyzer, 'get_learning_status'):
                learning_status = self.analyzer.get_learning_status()
                print(f"   누적 학습: {learning_status.get('learning_examples', 0)}개 예시")
                print(f"   적응형 패턴: {learning_status.get('adaptive_patterns', 0)}개")
        
        # 높은 위험도일 때 음성 경고
        if risk_score >= 0.7:
            await self._voice_alert(risk_score, scam_type)
        
        print("-" * 50)
    
    async def _request_user_feedback(self, analysis_id: str):
        """사용자 피드백 요청"""
        
        print(f"\n💬 이 분석이 정확했나요? (분석 ID: {analysis_id[-8:]})")
        print("   1: 정확함 (correct)")
        print("   2: 틀림 (wrong)")  
        print("   3: 확실하지 않음 (uncertain)")
        print("   Enter: 건너뛰기")
        
        try:
            # 비동기 입력 받기 (타임아웃 설정)
            user_input = await asyncio.wait_for(
                asyncio.to_thread(input, "선택: "),
                timeout=self.config.get('feedback_timeout', 10.0)
            )
            
            feedback_map = {
                "1": "correct",
                "2": "wrong", 
                "3": "uncertain"
            }
            
            if user_input.strip() in feedback_map:
                feedback = feedback_map[user_input.strip()]
                
                # 실제 라벨 추정 (간단화)
                actual_label = "scam" if feedback == "correct" else "legitimate"
                
                result = await self.feedback_manager.submit_feedback(
                    analysis_id=analysis_id,
                    feedback_data={
                        "actual_label": actual_label,
                        "user_feedback": feedback,
                        "user_id": self.session_id
                    }
                )
                
                if result.get("success"):
                    print(f"✅ 피드백 감사합니다! 학습에 반영되었습니다.")
                else:
                    print(f"⚠️ 피드백 처리 중 문제가 발생했습니다.")
            
        except asyncio.TimeoutError:
            print("⏰ 피드백 시간 초과 - 건너뛰기")
        except Exception as e:
            logger.error(f"피드백 처리 오류: {e}")
    
    def _generate_analysis_id(self, text: str) -> str:
        """분석 고유 ID 생성"""
        import hashlib
        return hashlib.md5(f"{text}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
    
    async def _voice_alert(self, risk_score: float, scam_type: str):
        """음성 경고"""
        
        try:
            if risk_score >= 0.8:
                alert_text = f"위험! {scam_type} 의심됩니다. 즉시 통화를 중단하세요!"
            else:
                alert_text = f"주의하세요. {scam_type} 가능성이 있습니다."
            
            print(f"🔊 음성 경고: {alert_text}")
            await self._speak(alert_text)
            
        except Exception as e:
            logger.warning(f"음성 경고 실패: {e}")
    
    async def _cleanup_mode(self):
        """탐지 모드 정리"""
        
        try:
            # STT 서비스 정리
            if hasattr(self, 'stt_service'):
                self.stt_service.stop()
            
            # 분석 큐 정리
            while not self.analysis_queue.empty():
                try:
                    self.analysis_queue.get_nowait()
                except:
                    break
            
            # 학습 데이터 저장 (학습 기능이 있을 때)
            if LEARNING_AVAILABLE and hasattr(self.analyzer, '_save_learning_data'):
                self.analyzer._save_learning_data()
                print("💾 학습 데이터 저장 완료")
            
            logger.info("탐지 모드 정리 완료")
            
        except Exception as e:
            logger.error(f"탐지 모드 정리 오류: {e}")
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """대화 요약 조회 (학습 정보 포함)"""
        
        total_inputs = len(self.current_conversation)
        
        if total_inputs == 0:
            return {"message": "분석된 대화가 없습니다."}
        
        summary = {
            "total_inputs": total_inputs,
            "session_duration": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            "latest_inputs": [item['text'] for item in self.current_conversation[-3:]],
            "analysis_count": self.stats['total_interactions'],
            "feedback_count": getattr(self.feedback_manager, 'feedback_count', 0)
        }
        
        # 학습 정보 추가 (학습 기능이 있을 때)
        if LEARNING_AVAILABLE and hasattr(self.analyzer, 'get_learning_status'):
            learning_status = self.analyzer.get_learning_status()
            summary["learning_status"] = learning_status
        
        return summary