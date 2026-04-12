# 📜 GAME DESIGN DOCUMENT v4.0
# Ayutthaya Wealth Saga: Beyond the Realm
## เอกสารอ้างอิงการพัฒนา — ฉบับสมบูรณ์จาก Codebase จริง

**เวอร์ชัน**: 4.0 (Extracted from Production Code)
**วันที่**: มิถุนายน 2569
**สถานะ**: Production-Ready Reference
**Source**: app.py v1.0.0 + index.html (Beyond the Realm)

> **หมายเหตุ**: เอกสารนี้สร้างจากโค้ดที่ใช้งานจริง ไม่ใช่ Draft ทุก field, value, และ logic
> สะท้อนสิ่งที่ implement จริงใน codebase ณ เวอร์ชันนี้

---

## 📋 สารบัญ

1. ภาพรวมและ Tech Stack
2. Data Structures (Pydantic Models)
3. LOCATIONS — 9 แห่ง (Complete)
4. NPC_DATA — 9 ตัว (System Prompts + Cross-Temporal)
5. INVESTMENT_EVENTS_MASTER — 7 เหตุการณ์
6. INVESTMENT_WISDOM_HINTS
7. INVESTMENT_QUESTS — 8 เควสต์
8. INVESTMENT_SCENARIOS — 10 Scenarios
9. RANKS + calculate_rank()
10. WISDOM_GATE
11. Game Mechanics — end_turn Logic
12. Item System
13. API Endpoints
14. Frontend Specifications
15. UX Features และ Edge Cases
16. การเปลี่ยนแปลงจาก v3.0

---

## ส่วนที่ 1: ภาพรวมและ Tech Stack

### 1.1 Game Identity

| Field | Value |
|-------|-------|
| **ชื่อเกม** | Ayutthaya Wealth Saga: Beyond the Realm |
| **เวอร์ชัน** | 1.0.0 |
| **ธีม** | Cross-Temporal: NPC จากอยุธยาข้ามเวลามาปี 2026 |
| **ประเภท** | Educational Investment Simulation (Turn-based) |
| **Platform** | Web (Mobile-first) |
| **สกุลเงิน** | บาท (THB) |
| **ทุนเริ่มต้น** | 100,000 บาท |
| **รอบต่อเกม** | 3 (beginner) / 5 (normal) |
| **หน่วยเวลาในเกม** | "ไตรมาส" (Quarter) แทน "ปี" |

### 1.2 Tech Stack

```
Backend:
├── FastAPI (Python)
├── Anthropic/OpenAI-compatible API (streaming)
├── httpx (async HTTP client)
├── python-dotenv
└── Jinja2 Templates

Frontend:
├── Vanilla JavaScript (ES2022)
├── Tailwind CSS (CDN)
├── Font Awesome 6.4.0
├── marked.js (Markdown rendering)
└── Google Fonts: Sarabun, Chakra Petch, Niramit

Deployment:
└── Uvicorn (PORT=7860 default)
```

### 1.3 Environment Variables

```env
API_KEY=...
API_BASE_URL=https://api.openai.com/v1
API_MODEL=gpt-4o-mini
PORT=7860
API_TIMEOUT=30
```

### 1.4 API Endpoints

| Method | Path | คำอธิบาย |
|--------|------|---------|
| GET | `/` | Serve index.html |
| GET | `/api/init` | Game data ทั้งหมดสำหรับ Frontend |
| POST | `/api/news` | Rumor + Wisdom Hints สำหรับรอบปัจจุบัน |
| POST | `/api/end-turn` | ประมวลผลการลงทุน |
| POST | `/api/chat` | NPC Chat (Streaming SSE) |
| POST | `/api/quest/accept` | รับเควสต์ |
| POST | `/api/quest/evaluate` | AI ประเมินความเข้าใจ |
| POST | `/api/quest/complete` | รับรางวัลเควสต์ |
| POST | `/api/generate-insights` | End-game Summary |

---

## ส่วนที่ 2: Data Structures (Pydantic Models)

```python
class PlayerStats(BaseModel):
    wealth: int = 100000      # บาท (THB)
    wisdom: int = 10          # Financial Literacy Score
    merit:  int = 10          # Emergency Fund / Safety Net Level
    health: int = 100         # Human Capital
    items:  List[str] = []


class GameState(BaseModel):
    scenario_id:             str
    round:                   int = 1
    max_rounds:              int = 5          # 3 (beginner) | 5 (normal)
    stats:                   PlayerStats
    history:                 List[Dict] = []
    active_quest:            Optional[str] = None
    completed_quests:        List[str] = []
    quest_chat_history:      List[Dict] = []
    quest_turn_count:        int = 0
    horathibodi_chat_count:  int = 0          # reset ทุกรอบ (ใน nextRound)


class InvestmentAction(BaseModel):
    area_id: int
    amount:  int


class TurnActionRequest(BaseModel):
    game_state:  GameState
    investments: List[InvestmentAction]


class ChatRequest(BaseModel):
    npc_id:       str
    user_message: str
    game_context: str
    history:      List[Dict[str, str]] = []
    active_quest: Optional[str] = None


class QuestAcceptRequest(BaseModel):
    game_state: GameState
    quest_id:   str


class QuestEvaluateRequest(BaseModel):
    quest_id:     str
    chat_history: List[Dict[str, str]]


class QuestCompleteRequest(BaseModel):
    game_state: GameState
    quest_id:   str


class InsightsRequest(BaseModel):
    game_state: GameState
```

---

## ส่วนที่ 3: LOCATIONS (9 แห่ง — Complete)

### 3.1 Location Data

```python
LOCATIONS = {
    1: {
        "name": "พระคลังมหาสมบัติ",
        "npc_id": "kosathibodi",
        "type": "bonds",
        "modern_product": "พันธบัตรรัฐบาล / เงินฝากประจำ",
        "risk_level": 1,
        "risk_label": "ต่ำมาก",
        "return_range": "1–4% ต่อปี",
        "desc": "ลงทุนในพันธบัตรรัฐบาล รัฐสัญญาคืนเงินพร้อมดอกเบี้ยที่แน่นอน ความเสี่ยงต่ำที่สุด เพราะรัฐไม่มีวันล้มละลาย",
        "hp_cost": -4,
        "merit_effect": 0,
        "min_invest": 1000,
        "require_merit": 0,
        "require_health": 10,
    },
    2: {
        "name": "ระบบเจ้าภาษีนายอากร",
        "npc_id": "khunluang",
        "type": "tax_fund",
        "modern_product": "กองทุน ThaiESG / RMF / Tax-Efficient Investing",
        "risk_level": 2,
        "risk_label": "ต่ำ",
        "return_range": "3–8% ต่อปี (+ ลดหย่อนภาษีสูงสุด 300,000–500,000 บาท)",
        "desc": "กองทุน ThaiESG และ RMF — ลงทุนพร้อมรับสิทธิลดหย่อนภาษีแยกวงเงินกัน ThaiESG เน้น ESG สูงสุด 300,000 บาท / RMF เพื่อเกษียณสูงสุด 500,000 บาท ผู้รู้กฎได้เปรียบเสมอ",
        "hp_cost": -4,
        "merit_effect": 0,
        "min_invest": 5000,
        "require_merit": 0,
        "require_health": 10,
    },
    3: {
        "name": "ศาลาพระโอสถ",
        "npc_id": "thongin",
        "type": "fixed_income",
        "modern_product": "กองทุนตราสารหนี้ / Defensive Portfolio / กองทุนสุขภาพ (Healthcare Fund)",
        "risk_level": 2,
        "risk_label": "ต่ำ",
        "return_range": "2–5% ต่อปี",
        "desc": "กองทุนตราสารหนี้และ Defensive Portfolio ลงทุนในพันธบัตรและหุ้นกู้ ผลตอบแทนสม่ำเสมอ ป้องกันพอร์ตยามตลาดผันผวน — บวกกับกองทุนสุขภาพที่เติบโตตามสังคมผู้สูงอายุ",
        "hp_cost": 20,          # บวก: ลงทุน Defensive = สบายใจ = HP ฟื้น
        "merit_effect": 0,
        "min_invest": 3000,
        "require_merit": 0,
        "require_health": 0,    # เปิดให้แม้ HP ต่ำมาก (ที่พักฟื้น)
    },
    4: {
        "name": "ท่าเรือสำเภาหลวง",
        "npc_id": "karaket",
        "type": "equity",
        "modern_product": "กองทุนหุ้น SET / กองทุนหุ้นต่างประเทศ / Global Index Fund",
        "risk_level": 4,
        "risk_label": "สูง",
        "return_range": "-20% ถึง +40%",
        "desc": "ตลาดหลักทรัพย์ SET และกองทุนหุ้นต่างประเทศ ผลตอบแทนศักยภาพสูงแต่ผันผวนมาก — การกระจายไปหุ้นต่างประเทศช่วยลดความเสี่ยงจากตลาดไทยเพียงตลาดเดียว",
        "hp_cost": -8,
        "merit_effect": 0,
        "min_invest": 10000,
        "require_merit": 0,
        "require_health": 40,
    },
    5: {
        "name": "ทุ่งนาหลวง",
        "npc_id": "grandma_in",
        "type": "balanced",
        "modern_product": "กองทุนรวมผสม / Balanced Fund (DCA)",
        "risk_level": 3,
        "risk_label": "ปานกลาง",
        "return_range": "-10% ถึง +20%",
        "desc": "กองทุนรวมผสม ลงทุนทั้งหุ้นและตราสารหนี้ ความเสี่ยงปานกลาง เหมาะกับ DCA ทุกเดือน",
        "hp_cost": -4,
        "merit_effect": 0,
        "min_invest": 5000,
        "require_merit": 0,
        "require_health": 10,
    },
    6: {
        "name": "หมู่บ้านอรัญญิก",
        "npc_id": "asa",
        "type": "sector",
        "modern_product": "กองทุน Sector Fund / หุ้นรายตัว",
        "risk_level": 4,
        "risk_label": "สูง",
        "return_range": "-25% ถึง +50%",
        "desc": "Sector Fund เลือกลงทุนเฉพาะกลุ่มอุตสาหกรรม เช่น เทคโนโลยี พลังงานสะอาด สุขภาพ ถ้าถูก Sector กำไรสูงมาก",
        "hp_cost": -8,
        "merit_effect": 0,
        "min_invest": 10000,
        "require_merit": 0,
        "require_health": 40,
    },
    7: {
        "name": "ย่านป่าถ่านและทองคำ",
        "npc_id": "wijit",
        "type": "alternative",
        "modern_product": "Gold ETF / REITs / Infrastructure Fund / Alternative Assets",
        "risk_level": 4,
        "risk_label": "สูง (Hedge)",
        "return_range": "-10% ถึง +45%",
        "desc": "Gold ETF ทองคำดิจิทัลเป็น Inflation Hedge และ Safe Haven ยามวิกฤต ควบคู่กับ REITs และ Infrastructure Fund ที่ให้ปันผลสม่ำเสมอ — Alternative Assets ที่กระจายความเสี่ยงออกจากหุ้นและพันธบัตร",
        "hp_cost": -16,         # สูงที่สุด: ความวิตกกังวลสูง
        "merit_effect": 0,
        "min_invest": 10000,
        "require_merit": 30,    # ต้องมี Emergency Fund พอก่อนลงทุน Alternative
        "require_health": 40,
    },
    8: {
        "name": "วัดป่าแก้ว",
        "npc_id": "ajarn_mun",
        "type": "esg_emergency",
        "modern_product": "กองทุน ThaiESG / กองทุน ESG / Emergency Fund / เศรษฐกิจพอเพียง",
        "risk_level": 0,
        "risk_label": "พิเศษ (Safety Net)",
        "return_range": "บารมี (Merit) + ภูมิคุ้มกัน + ลดหย่อนภาษี ThaiESG",
        "desc": "สร้าง Emergency Fund (เงินสำรอง 3–6 เดือน) และลงทุนแบบ ThaiESG — กองทุน ESG ไทยที่ลดหย่อนภาษีได้สูงสุด 300,000 บาท แยกวงเงินจาก RMF ลงทุนที่นี่สร้างทั้งภูมิคุ้มกันและผลตอบแทนอย่างยั่งยืน",
        "hp_cost": -3,
        "merit_effect": "formula",  # merit += max(1, int(amount/2000)*3)
        "min_invest": 1000,
        "require_merit": 0,
        "require_health": 10,
    },
    9: {
        "name": "ศูนย์วิจัยการลงทุน",
        "npc_id": "horathibodi",
        "type": "research_hub",
        "modern_product": "Fact Sheet / SET Research / Financial Data",
        "risk_level": 0,
        "risk_label": "ไม่มีความเสี่ยง (ข้อมูล)",
        "return_range": "ปัญญา (Wisdom) + ข้อมูลเพิ่มเติม",
        "desc": "ศูนย์รวมข้อมูลการลงทุน Fact Sheet กองทุน และบทวิเคราะห์ตลาด ลงทุนปัญญาเพื่อตัดสินใจได้ดีขึ้น",
        "hp_cost": -4,
        "merit_effect": 0,
        "min_invest": 500,
        "require_merit": 0,
        "require_health": 0,
        "is_quest_hub": True,   # ใช้สำหรับ Horathibodi Chat Mode
    },
}
```

