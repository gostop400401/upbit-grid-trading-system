# 기술 설계서 (Technical Design Document)

## 1. 개요 (Overview)
본 문서는 `Upbit Grid Trading System`의 구현을 위한 상세 기술 설계를 다룹니다. `PRD.md`에 정의된 요구사항을 바탕으로 시스템 구조, 데이터베이스, 클래스 설계 등을 정의합니다.

## 2. 프로젝트 구조 (Project Structure)
```
upbit-grid-trading/
├── .env                # 환경 변수 (API Keys, Discord Token 등)
├── main.py             # 프로그램 진입점 (Entry Point)
├── requirements.txt    # 의존성 라이브러리 목록
├── database/
│   └── database.py     # DB 연결 및 관리 (SQLite)
├── models/
│   ├── contract.py     # 계약(Contract) 데이터 모델
│   └── trade.py        # 거래(Trade) 데이터 모델
├── modules/
│   ├── discord_bot.py  # 디스코드 봇 인터페이스 및 커맨드 핸들러
│   ├── upbit_handler.py# 업비트 API 통신 및 제한 관리
│   ├── trading_manager.py # 매매 로직, 상태 관리, 주문 실행 총괄
│   └── utils.py        # 로깅, 유틸리티 함수
└── logs/               # 로그 파일 저장
    └── system.log
```

## 3. 데이터베이스 스키마 (Database Schema)
**Database**: SQLite (`trading.db`)

### 3.1. Contracts (활성 계약 테이블)
| Field | Type | Description |
|---|---|---|
| id | INTEGER PK | 계약 고유 ID (Auto Increment) |
| coin_ticker | TEXT | 코인 티커 (예: KRW-USDT) |
| buy_price | REAL | 매수 체결 가격 |
| buy_amount | REAL | 매수 수량 |
| target_price | REAL | 매도 목표 가격 |
| status | TEXT | 상태 (ACTIVE, CLOSED) |
| created_at | DATETIME | 계약 생성 시간 |
| order_uuid | TEXT | 관련 매수/매도 주문 UUID |
| sell_price | REAL | 매도 체결 가격 (Active일 경우 Null) |
| profit | REAL | 실현 수익금 (Active일 경우 Null) |
| profit_rate | REAL | 수익률 (Active일 경우 Null) |
| finished_at | DATETIME | 거래 종료 시간 (Active일 경우 Null) |

### 3.2. Trades (거래 내역 테이블)
| Field | Type | Description |
|---|---|---|
| id | INTEGER PK | 거래 고유 ID |
| contract_id | INTEGER | 관련 계약 ID (FK) |
| type | TEXT | 거래 유형 (BUY, SELL) |
| price | REAL | 체결 가격 |
| amount | REAL | 체결 수량 |
| fee | REAL | 수수료 |
| profit | REAL | 실현 손익 (매도 시 기록, 매수 시 0) |
| executed_at | DATETIME | 체결 시간 |

### 3.3. Config (설정 저장 테이블)
| Field | Type | Description |
|---|---|---|
| key | TEXT PK | 설정 키 (예: last_grid_config) |
| value | TEXT | 설정 값 (JSON 문자열) |
| updated_at | DATETIME | 마지막 수정 시간 |

## 4. 클래스 및 모듈 설계 (Class & Module Design)

### 4.1. `UpbitHandler`
*   **역할**: 업비트 API와의 통신을 전담하며, Rate Limit을 준수합니다. **WebSocket**을 사용하여 실시간 시세를 수신합니다.
*   **주요 메서드**:
    *   `connect_websocket(ticker)`: 시세 수신을 위한 웹소켓 연결
    *   `get_balance(ticker)`: 잔액 조회 (REST API)
    *   `get_current_price(ticker)`: 현재가 조회
    *   `buy_limit_order(ticker, price, amount)`: 지정가 매수
    *   `sell_limit_order(ticker, price, amount)`: 지정가 매도
    *   `get_order_status(uuid)`: 주문 상태 확인
    *   `cancel_order(uuid)`: 주문 취소

