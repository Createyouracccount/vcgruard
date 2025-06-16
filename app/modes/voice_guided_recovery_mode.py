"""
VoiceGuard AI - 음성 가이드 사후대처 모드
실시간 음성 인식을 통한 보이스피싱 피해 사후대처 지원
금융감독원 공식 절차 기반

파일 위치: app/modes/voice_guided_recovery_mode.py
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from .base_mode import BaseMode, ModeState

logger = logging.getLogger(__name__)

class RecoveryStage(Enum):
    """사후대처 단계"""
    SITUATION_ASSESSMENT = "상황_평가"
    EMERGENCY_REPORTING = "긴급_신고"
    PERSONAL_INFO_PROTECTION = "개인정보_보호"
    IDENTITY_THEFT_CHECK = "명의도용_확인"
    LEGAL_PROCEDURES = "법적_절차"
    FOLLOW_UP = "사후_관리"

class DamageType(Enum):
    """피해 유형"""
    MONEY_TRANSFER = "금전_송금"
    PERSONAL_INFO_LEAK = "개인정보_유출"
    MALICIOUS_APP = "악성앱_설치"
    ACCOUNT_INFO_PROVIDED = "계좌정보_제공"
    CARD_INFO_PROVIDED = "카드정보_제공"
    ID_INFO_PROVIDED = "신분증정보_제공"

@dataclass
class RecoveryStep:
    """회복 단계 정보"""
    step_id: str
    title: str
    description: str
    voice_guidance: str
    action_required: bool
    completion_phrase: List[str]  # 사용자가 완료했다고 말할 수 있는 표현들
    next_step: Optional[str] = None
    
class VoiceGuidedRecoveryMode(BaseMode):
    """음성 가이드 사후대처 모드 - 금융감독원 공식 절차 기반"""
    
    @property
    def mode_name(self) -> str:
        return "음성 가이드 사후대처"
    
    @property
    def mode_description(self) -> str:
        return "음성 인식을 통한 실시간 보이스피싱 피해 사후대처 지원 (금융감독원 기준)"
    
    def _load_mode_config(self) -> Dict[str, Any]:
        """사후대처 모드 설정"""
        return {
            'voice_guided': True,
            'step_by_step': True,
            'official_procedures': True,
            'real_time_support': True,
            'voice_commands': True,
            'progress_tracking': True
        }
    
    async def _initialize_mode(self) -> bool:
        """음성 가이드 사후대처 모드 초기화"""
        
        try:
            # 피해 상황 데이터
            self.victim_data = {
                'damage_types': [],
                'financial_loss': 0,
                'time_of_incident': None,
                'current_stage': RecoveryStage.SITUATION_ASSESSMENT,
                'completed_steps': set(),
                'contact_numbers': {},
                'evidence_collected': []
            }
            
            # 음성 명령 인식 패턴
            self.voice_commands = {
                'yes': ['예', '네', '맞습니다', '그렇습니다', '완료했습니다', '했습니다', '됐습니다'],
                'no': ['아니요', '아닙니다', '안했습니다', '못했습니다', '안됐습니다'],
                'help': ['도움말', '도와주세요', '어떻게', '모르겠습니다', '설명해주세요'],
                'repeat': ['다시', '한번더', '다시말해주세요', '다시설명해주세요'],
                'skip': ['건너뛰기', '넘어가기', '다음', '스킵'],
                'emergency': ['긴급', '응급', '급해요', '빨리']
            }
            
            # 금융감독원 공식 절차 단계들
            self.recovery_steps = self._initialize_recovery_steps()
            
            # STT 서비스 초기화 (음성 인식용)
            try:
                from services.simple_stt_service import SttService
                self.stt_service = SttService(
                    client_id="demo",
                    client_secret="demo",
                    transcript_callback=self._on_voice_input
                )
            except ImportError:
                self.stt_service = None
                logger.warning("STT 서비스를 사용할 수 없습니다. 텍스트 입력을 사용합니다.")
            
            # 음성 입력 큐
            self.voice_queue = asyncio.Queue(maxsize=20)
            
            logger.info("✅ 음성 가이드 사후대처 모드 초기화 완료")
            return True
            
        except Exception as e:
            logger.error(f"음성 가이드 사후대처 모드 초기화 실패: {e}")
            return False
    
    def _initialize_recovery_steps(self) -> Dict[str, RecoveryStep]:
        """금융감독원 공식 절차 기반 회복 단계 초기화"""
        
        steps = {}
        
        # 1단계: 상황 평가
        steps['situation_assessment'] = RecoveryStep(
            step_id='situation_assessment',
            title='피해 상황 평가',
            description='어떤 유형의 피해를 당하셨는지 확인합니다',
            voice_guidance='안녕하세요. VoiceGuard 사후대처 지원 시스템입니다. 먼저 어떤 피해를 당하셨는지 말씀해주세요. 돈을 송금하셨나요, 개인정보를 알려주셨나요, 아니면 앱을 설치하셨나요?',
            action_required=True,
            completion_phrase=['평가완료', '확인완료'],
            next_step='emergency_reporting'
        )
        
        # 2단계: 긴급 신고 (금융감독원 공식 절차)
        steps['emergency_reporting'] = RecoveryStep(
            step_id='emergency_reporting',
            title='긴급 신고 및 지급정지',
            description='112, 1332, 관련 금융회사에 즉시 신고',
            voice_guidance='지금 즉시 세 곳에 전화해야 합니다. 첫째, 112 경찰청에 신고하세요. 둘째, 1332 금융감독원에 신고하세요. 셋째, 송금한 은행 고객센터에 지급정지를 신청하세요. 각각 신고가 완료되면 완료했다고 말씀해주세요.',
            action_required=True,
            completion_phrase=['신고완료', '지급정지완료', '모두완료'],
            next_step='personal_info_protection'
        )
        
        # 3단계: 개인정보 보호 조치
        steps['personal_info_protection'] = RecoveryStep(
            step_id='personal_info_protection',
            title='개인정보 보호 조치',
            description='공동인증서 재발급 및 악성앱 삭제',
            voice_guidance='이제 개인정보 보호 조치를 시작합니다. 첫째, 기존 공동인증서를 삭제하고 재발급받으세요. 둘째, 휴대폰을 초기화하거나 통신사에 방문해서 악성앱을 삭제하세요. 완료되면 말씀해주세요.',
            action_required=True,
            completion_phrase=['인증서완료', '휴대폰완료', '보호조치완료'],
            next_step='info_exposure_registration'
        )
        
        # 4단계: 개인정보 노출사실 등록
        steps['info_exposure_registration'] = RecoveryStep(
            step_id='info_exposure_registration',
            title='개인정보 노출사실 등록',
            description='금융감독원 개인정보노출자 사고예방시스템 등록',
            voice_guidance='이제 금융감독원 개인정보노출자 사고예방시스템에 등록해야 합니다. pd.fss.or.kr에 접속해서 휴대폰 인증 후 개인정보 노출 사실을 등록하세요. 이렇게 하면 신규 계좌개설과 카드발급이 제한됩니다. 완료되면 말씀해주세요.',
            action_required=True,
            completion_phrase=['등록완료', '시스템등록완료'],
            next_step='account_check'
        )
        
        # 5단계: 계좌 개설 여부 조회
        steps['account_check'] = RecoveryStep(
            step_id='account_check',
            title='명의도용 계좌 확인',
            description='본인 명의로 무단 개설된 계좌 확인',
            voice_guidance='이제 명의도용으로 개설된 계좌가 있는지 확인해보겠습니다. www.payinfo.or.kr에 접속해서 공동인증서로 로그인하세요. 내계좌한눈에에서 모든 계좌를 확인하고, 모르는 계좌가 있으면 즉시 해당 은행에 신고하세요. 확인이 완료되면 말씀해주세요.',
            action_required=True,
            completion_phrase=['계좌확인완료', '조회완료'],
            next_step='phone_check'
        )
        
        # 6단계: 휴대폰 개설 여부 조회
        steps['phone_check'] = RecoveryStep(
            step_id='phone_check',
            title='명의도용 휴대폰 확인',
            description='본인 명의로 무단 개통된 휴대폰 확인',
            voice_guidance='이제 명의도용으로 개통된 휴대폰이 있는지 확인해보겠습니다. www.msafer.or.kr에 접속해서 가입사실현황조회를 하세요. 모르는 휴대폰이 있으면 즉시 해당 통신사에 회선 해지를 신청하세요. 그리고 가입제한 서비스로 신규 개통을 차단하세요. 완료되면 말씀해주세요.',
            action_required=True,
            completion_phrase=['휴대폰확인완료', '차단완료'],
            next_step='legal_procedures'
        )
        
        # 7단계: 법적 절차
        steps['legal_procedures'] = RecoveryStep(
            step_id='legal_procedures',
            title='피해금 환급 신청',
            description='사건사고사실확인원 발급 및 피해금 환급 신청',
            voice_guidance='마지막으로 피해금 환급을 신청해보겠습니다. 가까운 경찰서나 사이버수사대에 방문해서 사건사고사실확인원을 발급받으세요. 그리고 지급정지를 신청한 은행 영업점에 3일 이내에 제출해서 피해금 환급을 신청하세요. 완료되면 말씀해주세요.',
            action_required=True,
            completion_phrase=['서류발급완료', '환급신청완료', '모든절차완료'],
            next_step='follow_up'
        )
        
        # 8단계: 사후 관리
        steps['follow_up'] = RecoveryStep(
            step_id='follow_up',
            title='사후 관리 및 예방',
            description='지속적인 모니터링 및 재발 방지',
            voice_guidance='모든 공식 절차가 완료되었습니다. 앞으로 정기적으로 계좌와 신용정보를 확인하시고, 의심스러운 연락이 오면 즉시 차단하세요. VoiceGuard가 항상 여러분의 안전을 지켜드리겠습니다.',
            action_required=False,
            completion_phrase=['이해했습니다', '감사합니다'],
            next_step=None
        )
        
        return steps
    
    async def _run_mode_logic(self):
        """음성 가이드 사후대처 메인 로직"""
        
        print("🚨 VoiceGuard 음성 가이드 사후대처 시스템")
        print("📞 실시간 음성 인식으로 단계별 안내를 받으실 수 있습니다")
        print("🔊 시스템이 말하는 대로 따라하시면 됩니다")
        print("=" * 60)
        
        # 환영 메시지 및 음성 안내
        welcome_message = "안녕하세요. VoiceGuard 사후대처 지원 시스템입니다. 보이스피싱 피해를 당하셨군요. 걱정하지 마세요. 금융감독원 공식 절차에 따라 단계별로 안내해드리겠습니다. 제가 말하는 대로 따라하시면 됩니다."
        
        await self._speak_and_wait(welcome_message)
        
        # STT 서비스 시작
        if self.stt_service:
            self.stt_service.start()
            print("🎤 음성 인식이 시작되었습니다. 말씀해주세요.")
        else:
            print("⌨️ 텍스트 입력 모드로 진행합니다.")
        
        # 단계별 진행
        current_step_id = 'situation_assessment'
        
        while current_step_id and self.is_running:
            try:
                current_step = self.recovery_steps[current_step_id]
                success = await self._execute_recovery_step(current_step)
                
                if success:
                    # 다음 단계로 진행
                    current_step_id = current_step.next_step
                    if current_step_id:
                        transition_message = f"좋습니다. 이제 다음 단계로 넘어가겠습니다."
                        await self._speak_and_wait(transition_message, wait_time=2)
                else:
                    # 현재 단계 재시도 또는 중단
                    retry_message = "단계를 다시 진행하시겠습니까? 예 또는 아니오로 답해주세요."
                    response = await self._get_voice_response(retry_message)
                    
                    if not self._is_positive_response(response):
                        break
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"단계 실행 오류: {e}")
                error_message = "단계 진행 중 오류가 발생했습니다. 다시 시도하겠습니다."
                await self._speak_and_wait(error_message)
        
        # 완료 메시지
        completion_message = "모든 사후대처 절차가 완료되었습니다. 빠른 회복을 위해 추가 조치사항들도 꼭 실행해주세요. VoiceGuard가 함께 하겠습니다."
        await self._speak_and_wait(completion_message)
        
        # STT 서비스 정리
        if self.stt_service:
            self.stt_service.stop()
    
    async def _execute_recovery_step(self, step: RecoveryStep) -> bool:
        """개별 회복 단계 실행"""
        
        print(f"\n{'='*50}")
        print(f"🔄 {step.title}")
        print(f"📝 {step.description}")
        print(f"{'='*50}")
        
        # 음성 안내 시작
        await self._speak_and_wait(step.voice_guidance)
        
        if not step.action_required:
            # 행동이 필요하지 않은 단계 (정보 제공만)
            await asyncio.sleep(3)
            return True
        
        # 사용자 행동 완료 대기
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # 특별한 단계별 처리
                if step.step_id == 'situation_assessment':
                    success = await self._handle_situation_assessment()
                elif step.step_id == 'emergency_reporting':
                    success = await self._handle_emergency_reporting()
                else:
                    # 일반적인 완료 확인
                    success = await self._wait_for_step_completion(step)
                
                if success:
                    self.victim_data['completed_steps'].add(step.step_id)
                    completion_message = f"✅ {step.title} 단계가 완료되었습니다."
                    await self._speak_and_wait(completion_message)
                    return True
                else:
                    if attempt < max_attempts - 1:
                        retry_message = f"다시 한 번 시도해보겠습니다. {step.voice_guidance}"
                        await self._speak_and_wait(retry_message)
            
            except Exception as e:
                logger.error(f"단계 실행 오류: {e}")
                if attempt == max_attempts - 1:
                    error_message = "이 단계를 완료하는데 어려움이 있습니다. 직접 전화로 도움을 요청하시기 바랍니다."
                    await self._speak_and_wait(error_message)
                    return False
        
        return False
    
    async def _handle_situation_assessment(self) -> bool:
        """상황 평가 단계 처리"""
        
        # 피해 유형 확인
        damage_questions = [
            ("돈을 송금하거나 이체하셨나요?", DamageType.MONEY_TRANSFER),
            ("개인정보나 신분증 정보를 알려주셨나요?", DamageType.PERSONAL_INFO_LEAK),
            ("의심스러운 앱을 설치하셨나요?", DamageType.MALICIOUS_APP),
            ("계좌번호나 비밀번호를 알려주셨나요?", DamageType.ACCOUNT_INFO_PROVIDED),
            ("카드번호나 카드 정보를 알려주셨나요?", DamageType.CARD_INFO_PROVIDED)
        ]
        
        for question, damage_type in damage_questions:
            response = await self._get_voice_response(question)
            if self._is_positive_response(response):
                self.victim_data['damage_types'].append(damage_type)
        
        if not self.victim_data['damage_types']:
            clarification = "혹시 다른 형태의 피해를 당하셨다면 자세히 말씀해주세요."
            await self._get_voice_response(clarification)
            # 기본적으로 개인정보 유출로 분류
            self.victim_data['damage_types'].append(DamageType.PERSONAL_INFO_LEAK)
        
        # 금전 피해가 있는 경우 금액 확인
        if DamageType.MONEY_TRANSFER in self.victim_data['damage_types']:
            amount_question = "송금하신 금액이 얼마인지 말씀해주세요. 예를 들어, 백만원, 오십만원 이렇게 말씀해주세요."
            amount_response = await self._get_voice_response(amount_question)
            # 금액 파싱 (간단한 버전)
            self.victim_data['financial_loss'] = self._parse_amount(amount_response)
        
        # 발생 시간 확인
        time_question = "피해가 언제 발생했나요? 방금 전, 오늘, 어제, 며칠 전 중에서 말씀해주세요."
        time_response = await self._get_voice_response(time_question)
        self.victim_data['time_of_incident'] = self._parse_time(time_response)
        
        return True
    
    async def _handle_emergency_reporting(self) -> bool:
        """긴급 신고 단계 처리"""
        
        emergency_contacts = [
            ("112", "경찰청", "보이스피싱 피해 신고"),
            ("1332", "금융감독원", "금융 피해 신고"),
        ]
        
        # 송금 피해가 있는 경우 은행 연락처도 추가
        if DamageType.MONEY_TRANSFER in self.victim_data['damage_types']:
            bank_question = "어느 은행으로 송금하셨나요? 은행 이름을 말씀해주세요."
            bank_response = await self._get_voice_response(bank_question)
            bank_info = self._get_bank_contact(bank_response)
            if bank_info:
                emergency_contacts.append(bank_info)
        
        completed_calls = 0
        for number, institution, purpose in emergency_contacts:
            call_instruction = f"이제 {number}번 {institution}에 전화해서 {purpose}를 하세요. 통화가 끝나면 완료했다고 말씀해주세요."
            await self._speak_and_wait(call_instruction)
            
            # 완료 대기 (더 긴 시간 허용)
            completion_response = await self._get_voice_response(
                "통화가 완료되셨나요?", 
                timeout=300  # 5분 대기
            )
            
            if self._is_positive_response(completion_response):
                completed_calls += 1
                self.victim_data['contact_numbers'][institution] = number
                confirmation = f"✅ {institution} 신고가 완료되었습니다."
                await self._speak_and_wait(confirmation)
            else:
                retry_message = f"⚠️ {institution} 신고가 매우 중요합니다. 꼭 완료해주세요."
                await self._speak_and_wait(retry_message)
        
        return completed_calls >= 2  # 최소 2곳 이상 신고 완료
    
    async def _wait_for_step_completion(self, step: RecoveryStep) -> bool:
        """단계 완료 대기"""
        
        completion_question = f"{step.title} 단계를 완료하셨나요? 완료했다고 말씀해주세요."
        response = await self._get_voice_response(completion_question, timeout=300)
        
        # 완료 표현 확인
        for phrase in step.completion_phrase:
            if phrase in response:
                return True
        
        # 긍정적 응답 확인
        return self._is_positive_response(response)
    
    def _on_voice_input(self, text: str):
        """STT 콜백 - 음성 입력 처리"""
        if text and text.strip():
            try:
                loop = asyncio.get_running_loop()
                loop.call_soon_threadsafe(self.voice_queue.put_nowait, text.strip())
            except Exception as e:
                logger.error(f"음성 입력 처리 오류: {e}")
    
    async def _get_voice_response(self, question: str, timeout: float = 30.0) -> str:
        """음성 응답 받기"""
        
        await self._speak_and_wait(question)
        
        try:
            if self.stt_service:
                # 음성 인식 모드
                response = await asyncio.wait_for(
                    self.voice_queue.get(),
                    timeout=timeout
                )
            else:
                # 텍스트 입력 모드
                print("💬 답변을 입력하세요: ", end="")
                response = await asyncio.wait_for(
                    asyncio.to_thread(input),
                    timeout=timeout
                )
            
            print(f"👤 사용자: {response}")
            return response.lower()
            
        except asyncio.TimeoutError:
            timeout_message = "응답 시간이 초과되었습니다. 도움이 필요하시면 도움말이라고 말씀해주세요."
            await self._speak_and_wait(timeout_message)
            return ""
        except Exception as e:
            logger.error(f"음성 응답 받기 오류: {e}")
            return ""
    
    async def _speak_and_wait(self, text: str, wait_time: float = 1.0):
        """음성 출력 후 대기"""
        
        print(f"🤖 VoiceGuard: {text}")
        
        # TTS 출력
        try:
            await self._speak(text)
        except Exception as e:
            logger.warning(f"TTS 출력 실패: {e}")
        
        # 약간의 대기 시간
        await asyncio.sleep(wait_time)
    
    def _is_positive_response(self, response: str) -> bool:
        """긍정적 응답인지 확인"""
        positive_patterns = self.voice_commands['yes']
        return any(pattern in response for pattern in positive_patterns)
    
    def _parse_amount(self, response: str) -> int:
        """금액 파싱 (간단한 버전)"""
        
        amount_mapping = {
            '만원': 10000,
            '십만원': 100000,
            '백만원': 1000000,
            '천만원': 10000000,
            '억': 100000000
        }
        
        for korean_amount, value in amount_mapping.items():
            if korean_amount in response:
                # 숫자 추출 시도
                numbers = ['일', '이', '삼', '사', '오', '육', '칠', '팔', '구']
                multiplier = 1
                for i, num in enumerate(numbers, 1):
                    if num in response:
                        multiplier = i
                        break
                
                return value * multiplier
        
        return 0  # 파싱 실패시 0 반환
    
    def _parse_time(self, response: str) -> str:
        """시간 파싱"""
        
        if any(word in response for word in ['방금', '조금전', '금방']):
            return 'recent'
        elif '오늘' in response:
            return 'today'
        elif '어제' in response:
            return 'yesterday'
        elif any(word in response for word in ['며칠', '몇일', '일주일']):
            return 'days_ago'
        else:
            return 'unknown'
    
    def _get_bank_contact(self, bank_name: str) -> Optional[tuple]:
        """은행 연락처 정보 반환"""
        
        bank_contacts = {
            '국민': ('1588-9999', '국민은행', '지급정지 신청'),
            '신한': ('1599-8000', '신한은행', '지급정지 신청'),
            '우리': ('1599-0800', '우리은행', '지급정지 신청'),
            '하나': ('1599-1111', '하나은행', '지급정지 신청'),
            '농협': ('1661-8100', 'NH농협은행', '지급정지 신청'),
            '기업': ('1588-2588', 'IBK기업은행', '지급정지 신청'),
            'KB': ('1588-9999', 'KB국민은행', '지급정지 신청'),
        }
        
        for key, contact_info in bank_contacts.items():
            if key in bank_name:
                return contact_info
        
        return ('해당은행고객센터', '송금은행', '지급정지 신청')
    
    async def _cleanup_mode(self):
        """음성 가이드 사후대처 모드 정리"""
        
        try:
            # STT 서비스 정리
            if self.stt_service:
                self.stt_service.stop()
            
            # 음성 큐 정리
            while not self.voice_queue.empty():
                try:
                    self.voice_queue.get_nowait()
                except:
                    break
            
            # 진행 상황 요약 저장
            summary = {
                'session_id': self.session_id,
                'completion_time': datetime.now(),
                'damage_types': [dt.value for dt in self.victim_data['damage_types']],
                'completed_steps': list(self.victim_data['completed_steps']),
                'financial_loss': self.victim_data['financial_loss'],
                'contacts_made': self.victim_data['contact_numbers'],
                'time_of_incident': self.victim_data['time_of_incident']
            }
            
            logger.info(f"음성 가이드 사후대처 세션 완료: {summary}")
            
            # 최종 안내 메시지
            final_message = """