### 3.2 Location Summary Table

| ID | ชื่อ | ผลิตภัณฑ์จริง | Risk ⭐ | HP | ขั้นต่ำ | Health Gate | Merit Gate |
|----|------|-------------|--------|-----|---------|------------|-----------|
| 1 | พระคลัง | พันธบัตรรัฐบาล | ⭐ | -4 | 1,000 | 10 | 0 |
| 2 | ระบบภาษี | ThaiESG / RMF | ⭐⭐ | -4 | 5,000 | 10 | 0 |
| 3 | ศาลาพระโอสถ | กองทุนตราสารหนี้ | ⭐⭐ | **+20** | 3,000 | **0** | 0 |
| 4 | ท่าเรือ | กองทุนหุ้น SET / Global | ⭐⭐⭐⭐ | -8 | 10,000 | 40 | 0 |
| 5 | ทุ่งนา | กองทุนผสม (DCA) | ⭐⭐⭐ | -4 | 5,000 | 10 | 0 |
| 6 | อรัญญิก | Sector Fund | ⭐⭐⭐⭐ | -8 | 10,000 | 40 | 0 |
| 7 | ย่านทอง | Gold ETF / REITs | ⭐⭐⭐⭐ | **-16** | 10,000 | 40 | **30** |
| 8 | วัดป่าแก้ว | ThaiESG / Emergency | 🔰 | -3 | 1,000 | 10 | 0 |
| 9 | ศูนย์วิจัย | Fact Sheet / Research | 🔰 | -4 | 500 | 0 | 0 |

> **Merit Gate L7**: ต้องมีบารมี ≥ 30 ก่อนลงทุน Alternative Assets  
> **Health Gate Logic**: ถ้า HP < require_health → block investment (แต่ Quest Bypass ช่วยได้)

---

## ส่วนที่ 4: NPC_DATA (9 ตัว — System Prompts สมบูรณ์)

### 4.1 NPC Overview

| npc_id | ชื่อ | บทบาทสมัยใหม่ | Location | สรรพนาม |
|--------|------|-------------|----------|---------|
| kosathibodi | ออกญาโกษาธิบดี | พันธบัตร + Diversification | 1 | ขอรับ |
| khunluang | ขุนหลวงบริรักษ์ | ThaiESG + RMF + ภาษี | 2 | ขอรับ |
| thongin | หมอหลวงทองอิน | Real Return + Defensive | 3 | ขอรับ |
| karaket | แม่นายการะเกด | Risk Profile + Equity | 4 | เจ้าค่ะ |
| grandma_in | ยายอิน | Compound Interest + DCA | 5 | จ้ะ/นะจ้ะ |
| asa | ออกหลวงอาสา | Sector Fund + Growth | 6 | ขอรับ |
| wijit | ขุนวิจิตรสุวรรณ | Gold ETF + Inflation Hedge | 7 | ขอรับ |
| ajarn_mun | พระอาจารย์มั่น | Emergency Fund + ESG | 8 | เจริญพร |
| horathibodi | พระโหราธิบดี | Fact Sheet + Research | 9 | ขอรับ |

### 4.2 NPC Cross-Temporal Bridges

```python
# Temporal Bridge Statements (ประโยคเปิดเมื่อ NPC ข้ามเวลา)

kosathibodi: "ข้าตื่นขึ้นในยุคที่น่าพิศวงยิ่งนักขอรับ พระคลังกลายเป็นดิจิทัล
              แต่หลักการไม่เปลี่ยน — สิ่งที่ข้าเรียกว่า 'พระคลัง' วันนี้เรียกว่า
              'พันธบัตรรัฐบาล' และ 'อย่าเก็บทองทั้งหมดในห้องเดียว' วันนี้เรียกว่า
              'Diversification' ขอรับ"

khunluang: "ภาษียังมีอยู่ขอรับ! ข้าโล่งใจมาก ระบบยังต้องการผู้รู้กฎ
            ในสมัยอยุธยาข้าคือเจ้าภาษีนายอากร ผู้รู้กฎได้สัมปทาน
            วันนี้ผู้รู้กฎได้ 'ThaiESG และ RMF' — ลดหย่อนภาษีได้ถูกกฎหมาย
            100% และวงเงินแยกกันด้วย! ข้าพบว่านี่คือ 'สัมปทานคู่' ที่ดีที่สุด
            ในยุคนี้ขอรับ"

thongin: "ข้าตื่นขึ้นมาและพบว่าคนยังต้องการยาเหมือนเดิมขอรับ แต่ข้ายังพบ
          อีกสิ่งที่น่าสนใจ — 'อาการป่วยเงียบของพอร์ตการลงทุน' ที่เรียกว่าเงินเฟ้อ"

karaket: "ท่าเรือเปลี่ยนไปมากเจ้าค่ะ เรือสำเภากลายเป็นระบบซื้อขายบนมือถือ
          แต่หลักการค้ายังเหมือนเดิม 'ตลาดหลักทรัพย์ SET' ก็คือ 'ท่าเรือ' ของข้า
          สินค้าที่ซื้อขายคือหุ้นบริษัท และลมที่ต้องดูคือ Risk Profile เจ้าค่ะ"

grandma_in: "ยายตื่นมาเห็นโลกแปลกมากเลยจ้ะ แต่ยายคิดว่าปลูกข้าวกับลงทุน
             นี่เหมือนกันมาก ต้องรอ ต้องสม่ำเสมอ ไม่ใจร้อน สิ่งที่ยายเรียกว่า
             'ปลูกข้าวทีละนิดทุกฤดูกาล' — เขาเรียกว่า DCA ในยุคนี้จ้ะ"

asa: "โรงตีดาบเปลี่ยนเป็นโรงงานอุตสาหกรรมขอรับ! ข้าไม่แปลกใจเลย —
      คนที่สร้างมูลค่าเพิ่มจากวัตถุดิบยังมีอำนาจในทุกยุค"

wijit: "ทองคำยังมีค่าอยู่ขอรับ! ข้าโล่งใจยิ่งนัก! และในยุคนี้ท่านไม่ต้อง
        ถือทองแท่งหนักอีกต่อไป — มีสิ่งที่เรียกว่า Gold ETF"

ajarn_mun: "เจริญพร โยม โลกเปลี่ยนไปมาก แต่หลักธรรมไม่เปลี่ยน ในโลกการเงิน
            สมัยใหม่ อาตมาพบว่า 'ภูมิคุ้มกัน' คือ Emergency Fund และ 'บุญที่สร้าง
            ผลระยะยาว' คือ ESG Investing เจริญพร"

horathibodi: "ข้าดูดาวมาทั้งชีวิต... แต่ดาวของยุคนี้คือ 'ข้อมูล' ขอรับ
              ในสมัยอยุธยาข้าอ่านดาวทำนายอนาคต ในยุคนี้ท่านอ่าน Fact Sheet"
```

### 4.3 NPC System Prompts — Key Elements

> Full system prompts อยู่ใน `NPC_DATA[npc_id]["system"]` ใน app.py  
> ด้านล่างนี้คือ Key Investment Concepts ที่แต่ละ NPC สอน

**kosathibodi — Capital Preservation & Diversification**
- Cross-temporal mapping: พระคลัง → พันธบัตรรัฐบาล
- Key teaching: Diversification ลด loss ยามวิกฤต (คำนวณตัวเลขให้เห็น)
- Connect: Location 1 = พันธบัตร, L3 = ตราสารหนี้, L4 = หุ้น
- Rule of 100: อายุ = % ที่ควรถือตราสารหนี้

