"""
profile-build Skill
Profile Agent로부터 입력받은 사용자 정보를 검증하고, 
표준 JSON 스키마로 정규화하여 파일로 저장합니다.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple, Optional, Any


class ProfileBuildSkill:
    """프로필 생성 및 저장 스킬"""
    
    def __init__(self, profiles_dir: str = "./data/profiles"):
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
    
    def execute(self, input_data: Dict[str, Any], user_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        스킬 메인 실행
        
        Args:
            input_data: Profile Agent로부터 받은 입력 데이터
            user_id: 생성된 user_id (user_YYYYMMDD_###)
        
        Returns:
            (성공 여부, 메시지, 생성된 프로필 JSON)
        """
        # 1. 입력 데이터 재검증
        is_valid, error_msg = self._validate_input(input_data)
        if not is_valid:
            return False, f"❌ 입력 검증 실패: {error_msg}", None
        
        # 2. 기존 프로필 확인 (수정인 경우)
        existing_profile = None
        existing_file = None
        email = input_data.get("email")
        
        existing_file = self._find_existing_profile(email)
        if existing_file:
            try:
                with open(existing_file, 'r', encoding='utf-8') as f:
                    existing_profile = json.load(f)
            except (json.JSONDecodeError, IOError):
                existing_profile = None
        
        # 3. JSON 스키마 생성
        profile_json = self._create_schema(input_data, user_id, existing_profile)
        
        # 4. 파일 저장
        success, save_msg = self._save_profile(profile_json, user_id, existing_file)
        if not success:
            return False, save_msg, None
        
        return True, save_msg, profile_json
    
    def _validate_input(self, input_data: Dict) -> Tuple[bool, str]:
        """입력 데이터 재검증"""
        required_fields = ["name", "email", "school", "major", "year", "report_time"]
        
        for field in required_fields:
            if field not in input_data or not input_data[field]:
                return False, f"필수 필드 누락: {field}"
        
        # 이메일 형식 재확인
        if "@" not in input_data.get("email", ""):
            return False, "이메일 형식 오류"
        
        # 배열 필드 확인
        for field in ["interests", "positions", "activity_types"]:
            if field not in input_data:
                input_data[field] = []
            if not isinstance(input_data[field], list):
                return False, f"{field}는 배열이어야 합니다."
        
        if "regions" not in input_data:
            input_data["regions"] = []
        if not isinstance(input_data["regions"], list):
            return False, "regions는 배열이어야 합니다."
        
        return True, ""
    
    def _find_existing_profile(self, email: str) -> Optional[Path]:
        """email로 기존 프로필 찾기"""
        for profile_file in self.profiles_dir.glob("user_profile_*.json"):
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get("basic_info", {}).get("email") == email:
                        return profile_file
            except (json.JSONDecodeError, IOError):
                continue
        
        return None
    
    def _create_schema(self, input_data: Dict, user_id: str, 
                       existing_profile: Optional[Dict]) -> Dict:
        """표준 JSON 스키마 생성"""
        now = datetime.now().isoformat(timespec='seconds')
        
        # 버전 계산
        if existing_profile:
            version = existing_profile.get("metadata", {}).get("version", 1) + 1
            created_at = existing_profile.get("metadata", {}).get("created_at")
        else:
            version = 1
            created_at = now
        
        profile = {
            "user_id": user_id,
            "basic_info": {
                "name": input_data.get("name"),
                "email": input_data.get("email"),
                "school": input_data.get("school"),
                "major": input_data.get("major"),
                "year": input_data.get("year")
            },
            "interests": {
                "fields": input_data.get("interests", []),
                "keywords_base": input_data.get("interests", [])
            },
            "career_goal": {
                "positions": input_data.get("positions", []),
                "skills": []
            },
            "preferences": {
                "activity_types": input_data.get("activity_types", []),
                "regions": input_data.get("regions", []),
                "available_hours_per_week": input_data.get("available_hours_per_week")
            },
            "availability": {
                "report_time": input_data.get("report_time"),
                "timezone": "Asia/Seoul"
            },
            "metadata": {
                "created_at": created_at,
                "updated_at": now,
                "version": version,
                "source": "profile_agent_onboarding"
            }
        }
        
        return profile
    
    def _save_profile(self, profile_json: Dict, user_id: str, 
                      existing_file: Optional[Path]) -> Tuple[bool, str]:
        """프로필 JSON 파일 저장"""
        try:
            if existing_file:
                # 기존 파일 업데이트
                file_path = existing_file
                action = "수정"
            else:
                # 새 파일 생성
                file_path = self.profiles_dir / f"user_profile_{user_id}.json"
                action = "생성"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(profile_json, f, ensure_ascii=False, indent=2)
            
            msg = f"✅ 프로필 {action} 완료: {file_path.name}"
            return True, msg
        
        except IOError as e:
            return False, f"❌ 파일 저장 실패: {e}"
    
    def load_profile(self, user_id: str) -> Optional[Dict]:
        """프로필 로드"""
        file_path = self.profiles_dir / f"user_profile_{user_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None


# 단독 실행 테스트용
if __name__ == "__main__":
    # 테스트 데이터
    test_input = {
        "name": "최기범",
        "email": "test@example.com",
        "school": "강원대학교",
        "major": "AI융합학과",
        "year": "2학년",
        "interests": ["의료AI", "데이터 분석"],
        "positions": ["AI 개발자"],
        "activity_types": ["해커톤", "공모전"],
        "regions": ["온라인", "강원"],
        "available_hours_per_week": 5,
        "report_time": "08:00"
    }
    
    skill = ProfileBuildSkill()
    user_id = "user_20260702_001"
    
    success, msg, profile = skill.execute(test_input, user_id)
    print(msg)
    
    if success:
        print("\n생성된 프로필:")
        print(json.dumps(profile, ensure_ascii=False, indent=2))
