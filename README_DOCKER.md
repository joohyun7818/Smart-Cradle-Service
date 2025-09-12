이 저장소의 도커 관련 파일을 "처음부터" 재설정했습니다.

왜 이렇게 했나?
- 기존 설정에는 개발용·프로덕션용 설정이 혼재되어 있고, `.env` 같은 민감 정보가 실수로 추적될 위험이 있었습니다.
- 학습 목적이라면 간단하고 명확한 최소 구성(Flask web, MySQL, Mosquitto)을 제공하는 편이 이해에 도움이 됩니다.

무엇이 바뀌었나?
- 삭제: 이전의 복잡하거나 중복된 docker-compose 및 .env 파일들을 정리했습니다.
- 추가: 최소한의 `docker-compose.yml`, `Dockerfile`, `requirements.txt`, `.env.example`, 그리고 학습용 `README_DOCKER.md`를 추가했습니다.

다음 단계
1. `smart_cradle_server/.env.example`를 복사하여 `smart_cradle_server/.env`로 만들고 값(특히 비밀번호)을 설정하세요.
2. 도커 빌드 및 실행:
   docker compose build
   docker compose up -d
3. 로그 확인: `docker compose logs -f web`

필요하면 제가 바로 빌드/시작까지 해드릴게요. 안전상의 이유로 실제 비밀번호는 `.env`에만 두세요.