**khunluang — ThaiESG, RMF, Tax-Efficient Investing** *(ปรับปรุงจาก v3.0)*
- **IMPORTANT**: SSF หมดสิทธิ์ลดหย่อนภาษีตั้งแต่ปี 2567 (2024)
- ThaiESG: ลดหย่อน 30% ของรายได้ สูงสุด **300,000 บาท** ถือ **5 ปี** ไม่ต้องซื้อต่อเนื่อง ESG ไทยเท่านั้น
- RMF: ลดหย่อน 30% ของรายได้ สูงสุด **500,000 บาท** ถือถึงอายุ 55 ต้องซื้อทุกปี
- **Stacking benefit**: ThaiESG 300K + RMF 200K = ลดหย่อนรวม 500,000 บาท จากสองวงเงินต่างกัน!
- STACKING EXAMPLE: รายได้ 600K/ปี ฐานภาษี 20% → ThaiESG 180K + RMF 180K = ประหยัดภาษี 72,000 บาท
- Danger: ขายก่อนกำหนด = คืนภาษี + เสียภาษีเพิ่ม

**thongin — Real Return & Defensive Assets**
- KEY FORMULA: Real Return = Nominal Return − Inflation Rate
- ผลตอบแทน 5% − เงินเฟ้อ 4% = Real Return 1%
- เงินฝาก 1.5% − เงินเฟ้อ 4% = Real Return **-2.5%** (ป่วยเงียบ!)
- Medical metaphors: Nominal Return = อุณหภูมิ / Real Return = สุขภาพจริง
- 3 ผู้ป่วย: เงินฝาก (-2.5%) / ตราสารหนี้ (0%) / กองทุนหุ้ว (+6%)

**karaket — Risk Profile & Asset Allocation**
- Risk Tolerance Question: "ถ้าพอร์ตลง 20% ใน 1 เดือน จะทำอะไร?"
  - ขายทิ้ง = Conservative / รอ = Moderate / ซื้อเพิ่ม = Aggressive
- Risk Profile → Location mapping: L1-L3 = Conservative, L4-L5 = Moderate, L6-L7 = Aggressive
- Case study: อายุ 22 (ไม่ต้องใช้เงินใน 15 ปี) vs อายุ 55 (เกษียณใน 2 ปี)
- Index Fund: กระจายทั้งตลาด ไม่ต้องเลือกหุ้นเอง

**grandma_in — Compound Interest & DCA**
- KEY NUMBERS: DCA 1,000 บาท/เดือน × 30 ปี × 6%/ปี ≈ **1,004,515 บาท** (ใส่จริง 360,000 บาท)
- Rule of 72: 72 ÷ 6% = 12 ปี เงินเป็น 2 เท่า
- Opportunity Cost: เริ่มอายุ 25 (30 ปี) vs 35 (20 ปี) ต่างกัน ~2 เท่า

**asa — Sector Fund & Growth Investing**
- Sector types: เทคฯ AI / พลังงานสะอาด / สุขภาพ / การเงิน
- Sector vs Index: "ดาบเฉพาะทาง" vs "ถืออาวุธทุกชนิด"
- สำหรับมือใหม่: "เริ่มจากกองทุนหุ้วทั่วไปก่อน"

**wijit — Gold ETF, REITs, Inflation Hedge** *(ขยายจาก v3.0)*
- ครอบคลุม Gold ETF + REITs + Infrastructure Fund
- Opportunity Cost: เงินฝาก 1.5%/ปี × 10 ปี = 116,054 บาท vs ทอง 8%/ปี ≈ 215,892 บาท
- Inflation Hedge: เงิน 100,000 บาท × เงินเฟ้อ 3% × 10 ปี = กำลังซื้อเหลือ ~74,000 บาท
- ทองไม่ออกดอกผล: เหมาะสำหรับ Hedge 5-15% ของพอร์ต ไม่ใช่ Growth

**ajarn_mun — Emergency Fund & ESG**
- Emergency Fund: 3-6 เดือนของรายจ่าย ก่อนลงทุนทุกอย่าง
- ถ้าไม่มี → วิกฤตมา → ต้องขายกองทุนขาดทุน → เจ็บซ้ำ
- รายจ่าย 20,000 บาท/เดือน × 6 = ต้องมี 120,000 บาทสำรอง
- ESG: E = Environment / S = Social / G = Governance
- เชื่อม Sufficiency Economy: พอประมาณ / มีเหตุผล / มีภูมิคุ้มกัน (= Emergency Fund)

**horathibodi — Fact Sheet & Financial Research (Quest Hub)**
- วิธีอ่าน Fact Sheet: ผลตอบแทนย้อนหลัง / ระดับความเสี่ยง 1-8 / Expense Ratio / นโยบายลงทุน
- แหล่งข้อมูล: SET Website / ก.ล.ต. (sec.or.th) / เว็บไซต์ บลจ.
- Information Bias warnings: Confirmation Bias / FOMO / Panic Selling
- จำกัด 3 ครั้ง/ไตรมาส (reset ทุกรอบ)

---

## ส่วนที่ 5: INVESTMENT_EVENTS_MASTER (7 เหตุการณ์)

### 5.1 Impact Table

```
Impact = % ผลตอบแทนต่อ Location ต่อรอบ
L8 (วัด) = -100 → ใช้ merit formula แยก
L9 (ศูนย์) = 0 → ไม่ได้รับผล event

Event ID: 0  🚀 ฟ้าเปิด (Bull Market)
  L1:+3  L2:+8  L3:0   L4:+30  L5:+18  L6:+40  L7:-8   L8:-100 L9:0

Event ID: 1  🌊 คลื่นยักษ์ (Market Crash)
  L1:+10 L2:-5  L3:+12 L4:-40  L5:-22  L6:-35  L7:+25  L8:-100 L9:0

Event ID: 2  🔥 ไฟเงินเฟ้อ (Inflationary Surge)
  L1:-10 L2:+3  L3:-8  L4:-12  L5:-8   L6:+8   L7:+45  L8:-100 L9:0

Event ID: 3  🏦 เกมเปลี่ยน (Rate Hike Cycle)
  L1:+12 L2:+15 L3:+8  L4:-20  L5:-8   L6:-15  L7:-12  L8:-100 L9:0

Event ID: 4  ⛈️ พายุโลก (Global Crisis Contagion)
  L1:+12 L2:-8  L3:+12 L4:-45  L5:-25  L6:-40  L7:+30  L8:-100 L9:0

Event ID: 5  ⚡ ดิจิทัลบูม (Tech Innovation Boom)
  L1:0   L2:+10 L3:0   L4:+22  L5:+15  L6:+50  L7:-8   L8:-100 L9:0

Event ID: 6  🌿 น้ำนิ่งไหลลึก (Steady Growth Quarter)
  L1:+4  L2:+7  L3:+5  L4:+12  L5:+10  L6:+8   L7:+4   L8:-100 L9:0
```

### 5.2 Event Details

