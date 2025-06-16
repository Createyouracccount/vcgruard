"""
VoiceGuard AI - 운영 모드 패키지 (수정 버전)
중복 제거 및 구조 정리
"""

# 모드 클래스들은 modes 패키지에서 import
from app.modes.base_mode import BaseMode, ModeState
from app.modes.detection_mode import DetectionMode
from app.modes.prevention_mode import PreventionMode
from app.modes.post_incident_mode import PostIncidentMode
from app.modes.consultation_mode import ConsultationMode

# 모드 팩토리 (업데이트)
MODE_REGISTRY = {
    'prevention': PreventionMode,
    'detection': DetectionMode,
    'post_incident': PostIncidentMode, 
    'consultation': ConsultationMode
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
            'description': mode_descriptions[name],
            'available': True,
            'features': _get_mode_features(name)
        }
    return info

def _get_mode_features(mode_name: str) -> list:
    """모드별 특징 반환"""
    features = {
        'prevention': [
            '보이스피싱 수법 학습',
            '실전 시나리오 훈련',
            '지식 퀴즈',
            '개인별 진도 관리'
        ],
        'detection': [
            '실시간 텍스트 분석',
            'AI 기반 위험도 평가',
            '8가지 사기 유형 탐지',
            '즉시 경고 및 대응 안내'
        ],
        'post_incident': [
            '금융감독원 공식 절차',
            '단계별 체크리스트',
            '피해금 환급 안내',
            '명의도용 확인',
            '개인정보 보호 조치'
        ],
        'consultation': [
            '자주 묻는 질문 답변',
            '상황별 대처법 안내',
            '관련 기관 연락처',
            '예방 수칙 제공'
        ]
    }
    return features.get(mode_name, [])

# 모드 추천 시스템
def recommend_mode_for_situation(situation: str) -> str:
    """상황에 따른 모드 추천"""
    
    situation_lower = situation.lower()
    
    # 피해를 이미 당한 경우
    if any(keyword in situation_lower for keyword in 
           ['당했', '송금했', '속았', '피해', '이체했', '빼앗겼']):
        return 'post_incident'
    
    # 의심스러운 통화를 받고 있는 경우
    elif any(keyword in situation_lower for keyword in 
             ['지금', '전화', '말하고있', '통화중', '확인해달라']):
        return 'detection'
    
    # 학습하고 싶은 경우
    elif any(keyword in situation_lower for keyword in 
             ['배우고', '공부', '학습', '알고싶', '훈련']):
        return 'prevention'
    
    # 질문이 있는 경우
    elif any(keyword in situation_lower for keyword in 
             ['궁금', '질문', '문의', '물어보고']):
        return 'consultation'
    
    # 기본값
    else:
        return 'prevention'

def get_emergency_guidance() -> str:
    """긴급 상황 가이드"""
    return """
🚨 긴급 상황 대처법

📞 즉시 연락할 곳:
• 112 (경찰청) - 보이스피싱 신고
• 1332 (금융감독원) - 금융피해 신고
• 해당 은행 고객센터 - 지급정지 신청

⚡ 즉시 해야 할 일:
1. 통화 중이라면 즉시 끊기
2. 송금했다면 은행에 지급정지 신청
3. 개인정보 제공했다면 관련 기관에 신고
4. 앱 설치했다면 휴대폰 초기화

🛡️ 절대 하지 말 것:
• 추가 개인정보 제공
• 더 이상의 송금
• 의심스러운 링크 클릭
• 사기범과의 계속 연락

💡 VoiceGuard 사후대처 모드를 이용하여
   체계적인 대응 절차를 따라하세요!
"""

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
    'get_mode_info',
    'recommend_mode_for_situation',
    'get_emergency_guidance'
]