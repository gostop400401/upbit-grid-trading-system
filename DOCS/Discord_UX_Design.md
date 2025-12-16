# Discord 명령어 UX 개선 설계서

## 🎯 목표
**"최소한의 타이핑으로 최대한의 정보를 얻을 수 있도록"**

---

## 🚀 핵심 UX 개선 사항

### 1. **슬래시 명령어 (Slash Commands) 지원** ⭐ 최우선

#### 기존 방식 vs 개선안
```
❌ 기존: !상태          (타이핑 필요)
✅ 개선: /상태          (자동완성 지원)
```

#### 장점
- **자동완성**: `/` 입력 시 명령어 목록 자동 표시
- **파라미터 힌트**: 필요한 인자를 Discord가 안내
- **오타 방지**: 선택 방식이라 오타 불가능
- **모바일 친화적**: 터치로 선택 가능

#### 구현 우선순위
```python
# Phase 1: 슬래시 명령어로 전환
@app_commands.command(name="상태", description="시스템 현황 조회")
async def status(interaction: discord.Interaction):
    ...

@app_commands.command(name="포지션", description="활성 계약 상세 조회")
async def positions(interaction: discord.Interaction):
    ...
```

---

### 2. **단축어 (Aliases) 지원**

#### 자주 사용하는 명령어는 짧게
```python
명령어              단축어
/상태      →      /ㅅㅌ, /s, /stat
/포지션    →      /ㅍㅈㅅ, /p, /pos
/수익      →      /ㅅㅇ, /profit
/잔고      →      /ㅈㄱ, /bal
/긴급청산  →      /panic, /청산
```

#### 자동 완성 예시
```
사용자 입력: /ㅅ
Discord 표시:
  → /상태 (시스템 현황 조회)
  → /수익 (거래 통계 조회)
```

---

### 3. **버튼 인터페이스 (Interactive Buttons)**

#### 기존 vs 개선안
```
❌ 기존: 텍스트만 표시
✅ 개선: 버튼으로 추가 작업 가능
```

#### 예시: `/상태` 명령어 응답
```
📊 시스템 상태
├─ 실행 중 ✅
├─ 활성 계약: 9개
└─ 총 손익: +15,230원

[📋 상세 포지션 보기]  [💰 수익 상세]  [🔄 새로고침]
```

#### 버튼 클릭 시
- **상세 포지션 보기**: `/포지션` 자동 실행
- **수익 상세**: `/수익` 자동 실행
- **새로고침**: 현재 명령어 재실행

---

### 4. **선택 메뉴 (Select Menu)**

#### 활용 예시: `/주문취소`
```
사용자: /주문취소

봇 응답:
📋 미체결 주문 목록
┌─────────────────────────┐
│ 취소할 주문을 선택하세요  │
├─────────────────────────┤
│ ○ 1480원 - 4 USDT      │
│ ○ 1482원 - 4 USDT      │
│ ○ 1484원 - 4 USDT      │
│ ● 모두 선택             │
└─────────────────────────┘

[취소하기]  [닫기]
```

---

### 5. **스마트 파라미터 처리**

#### 자동 단위 인식
```python
/거래내역 10        # 10개 조회
/거래내역          # 기본값 10개 자동 적용
/거래내역 all      # 전체 조회
/거래내역 오늘      # 오늘 것만
```

#### 유연한 입력
```python
/주문취소 1480     # 가격만 입력
/주문취소 1480원   # 단위 포함 가능
/주문취소 1,480    # 쉼표 포함 가능
```

---

### 6. **페이지네이션 (Pagination)**

#### 긴 목록은 페이지 단위로
```
📋 활성 계약 목록 (1/3 페이지)

Contract #2: 1500원 → 1503원 (+3)
Contract #3: 1498원 → 1501원 (+3)
...

[◀️ 이전]  [1] [2] [3]  [다음 ▶️]
```

---

### 7. **상황별 안내 메시지**

#### 빈 결과 시
```
✅ 잘했어요!
현재 미체결 주문이 없습니다.
모든 그리드가 활성 계약으로 관리되고 있어요.

[📊 포지션 보기]  [💰 수익 확인]
```

#### 오류 발생 시
```
❌ 일시적인 문제가 발생했어요

문제: 업비트 API 연결 실패
원인: 네트워크 일시 지연

💡 해결 방법:
1. 잠시 후 다시 시도해주세요
2. 문제가 계속되면 관리자에게 문의하세요

[🔄 다시 시도]  [📞 관리자 호출]
```

---

### 8. **진행 상황 표시**

#### 시간이 걸리는 작업
```
사용자: /긴급청산

봇 응답:
⏳ 긴급 청산 중...
├─ [████████░░] 80%
├─ 9개 중 7개 계약 청산 완료
└─ 예상 완료: 약 5초

(실시간 업데이트)
```

---

### 9. **확인 절차 개선**

#### 기존 vs 개선안
```
❌ 기존: "YES를 입력하세요"
✅ 개선: 버튼 클릭
```

#### 예시: `/긴급청산`
```
⚠️ 긴급 청산 확인

📊 현재 포지션
├─ 활성 계약: 9개
├─ 예상 청산가: 시장가
└─ 예상 손익: -1,250원 (-0.3%)

❗ 이 작업은 되돌릴 수 없습니다

[🔴 청산 실행]  [❌ 취소]
```

