import asyncio
from core.learning_enhanced_analyzer import LearningEnhancedAnalyzer
from core.llm_manager import llm_manager

async def test_learning():
    analyzer = LearningEnhancedAnalyzer(llm_manager)
    
    # 테스트 분석
    result = await analyzer.analyze_with_learning(
        "안녕하십니까. 금융감독원에서 연락드렸습니다."
    )
    
    print("🔍 테스트 결과:")
    print(f"  위험도: {result['final_risk_score']:.2f}")
    print(f"  Few-shot 적용: {result['few_shot_applied']}")
    
    # 학습 상태 확인
    status = analyzer.get_learning_status()
    print(f"📊 Few-shot 예시: {status['few_shot_pool_size']}")

if __name__ == "__main__":
    asyncio.run(test_learning())