🎯 사후대처 세션이 완료되었습니다.

📞 추가 연락처:
• 경찰청: 112
• 금융감독원: 1332  
• 대검찰청 사이버수사과: 1301

🌐 유용한 웹사이트:
• 개인정보노출자 사고예방: pd.fss.or.kr
• 계좌정보통합관리: www.payinfo.or.kr
• 명의도용방지서비스: www.msafer.or.kr

⚠️ 중요 안내:
• 피해금 환급까지 2-3주 소요될 수 있습니다
• 의심스러운 연락이 오면 즉시 차단하세요
• 정기적으로 계좌와 신용정보를 확인하세요

💪 VoiceGuard가 항상 여러분의 안전을 지켜드리겠습니다!
            """
            
            print(final_message)
            
        except Exception as e:
            logger.error(f"음성 가이드 사후대처 모드 정리 오류: {e}")
    
    def get_recovery_progress(self) -> Dict[str, Any]:
        """사후대처 진행 상황 조회"""
        
        total_steps = len(self.recovery_steps)
        completed_count = len(self.victim_data['completed_steps'])
        
        return {
            "session_id": self.session_id,
            "victim_data": self.victim_data.copy(),
            "progress": {
                "total_steps": total_steps,
                "completed_steps": completed_count,
                "completion_rate": completed_count / total_steps if total_steps > 0 else 0,
                "current_stage": self.victim_data['current_stage'].value
            },
            "recovery_steps": {
                step_id: {
                    "title": step.title,
                    "completed": step_id in self.victim_data['completed_steps']
                }
                for step_id, step in self.recovery_steps.items()
            }
        }
    
    def get_emergency_contacts(self) -> Dict[str, str]:
        """긴급 연락처 조회"""
        
        return {
            "경찰청_보이스피싱신고": "112",
            "금융감독원_금융피해신고": "1332",
            "대검찰청_사이버수사과": "1301",
            "한국인터넷진흥원_인터넷신고센터": "privacy.go.kr",
            "개인정보보호위원회": "privacy.go.kr",
            "소비자분쟁조정위원회": "www.ccourt.go.kr"
        }
    
    def get_official_websites(self) -> Dict[str, str]:
        """공식 웹사이트 목록"""
        
        return {
            "개인정보노출자_사고예방시스템": "https://pd.fss.or.kr",
            "계좌정보통합관리서비스": "https://www.payinfo.or.kr", 
            "명의도용방지서비스": "https://www.msafer.or.kr",
            "금융감독원_보이스피싱지킴이": "https://www.fss.or.kr",
            "금융소비자정보_포털": "https://finlife.fss.or.kr",
            "한국인터넷진흥원": "https://www.kisa.or.kr",
            "대검찰청": "https://www.spo.go.kr",
            "경찰청": "https://www.police.go.kr"
        }
    
    def generate_action_checklist(self) -> List[Dict[str, Any]]:
        """실행 체크리스트 생성"""
        
        checklist = []
        
        # 긴급 대응 (즉시)
        checklist.append({
            "category": "긴급_대응",
            "priority": "즉시",
            "actions": [
                "112 경찰청 신고",
                "1332 금융감독원 신고", 
                "송금은행 고객센터 지급정지 신청",
                "가족/지인에게 상황 알림"
            ]
        })
        
        # 개인정보 보호 (1일 이내)
        checklist.append({
            "category": "개인정보_보호",
            "priority": "1일_이내",
            "actions": [
                "공동인증서 삭제 및 재발급",
                "휴대폰 초기화 또는 악성앱 삭제",
                "모든 금융앱 재설치",
                "비밀번호 전체 변경"
            ]
        })
        
        # 시스템 등록 (3일 이내)
        checklist.append({
            "category": "시스템_등록",
            "priority": "3일_이내", 
            "actions": [
                "개인정보노출자 사고예방시스템 등록 (pd.fss.or.kr)",
                "계좌개설 여부 조회 (www.payinfo.or.kr)",
                "휴대폰개설 여부 조회 (www.msafer.or.kr)",
                "의심계좌/휴대폰 해지 신청"
            ]
        })
        
        # 법적 절차 (1주 이내)
        checklist.append({
            "category": "법적_절차",
            "priority": "1주_이내",
            "actions": [
                "경찰서/사이버수사대 방문",
                "사건사고사실확인원 발급",
                "은행 영업점 피해금환급 신청",
                "관련 서류 제출"
            ]
        })
        
        # 사후 관리 (지속적)
        checklist.append({
            "category": "사후_관리", 
            "priority": "지속적",
            "actions": [
                "정기적 계좌 모니터링",
                "신용정보 확인",
                "의심스러운 연락 차단",
                "가족 대상 예방교육"
            ]
        })
        
        return checklist
    
    async def provide_personalized_guidance(self) -> str:
        """개인화된 추가 안내"""
        
        damage_types = self.victim_data['damage_types']
        guidance_parts = []
        
        # 피해 유형별 맞춤 안내
        if DamageType.MONEY_TRANSFER in damage_types:
            guidance_parts.append("""
