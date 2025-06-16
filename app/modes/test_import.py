try:
    from app.modes.post_incident_mode import PostIncidentMode
    print("✅ PostIncidentMode import 성공")
    print(f"📝 클래스: {PostIncidentMode}")
    print(f"📍 파일: {PostIncidentMode.__module__}")
except Exception as e:
    print(f"❌ Import 실패: {e}")