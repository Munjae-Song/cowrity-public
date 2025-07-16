# Cowrity Ver. 0.1 - FactoryStat

다중 AI 언어모델을 활용한 텍스트 처리 도구

## 주요 기능

- **다중 AI 모델 지원**: Claude, Perplexity, Gemini, OpenAI
- **문장 다듬기**: 자연스럽고 읽기 쉬운 문장으로 개선
- **팩트 체크**: 사실 관계 검증 및 수정
- **토론 기능**: 비판적 분석과 다양한 시각 제공
- **사용자 목적별 맞춤형 응답**: 작가, 학생, 기자, 회사원 관점
- **자동 클립보드 복사**: 응답 자동 복사 기능
- **노션 업로드**: 클립보드 내용을 노션에 바로 업로드

## 설치 방법

### 1. 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. API 키 설정

1. `profile.env.example` 파일을 복사하여 `profile.env` 파일을 생성합니다:
   ```bash
   copy profile.env.example profile.env
   ```

2. `profile.env` 파일을 열고 실제 API 키를 입력합니다:
   ```
   CLAUDE_API_KEY=your_actual_claude_api_key
   PERPLEXITY_API_KEY=your_actual_perplexity_api_key
   GEMINI_API_KEY=your_actual_gemini_api_key
   OPENAI_API_KEY=your_actual_openai_api_key
   
   # 노션 업로드 기능을 사용하려면 추가로 설정
   NOTION_API_KEY=your_actual_notion_api_key
   NOTION_DATABASE_ID=your_actual_notion_database_id
   ```

### 3. 필요한 API 키 발급

- **Claude API**: [Anthropic Console](https://console.anthropic.com)
- **Perplexity API**: [Perplexity AI](https://perplexity.ai)
- **Gemini API**: [Google AI Studio](https://aistudio.google.com/app/apikey)
- **OpenAI API**: [OpenAI Platform](https://platform.openai.com/api-keys)
- **Notion API**: [Notion Developers](https://developers.notion.com)

## 사용 방법

```bash
python cowrity.py
```

## 노션 업로드 설정

노션 업로드 기능을 사용하려면 다음 단계를 따라 설정하세요:

1. [Notion Developers](https://developers.notion.com)에서 새 integration을 생성
2. Integration에서 API 키를 복사하여 `profile.env`의 `NOTION_API_KEY`에 입력
3. 노션에서 새 데이터베이스를 생성하거나 기존 데이터베이스 사용
4. 데이터베이스에 integration을 연결 (Share → Add people → 생성한 integration 선택)
5. 데이터베이스 URL에서 데이터베이스 ID를 복사하여 `profile.env`의 `NOTION_DATABASE_ID`에 입력
   - 예: `https://www.notion.so/your-workspace/database-id?v=view-id`에서 `database-id` 부분

## 주의사항

- `profile.env` 파일은 절대 GitHub에 커밋하지 마세요 (이미 .gitignore에 추가됨)
- API 키는 안전하게 보관하세요
- 각 API 서비스의 사용량 제한을 확인하세요
- 노션 업로드 기능은 선택사항입니다 (API 키가 없어도 다른 기능은 정상 작동)

## 지원 모델

- **Claude**: Sonnet 4, Opus 4, Haiku 3.5
- **Perplexity**: Sonar, Sonar Pro
- **Gemini**: 2.5 Flash, 2.5 Pro
- **OpenAI**: GPT-4.1, o3 (추론모델)

## 라이선스

FactoryStat - All rights reserved
