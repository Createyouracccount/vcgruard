"""
VoiceGuard AI - 운영 모드 패키지
모든 운영 모드를 통합 관리
"""

from app.modes.base_mode import BaseMode, ModeState
from app.modes.detection_mode import DetectionMode
from app.modes.prevention_mode import PreventionMode
from app.modes.post_incident_mode import PostIncidentMode
from app.modes.consultation_mode import ConsultationMode

from .voice_guided_recovery_mode import VoiceGuidedRecoveryMode

# 음성 가이드 모드가 있다면 추가 (없으면 주석 처리)
# from app.modes.voice_guided_recovery_mode import VoiceGuidedRecoveryMode

# 모드 팩토리
MODE_REGISTRY = {
    'prevention': PreventionMode,
    'detection': DetectionMode,
    'post_incident': PostIncidentMode,
    # 'consultation': ConsultationMode,
    'voice_recovery': VoiceGuidedRecoveryMode, 
}

def get_mode_class(mode_name: str):
    """모드 이름으로 클래스 반환"""
    return MODE_REGISTRY.get(mode_name)

def get_available_modes():
    """사용 가능한 모드 목록 반환"""
    return list(MODE_REGISTRY.keys())

def get_mode_info():
    """모드 정보 반환"""
    mode_descriptions = {
        'prevention': '🎓 예방 교육 - 보이스피싱 수법 학습 및 대응 훈련',
        'detection': '🔍 실시간 탐지 - 의심스러운 통화 내용 분석',
        'post_incident': '🚨 사후 대처 - 피해 발생 후 금융감독원 기준 체계적 대응',
        'consultation': '💬 상담 문의 - 보이스피싱 관련 질문 답변'
    }
    
    info = {}
    for name, mode_class in MODE_REGISTRY.items():
        info[name] = {
            'class': mode_class.__name__,
            'description': mode_descriptions.get(name, f"{name} 모드"),
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