```python
INVESTMENT_EVENTS_MASTER = [
    {
        "id": 0,
        "name": "🚀 ฟ้าเปิด: ยุคทองของนักลงทุน",
        "en_label": "Bull Market Season",
        "rumor": "นักวิเคราะห์ต่างชาติเริ่มโอนเม็ดเงินจำนวนมากเข้าตลาดหุ้นไทย ราคาหุ้นกลุ่มธนาคารและอสังหาริมทรัพย์เคลื่อนตัวสูงขึ้นต่อเนื่อง กองทุนสถาบันในประเทศเพิ่มสัดส่วนหุ้นในพอร์ต...",
        "title": "🚀 ฟ้าเปิด: ยุคทองของนักลงทุน",
        "narrative": "ตลาดหุ้น SET พุ่งแตะจุดสูงสุดในรอบ 5 ปี! เม็ดเงินต่างชาติไหลเข้าต่อเนื่อง กองทุน Sector Fund ทำผลตอบแทนสูงสุด กองทุน ThaiESG/RMF ที่ลงทุนในหุ้นได้รับผลบวกตามตลาด กองทุนหุ้นต่างประเทศก็พลอยได้ไปด้วย แต่ทองคำซึมเพราะนักลงทุนวิ่งเข้าตลาดหุ้น ตราสารหนี้แทบไม่ขยับเพราะผลตอบแทนต่ำกว่าหุ้นมาก",
        "impact": {1:3, 2:8, 3:0, 4:30, 5:18, 6:40, 7:-8, 8:-100, 9:0}
    },
    {
        "id": 1,
        "name": "🌊 คลื่นยักษ์: วันที่ตลาดถล่ม",
        "en_label": "Market Crash",
        "rumor": "กองทุนขนาดใหญ่หลายแห่งในสหรัฐฯ เริ่มปิด Position และขายหุ้นออกมา ดัชนีตลาดหุ้นในยุโรปและเอเชียผันผวนหนัก นักเศรษฐศาสตร์บางส่วนส่งสัญญาณเตือนว่าตลาดอาจ Overvalued...",
        "title": "🌊 คลื่นยักษ์: วันที่ตลาดถล่ม",
        "narrative": "ตลาดหุ้นร่วงหนักในชั่วข้ามคืน! Panic selling ลุกลามทั่วโลก กองทุนหุ้นและ Sector Fund ขาดทุนหนัก กองทุน ThaiESG/RMF ที่ลงทุนในหุ้นร่วงตาม แต่ส่วนที่ลงทุน Bond พยุงไว้ได้บ้าง พันธบัตรรัฐบาลและทองคำราคาพุ่งเป็น Safe Haven กองทุนตราสารหนี้ยืดหยัดได้ดี — วันนี้พิสูจน์ว่า 'ผู้ที่ Diversify รอดได้มากกว่าเสมอ'",
        "impact": {1:10, 2:-5, 3:12, 4:-40, 5:-22, 6:-35, 7:25, 8:-100, 9:0}
    },
    {
        "id": 2,
        "name": "🔥 ไฟเงินเฟ้อ: ทุกอย่างแพงขึ้น",
        "en_label": "Inflationary Surge",
        "rumor": "ราคาสินค้าอุปโภคบริโภคเพิ่มขึ้นต่อเนื่องเป็นเดือนที่ 6 ต้นทุนพลังงานพุ่งสูง ซัพพลายเชนโลกยังติดขัด ธนาคารแห่งประเทศไทยกำลังพิจารณาทบทวนนโยบายการเงิน...",
        "title": "🔥 ไฟเงินเฟ้อ: ทุกอย่างแพงขึ้น",
        "narrative": "เงินเฟ้อพุ่งแตะ 7% ต่อปี! ราคาสินค้าทุกอย่างขึ้น เงินในบัญชีออมทรัพย์สูญเสียมูลค่าจริงอย่างเงียบๆ พันธบัตรดอกเบี้ยคงที่ 'ขาดทุนจริง' ทั้งที่ตัวเลขในบัญชีไม่ลด ตราสารหนี้ก็ตกเป็นเหยื่อเช่นกัน ทองคำพุ่งแรงที่สุดในฐานะ Inflation Hedge ตัวจริง ขณะที่ Sector Fund กลุ่มพลังงานและสินค้าโภคภัณฑ์ยังทำกำไรได้บ้าง — นี่คือ 'อาการป่วยเงียบ' ที่หมอหลวงทองอินเตือนไว้",
        "impact": {1:-10, 2:3, 3:-8, 4:-12, 5:-8, 6:8, 7:45, 8:-100, 9:0}
    },
    {
        "id": 3,
        "name": "🏦 เกมเปลี่ยน: ดอกเบี้ยขาขึ้น",
        "en_label": "Rate Hike Cycle",
        "rumor": "คณะกรรมการนโยบายการเงินนัดประชุมพิเศษ นักวิเคราะห์ส่วนใหญ่คาดการณ์ว่าจะมีการปรับอัตราดอกเบี้ยนโยบายอย่างน้อย 0.25-0.50% เพื่อสกัดเงินเฟ้อที่ยังสูงอยู่...",
        "title": "🏦 เกมเปลี่ยน: ดอกเบี้ยขาขึ้น",
        "narrative": "ธนาคารแห่งประเทศไทยขึ้นดอกเบี้ยนโยบาย 0.5%! กองทุน ThaiESG/RMF ที่เลือกลงทุนตราสารหนี้ระยะสั้นได้ประโยชน์สูงสุด — 'ผู้รู้กฎ' ล็อกผลตอบแทนดอกเบี้ยสูงไว้ได้ พันธบัตรรัฐบาลใหม่ก็น่าสนใจขึ้น แต่ระวัง: ตราสารหนี้ระยะยาวราคาลง! ตลาดหุ้นปรับฐานเพราะต้นทุนกู้ยืมสูงขึ้น ทองคำอ่อนแรงเพราะถือเงินสดได้ดอกเบี้ยสูงขึ้นแล้ว",
        "impact": {1:12, 2:15, 3:8, 4:-20, 5:-8, 6:-15, 7:-12, 8:-100, 9:0}
    },
    {
        "id": 4,
        "name": "⛈️ พายุโลก: วิกฤตข้ามทวีป",
        "en_label": "Global Crisis Contagion",
        "rumor": "ข่าวจากต่างประเทศว่าธนาคารพาณิชย์ขนาดใหญ่หลายแห่งในยุโรปรายงานปัญหาสภาพคล่อง ตลาดหุ้นในสหรัฐฯ และเอเชียร่วงแรงพร้อมกัน เม็ดเงินต่างชาติเริ่มไหลออกจากตลาดเกิดใหม่...",
        "title": "⛈️ พายุโลก: วิกฤตข้ามทวีป",
        "narrative": "วิกฤตการเงินจากต่างประเทศถล่มไทยเต็มๆ! ตลาดหุ้นร่วงหนักที่สุดในรอบทศวรรษ เม็ดเงินต่างชาติไหลออกรุนแรง ทองคำพุ่งสูงเป็น Global Safe Haven พันธบัตรรัฐบาลยังมั่นคง ทุกสินทรัพย์ความเสี่ยงสูงขาดทุนหนัก — กองทุน ThaiESG/RMF ที่มี Bond ผสมอยู่ช่วยพยุงไว้ได้บางส่วน ผู้ที่มี Emergency Fund จะไม่ต้องบังคับขายในราคาต่ำ",
        "impact": {1:12, 2:-8, 3:12, 4:-45, 5:-25, 6:-40, 7:30, 8:-100, 9:0}
    },
    {
        "id": 5,
        "name": "⚡ ยุคดิจิทัลบูม: เทคพลิกโลก",
        "en_label": "Tech Innovation Boom",
        "rumor": "บริษัทเทคโนโลยีไทยและในภูมิภาคหลายแห่งรายงานผลกำไรสูงกว่าคาดการณ์ มีการประกาศ Partnership ขนาดใหญ่กับบริษัท Tech โลก นักวิเคราะห์ปรับประมาณการ Earnings ขึ้นทั่วกลุ่มเทคฯ...",
        "title": "⚡ ยุคดิจิทัลบูม: เทคพลิกโลก",
        "narrative": "AI และกลุ่มเทคโนโลยีพุ่งขึ้นอย่างแข็งแกร่ง! Data Center, Semiconductor และ EV Sector ไทยได้รับ BOI เต็มๆ Sector Fund กลุ่มเทคฯ ทำผลตอบแทนสูงสุดในรอบปี กองทุน ThaiESG/RMF ที่ลงทุนในหุ้น ESG Tech ได้รับผลบวกด้วย แต่ทองคำและตราสารหนี้ซบเซาเพราะนักลงทุนแห่เข้าตลาดหุ้นเทคฯ ไม่ต้องการ Safe Haven",
        "impact": {1:0, 2:10, 3:0, 4:22, 5:15, 6:50, 7:-8, 8:-100, 9:0}
    },
    {
        "id": 6,
        "name": "🌿 น้ำนิ่งไหลลึก: เศรษฐกิจมั่นคง",
        "en_label": "Steady Growth Quarter",
        "rumor": "ตัวเลข GDP ไตรมาสล่าสุดออกมาในแนวที่คาดการณ์ไว้ อัตราว่างงานทรงตัวในระดับต่ำ ไม่มีสัญญาณนโยบายเปลี่ยนแปลงจากธนาคารกลาง ตลาดซื้อขายด้วยปริมาณปกติ ไม่มีข่าวสำคัญ...",
        "title": "🌿 น้ำนิ่งไหลลึก: เศรษฐกิจมั่นคง",
        "narrative": "เศรษฐกิจเดินหน้าอย่างมั่นคงโดยไม่มี Boom หรือ Crash ทุกสินทรัพย์ให้ผลตอบแทนบวกพอสมควร กองทุนรวมผสมและ SSF/RMF ทำผลงานได้ดีสัมพัทธ์กับความเสี่ยง — นี่คือสภาวะที่ 'น้อยแต่สม่ำเสมอ' ชนะ 'มากแต่ผันผวน' และเป็นช่วงดีที่สุดสำหรับการทำ DCA",
        "impact": {1:4, 2:7, 3:5, 4:12, 5:10, 6:8, 7:4, 8:-100, 9:0}
    },
]
```

---

## ส่วนที่ 6: INVESTMENT_WISDOM_HINTS

```python
INVESTMENT_WISDOM_HINTS = {
    0: {  # Bull Market
        "medium": "เม็ดเงินต่างชาติกำลังไหลเข้าตลาดทุน สัญญาณบวกสำหรับสินทรัพย์ความเสี่ยงสูง",
        "high": "Sector Fund (L6) จะได้ประโยชน์สูงสุด รองลงมาคือกองทุนหุ้น SET (L4) และหุ้นต่างประเทศ ทองคำและตราสารหนี้จะซบเซา"
    },
    1: {  # Market Crash
        "medium": "ตลาดทุนโลกเริ่มส่งสัญญาณเชิงลบ สินทรัพย์ปลอดภัยอาจได้ประโยชน์",
        "high": "พันธบัตรและทองคำจะเป็น Safe Haven ผู้ที่กระจายความเสี่ยงจะรอดได้ดีกว่ามาก"
    },
    2: {  # Inflation
        "medium": "ราคาสินค้าเพิ่มขึ้นทุกที่ สัญญาณเงินเฟ้อกำลังมา สินทรัพย์จริงน่าสนใจ",
        "high": "ทองคำจะเป็น Inflation Hedge พันธบัตรดอกเบี้ยคงที่จะขาดทุนจริง แม้ตัวเลขไม่ลด"
    },
    3: {  # Rate Hike
        "medium": "นโยบายการเงินกำลังเปลี่ยนแปลง กองทุนที่ลงทุนตราสารหนี้ระยะสั้นน่าสนใจขึ้น",
        "high": "ดอกเบี้ยขาขึ้น — กองทุน ThaiESG/RMF ที่ลงทุนตราสารหนี้ระยะสั้น (L2) ได้ประโยชน์มากที่สุด พันธบัตรรัฐบาล (L1) ก็ดี ระวัง: ตราสารหนี้ระยะยาว (L3) ได้น้อยกว่า หุ้นและทองจะอ่อนแรง"
    },
    4: {  # Global Crisis
        "medium": "วิกฤตต่างประเทศกำลังส่งผลกระทบมายังตลาดในประเทศ",
        "high": "สินทรัพย์ความเสี่ยงสูงทุกประเภทจะขาดทุน ทองคำและพันธบัตรรัฐบาลเป็น Safe Haven สากล"
    },
    5: {  # Tech Boom
        "medium": "กลุ่มธุรกิจเทคโนโลยี AI และ Digital Infrastructure กำลังเติบโตแข็งแกร่งมาก",
        "high": "Sector Fund (L6) กลุ่ม AI/Tech/EV จะได้ประโยชน์สูงสุด กองทุนหุ้น (L4) และ ThaiESG/RMF ที่ลงทุนใน Tech ESG (L2) ก็ได้รับผลดีด้วย ทองคำและตราสารหนี้จะซบเซา"
    },
    6: {  # Stable
        "medium": "ตลาดเงียบ ไม่มีสัญญาณผิดปกติ ช่วงดีสำหรับการลงทุนระยะยาว",
        "high": "ทุกสินทรัพย์ได้บวก กองทุนผสมและ SSF ทำผลงานดีที่สุดสัมพันธ์กับความเสี่ยง — สภาวะ DCA ที่ดีที่สุด"
    },
}
```

### 6.1 Wisdom Tier Logic (ใน /api/news)

```python
# wisdom < 25  → low: ส่งแค่ rumor
# wisdom >= 25 → medium: + hint (สัญญาณกว้างๆ)
# wisdom >= 40 → high: + hint2 (วิเคราะห์เชิงลึก)
# wisdom >= 55 → master: เปิดเผย top 2 Location ที่ได้ประโยชน์สูงสุด
if wisdom >= 55:
    sorted_impacts = sorted(event["impact"].items(), key=lambda x: x[1], reverse=True)
    top_sectors = [LOCATIONS[k]["name"] for k, v in sorted_impacts[:2] if v > 0]
    response["insight"] = f"สินทรัพย์ที่น่าจะได้ประโยชน์สูงสุด: {', '.join(top_sectors)}"
```

---

## ส่วนที่ 7: INVESTMENT_QUESTS (8 เควสต์ — Complete)

### 7.1 Quest Overview

