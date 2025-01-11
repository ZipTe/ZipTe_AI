
# 1. Project Overview (프로젝트 개요)
- 프로젝트 이름: ZIPTE_AI
- 해당 레포지토리 역할 : 아파트 정보를 제공하고 , 개인별 적절한 아파트를 추천해주는 AI 개발
- 프로젝트 기간 : 2024.10.27 ~ 2025.01.05 (1인 개발)

<br/>
<br/>

# 2. Team Member (팀원 소개)
| 이도연 |
|:------:|
| <img src="https://github.com/user-attachments/assets/653c94e3-5837-4e40-8ee9-b0ff135b59e7" alt="이도연" width="150"> | 
| BE |
| [GitHub](https://github.com/doup2001) | 

<br/>
<br/>

# 3. Key Features (주요 기능)
- **아파트**:
  - FastAPI를 통해, 아파트의 정보 및 유사한 아파트 데이터 받기
  - FastAPI를 통해, 개인별 선호도에 따른 아파트 데이터 받기
  - FastAPI를 통해, 지난 N년간 아파트별 실거래가를 받기
  - FastAPI를 통해, 지난 N년간 특정 법정동별 가격 정보(평당) 데이터 받기

<br/>
<br/>

# 4. Technology Stack (기술 스택)
## 5. AI
|  |  |  |
|-----------------|-----------------|-----------------|
| FastAPI    | <img src="https://github.com/user-attachments/assets/f332679d-80db-49ba-858f-b389247ccb95" width="100" /> |   |

<br/>

## 6. Cooperation
|  |  |
|-----------------|-----------------|
| Git    |  <img src="https://github.com/user-attachments/assets/483abc38-ed4d-487c-b43a-3963b33430e6" alt="git" width="100">    |
| Notion    |  <img src="https://github.com/user-attachments/assets/34141eb9-deca-416a-a83f-ff9543cc2f9a" alt="Notion" width="100">    |

<br/>

# 7. Project Structure (프로젝트 구조)
```plaintext
main.py
│   └── routers
│       ├── __init__.py
│       ├── __pycache__
│       ├── aptprice.py
│       ├── find.py
│       ├── price copy.py
│       ├── price.py
│       ├── properties.py
│       └── recommendation.py
```

<br/>
<br/>

# 8. Development Workflow (개발 워크플로우)
## 브랜치 전략 (Branch Strategy)
우리의 브랜치 전략은 Git Flow를 기반으로 하며, 다음과 같은 브랜치를 사용합니다.

- Main Branch
  - 배포 가능한 상태의 코드를 유지합니다.
  - 모든 배포는 이 브랜치에서 이루어집니다.
 
- Devlop Branch
  - 만든 기능들이 작동하는지 코드를 합병합니다.
  
- {feat} Branch
  - 모든 기능 개발은 feat 브랜치에서 이루어집니다.

<br/>
<br/>

# 9. 커밋 컨벤션

## type 종류
```
feat : 새로운 기능 추가
fix : 버그 수정
docs : 문서 수정
style : 코드 포맷팅, 세미콜론 누락, 코드 변경이 없는 경우
refactor : 코드 리펙토링
test : 테스트 코드, 리펙토링 테스트 코드 추가
chore : 설정 추가
```

<br/>

## 커밋 이모지
```
== 코드 관련
📝	코드 작성
🔥	코드 제거
♻️️	코드 리팩토링

== 문서&파일
📰	새 파일 생성
♻️️	파일 제거
📚	문서 작성

== 버그
🐛	버그 리포트
🚑	버그를 고칠 때

== 기타
🐎	성능 향상
✨	새로운 기능 구현
💡	새로운 아이디어
🚀	배포
```

<br/>

## 커밋 예시
```
== ex1
✨Feat: "회원 가입 기능 구현"

SMS, 이메일 중복확인 API 개발

== ex2
🔨chore: styled-components 라이브러리 설치

UI개발을 위한 라이브러리 styled-components 설치
```

<br/>
<br/>

# 10. ERD
![ERDV62](https://github.com/user-attachments/assets/2e260523-5524-4c9a-a8af-4675455614ab)


