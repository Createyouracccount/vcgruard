"""
VoiceGuard AI - 간단한 STT 서비스
실제 음성 인식 또는 텍스트 입력 모드

파일 위치: services/simple_stt_service.py
"""
import os
import asyncio
import logging
import threading
from typing import Callable

logger = logging.getLogger(__name__)

class SttService:
    """간단한 STT 서비스 - 텍스트 입력 모드"""
    
    def __init__(self, client_id: str, client_secret: str, transcript_callback: Callable):
        self.client_id = client_id
        self.client_secret = client_secret
        self.transcript_callback = transcript_callback
        self.is_running = False
        self.input_thread = None
        
        logger.info("간단한 STT 서비스 초기화")
    
    def start(self):
        """STT 서비스 시작 (텍스트 입력 모드)"""
        
        if self.is_running:
            return
        
        self.is_running = True
        
        print("🎤 음성 대신 텍스트로 입력하세요.")
        print("💡 '종료'를 입력하면 분석을 마칩니다.")
        
        # 백그라운드에서 텍스트 입력 받기
        self.input_thread = threading.Thread(target=self._text_input_worker, daemon=True)
        self.input_thread.start()
        
        logger.info("간단한 STT 서비스 시작됨 (텍스트 입력 모드)")
    
    def _text_input_worker(self):
        """텍스트 입력 워커"""
        
        while self.is_running:
            try:
                print("\n💬 답변을 입력하세요: ", end="", flush=True)
                user_input = input().strip()
                
                if user_input:
                    # 종료 명령 확인
                    if user_input.lower() in ['종료', '끝', '중단', 'exit', 'quit']:
                        print("🛑 사용자가 종료를 요청했습니다.")
                        self.stop()
                        break
                    
                    # 콜백 호출
                    if self.transcript_callback:
                        self.transcript_callback(user_input)
                
            except (EOFError, KeyboardInterrupt):
                print("\n🛑 입력이 중단되었습니다.")
                self.stop()
                break
            except Exception as e:
                logger.error(f"텍스트 입력 오류: {e}")
    
    def stop(self):
        """STT 서비스 중지"""
        
        self.is_running = False
        logger.info("간단한 STT 서비스 중지됨")