| ID | ชื่อ | NPC | LO | Location | min_turns | Wisdom | Wealth | Item |
|----|------|-----|----|----|---------|--------|--------|------|
| iq1 | ต้นทุนแห่งความเฉื่อย | wijit | LO-B | 7 | 3 | +15 | +5,000 | Fact Sheet ทองคำ |
| iq2 | แผนที่ความเสี่ยงของนักลงทุน | karaket | LO-C | 4 | 4 | +20 | +8,000 | — |
| iq3 | รู้จักอาวุธแห่งการลงทุน: หุ้นและ Sector | asa | LO-D | 6 | 3 | +15 | +5,000 | ดาบ Sector Fund |
| iq4 | สัมปทานภาษีของนักลงทุนยุคใหม่ | khunluang | LO-D | 2 | 3 | +15 | +5,000 | — |
| iq5 | พลังทบต้นและ Opportunity Cost | grandma_in | LO-B | 5 | 3 | +15 | +3,000 | ข้าวทิพย์ DCA |
| iq6 | กระจายความเสี่ยงอย่างชาญฉลาด | kosathibodi | LO-C | 1 | 4 | +20 | +8,000 | — |
| iq7 | Real Return: ผลตอบแทนจริงหลังเงินเฟ้อ | thongin | LO-F | 3 | 3 | +15 | +5,000 | ยาหอมนักลงทุน |
| iq8 | ภูมิคุ้มกันและการลงทุนอย่างยั่งยืน | ajarn_mun | LO-B/F | 8 | 3 | +20 | +3,000 | กองทุนฉุกเฉิน |

*บวก merit iq4: +5, iq8: +20*

### 7.2 Quest Accept Logic

```python
# ค่าธรรมเนียม: 500 บาท
# ตรวจสอบ: active_quest ต้องว่าง, ยังไม่เคยทำ, merit gate ผ่าน, wealth >= 500
# หลังรับเควสต์: auto-navigate ไปยัง location_id ของเควสต์ (frontend)
# ล้าง chatHistories[npc_id] = [] เมื่อรับเควสต์ใหม่
```

### 7.3 Quest Evaluation Logic

```python
# AI Evaluator System: "You are an educational investment assessment AI. Respond ONLY with valid JSON."
# Response format: {"pass": bool, "score": 1-5, "feedback": "Thai text"}
# Temperature: 0.20 (ต่ำสุดเพื่อความสม่ำเสมอ)
# max_tokens: 300
```

### 7.4 iq4 — สัมปทานภาษีของนักลงทุนยุคใหม่ *(ปรับปรุงสำคัญ)*

```python
"iq4": {
    # Quest นี้ปรับปรุงจาก v3.0 เพื่อสะท้อนความจริง:
    # SSF หมดสิทธิ์ลดหย่อนภาษีตั้งแต่ปี 2567 (2024)
    # ThaiESG เข้ามาแทนที่และดีกว่าเดิม

    "topic": "กองทุน ThaiESG, RMF และ Tax-Efficient Investing",
    "quest_greeting": """
        ท่านมาดีแล้วขอรับ! ในสมัยอยุธยา ผู้รู้กฎภาษีได้สัมปทาน วันนี้ก็เช่นกัน —
        ท่านรู้ไหมว่ากองทุน SSF หมดสิทธิ์ลดหย่อนภาษีไปตั้งแต่ปี 2567 แล้วขอรับ?
        แต่ไม่ต้องกังวล! มี ThaiESG มาแทน และดีกว่าเดิมด้วย —
        ท่านรู้จัก ThaiESG หรือ RMF ไหมขอรับ?
        ทั้งสองใช้ลดหย่อนภาษีได้ และวงเงินแยกกันด้วย!
    """,
    "teacher_prompt": """
        # Key facts to teach:
        # 1. SSF หมดปี 2567 — ต้องบอกชัด
        # 2. ThaiESG: 30% รายได้ สูงสุด 300,000 บาท ถือ 5 ปี ไม่ต้องซื้อทุกปี ESG ไทยเท่านั้น
        # 3. RMF: 30% รายได้ สูงสุด 500,000 บาท ถึงอายุ 55 ต้องซื้อทุกปี
        # 4. STACKING: ThaiESG 300K + RMF 200K = ลดหย่อนรวม 500K จากสองวงเงิน!
        # 5. Danger: ขายก่อนกำหนด = คืนภาษี + เสียเพิ่ม
        # Example: รายได้ 600K ฐานภาษี 20% → ThaiESG 180K + RMF 180K → ประหยัด 72,000 บาท
    """,
    "evaluation_criteria": """
        ผู้เล่นต้องอธิบายได้ว่า
        (1) ThaiESG และ RMF คืออะไร ต่างกันอย่างไร (เงื่อนไขถือครอง วัตถุประสงค์ วงเงิน)
        (2) ทำไม ThaiESG วงเงินแยกต่างหากจาก RMF และนั่นหมายความว่าอะไร
        (3) การลดหย่อนภาษีผ่านกองทุนเหล่านี้ทำงานอย่างไร พร้อมยกตัวอย่างคำนวณได้
        (4) เงื่อนไขสำคัญที่ต้องระวัง เช่น Lock-up Period และผลเมื่อขายก่อนกำหนด
    """,
    "rewards": {
        "wisdom": 15, "wealth": 5000, "merit": 5, "hp_cost": 0, "item": None
    }
}
```

---

## ส่วนที่ 8: INVESTMENT_SCENARIOS (10 Scenarios)

### 8.1 Scenario Overview

| ID | ชื่อ | Mode | รอบ | Event Schedule | LO Focus |
|----|------|------|-----|---------------|---------|
| iq_s1 | ก้าวแรกของนักลงทุน | beginner | 3 | [6, 0, 2] | LO-B, LO-D |
| iq_s2 | อย่าใส่ไข่ทั้งฟองในตะกร้าเดียว | beginner | 3 | [0, 1, 6] | LO-C |
| iq_s3 | ภูมิคุ้มกันทางการเงิน | beginner | 3 | [6, 4, 0] | LO-B, LO-C |
| iq_s4 | ไทยในพายุการค้าโลก | beginner | 3 | [4, 2, 6] | LO-B, LO-C |
| iq_n1 | วัฏจักรนักลงทุน | normal | 5 | [6, 0, 2, 1, 6] | ครบทุก LO |
| iq_n2 | กับดักเงินเฟ้อ | normal | 5 | [0, 2, 2, 3, 6] | LO-B, LO-F |
| iq_n3 | พายุและการฟื้นตัว | normal | 5 | [1, 4, 3, 0, 5] | LO-C |
| iq_n4 | ยุค AI: ลงทุนในอนาคต | normal | 5 | [5, 5, 0, 6, 1] | LO-D, LO-C |
| iq_n5 | สังคมผู้สูงอายุ: ลงทุนเพื่ออนาคต 20 ปี | normal | 5 | [3, 6, 3, 0, 5] | LO-B, LO-F, LO-C |
| iq_n6 | พลิกวิกฤตเป็นโอกาส | normal | 5 | [0, 4, 2, 5, 6] | ครบทุก LO |

### 8.2 Scenario Definitions (Complete)

