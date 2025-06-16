"""
VoiceGuard AI - 상담 모드 (별도 파일)
"""

from app.modes.base_mode import BaseMode

class ConsultationMode(BaseMode):
    """상담 모드 - 보이스피싱 관련 질문 답변"""
    
    @property
    def mode_name(self) -> str:
        return "상담 문의"
    
    @property
    def mode_description(self) -> str:
        return "보이스피싱 관련 질문에 답변드립니다"
    
    def _load_mode_config(self):
        return {'interactive_qa': True, 'knowledge_base': True}
    
    async def _initialize_mode(self) -> bool:
        print("💬 상담 모드를 시작합니다.")
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

Q: 악성 앱을 설치했는데 어떻게 하나요?
A: 1) 즉시 휴대폰 초기화 또는 통신사 고객센터 방문
   2) 모든 금융 앱 재설치
   3) 비밀번호 전체 변경
   4) 공동인증서 재발급

Q: 돈을 송금했는데 되돌릴 수 있나요?
A: 1) 즉시 112 신고
   2) 1332 (금융감독원) 신고
   3) 해당 은행에 지급정지 신청
   4) 전기통신금융사기 피해 특별법에 따라 환급 가능

🔄 향후 AI 챗봇 기능이 추가될 예정입니다.
        """)
        
        input("\n계속하려면 Enter를 누르세요...")