💰 금전 피해 특별 안내:
• 피해금 환급 성공률: 약 70-80%
• 환급 소요기간: 평균 2-3주
• 지급정지 신청이 가장 중요함
• 24시간 이내 신고시 환급 가능성 증가
            """)
        
        if DamageType.PERSONAL_INFO_LEAK in damage_types:
            guidance_parts.append("""
🔒 개인정보 유출 특별 안내:
• 즉시 관련 금융기관에 모니터링 강화 요청
• 6개월간 정기적으로 신용정보 확인
• 새로운 금융상품 가입시 주의
• 명의도용 가능성 지속 모니터링 필요
            """)
        
        if DamageType.MALICIOUS_APP in damage_types:
            guidance_parts.append("""
📱 악성앱 설치 특별 안내:
• 휴대폰 완전 초기화 권장
• 모든 금융앱 재설치 필수
• 루팅/탈옥 상태 확인 및 복구
• 보안앱 설치 (V3 Mobile, 알약M 등)
            """)
        
        # 시간 기반 긴급도
        time_guidance = ""
        if self.victim_data['time_of_incident'] == 'recent':
            time_guidance = """
⏰ 최근 피해 발생 - 긴급 대응 필요:
• 모든 절차를 24시간 이내 완료 권장
• 추가 피해 확산 방지가 최우선
• 실시간 계좌 모니터링 설정
            """
        
        return "\n".join(guidance_parts) + time_guidance
    
    def get_prevention_tips(self) -> List[str]:
        """재발 방지 팁"""
        
        return [
            "🔐 공공기관은 전화로 개인정보를 절대 요구하지 않습니다",
            "📞 의심스러운 전화는 즉시 끊고 공식 번호로 재확인하세요",
            "💳 금융정보는 공식 앱이나 웹사이트에서만 입력하세요",
            "📱 출처불명 앱은 절대 설치하지 마세요",
            "👨‍👩‍👧‍👦 가족 간 보이스피싱 예방 수칙을 공유하세요",
            "🚨 '긴급', '즉시' 등의 압박용어에 주의하세요",
            "💰 큰 금액 이체 전에는 반드시 가족과 상의하세요",
            "🔍 정기적으로 본인 명의 계좌/휴대폰을 확인하세요",
            "📚 최신 보이스피싱 수법을 지속적으로 학습하세요",
            "🛡️ VoiceGuard 같은 보안 시스템을 활용하세요"
        ]

# 사용 예제 및 테스트 함수
async def test_voice_guided_recovery():
    """음성 가이드 사후대처 모드 테스트"""
    
    print("🧪 음성 가이드 사후대처 모드 테스트")
    
    # 더미 서비스들로 테스트 환경 구성
    class DummyTTSService:
        async def text_to_speech_stream(self, text):
            yield b''  # 더미 오디오 데이터
    
    class DummyAudioManager:
        async def play_audio_stream(self, stream):
            async for chunk in stream:
                pass  # 더미 재생
    
    # 모드 인스턴스 생성
    mode = VoiceGuidedRecoveryMode(
        llm_manager=None,
        audio_manager=DummyAudioManager(),
        tts_service=DummyTTSService(),
        session_id="test_session"
    )
    
    # 초기화 테스트
    success = await mode._initialize_mode()
    print(f"✅ 초기화: {'성공' if success else '실패'}")
    
    # 단계 정보 출력
    print("\n📋 사후대처 단계들:")
    for step_id, step in mode.recovery_steps.items():
        print(f"  {step.step_id}: {step.title}")
    
    # 긴급 연락처 출력
    print("\n📞 긴급 연락처:")
    contacts = mode.get_emergency_contacts()
    for name, number in contacts.items():
        print(f"  {name}: {number}")
    
    # 체크리스트 출력
    print("\n📝 실행 체크리스트:")
    checklist = mode.generate_action_checklist()
    for item in checklist:
        print(f"  {item['category']} ({item['priority']}):")
        for action in item['actions']:
            print(f"    - {action}")
    
    print("\n🎯 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(test_voice_guided_recovery())