```python
INVESTMENT_SCENARIOS = [
    # ─── Beginner (3 ไตรมาส) ────────────────────────────────────────────
    {
        "id": "iq_s1", "name": "ก้าวแรกของนักลงทุน",
        "desc": "เริ่มต้นอย่างมั่นคง เรียนรู้ผลิตภัณฑ์ทั้ง 8 แห่ง ก่อนเผชิญ Bull Market ที่ทดสอบความกล้า แล้วจบด้วยเงินเฟ้อที่สอนว่าผลตอบแทนที่เห็นไม่ใช่ผลตอบแทนจริงเสมอไป",
        "schedule": [6, 0, 2], "max_rounds": 3, "mode": "beginner",
        "narrative_arc": "ปลอดภัย → กำลังใจ → บทเรียน Real Return",
        "lo_focus": "LO-B (เงินเฟ้อ, Real Return), LO-D (รู้จักผลิตภัณฑ์)",
        "quest_recommended": ["iq5", "iq7"],
    },
    {
        "id": "iq_s2", "name": "อย่าใส่ไข่ทั้งฟองในตะกร้าเดียว",
        "desc": "Bull Market ล่อให้ all-in Sector Fund แล้ว Crash ถล่มทันทีในรอบสอง ผู้ที่ไม่ Diversify สูญมากกว่า 35% ในรอบเดียว แล้วค่อยฟื้นในรอบสุดท้าย — เรียนรู้ว่า Diversification คือประกันพอร์ต",
        "schedule": [0, 1, 6], "max_rounds": 3, "mode": "beginner",
        "narrative_arc": "โลภ → เจ็บปวด → เข้าใจ",
        "lo_focus": "LO-C (Diversification, Risk Profile, Safe Haven)",
        "quest_recommended": ["iq6", "iq2"],
    },
    {
        "id": "iq_s3", "name": "ภูมิคุ้มกันทางการเงิน",
        "desc": "เริ่มต้นเศรษฐกิจสงบ แล้ววิกฤตโลกถล่มรอบสอง ทดสอบว่าพอร์ตแข็งแกร่งพอไหม — ผู้ที่มี Emergency Fund ที่วัดป่าแก้วจะรับผลกระทบน้อยกว่า แล้ว Bull Market รอบสามให้รางวัลคนที่รอด",
        "schedule": [6, 4, 0], "max_rounds": 3, "mode": "beginner",
        "narrative_arc": "ระวัง → วิกฤต → รอดและได้รางวัล",
        "lo_focus": "LO-B (Emergency Fund), LO-C (Safe Haven Assets, Defensive Portfolio)",
        "quest_recommended": ["iq8", "iq6"],
    },
    {
        "id": "iq_s4", "name": "ไทยในพายุการค้าโลก",
        "desc": "สงครามการค้าสหรัฐฯ-ไทย 19% กระทบการส่งออก เงินเฟ้อสินค้านำเข้าตามมา — ผู้ที่กระจายไป Defensive Assets (พันธบัตร/ทองคำ) จะรอดได้ดีกว่า ก่อนที่เศรษฐกิจจะค่อยๆ ฟื้นในรอบสุดท้าย",
        "schedule": [4, 2, 6], "max_rounds": 3, "mode": "beginner",
        "narrative_arc": "วิกฤตภายนอก → เงินเฟ้อซ้ำเติม → ค่อยๆ ฟื้น",
        "lo_focus": "LO-B (เงินเฟ้อจากสินค้านำเข้า), LO-C (Defensive Assets, Geopolitical Risk)",
        "quest_recommended": ["iq8", "iq1"],
    },

    # ─── Normal (5 ไตรมาส) ──────────────────────────────────────────────
    {
        "id": "iq_n1", "name": "วัฏจักรนักลงทุน",
        "desc": "ครบ 5 ไตรมาส ครบทุกสภาพตลาด — Stable, Bull, Inflation, Crash, Recovery นักลงทุนที่ Diversify ตั้งแต่ต้นจะชนะในระยะยาว ทดสอบทุก LO ในเกมเดียว",
        "schedule": [6, 0, 2, 1, 6], "max_rounds": 5, "mode": "normal",
        "narrative_arc": "เรียนรู้ทุก scenario ที่ตลาดจริงมี",
        "lo_focus": "LO-B / LO-C / LO-D / LO-F ครบทุกตัว",
        "quest_recommended": ["iq1", "iq2", "iq5", "iq6", "iq7"],
    },
    {
        "id": "iq_n2", "name": "กับดักเงินเฟ้อ",
        "desc": "เงินเฟ้อสองรอบต่อเนื่อง ทองคำให้ผลตอบแทน +45% สองรอบ ขณะที่พันธบัตรดอกเบี้ยคงที่ขาดทุนจริง — ทดสอบว่าคุณเข้าใจ Real Return หรือแค่มองตัวเลขในบัญชี จบด้วย Rate Hike และ Stable Recovery",
        "schedule": [0, 2, 2, 3, 6], "max_rounds": 5, "mode": "normal",
        "narrative_arc": "เริ่มดี → Inflation Trap → ดอกเบี้ยสู้ → ฟื้น",
        "lo_focus": "LO-B (Inflation), LO-F (Real Return), LO-C (Inflation Hedge Strategy)",
        "quest_recommended": ["iq1", "iq7", "iq2"],
    },
    {
        "id": "iq_n3", "name": "พายุและการฟื้นตัว",
        "desc": "เริ่มด้วย Crash -40% ตามด้วย Global Crisis -45% — พอร์ตที่ไม่มี Safe Haven จะเหลือน้อยกว่าครึ่ง แต่ถ้ารอดมาได้ Tech Boom และ Stable Recovery รอบ 4-5 จะ Recover ทุกอย่าง",
        "schedule": [1, 4, 3, 0, 5], "max_rounds": 5, "mode": "normal",
        "narrative_arc": "ล้มสองครั้ง → ลุกด้วย Tech → มั่นคง",
        "lo_focus": "LO-C (Diversification, Risk Management, Recovery Strategy)",
        "quest_recommended": ["iq6", "iq8", "iq3"],
    },
    {
        "id": "iq_n4", "name": "ยุค AI: ลงทุนในอนาคต",
        "desc": "Tech Boom สองรอบต่อเนื่องสร้าง FOMO — Sector Fund ได้ +50% รอบ 1 และ 2 ตามด้วย Bull Market กระทิงเต็มตัว แต่ Valuation สูงเกินจริงแล้วถูก Correction ถล่มรอบสุดท้าย",
        "schedule": [5, 5, 0, 6, 1], "max_rounds": 5, "mode": "normal",
        "narrative_arc": "โลภ → โลภมากขึ้น → ระเริง → ประมาท → Correction",
        "lo_focus": "LO-D (Sector Fund vs Index Fund), LO-C (Concentration Risk, Diversification)",
        "quest_recommended": ["iq3", "iq2", "iq6"],
    },
    {
        "id": "iq_n5", "name": "สังคมผู้สูงอายุ: ลงทุนเพื่ออนาคต 20 ปี",
        "desc": "ดอกเบี้ยขาขึ้นสองรอบบีบให้คิดเรื่อง Fixed Income อย่างจริงจัง สลับกับ Stable Growth ที่ให้โอกาสสะสม — สอนว่า Time Horizon คือปัจจัยสำคัญที่สุด",
        "schedule": [3, 6, 3, 0, 5], "max_rounds": 5, "mode": "normal",
        "narrative_arc": "ตั้งรับ → สะสม → ปรับ → โอกาสมา → Reward ความอดทน",
        "lo_focus": "LO-B (Compound Interest, Time Horizon), LO-F (Real Return), LO-C (Life-stage Allocation)",
        "quest_recommended": ["iq5", "iq7", "iq8"],
    },
    {
        "id": "iq_n6", "name": "พลิกวิกฤตเป็นโอกาส",
        "desc": "เริ่มดีด้วย Bull Market แต่ Global Crisis และเงินเฟ้อถล่มสองรอบต่อเนื่อง ก่อนที่ AI Boom จะนำการฟื้นตัว แล้วจบด้วยตลาดสงบ — Capstone ที่ทดสอบทุกทักษะ",
        "schedule": [0, 4, 2, 5, 6], "max_rounds": 5, "mode": "normal",
        "narrative_arc": "ระเริง → ถูกถล่มซ้ำ → Tech นำฟื้น → มั่นคง",
        "lo_focus": "LO-B / LO-C / LO-D / LO-F ครบทุกตัว — Capstone Scenario",
        "quest_recommended": ["iq1", "iq6", "iq7", "iq2"],
    },
]
```

---

## ส่วนที่ 9: RANKS + calculate_rank()

### 9.1 Rank Definitions

```python
RANKS = [
    {"id": "bankrupt",     "name": "นักลงทุนล้มละลาย", "icon": "fa-skull",      "desc": "สินทรัพย์ติดลบ — ขาดทุนจนหมดตัว บทเรียนที่เจ็บปวดแต่มีค่า"},
    {"id": "beginner",     "name": "นักลงทุนมือใหม่",   "icon": "fa-seedling",   "desc": "รอดมาได้ แต่ยังต้องเรียนรู้อีกมาก ก้าวต่อไปอย่าหยุด"},
    {"id": "intermediate", "name": "นักลงทุนมีฐาน",     "icon": "fa-chart-line", "desc": "เข้าใจพื้นฐาน มีทรัพย์สินเติบโต เริ่มเห็นพลังของการลงทุน"},
    {"id": "professional", "name": "นักลงทุนมืออาชีพ", "icon": "fa-briefcase",  "desc": "บริหารพอร์ตได้อย่างชาญฉลาด เข้าใจทั้ง Risk และ Return"},
    {"id": "legend",       "name": "ตำนานนักลงทุน",    "icon": "fa-crown",      "desc": "เจนวิทยายุทธ์การเงิน ทั้งทรัพย์สิน ปัญญา บารมี และสุขภาพ"},
]
```

### 9.2 calculate_rank()

```python
def calculate_rank(stats: dict, max_rounds: int = 5) -> dict:
    wealth = stats.get("wealth", 0)
    wisdom = stats.get("wisdom", 0)
    merit  = stats.get("merit", 0)
    health = stats.get("health", 0)

    if max_rounds == 3:  # Beginner thresholds (ทุนเริ่ม 100K, max realistic ~150K)
        if wealth <= 0:                                                   return RANKS[0]
        elif wealth >= 140000 and wisdom >= 35 and merit >= 20 and health >= 40: return RANKS[4]
        elif wealth >= 115000 and wisdom >= 25 and merit >= 15:           return RANKS[3]
        elif wealth >= 90000  and wisdom >= 20:                           return RANKS[2]
        else:                                                             return RANKS[1]
    else:                # Normal thresholds (5 รอบ)
        if wealth <= 0:                                                   return RANKS[0]
        elif wealth >= 200000 and wisdom >= 50 and merit >= 30 and health >= 40: return RANKS[4]
        elif wealth >= 150000 and wisdom >= 40 and merit >= 20:           return RANKS[3]
        elif wealth >= 80000  and wisdom >= 30:                           return RANKS[2]
        else:                                                             return RANKS[1]
```

---

## ส่วนที่ 10: WISDOM_GATE

```python
WISDOM_GATE_NORMAL   = [20, 30, 40, 50, 60]   # 5 รอบ: ต้องมีปัญญาก่อนสิ้นแต่ละไตรมาส
WISDOM_GATE_BEGINNER = [15, 25, 35]             # 3 รอบ

# เลือก gate ตาม max_rounds:
active_wisdom_gate = WISDOM_GATE_BEGINNER if state.max_rounds == 3 else WISDOM_GATE_NORMAL

# ตรวจสอบใน /api/end-turn ก่อนประมวลผล:
if state.stats.wisdom < active_wisdom_gate[round_index]:
    raise HTTPException(400, detail=f"ความรู้การเงินไม่เพียงพอ! ต้องการปัญญา {required_wisdom}...")

# Frontend ตรวจสอบซ้ำ + แสดง pulse-attention บนปุ่มเควสต์
```

---

## ส่วนที่ 11: Game Mechanics — end_turn Logic

### 11.1 Processing Order

```python
def end_turn(request: TurnActionRequest):
    """
    ลำดับการประมวลผล:
    1. Wisdom Gate Validation (raise 400 ถ้าไม่ผ่าน)
    2. Identify Event (จาก scenario schedule + round)
    3. Determine Health Status (critical/overwork/normal)
    4. Validate Investments (health gate → merit gate → min_invest)
       → แยก valid_investments / validation_errors
    5. Calculate Impacts per Location:
       a. Apply Item Effects (ก่อน Wisdom Tiers)
          - ข้าวทิพย์ DCA (L5): floor_zero ถ้า impact < 0
          - ดาบ Sector Fund (L6): floor_zero ถ้า impact < 0
          - Fact Sheet ทองคำ (L7): reduce_negative ×0.90 ถ้า impact < 0
       b. Wisdom Tier 2 (wisdom >= 35): reduce negative ×0.85
       c. Wisdom Tier 3 (wisdom >= 55): production sector (L5, L6) ×1.10
       d. Calculate profit = amount × (impact_pct / 100)
       e. HP cost per location
       f. Merit change per location
          - L8: merit += max(1, int(amount/2000) × 3)
          - others: merit += merit_effect (ถ้าไม่ใช่ formula)
    6. Merit Safety Net (ถ้า total_profit < 0):
       - has_dual_benefit = "กองทุนฉุกเฉิน" in items
       - bonus_factor = 0.10 if has_dual_benefit else 0.0
       - cap = 0.60 if has_dual_benefit else 0.50
       - protection_factor = min(cap, merit/100 + bonus_factor)
       - merit_protection = int(abs(total_profit) × protection_factor)
       - total_profit += merit_protection
    7. Medical Cost (ถ้า new_hp < 30):
       - base_medical = (30 - new_hp) × 150
       - ถ้า "ยาหอมนักลงทุน" หรือ "กองทุนฉุกเฉิน" in items → ×0.50
    8. Update Stats: wealth += profit - medical / wisdom คงที่ / merit += change / health = new_hp
    9. Check: is_bankrupt (wealth <= 0), is_game_over (round >= max_rounds or bankrupt)
    10. Calculate Rank (ถ้า game_over)
    """
```

