"""
VoiceGuard AI - 운영 모드 패키지
모든 운영 모드를 통합 관리
"""

from app.modes.base_mode import BaseMode, ModeState
from app.modes.detection_mode import DetectionMode
from app.modes.prevention_mode import PreventionMode
from app.modes.post_incident_mode import PostIncidentMode
from app.modes.voice_guided_recovery_mode import VoiceGuidedRecoveryMode

class ConsultationMode(BaseMode):
    """상담 모드 (간소화 버전)"""
    
    @property
    def mode_name(self) -> str:
        return "상담 문의"
    
    @property
    def mode_description(self) -> str:
        return "보이스피싱 관련 질문에 답변드립니다"
    
    def _load_mode_config(self):
        return {'interactive_qa': True, 'knowledge_base': True}
    
    async def _initialize_mode(self) -> bool:
        print("💬 상담 모드는 현재 개발 중입니다.")
        return True
    
    async def _run_mode_logic(self):
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

🔄 향후 AI 챗봇 기능이 추가될 예정입니다.
        """)
        
        input("\n계속하려면 Enter를 누르세요...")

# 모드 팩토리
MODE_REGISTRY = {
    'prevention': PreventionMode,
    'detection': DetectionMode,
    'post_incident': PostIncidentMode,  
    'voice_recovery': VoiceGuidedRecoveryMode,  # 새로운 음성 가이드 사후대처
    # 'consultation': ConsultationMode
}

def get_mode_class(mode_name: str):
    """모드 이름으로 클래스 반환"""
    return MODE_REGISTRY.get(mode_name)

def get_available_modes():
    """사용 가능한 모드 목록 반환"""
    return list(MODE_REGISTRY.keys())

def get_mode_info():
    """모드 정보 반환"""
    info = {}
    for name, mode_class in MODE_REGISTRY.items():
        # 임시 인스턴스로 정보 추출 (실제로는 초기화 안함)
        info[name] = {
            'class': mode_class.__name__,
            'description': f"{name} 모드",
            'available': True
        }
    return info

__all__ = [
    'BaseMode', 
    'ModeState',
    'DetectionMode', 
    'PreventionMode', 
    'PostIncidentMode', 
    'ConsultationMode',
    'MODE_REGISTRY',
    'get_mode_class',
    'get_available_modes',
    'get_mode_info'
]