### 4.2. `TradingManager`
*   **역할**: 핵심 매매 로직을 수행하고 전체 상태를 관리합니다. `UpbitHandler`와 DB 모델을 사용합니다.
*   **주요 메서드**:
    *   `start_trading(config)`: 초기 그리드 생성 및 매수 주문 배치
    *   `process_buy_fill(order)`: 매수 체결 처리 (계약 생성, 매도 주문)
    *   `process_sell_fill(order)`: 매도 체결 처리 (수익 실현, 재매수 주문)
    *   `check_price_range()`: 범위 이탈 여부 감시
    *   `recover_state()`: 재시작 시 상태 복구 (누락된 주문 확인)

### 4.3. `DiscordBot`
*   **역할**: 사용자와의 상호작용(명령어 처리, 알림 발송)을 담당합니다.
*   **주요 명령어**:
    *   `!시작`: 설정 위자드 시작 -> `TradingManager.start_trading` 호출
    *   `!종료`: 매매 종료 및 프로세스 정리
    *   `!상태`: 현재 Active 계약 수, 추정 수익 등 조회
    *   `!청산`: 긴급 청산 요청
    *   `!리포트`: 계약별 매수/매도/손익 성과 리포트 출력 (최근 N건)

## 5. 데이터 흐름 및 프로세스 (Data Flow & Process)

### 5.1. 매수 체결 프로세스
1.  `UpbitHandler`가 주문 체결(Filled) 감지 (Polling/Socket).
2.  `TradingManager`의 `process_buy_fill` 호출.
3.  DB `Contracts` 테이블에 새로운 레코드 생성.
4.  목표가 계산 후 `UpbitHandler.sell_limit_order` 호출.
5.  `DiscordBot`을 통해 체결 알림 전송.

### 5.2. 매도 체결 프로세스
1.  `UpbitHandler`가 주문 체결(Filled) 감지 (Polling/Socket).
2.  `TradingManager`의 `process_sell_fill` 호출.
3.  DB `Contracts` 테이블 업데이트 (상태: CLOSED, 수익 정보 기록).
4.  DB `Trades` 테이블에 매도 거래 내역 기록.
5.  수익 실현 후, 동일 가격(진입가)에 `UpbitHandler.buy_limit_order` 재배치 (재진입).
6.  `DiscordBot`을 통해 익절 알림 전송.

### 5.3. 시스템 복구 프로세스 (Startup)
1.  `main.py` 실행 시 `TradingManager.recover_state` 수행.
2.  DB에서 `Contracts` 중 상태가 'ACTIVE'인 항목 로드.
3.  `UpbitHandler`를 통해 미체결 주문 목록 조회.
4.  각 Active 계약에 대응하는 매도 주문이 존재하는지 확인.
5.  주문이 없다면 즉시 해당 목표가로 매도 주문 재전송.

### 5.4. 예외 및 동시성 처리 로직 (Concurrency & Exception Logic)
*   **Idempotency (멱등성)**: 웹소켓 재연결 등으로 인한 중복 이벤트 방지를 위해, 주문 처리 전 `order_uuid`가 DB에 이미 존재하는지 중복 검사 수행.
*   **Partial Fills (부분 체결)**: `remained_volume`이 0이 될 때까지 대기(Wait)하거나 누적 체결량을 관리. V1에서는 **완전 체결(Fully Filled)** 시에만 다음 단계로 진행하는 것을 원칙으로 함.
*   **Retry Logic**: API 호출 실패(Timeout, 5xx) 시 `exponential backoff` 방식으로 최대 3회 재시도.
*   **Decimal Precision**: 부동 소수점 오차 방지를 위해 금액 계산 시 `decimal.Decimal` 사용.

## 6. 기술 스택 (Tech Stack)
*   **Python**: 3.9+
*   **Libraries**:
    *   `pyupbit`: 업비트 API
    *   `discord.py`: 디스코드 봇 (Async)
    *   `aiosqlite`: 비동기 SQLite DB 드라이버 (Main Loop Blocking 방지)
    *   `python-dotenv`: 환경 변수 관리
*   **Database**: SQLite3 (WAL Mode 활성화 권장)
