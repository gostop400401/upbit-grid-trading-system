# 🎨 Upbit Grid Trading Bot - 플랫 아이콘 가이드 (개정판)

**스타일**: 플랫 미니멀 라인 아이콘  
**적용일**: 2025-12-16 (개정)

---

## 🎯 디자인 방향 (수정)

### ❌ 이전 방향 (취소)
- ~~3D 글래스모피즘~~
- ~~복잡한 그라데이션~~
- ~~입체적인 그림자~~

### ✅ 새로운 방향
- **플랫 디자인** - 2D 평면적
- **라인 아이콘** - 심플한 선
- **소프트 컬러** - 부드러운 파스텔/비비드 단색
- **둥근 모서리** - 친근하고 모던한 느낌
- **Discord 최적화** - 작은 크기에서도 명확한 인식

---

## 📋 아이콘 교체 매핑표 (개정)

### 알림 관련 (Notification)

| 현재 | 용도 | 새 아이콘 | 색상 | 설명 |
|-----|------|----------|------|------|
| 🔔 | 매수 체결 | Flat Bell | Blue (#4A90E2) | 심플한 벨 라인 |
| 💰 | 익절 알림 | Flat Coin | Gold (#F5A623) | 동전 라인 아이콘 |
| ⚠️ | 경고 | Flat Alert | Orange (#FF9500) | 삼각형 경고 |
| ✅ | 성공 | Flat Check | Green (#7ED321) | 둥근 체크마크 |

### 상태 표시 (Status)

| 현재 | 용도 | 새 아이콘 | 색상 | 설명 |
|-----|------|----------|------|------|
| 📊 | 통계/차트 | Flat Chart | Purple (#9013FE) | 막대 차트 라인 |
| 📈 | 상승/수익 | Flat Up | Green (#7ED321) | 상승 화살표 |
| 📉 | 하락/손실 | Flat Down | Red (#D0021B) | 하락 화살표 |
| 🔄 | 새로고침 | Flat Refresh | Blue (#4A90E2) | 원형 화살표 |

### 액션 (Action)

| 현재 | 용도 | 새 아이콘 | 색상 | 설명 |
|-----|------|----------|------|------|
| 🚀 | 시작/론칭 | Flat Rocket | Gradient Blue | 로켓 실루엣 |
| ⏸️ | 일시정지 | Flat Pause | Gray (#9B9B9B) | 두 개의 세로선 |
| ❌ | 에러/취소 | Flat X | Red (#D0021B) | X 표시 |
| 📝 | 주문/문서 | Flat Doc | Blue (#4A90E2) | 문서 라인 |

---

## 🎨 디자인 스펙 (개정)

### 아이콘 규격
- **크기**: 128x128px (Discord 최적화)
- **포맷**: PNG (투명 배경)
- **스타일**: 플랫 라인 아이콘
- **선 두께**: 3-4px (명확한 인식)
- **모서리**: 둥글게 (border-radius)
- **색상**: 단색 또는 심플한 그라데이션

### 색상 팔레트 (플랫 디자인용)
```css
/* Primary Colors */
--blue: #4A90E2;      /* 알림, 정보 */
--green: #7ED321;     /* 성공, 상승 */
--red: #D0021B;       /* 에러, 하락 */
--orange: #FF9500;    /* 경고 */
--gold: #F5A623;      /* 수익, 코인 */
--purple: #9013FE;    /* 통계, 차트 */
--gray: #9B9B9B;      /* 비활성 */

/* Soft Variants (배경용) */
--blue-light: rgba(74, 144, 226, 0.1);
--green-light: rgba(126, 211, 33, 0.1);
--red-light: rgba(208, 2, 27, 0.1);
```

---

## � Discord 임베드 적용 방법 (개정)

### 옵션 1: 이모지 직접 교체 (가장 간단) ⭐ 추천

Discord의 커스텀 이모지 기능 사용:

```python
# 1. Discord 서버에 커스텀 이모지 업로드
# 2. 코드에서 이모지 ID로 참조

# Before
await channel.send("🔔 **매수 체결 알림**")

# After
await channel.send("<:bell:1234567890> **매수 체결 알림**")
```

**장점:**
- ✅ 코드 수정 최소화
- ✅ 빠른 로딩
- ✅ Discord 네이티브 지원

### 옵션 2: Embed Thumbnail

```python
embed = discord.Embed(
    title="매수 체결 알림",
    color=0x4A90E2
)
embed.set_thumbnail(url="attachment://icon_notification.png")

file = discord.File("assets/icons/icon_notification.png")
await channel.send(file=file, embed=embed)
```

---

## 📱 Discord 커스텀 이모지 vs 이미지 파일

### Discord 커스텀 이모지 (추천) ✅

**장점:**
- 인라인 텍스트 사용 가능
- 로딩 빠름
- 코드 간단
- 무료 서버: 50개, Nitro 서버: 250개

**단점:**
- 서버별 관리 필요
- 크기 제한 (256KB)

### 이미지 파일 첨부

**장점:**
- 서버 제한 없음
- 고해상도 가능

**단점:**
- 매번 파일 첨부 필요
- 로딩 느림
- 코드 복잡

---

## 🚀 구현 계획 (개정)

### Phase 1: 아이콘 생성
- [ ] 플랫 라인 아이콘 12개 생성 (128x128px)
- [ ] 투명 배경 PNG 저장
- [ ] `assets/icons/` 폴더 정리

### Phase 2: Discord 서버 설정
- [ ] Discord 서버에 커스텀 이모지 업로드
- [ ] 이모지 ID 확인 및 기록

### Phase 3: 코드 수정
- [ ] 이모지 맵핑 딕셔너리 생성
- [ ] `discord_bot.py`에 helper 함수 추가
- [ ] 모든 알림 메시지 업데이트

### Phase 4: 테스트 & 배포
- [ ] 로컬 테스트
- [ ] 서버 배포
- [ ] 실제 환경 확인

---

## 📝 아이콘 생성 리스트 (필수 12개)

### 우선순위 1: 핵심 알림 (4개)
1. ✅ Bell (알림) - Blue
2. ✅ Coin (수익) - Gold
3. ✅ Check (성공) - Green
4. ✅ Warning (경고) - Orange

### 우선순위 2: 상태 표시 (4개)
5. ✅ Chart (통계) - Purple
6. ✅ Up Arrow (상승) - Green
7. ✅ Down Arrow (하락) - Red
8. ✅ Refresh (새로고침) - Blue

### 우선순위 3: 액션 (4개)
9. ✅ Rocket (시작) - Blue Gradient
10. ✅ Pause (일시정지) - Gray
11. ✅ X Mark (에러) - Red
12. ✅ Document (주문) - Blue

---

## � 참고사항

### Discord 커스텀 이모지 업로드 방법
1. 서버 설정 → 이모지 → 이모지 업로드
2. 이름 지정 (예: `bell`, `coin`, `check`)
3. 이모지 클릭 → "이모지 복사" → 코드에 붙여넣기
4. 형식: `<:이름:ID>` 또는 `<a:이름:ID>` (애니메이션)

### 코드에서 이모지 사용
```python
# 이모지 맵 정의
ICONS = {
    'bell': '<:bell:1234567890>',
    'coin': '<:coin:1234567891>',
    'check': '<:check:1234567892>',
    'warning': '<:warning:1234567893>',
    'chart': '<:chart:1234567894>',
    'up': '<:up:1234567895>',
    'down': '<:down:1234567896>',
    'refresh': '<:refresh:1234567897>',
    'rocket': '<:rocket:1234567898>',
    'pause': '<:pause:1234567899>',
    'error': '<:error:1234567900>',
    'doc': '<:doc:1234567901>',
}

# 사용
await channel.send(f"{ICONS['bell']} **매수 체결 알림**")
```

---

## 🎯 기대 효과

| 항목 | Before | After |
|-----|--------|-------|
| 디자인 | 기본 이모지 | 커스텀 플랫 아이콘 |
| 브랜딩 | 일반적 | 전문적/고유 |
| 가독성 | 보통 | 우수 |
| 로딩속도 | 즉시 | 즉시 (커스텀 이모지) |
| 유지보수 | 쉬움 | 쉬움 |

---

**제작**: Gemini 3 Flash  
**스타일**: 플랫 미니멀 라인 아이콘 (Discord 최적화)