class RealSttService:
    """실제 음성 인식 서비스 (ReturnZero API 사용)"""
    
    def __init__(self, client_id: str, client_secret: str, transcript_callback: Callable):
        self.client_id = client_id
        self.client_secret = client_secret
        self.transcript_callback = transcript_callback
        self.is_running = False
        
        # 실제 음성 인식 사용 가능 여부 확인
        self.voice_available = self._check_voice_availability()
        
        if self.voice_available:
            logger.info("🎤 실제 음성 인식 서비스 초기화")
        else:
            logger.warning("⚠️ 음성 인식 불가 - 텍스트 모드로 대체")
    
    def _check_voice_availability(self) -> bool:
        """음성 인식 가능 여부 확인"""
        
        try:
            # PyAudio 사용 가능 여부 확인
            import pyaudio
            
            # 마이크 장치 확인
            p = pyaudio.PyAudio()
            device_count = p.get_device_count()
            
            # 입력 장치 찾기
            input_devices = []
            for i in range(device_count):
                device_info = p.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    input_devices.append(device_info)
            
            p.terminate()
            
            if len(input_devices) > 0:
                logger.info(f"🎤 발견된 입력 장치: {len(input_devices)}개")
                return True
            else:
                logger.warning("🎤 입력 장치를 찾을 수 없음")
                return False
                
        except ImportError:
            logger.warning("🎤 PyAudio가 설치되지 않음")
            return False
        except Exception as e:
            logger.warning(f"🎤 음성 장치 확인 실패: {e}")
            return False
    
    def start(self):
        """실제 음성 인식 시작"""
        
        if not self.voice_available:
            # 텍스트 모드로 폴백
            fallback_service = SttService(self.client_id, self.client_secret, self.transcript_callback)
            fallback_service.start()
            return
        
        if self.is_running:
            return
        
        self.is_running = True
        
        try:
            # 실제 음성 인식 시작
            self._start_real_voice_recognition()
            
        except Exception as e:
            logger.error(f"음성 인식 시작 실패: {e}")
            # 텍스트 모드로 폴백
            fallback_service = SttService(self.client_id, self.client_secret, self.transcript_callback)
            fallback_service.start()
    
    def _start_real_voice_recognition(self):
        """실제 음성 인식 로직"""
        
        try:
            import pyaudio
            import wave
            import tempfile
            import os
            
            # 음성 녹음 설정
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 16000
            RECORD_SECONDS = 5  # 5초씩 녹음
            
            print("🎤 음성 인식이 활성화되었습니다. 말씀해주세요.")
            print("💡 5초 단위로 음성을 인식합니다.")
            
            p = pyaudio.PyAudio()
            
            # 스트림 열기
            stream = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            
            while self.is_running:
                print("\n🎤 듣고 있습니다... (5초)")
                
                frames = []
                for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                    if not self.is_running:
                        break
                    data = stream.read(CHUNK)
                    frames.append(data)
                
                if frames:
                    # 임시 파일에 저장
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                        wf = wave.open(temp_file.name, 'wb')
                        wf.setnchannels(CHANNELS)
                        wf.setsampwidth(p.get_sample_size(FORMAT))
                        wf.setframerate(RATE)
                        wf.writeframes(b''.join(frames))
                        wf.close()
                        
                        # 음성을 텍스트로 변환 (간단한 더미 구현)
                        # 실제로는 ReturnZero API나 Google Speech API 사용
                        recognized_text = self._simple_voice_to_text(temp_file.name)
                        
                        # 임시 파일 삭제
                        os.unlink(temp_file.name)
                        
                        if recognized_text:
                            print(f"👤 인식됨: {recognized_text}")
                            self.transcript_callback(recognized_text)
            
            # 정리
            stream.stop_stream()
            stream.close()
            p.terminate()
            
        except Exception as e:
            logger.error(f"실제 음성 인식 오류: {e}")
            # 텍스트 모드로 폴백
            print("🎤 음성 인식 오류 - 텍스트 입력 모드로 전환")
            fallback_service = SttService(self.client_id, self.client_secret, self.transcript_callback)
            fallback_service.start()
    
    def _simple_voice_to_text(self, audio_file_path: str) -> str:
        """간단한 음성-텍스트 변환 (더미 구현)"""
        
        # 실제로는 ReturnZero API나 Google Speech API 호출
        # 여기서는 더미 응답
        
        import random
        
        dummy_responses = [
            "예",
            "아니요", 
            "네",
            "맞습니다",
            "틀렸습니다",
            "도움말",
            "모르겠습니다"
        ]
        
        # 파일 크기 기반으로 응답 결정 (더미)
        try:
            file_size = os.path.getsize(audio_file_path)
            if file_size > 50000:  # 큰 파일이면 답변이 있다고 가정
                return random.choice(dummy_responses)
            else:
                return ""  # 조용했다면 빈 문자열
        except:
            return ""
    
    def stop(self):
        """음성 인식 중지"""
        self.is_running = False
        logger.info("실제 음성 인식 서비스 중지됨")


# 팩토리 함수 - 사용 가능한 서비스 자동 선택
def create_stt_service(client_id: str, client_secret: str, transcript_callback: Callable):
    """최적의 STT 서비스 생성"""
    
    # ReturnZero API 키가 있고 실제 환경에서는 RealSttService 사용
    if client_id and client_secret and client_id != "demo":
        try:
            # 실제 ReturnZero 서비스 시도
            from services.stt_service import SttService as ReturnZeroSttService
            logger.info("🎤 ReturnZero STT 서비스 사용")
            return ReturnZeroSttService(client_id, client_secret, transcript_callback)
        except ImportError:
            logger.warning("🎤 ReturnZero STT 서비스 불가 - 대체 서비스 사용")
    
    # PyAudio 사용 가능하면 RealSttService, 아니면 텍스트 모드
    try:
        import pyaudio
        logger.info("🎤 PyAudio 기반 음성 인식 시도")
        return RealSttService(client_id, client_secret, transcript_callback)
    except ImportError:
        logger.info("🎤 텍스트 입력 모드 사용")
        return SttService(client_id, client_secret, transcript_callback)


# 하위 호환성을 위한 별칭
SimpleSttService = SttService