# 중복 매수 버그 수정 보고서

**날짜**: 2025-12-16  
**버그 발생 시간**: 2025-12-16 10:03:43-44 (KST)  
**수정자**: AI Agent (Antigravity)

---

## 🐛 문제 발견

### 증상
- 계약 ID 16, 17이 **1초 차이**로 동일한 가격(1488.0 KRW)에 중복 매수됨
- 수량: 각 4.0 USDT
- buy_order_uuid가 다름 → 완전히 별도의 두 주문이 실행됨

### 데이터베이스 분석 결과
```
계약 ID 16:
- 생성 시간: 2025-12-16 01:03:43 (UTC)
- buy_order_uuid: 7caea73f-eaba-4976-8c30-49de4a196092

계약 ID 17:
- 생성 시간: 2025-12-16 01:03:44 (UTC)
- buy_order_uuid: 364d029f-3a8b-4457-8cb3-3674218ecc66
```

---

## 🔍 근본 원인: Race Condition

### 1. 락(Lock) 미사용
- `self._lock = asyncio.Lock()` 정의는 했지만 실제로 사용하지 않음
- `_fill_empty_grids()` 함수가 동시에 여러 번 실행 가능

### 2. start_trading 동시성 제어 부족
```python
# [수정 전] 취약한 체크
if self.is_running:
    return "already running"
self.is_running = True  # ← 두 호출이 동시에 이 줄 전에 도달하면?
```

### 3. 여러 monitor_loop 태스크 동시 실행
- 기존 태스크를 명시적으로 취소하지 않음
- 첫 번째 태스크: 계속 실행 중
- 두 번째 태스크: 덮어쓰기로 생성됨
- 결과: 두 태스크가 동시에 `_fill_empty_grids()` 호출

---

## ✅ 해결 방법: "문지기(Gatekeeper)" 패턴

### 핵심 개념
```
[주문자] "야, 나 1488원에 주문 낼거다~"
   ↓
[문지기] 🔐 (락을 걸고 확인)
   ↓
[확인] 이미 1488원에 주문이 있나?
   ├─ YES → "안돼! 이미 주문 있어" ❌
   └─ NO  → "괜찮아! 주문 넣어" ✅
```

### 수정 내용

#### 1. start_trading 락 적용 및 태스크 관리
```python
async def start_trading(self, config: Dict) -> str:
    # 🔒 CRITICAL: Lock으로 동시 호출 방지
    async with self._lock:
        if self.is_running:
            return "already running"
        
        # 기존 태스크 명시적 취소
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            await self._monitor_task  # 취소 완료 대기
        
        # ... 시작 로직
```

**효과**: 여러 `!시작` 명령이 빠르게 들어와도 한 번에 하나만 처리

#### 2. _place_order_atomic 함수 추가
```python
async def _place_order_atomic(self, ticker: str, price: float, amount: float):
    """
    🔒 원자적(Atomic) 주문 실행 함수
    주문 직전에 마지막으로 3중 체크:
    1. 로컬 pending_buy_orders 확인
    2. DB active contracts 확인
    3. 거래소 open orders 확인
    """
    epsilon = 1e-4
    
    # 1. 로컬 pending 확인
    for existing_price in self.pending_buy_orders.values():
        if abs(existing_price - price) < epsilon:
            return None  # "안돼!"
    
    # 2. DB 확인
    active_contracts = await Contract.get_active_contracts()
    for contract in active_contracts:
        if abs(float(contract.buy_price) - price) < epsilon:
            return None  # "안돼!"
    
    # 3. 거래소 확인 (최종 방어선)
    open_orders = await self.handler.get_open_orders(ticker)
    if open_orders:
        for order in open_orders:
            if order.get('side') == 'bid' and abs(float(order.get('price', 0)) - price) < epsilon:
                return None  # "안돼!"
    
    # ✅ 모든 체크 통과! "괜찮아~ 주문 넣어!"
    uuid = await self.handler.buy_limit_order(ticker, price, amount)
    if uuid:
        self.pending_buy_orders[uuid] = price
    return uuid
```

**효과**: 주문 직전 마지막 순간에 3중 검증으로 중복 원천 차단

#### 3. _fill_empty_grids 전체를 락으로 보호
```python
async def _fill_empty_grids(self):
    # 🔒 CRITICAL: 전체 함수를 락으로 보호 (문지기 패턴)
    async with self._lock:
        try:
            # ... 그리드 스캔 로직
            
            if not is_contract_active and not is_pending and not is_order_open:
                # 🔒 원자적 주문 실행 (이미 락 안에 있음)
                uuid = await self._place_order_atomic(ticker, current_grid, amount)
                if uuid:
                    logger.info(f"✅ Order placed at {current_grid}")
                else:
                    logger.warning(f"⚠️ Order rejected at {current_grid}")
```

**효과**: 
- 한 번에 하나의 `_fill_empty_grids`만 실행
- 여러 태스크가 동시에 진입해도 순차 처리
- Race Condition 완전 차단

---

## 📝 배포 체크리스트

1. [x] 코드 수정 완료
2. [ ] GitHub 푸시
3. [ ] 서버 업데이트
4. [ ] 봇 재시작
5. [ ] 로그 모니터링

---

## 🔗 관련 파일

- **수정된 파일**: `modules/trading_manager.py`
- **주요 함수**:
  - `start_trading()` - 락 적용
  - `_fill_empty_grids()` - 락으로 보호
  - `_place_order_atomic()` - 신규 추가 (3중 검증)
