#!/usr/bin/env python3
"""
VoiceGuard AI - 통합 실행 메인 파일
모든 모드를 통합해서 실행할 수 있는 메인 시스템

파일 위치: 프로젝트 루트 폴더/main.py
"""

import asyncio
import os
import sys
import logging
import signal
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 패스에 추가
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def setup_basic_logging():
    """기본 로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(name)-15s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger('elevenlabs').setLevel(logging.WARNING)
    logging.getLogger('google').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

setup_basic_logging()
logger = logging.getLogger(__name__)

class VoiceGuardApp:
    """VoiceGuard AI 통합 애플리케이션"""
    
    def __init__(self):
        self.is_running = False
        self.current_mode = None
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    async def run(self):
        """메인 실행 함수"""
        
        print("🛡️" + "="*58 + "🛡️")
        print("🛡️" + " "*15 + "VoiceGuard AI 시스템" + " "*15 + "🛡️")
        print("🛡️" + " "*10 + "보이스피싱 AI 탐지 및 대응 시스템" + " "*10 + "🛡️")
        print("🛡️" + "="*58 + "🛡️")
        
        try:
            # 1. 환경 검증
            if not await self._check_environment():
                return
            
            # 2. 시스템 초기화
            if not await self._initialize_system():
                return
            
            # 3. 시그널 핸들러 설정
            self._setup_signal_handlers()
            
            # 4. 메인 메뉴
            await self._show_main_menu()
            
        except KeyboardInterrupt:
            print("\n👋 사용자에 의해 종료되었습니다.")
        except Exception as e:
            logger.error(f"시스템 실행 중 오류: {e}")
            print(f"❌ 시스템 오류: {e}")
        finally:
            await self._cleanup()
    
    async def _check_environment(self) -> bool:
        """환경 검증"""
        
        print("🔍 시스템 환경 검증 중...")
        
        # .env 파일 로드
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("✅ 환경 변수 로드 완료")
        except ImportError:
            print("❌ python-dotenv가 설치되지 않음")
            print("📝 실행: pip install python-dotenv")
            return False
        
        # Google API 키 확인 (필수)
        google_key = os.getenv("GOOGLE_API_KEY")
        if not google_key:
            print("❌ GOOGLE_API_KEY가 설정되지 않음")
            print("📝 .env 파일에 GOOGLE_API_KEY=your_key_here 추가 필요")
            return False
        else:
            print("✅ Google API 키 확인됨")
        
        # 선택적 API 키들
        elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
        if elevenlabs_key:
            print("✅ ElevenLabs TTS 키 확인됨")
        else:
            print("⚠️ ElevenLabs TTS 키 없음 (음성 출력 제한)")
        
        returnzero_id = os.getenv("RETURNZERO_CLIENT_ID")
        if returnzero_id:
            print("✅ ReturnZero STT 키 확인됨")
        else:
            print("⚠️ ReturnZero STT 키 없음 (음성 입력 제한)")
        
        print("✅ 환경 검증 완료")
        return True
    
    async def _initialize_system(self) -> bool:
        """시스템 초기화"""
        
        print("🚀 시스템 초기화 중...")
        
        try:
            # LLM Manager 초기화
            from core.llm_manager import llm_manager
            
            print("🧠 LLM 시스템 연결 확인 중...")
            health = await llm_manager.health_check()
            
            healthy_models = [model for model, status in health.items() if status]
            if healthy_models:
                print(f"✅ LLM 연결 성공: {', '.join(healthy_models)}")
            else:
                print("❌ LLM 연결 실패")
                return False
            
            # 기본 분석 테스트
            test_result = await llm_manager.analyze_scam_risk(
                text="테스트 메시지입니다."
            )
            print(f"✅ AI 분석 시스템 정상 작동 (처리시간: {test_result.processing_time:.2f}초)")
            
            # 모드 시스템 로드
            from app.modes import MODE_REGISTRY, get_available_modes
            available_modes = get_available_modes()
            print(f"✅ 사용 가능한 모드: {len(available_modes)}개")
            
            # 오디오 시스템 초기화 (선택적)
            try:
                from services.audio_manager import audio_manager
                from services.tts_service import tts_service
                
                if audio_manager.initialize_output():
                    print("✅ 오디오 출력 시스템 준비")
                else:
                    print("⚠️ 오디오 출력 시스템 제한")
                
                if await tts_service.test_connection():
                    print("✅ TTS 음성 출력 준비")
                else:
                    print("⚠️ TTS 음성 출력 제한")
                    
            except Exception as e:
                print(f"⚠️ 오디오 시스템 초기화 실패: {e}")
                print("📝 계속 진행하지만 음성 기능이 제한됩니다")
            
            print("🎉 시스템 초기화 완료!")
            return True
            
        except Exception as e:
            print(f"❌ 시스템 초기화 실패: {e}")
            logger.error(f"시스템 초기화 오류: {e}")
            return False
    
    def _setup_signal_handlers(self):
        """시그널 핸들러 설정"""
        
        def signal_handler(signum, frame):
            print(f"\n📶 종료 신호 수신 ({signum})")
            self.is_running = False
            if self.current_mode and hasattr(self.current_mode, 'stop'):
                self.current_mode.stop()
        
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)
    
    async def _show_main_menu(self):
        """메인 메뉴 표시 및 모드 선택"""
        
        while True:
            print("\n" + "="*70)
            print("🛡️ VoiceGuard AI - 보이스피싱 AI 탐지 및 대응 시스템")
            print("="*70)
            
            # 긴급 상황 안내
            print("\n🚨 긴급상황이신가요?")
            print("   💰 돈을 송금했다면 → 3번 또는 4번 선택")
            print("   📞 지금 의심스러운 통화 중이라면 → 2번 선택")
            print("   📞 긴급신고: 112(경찰), 1332(금융감독원)")
            
            print("\n📋 서비스 선택:")
            print("1. 🎓 예방 교육 - 보이스피싱 수법 학습 및 대응 훈련")
            print("2. 🔍 실시간 탐지 - 의심스러운 통화 내용 AI 분석")
            print("3. 🚨 사후 대처 - 피해 발생 후 체계적 대응 안내")
            print("4. 🎤 음성 가이드 사후대처 - 실시간 음성 안내로 피해 대응")
            print("5. 💬 상담 문의 - 보이스피싱 관련 질문 답변")
            print("6. ℹ️ 시스템 정보 - 현재 시스템 상태 확인")
            print("0. 🚪 종료")
            
            print("\n" + "="*70)
            
            try:
                choice = input("원하시는 서비스 번호를 입력하세요 (0-6): ").strip()
                
                if choice == "0":
                    print("👋 VoiceGuard AI를 이용해주셔서 감사합니다.")
                    break
                
                elif choice == "1":
                    await self._run_prevention_mode()
                
                elif choice == "2":
                    await self._run_detection_mode()
                
                elif choice == "3":
                    await self._run_post_incident_mode()
                
                elif choice == "4":
                    await self._run_voice_guided_recovery_mode()
                
                elif choice == "5":
                    await self._run_consultation_mode()
                
                elif choice == "6":
                    await self._show_system_info()
                
                else:
                    print("❌ 올바른 번호를 입력해주세요 (0-6)")
                    continue
                
                # 모드 실행 후 계속 여부 확인
                if choice != "0":
                    input("\n⏸️ 계속하려면 Enter를 누르세요...")
                
            except (EOFError, KeyboardInterrupt):
                break
            except Exception as e:
                print(f"❌ 입력 처리 오류: {e}")
    
    async def _run_prevention_mode(self):
        """예방 교육 모드 실행"""
        
        try:
            from app.modes.prevention_mode import PreventionMode
            await self._execute_mode(PreventionMode, "예방 교육")
        except Exception as e:
            print(f"❌ 예방 교육 모드 실행 실패: {e}")
    
    async def _run_detection_mode(self):
        """실시간 탐지 모드 실행"""
        
        try:
            from app.modes.detection_mode import DetectionMode
            await self._execute_mode(DetectionMode, "실시간 탐지")
        except Exception as e:
            print(f"❌ 실시간 탐지 모드 실행 실패: {e}")
    
    async def _run_post_incident_mode(self):
        """사후 대처 모드 실행"""
        
        try:
            from app.modes.post_incident_mode import PostIncidentMode
            await self._execute_mode(PostIncidentMode, "사후 대처")
        except Exception as e:
            print(f"❌ 사후 대처 모드 실행 실패: {e}")
    
    async def _run_voice_guided_recovery_mode(self):
        """음성 가이드 사후대처 모드 실행"""
        
        try:
            from app.modes.voice_guided_recovery_mode import VoiceGuidedRecoveryMode
            await self._execute_mode(VoiceGuidedRecoveryMode, "음성 가이드 사후대처")
        except Exception as e:
            print(f"❌ 음성 가이드 사후대처 모드 실행 실패: {e}")
    
    async def _run_consultation_mode(self):
        """상담 문의 모드 실행"""
        
        print("💬 상담 문의 모드 (간소화 버전)")
        print("-" * 40)
        
        print("""