---

### 10. **모바일 최적화**

#### 짧은 응답 옵션
```python
# 기본 모드 (상세)
/상태 → 전체 정보 + 버튼

# 간단 모드 (모바일)
/상태 간단 → 핵심 정보만
```

#### 예시
```
📊 상태 (간단)
✅ 실행중 | 9계약 | +15,230원

[상세보기]
```

---

## 🎨 UI/UX 구성 요소

### Embed 스타일 가이드

#### 성공 메시지
```python
embed = discord.Embed(
    title="✅ 작업 완료",
    description="...",
    color=discord.Color.green()
)
```

#### 경고 메시지
```python
embed = discord.Embed(
    title="⚠️ 주의 필요",
    description="...",
    color=discord.Color.orange()
)
```

#### 오류 메시지
```python
embed = discord.Embed(
    title="❌ 오류 발생",
    description="...",
    color=discord.Color.red()
)
```

#### 정보 메시지
```python
embed = discord.Embed(
    title="📊 정보",
    description="...",
    color=discord.Color.blue()
)
```

---

## ⌨️ 타이핑 최소화 전략

### 1. 기본값 활용
```python
/거래내역        # 자동으로 10개
/거래내역 20     # 명시적으로 20개
```

### 2. 자동 새로고침
```python
# /상태를 입력하면
# 5초마다 자동 업데이트 (옵션)
/상태 자동        # 자동 새로고침 모드
/상태 1회         # 1회만 (기본값)
```

### 3. 즐겨찾기 기능
```python
/즐겨찾기 추가 상태      # "/상태"를 즐겨찾기에 추가
/★                     # 즐겨찾기 1번 실행
/★2                    # 즐겨찾기 2번 실행
```

---

## 🔄 실시간 업데이트

### WebSocket 활용
```python
# 중요 이벤트 발생 시 자동 알림
매수 체결 → 자동 알림 + [포지션 보기] 버튼
매도 체결 → 자동 알림 + [수익 확인] 버튼
```

---

## 📱 플랫폼별 최적화

### 데스크톱
- 상세 정보 우선
- 키보드 단축키 지원

### 모바일
- 버튼 크기 확대
- 간단 모드 기본 제공
- 터치 최적화

---

## 🎯 구현 우선순위

### Phase 1 (필수)
1. ✅ **슬래시 명령어 전환** - 가장 중요!
2. ✅ **버튼 인터페이스** - 편의성 극대화
3. ✅ **확인 절차 개선** - 안전성 + 편의성
4. ✅ **페이지네이션** - 긴 목록 대응

### Phase 2 (권장)
5. 선택 메뉴 (Select Menu)
6. 단축어 (Aliases)
7. 진행 상황 표시
8. 상황별 안내 메시지

### Phase 3 (선택)
9. 스마트 파라미터 처리
10. 모바일 최적화
11. 즐겨찾기 기능
12. 자동 새로고침

---

## 💡 UX 원칙

### 1. **Zero Typing 원칙**
가능한 한 타이핑 없이 버튼/선택만으로 작업 완료

### 2. **One-Click 원칙**
자주 사용하는 작업은 1번의 클릭으로 완료

### 3. **Progressive Disclosure**
기본은 간단하게, 필요시 상세 정보 제공

### 4. **Error Prevention**
오류를 수정하는 것보다 발생하지 않도록 설계

### 5. **Feedback 원칙**
모든 작업에 즉각적인 피드백 제공

---

## 📋 체크리스트

### 명령어 구현 시 확인사항
- [ ] 슬래시 명령어로 구현
- [ ] description 명확히 작성
- [ ] 필요한 버튼/선택 메뉴 추가
- [ ] 오류 처리 및 안내 메시지
- [ ] 로딩 상태 표시
- [ ] 모바일에서 테스트
- [ ] 페이지네이션 필요 여부
- [ ] 확인 절차 필요 여부

---

## 🚀 다음 단계

1. **discord.py 2.0+ 업그레이드** (app_commands 지원)
2. **슬래시 명령어 스켈레톤 구축**
3. **공통 UI 컴포넌트 라이브러리 작성**
4. **Phase 1 명령어부터 순차 구현**

---

## 📖 참고 코드 템플릿

### 기본 슬래시 명령어
```python
@app_commands.command(name="상태", description="시스템 현황 조회")
async def status(interaction: discord.Interaction):
    # 즉시 응답 (3초 제한)
    await interaction.response.defer()
    
    # 데이터 수집
    data = await get_system_status()
    
    # Embed 생성
    embed = create_status_embed(data)
    
    # 버튼 추가
    view = StatusView()
    
    # 응답
    await interaction.followup.send(embed=embed, view=view)
```

### 버튼 뷰 템플릿
```python
class StatusView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)  # 5분 타임아웃
    
    @discord.ui.button(label="상세 포지션", style=discord.ButtonStyle.primary)
    async def positions_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        # /포지션 실행
        ...
    
    @discord.ui.button(label="새로고침", style=discord.ButtonStyle.secondary)
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        # 현재 명령어 재실행
        ...
```

### 확인 다이얼로그 템플릿
```python
class ConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.value = None
    
    @discord.ui.button(label="확인", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.value = True
        self.stop()
    
    @discord.ui.button(label="취소", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.value = False
        self.stop()
```