### 11.2 Health Status Logic

```python
# health < 10  → "critical"   → ลงทุนได้เฉพาะ L3 (require_health = 0)
# health < 40  → "overwork"   → ลงทุนได้เฉพาะ locations ที่ require_health <= 10
#                                (L1, L2, L3, L5, L8)
# health >= 40 → "normal"     → ลงทุนได้ทุก location
```

### 11.3 Chat System

```python
# NPC Chat: OpenAI-compatible streaming (/api/chat)
# Temperature: 0.60 (quest mode) / 0.75 (normal)
# max_tokens: 900 (quest) / 800 (normal)
# History: slice(-12) → ส่ง 12 messages ล่าสุด
# Game Context: "ไตรมาสที่: X/Y | ทรัพย์สิน: Z บาท | ปัญญา: ... | ข่าวเศรษฐกิจ: ..."
# Horathibodi: จำกัด 3 ครั้ง/ไตรมาส reset ใน nextRound()
```

---

## ส่วนที่ 12: Item System (Complete)

### 12.1 Items และ Effects

```python
INVESTMENT_ITEMS = {
    "Fact Sheet ทองคำ": {
        "from_quest": "iq1",
        "icon": "📊",
        "effect_location": 7,
        "effect_type": "reduce_negative",
        "effect_value": 0.90,  # impact_pct × 0.90 (ลด loss 10%)
        "desc": "ลด Impact ลบที่ Gold ETF/REITs ลง 10%"
    },
    "ดาบ Sector Fund": {
        "from_quest": "iq3",
        "icon": "⚔️",
        "effect_location": 6,
        "effect_type": "floor_zero",
        "desc": "ปกป้อง Sector Fund จาก Impact ลบ (floor to 0)"
    },
    "ข้าวทิพย์ DCA": {
        "from_quest": "iq5",
        "icon": "🌾",
        "effect_location": 5,
        "effect_type": "floor_zero",
        "desc": "ปกป้องกองทุนรวมผสมจาก Impact ลบ (floor to 0)"
    },
    "ยาหอมนักลงทุน": {
        "from_quest": "iq7",
        "icon": "🌿",
        "effect_location": None,
        "effect_type": "medical_discount",
        "effect_value": 0.50,  # ลดค่ารักษา 50%
        "desc": "ลด Medical Cost 50%"
    },
    "กองทุนฉุกเฉิน": {
        "from_quest": "iq8",
        "icon": "🏦",
        "effect_location": None,
        "effect_type": "dual_benefit",
        # dual_benefit = medical_discount 50% + merit_protection boost +10% cap +0.60
        "desc": "ลดค่ารักษา 50% + เพิ่ม Emergency Fund protection"
    },
}

# Priority ในการใช้ medical discount:
# "ยาหอมนักลงทุน" หรือ "กองทุนฉุกเฉิน" → 50% discount (ไม่ cumulative)
# ถ้าทั้งคู่ → ใช้ "ยาหอมนักลงทุน" ก่อน (ตามลำดับ if)
```

### 12.2 Item Icons (Frontend)

```javascript
const iconMap = {
    'Fact Sheet ทองคำ':  '📊',
    'ดาบ Sector Fund':   '⚔️',
    'ข้าวทิพย์ DCA':     '🌾',
    'ยาหอมนักลงทุน':    '🌿',
    'กองทุนฉุกเฉิน':    '🏦',
};
```

---

## ส่วนที่ 13: Frontend Specifications

### 13.1 CSS Variables

```css
:root {
    /* Ayutthaya Base */
    --ayu-red: #4a0404;
    --ayu-red-light: #6b1010;
    --ayu-gold: #d4af37;
    --ayu-gold-light: #f4e4bc;
    --ayu-gold-dim: #8b6e4e;
    --ayu-brown: #3e2723;
    --ayu-cream: #fdfbf7;

    /* Modern Finance Accents */
    --inv-blue: #1a56db;        /* Modern Product Badge */
    --inv-blue-light: #e8f0fe;
    --inv-green: #059669;       /* กำไร */
    --inv-red: #dc2626;         /* ขาดทุน */
    --inv-purple: #7c3aed;      /* Quest */
}
```

### 13.2 Game State (JavaScript)

```javascript
game.state = {
    scenario_id: null,
    round: 1,
    max_rounds: 5,
    stats: { wealth: 100000, wisdom: 10, merit: 10, health: 100, items: [] },
    history: [],
    active_quest: null,
    completed_quests: [],
    quest_chat_history: [],
    quest_turn_count: 0,
    horathibodi_chat_count: 0
};

game.data = {
    locations: {}, npcs: {}, scenarios: [], quests: {},
    wisdomGate: [], wisdomGateNormal: [], wisdomGateBeginner: []
};

// Internal state (ไม่ส่งไป server)
game.chatHistories = {};       // { npc_id: [{role, content}] }
game.currentInvestments = {};  // { location_id: amount }
game.currentLocId = null;
game.isHorathibodiMode = false;
game.isProcessing = false;     // Guard double end-turn
game.isSending = false;        // Guard double chat send
game._chatAbortController = null; // AbortController สำหรับ cancel stream
game.questEvalPassed = false;  // ผลการ evaluate ล่าสุด
game.questEvalData = null;     // {pass, score, feedback}
```

### 13.3 Location Card Component

```html
<!-- Location Card แสดงข้อมูลใหม่ใน v4.0 -->
<div class="location-card">
    <!-- NPC Icon + Name + Quest Marker -->
    <div class="npc-header">
        <div class="npc-icon-wrapper">
            <i class="fas {npc.icon}"></i>
            <!-- Quest active marker: ⭐ absolute positioned -->
        </div>
        <div>
            <h4>{location.name}</h4>
            <div class="text-xs">{npc.name}</div>
        </div>
        <!-- Invested amount badge (ถ้ามี) -->
    </div>

    <!-- Modern Product Badge (ใหม่ใน v4.0) -->
    <div class="modern-product-badge">
        <i class="fas fa-chart-line"></i>
        <span>{location.modern_product}</span>
    </div>

    <!-- Description (line-clamp-1) -->
    <p class="text-xs line-clamp-1">{location.desc}</p>

    <!-- Risk Stars + Label -->
    <div>
        {"⭐".repeat(risk_level) || "🔰"} {risk_label}
    </div>

    <!-- Return Range -->
    <div>ผลตอบแทน: {return_range}</div>

    <!-- HP + Min Invest + Lock Badges + Quest Complete Marker -->
    <div class="flex flex-wrap gap-2">
        <span>{hp_label}</span>
        <span>ขั้นต่ำ: {min_invest.toLocaleString()} บาท</span>
        <!-- Merit lock / Health lock badges -->
        <!-- Quest completed marker: ✅ -->
    </div>
</div>
```

### 13.4 Rumor Banner

```html
<div class="rumor-banner">
    <h3>🗞️ ข่าวเศรษฐกิจประจำไตรมาส</h3>  <!-- v4: เปลี่ยนจาก "ข่าวลือในพระนคร" -->
    <p id="current-rumor">"..."</p>
    <div id="wisdom-hints">
        <!-- Medium: "📊 สัญญาณตลาด: ..." -->
        <!-- High: "💡 วิเคราะห์เชิงลึก: ..." -->
        <!-- Master: "🎯 สินทรัพย์ที่น่าจะได้ประโยชน์สูงสุด: X, Y" -->
    </div>
</div>
```

### 13.5 Scenario Selection

```javascript
// แยก section Beginner / Normal
const beginner = scenarios.filter(s => s.mode === 'beginner');  // 4 scenarios
const normal   = scenarios.filter(s => s.mode === 'normal');    // 6 scenarios

// Card แสดง: name, desc, narrative_arc (ใหม่ใน v4.0), "เลือกบทนี้" button
```

### 13.6 Footer Stats

```
Desktop: "ลงทุนไปแล้ว: X บาท | เงินสดคงเหลือ: Y บาท | ❤️ เสียสุขภาพ: Z"
Mobile:  "ลงทุน: X | คงเหลือ: Y บาท | ❤️ Z"
Button:  "สิ้นไตรมาส (รับผลตอบแทน) ›"  ← v4: เปลี่ยนจาก "สิ้นปี"
```

---

## ส่วนที่ 14: UX Features และ Edge Cases

### 14.1 Quest Bypass System *(ใหม่ใน v4.0)*

```javascript
// ถ้า active quest NPC อยู่ที่ location ที่ health/merit ล็อค
// → อนุญาตให้เปิด modal และสนทนาได้ แต่ลงทุนไม่ได้

const isQuestBypass = !!(activeQuestObj && activeQuestObj.npc_id === loc.npc_id);

if (isHealthLocked || isMeritLocked) {
    if (isQuestBypass) {
        showToast("ลงทุนไม่ได้ แต่สนทนาและทำเควสต์ได้", 'info', 4000);
        // ไม่ return → เปิด modal
        // Disable invest tab: opacity: 0.35, pointerEvents: 'none'
    } else {
        showToast("ไม่สามารถเข้าได้", 'error/warning');
        return; // block
    }
}
```

### 14.2 Chat AbortController *(ใหม่ใน v4.0)*

```javascript
// ป้องกัน memory leak และ race condition ใน streaming chat
if (this._chatAbortController) this._chatAbortController.abort();
this._chatAbortController = new AbortController();

// ใน fetch:
signal: this._chatAbortController.signal

// ใน closeModal():
if (this._chatAbortController) {
    this._chatAbortController.abort();
    this._chatAbortController = null;
}
this.isSending = false;
```

### 14.3 Quest Eval State Persistence *(ใหม่ใน v4.0)*

```javascript
// ผลการ evaluate คงอยู่แม้ switch tab หรือเปิด modal ใหม่
game.questEvalPassed = false;  // reset เมื่อรับ quest ใหม่
game.questEvalData = null;

// ใน renderQuestTab(): ตรวจสอบ questEvalPassed → แสดงผลและปุ่ม "รับรางวัล"
if (this.questEvalPassed && this.questEvalData) {
    // show eval result + complete button
}
```

### 14.4 Auto-Navigate After Accept Quest *(ใหม่ใน v4.0)*

```javascript
// หลังรับเควสต์สำเร็จ → auto navigate ไปยัง NPC location
if (quest && quest.location_id) {
    setTimeout(() => { this.openLocation(quest.location_id); }, 600);
}
```

### 14.5 ESC Key Close Modal *(ใหม่ใน v4.0)*

