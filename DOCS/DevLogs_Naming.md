# Dev_logs 네이밍 컨벤션

**위치**: `Dev_logs/` (Git 추적 안됨)  
**적용일**: 2025-12-16

---

## 📋 네이밍 규칙

### 기본 형식
```
YYYY-MM-DD_category_description.extension
```

**예시:**
- `2025-12-16_bugfix_duplicate_order.md`
- `2025-12-16_db_trading.db`
- `2025-12-16_log_error.txt`

---

## 📁 카테고리 목록

| 카테고리 | 용도 | 확장자 |
|---------|------|-------|
| `bugfix` | 버그 수정 보고서 | `.md` |
| `playbook` | 작업 플레이북 | `.md` |
| `log` | 로그 파일 | `.txt` |
| `db` | DB 백업 | `.db` |
| `analysis` | 분석 보고서 | `.md` |
| `note` | 일반 노트 | `.md` |

---

## 🔄 정리 완료 (2025-12-16)

### Before
```
❌ BUGFIX_DuplicateOrder.md
❌ DEBUGGING_PLAYBOOK.md
❌ detailed_log_20251216.txt
```

### After
```
✅ 2025-12-16_bugfix_duplicate_order.md
✅ 2025-12-16_playbook_debugging.md
✅ 2025-12-16_log_duplicate_order.txt
✅ 2025-12-16_db_trading.db
```

---

**규칙**: 날짜 형식 `YYYY-MM-DD` + 소문자 + 언더스코어