💬 VoiceGuard 상담 서비스

자주 묻는 질문:

Q: 보이스피싱인지 어떻게 확인하나요?
A: 다음 특징이 있으면 의심하세요:
   - 전화로 개인정보/금융정보 요구
   - 긴급하게 돈을 요구
   - 공공기관 사칭
   - 앱 설치 요구

Q: 의심스러운 전화를 받았을 때 대처법은?
A: 1) 즉시 통화 끊기
   2) 해당 기관에 직접 확인
   3) 의심되면 112 신고

Q: 가족이 당했다고 하는데 진짜인가요?
A: 먼저 침착하게 가족에게 직접 연락해보세요.
   실제 응급상황이라면 112를 통해 확인 가능합니다.

Q: 개인정보를 알려줬는데 어떻게 하나요?
A: 즉시 관련 금융기관에 연락하여 계좌 모니터링을 
   강화하고, 필요시 계좌 변경을 고려하세요.

🔄 더 자세한 AI 상담은 향후 업데이트에서 제공될 예정입니다.
        """)
    
    async def _execute_mode(self, mode_class, mode_name: str):
        """모드 실행"""
        
        print(f"\n🎯 {mode_name} 모드를 시작합니다...")
        
        try:
            # 서비스 로드
            from core.llm_manager import llm_manager
            
            try:
                from services.audio_manager import audio_manager
                from services.tts_service import tts_service
            except ImportError:
                # 더미 서비스
                class DummyService:
                    def __getattr__(self, name):
                        return lambda *args, **kwargs: None
                    async def __aenter__(self):
                        return self
                    async def __aexit__(self, *args):
                        pass
                
                audio_manager = DummyService()
                tts_service = DummyService()
            
            # 모드 인스턴스 생성
            self.current_mode = mode_class(
                llm_manager=llm_manager,
                audio_manager=audio_manager,
                tts_service=tts_service,
                session_id=self.session_id
            )
            
            # 모드 실행
            await self.current_mode.run()
            
            print(f"✅ {mode_name} 모드가 완료되었습니다.")
            
        except Exception as e:
            print(f"❌ {mode_name} 모드 실행 중 오류: {e}")
            logger.error(f"{mode_name} 모드 오류: {e}")
        finally:
            self.current_mode = None
    
    async def _show_system_info(self):
        """시스템 정보 표시"""
        
        print("\n📊 VoiceGuard AI 시스템 정보")
        print("="*50)
        
        try:
            # LLM 상태
            from core.llm_manager import llm_manager
            health = await llm_manager.health_check()
            stats = llm_manager.get_performance_stats()
            
            print("🧠 AI 시스템:")
            for model, status in health.items():
                print(f"   {model}: {'✅ 정상' if status else '❌ 오류'}")
            
            print(f"\n📈 성능 통계:")
            print(f"   총 호출: {stats['total_calls']}회")
            print(f"   총 비용: ${stats['total_cost']:.4f}")
            print(f"   남은 예산: ${stats['remaining_budget']:.2f}")
            print(f"   평균 비용: ${stats['avg_cost_per_call']:.4f}/호출")
            
            # 모드 정보
            from app.modes import get_available_modes, get_mode_info
            modes = get_available_modes()
            print(f"\n🎯 사용 가능한 모드: {len(modes)}개")
            for mode in modes:
                print(f"   - {mode}")
            
            # 환경 정보
            print(f"\n🔧 환경 설정:")
            print(f"   Google API: {'✅' if os.getenv('GOOGLE_API_KEY') else '❌'}")
            print(f"   ElevenLabs TTS: {'✅' if os.getenv('ELEVENLABS_API_KEY') else '❌'}")
            print(f"   ReturnZero STT: {'✅' if os.getenv('RETURNZERO_CLIENT_ID') else '❌'}")
            print(f"   디버그 모드: {os.getenv('DEBUG', 'False')}")
            
            # 시스템 리소스 (선택적)
            try:
                import psutil
                cpu = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                print(f"\n💻 시스템 리소스:")
                print(f"   CPU 사용률: {cpu}%")
                print(f"   메모리 사용률: {memory.percent}%")
                print(f"   사용 가능 메모리: {memory.available // (1024**3)}GB")
            except ImportError:
                print(f"\n💻 시스템 리소스: psutil 미설치")
                
        except Exception as e:
            print(f"❌ 시스템 정보 조회 실패: {e}")
    
    async def _cleanup(self):
        """시스템 정리"""
        
        print("\n🧹 시스템 정리 중...")
        
        try:
            if self.current_mode and hasattr(self.current_mode, 'cleanup'):
                await self.current_mode.cleanup()
            
            print("✅ 시스템 정리 완료")
            
        except Exception as e:
            print(f"⚠️ 정리 중 오류 (무시): {e}")

async def main():
    """메인 함수"""
    
    # Python 버전 확인
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 이상이 필요합니다.")
        sys.exit(1)
    
    # 필수 패키지 확인
    try:
        import google.generativeai
    except ImportError:
        print("❌ google-generativeai 패키지가 설치되지 않음")
        print("📝 실행: pip install google-generativeai")
        sys.exit(1)
    
    # 애플리케이션 실행
    app = VoiceGuardApp()
    await app.run()

if __name__ == "__main__":
    try:
        # 이벤트 루프 정책 최적화 (Windows)
        if sys.platform.startswith('win'):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # 애플리케이션 실행
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n👋 안전하게 종료되었습니다.")
    except Exception as e:
        print(f"❌ 치명적 오류: {e}")
        sys.exit(1)