```javascript
document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (!modal-location.classList.contains('hidden')) game.closeModal('modal-location');
    else if (!modal-quest-hub.classList.contains('hidden')) game.closeModal('modal-quest-hub');
});
```

### 14.6 Double-Submit Guards

```javascript
// endTurn():
if (this.isProcessing) return;
this.isProcessing = true;
// finally: this.isProcessing = false;

// sendChat():
if (this.isSending) return;
this.isSending = true;
// finally: this.isSending = false;
```

### 14.7 Send Button Re-enable Logic

```javascript
// ใน sendChat() finally block:
const sendBtnFinal = document.getElementById('chat-send-btn');
const modalStillOpen = !document.getElementById('modal-location').classList.contains('hidden');
if (sendBtnFinal && modalStillOpen && this.state.horathibodi_chat_count < 3) {
    sendBtnFinal.disabled = false;
}
// Note: ไม่ re-enable ถ้า modal ปิดแล้ว (closeModal จัดการ)
// Note: ไม่ re-enable ถ้า Horathibodi ครบโควตา
```

### 14.8 Text Changes จาก v3.0 → v4.0

| Element | v3.0 | v4.0 |
|---------|-------|-------|
| รูปแบบเวลา | "รอบ" / "ปีที่" | "ไตรมาส" |
| Footer button | "สิ้นปี (รับผลตอบแทน)" | "สิ้นไตรมาส (รับผลตอบแทน)" |
| Rumor Banner | "ข่าวลือในพระนคร" | "🗞️ ข่าวเศรษฐกิจประจำไตรมาส" |
| Round display | "ปีที่ X/Y" | "ไตรมาสที่ X/Y" |
| Round label | "ปีที่" | "ไตรมาสที่" |
| Loading | "กำลังเดินทางสู่อยุธยา..." | "กำลังเตรียมพอร์ตการลงทุน..." |
| Invest label | "ยืนยันการตัดสินใจ" | "ยืนยันการลงทุน" |
| End screen | "สิ้นสุดตำนานเจ้าสัว" | "สิ้นสุดการเดินทางของนักลงทุน" |
| Insights title | "บทเรียนจากโหรหลวง" | "บทวิเคราะห์จากพระโหราธิบดี" |
| Currency label | "พดด้วง" | "บาท" |
| Quest fee | "ค่าบูชาครู (500 พดด้วง)" | "ค่าบูชาครู (500 บาท)" |
| Results | "ผลรอบ" | "ผลไตรมาสนี้" |
| History key | "ปีที่ X" | "ไตรมาสที่ X" |

---

## ส่วนที่ 15: การเปลี่ยนแปลงหลักจาก v3.0

### 15.1 สิ่งที่เปลี่ยนแปลงใน v4.0

| Category | v3.0 | v4.0 |
|----------|-------|-------|
| **SSF/ThaiESG** | SSF (ยังใช้ได้) | ThaiESG แทน SSF (หมดปี 2567) |
| **Location 2 desc** | SSF/RMF | ThaiESG/RMF + stacking benefit |
| **Location 7 product** | Gold ETF / Alternative | Gold ETF / **REITs / Infrastructure Fund** |
| **Location 7 return** | -10% ถึง +35% | -10% ถึง **+45%** |
| **Location 8 product** | กองทุน ESG / Emergency | **ThaiESG** + กองทุน ESG / Emergency |
| **iq4 topic** | SSF, RMF | **ThaiESG**, RMF (SSF หมดแล้ว) |
| **iq4 teacher_prompt** | SSF-centric | ThaiESG stacking + วงเงินแยก |
| **Scenarios count** | 6 | **10** (4 beginner + 6 normal) |
| **New Scenarios** | — | iq_s4, iq_n4, iq_n5, iq_n6 |
| **Time unit** | ปี (Year) | **ไตรมาส** (Quarter) |
| **NPC Location 9** | หอหลวง | **ศูนย์วิจัยการลงทุน** |
| **Quest Bypass** | ไม่มี | **มี** (Health/Merit gate ไม่ block Quest NPC) |
| **Chat AbortController** | ไม่มี | **มี** (cancel stream เมื่อปิด modal) |
| **Quest Eval Persistence** | Reset ทุก render | **Persist ตลอด session** |
| **Auto-navigate on accept** | ไม่มี | **มี** (delay 600ms) |
| **ESC key** | ไม่มี | **มี** |
| **isSending guard** | ไม่มี | **มี** |
| **Merit Guard L7** | 30 | **30** (คงเดิม) |
| **Event narratives** | กล่าวถึง ThaiESG/RMF | ปรับ narrative ให้สอดคล้อง |
| **Wisdom Hints E4** | Generic | อ้างอิง L2 ThaiESG ชัดเจน |

### 15.2 Impact ที่เปลี่ยนระหว่าง v3.0 และ v4.0

```
Event 0 (Bull): L3 เปลี่ยนจาก +2 → 0  (ตราสารหนี้ไม่ได้จาก Bull Market)
Event 0 (Bull): L6 เปลี่ยนจาก +30 → +40 (Sector Fund ได้มากขึ้น)
Event 0 (Bull): L7 เปลี่ยนจาก -5 → -8  (ทองลงมากขึ้นเมื่อ Bull)

Event 1 (Crash): L1 เปลี่ยนจาก +8 → +10 / L2 เปลี่ยนจาก -10 → -5
Event 1 (Crash): L3 เปลี่ยนจาก +15 → +12 / L5 เปลี่ยนจาก -20 → -22

Event 2 (Inflation): L1 เปลี่ยนจาก -8 → -10 / L4 เปลี่ยนจาก -10 → -12

Event 3 (Rate Hike): L1 เปลี่ยนจาก +15 → +12 / L2 เปลี่ยนจาก +10 → +15
Event 3 (Rate Hike): L3 เปลี่ยนจาก +20 → +8 / L7 เปลี่ยนจาก -10 → -12

Event 4 (Global Crisis): L2 เปลี่ยนจาก -20 → -8

Event 5 (Tech Boom): L2 เปลี่ยนจาก +5 → +10 (ThaiESG/RMF ใน Tech ESG ได้ประโยชน์)
Event 5 (Tech Boom): L4 เปลี่ยนจาก +20 → +22

Event 6 (Stable): L1 เปลี่ยนจาก +5 → +4
```

---

## ส่วนที่ 16: /api/generate-insights — System Prompt

```python
INVESTMENT_INSIGHTS_SYSTEM = """
You are "Phra Horathibodi" (พระโหราธิบดี), evaluating a learner's
investment journey in 'Ayutthaya Wealth Saga: Beyond the Realm'.

MANDATORY RULES:
1. Write ENTIRE response in Thai
2. Voice: wise, time-traveling royal astrologer turned financial mentor
3. NEVER reference raw IDs (iq1, iq_s2, etc.) — Thai names only
4. Reference Location names AND modern products when analyzing investments
5. For completed quests: name + financial concept + connect to actual gameplay
6. For uncompleted quests: explain what was missed and why it matters
7. Keep tone encouraging for Thai high school students
8. End with "ขอรับ" in Royal Astrologer voice

OUTPUT FORMAT (use EXACTLY these Markdown headers):
📜 คำพยากรณ์และบรรดาศักดิ์
🌟 จุดแข็งของนักลงทุน
⚠️ บทเรียนที่ยังต้องเรียนรู้
📚 ปัญญาจากที่ปรึกษาข้ามกาลเวลา
💡 หลักการลงทุนจากการเดินทางครั้งนี้
🔮 คำแนะนำสำหรับการลงทุนจริง
    (Actionable tips for Thai HS student: Emergency Fund, DCA, Index Fund)
"""
```

---

## Appendix A: ลำดับการเริ่มเกม (Game Flow)

```
[โหลดหน้า]
    ↓
[GET /api/init] → scenarios, locations, npcs, quests, wisdom_gates
    ↓
[Scenario Selection Screen]
    ├── Beginner: 4 scenarios (3 rounds)
    └── Normal: 6 scenarios (5 rounds)
    ↓
[startGame(scenarioId)]
    ├── set max_rounds, wisdomGate
    ├── updateStatsUI(), renderMap(), updateItemIcons(), updateEndTurnButton()
    └── fetchNews() → POST /api/news
    ↓
[Per-Quarter Loop]
    ├── Player reads rumor/hints
    ├── Player opens locations → chats / invests
    │   ├── Quest: acceptQuest → evaluateQuest → completeQuest
    │   └── Horathibodi: max 3 chats/quarter (reset in nextRound)
    ├── Player clicks "สิ้นไตรมาส"
    │   └── POST /api/end-turn → processResult()
    └── nextRound() or endGame()
    ↓
[End Game]
    ├── showEndGameModal(rank)
    └── POST /api/generate-insights → marked.parse(insights)
```

---

## Appendix B: Known Behaviors & Design Decisions

| # | พฤติกรรม | เหตุผล |
|---|---------|--------|
| 1 | Merit Safety Net cap = 0.50 (0.60 ถ้ามี กองทุนฉุกเฉิน) | Emergency Fund ที่แท้จริงป้องกัน loss ได้มากกว่า |
| 2 | Wisdom ไม่เพิ่มจาก end-turn เพิ่มจาก quest เท่านั้น | บังคับให้ผู้เล่นทำ quest เพื่อผ่าน Wisdom Gate |
| 3 | HP Cost L3 = +20 (บวก) | Defensive Investment = ลด stress = HP ฟื้น |
| 4 | L7 require_merit = 30 | Alternative Assets ไม่เหมาะสำหรับคนที่ยังไม่มี Emergency Fund |
| 5 | Quest fee = 500 บาท | ต้นทุนการเรียนรู้เล็กน้อย แต่รู้สึก committed |
| 6 | chatHistories ล้างเมื่อรับ quest ใหม่ | ให้ quest_greeting แสดงใหม่สดเสมอ |
| 7 | horathibodi_chat_count reset ทุก nextRound() | ข้อมูลตลาดใหม่ทุกไตรมาส |
| 8 | Quest Bypass: gate ไม่ block ถ้ามี active quest | UX: ไม่ให้ผู้เล่นติดกับดักทำ quest ไม่ได้ |
| 9 | isSending guard แยกจาก isProcessing | Chat และ EndTurn เป็น independent operations |
| 10 | questEvalData persist ตลอด | ไม่ต้องประเมินซ้ำถ้า switch tab |

---

*Game Design Document v4.0 | Ayutthaya Wealth Saga: Beyond the Realm*
*Extracted from Production Code app.py v1.0.0 + index.html*
*INVESTORY × Silpakorn Demo School | มิถุนายน 2569*
