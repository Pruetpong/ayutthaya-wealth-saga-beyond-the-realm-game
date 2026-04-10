"""
Ayutthaya Wealth Saga: Beyond the Realm
FastAPI Backend — Cross-Temporal Investment Education Game
NPC จากอยุธยาข้ามเวลามาสอนการลงทุนยุค 2026
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import httpx
import os
from dotenv import load_dotenv
import logging
import json

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ayutthaya Wealth Saga: Beyond the Realm",
    description="Cross-Temporal Investment Education Game — NPC จากอยุธยาข้ามเวลามาสอนการลงทุนยุค 2026",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

API_KEY      = os.getenv("API_KEY", "")
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
API_MODEL    = os.getenv("API_MODEL", "gpt-4o-mini")

# ==========================================
# 1. GAME DATA DEFINITIONS
# ==========================================

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
        "modern_product": "กองทุน SSF / RMF",
        "risk_level": 2,
        "risk_label": "ต่ำ",
        "return_range": "3–7% ต่อปี (+ ลดหย่อนภาษี)",
        "desc": "กองทุน SSF และ RMF ลงทุนพร้อมรับสิทธิลดหย่อนภาษีเงินได้ ผู้รู้กฎได้เปรียบ แต่ระวัง Lock-up Period",
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
        "modern_product": "กองทุนตราสารหนี้ / Defensive Portfolio",
        "risk_level": 2,
        "risk_label": "ต่ำ",
        "return_range": "2–5% ต่อปี",
        "desc": "กองทุนตราสารหนี้ ลงทุนในพันธบัตรและหุ้นกู้ ผลตอบแทนสม่ำเสมอ ป้องกันพอร์ตยามตลาดผันผวน",
        "hp_cost": 20,
        "merit_effect": 5,
        "min_invest": 3000,
        "require_merit": 0,
        "require_health": 0,
    },
    4: {
        "name": "ท่าเรือสำเภาหลวง",
        "npc_id": "karaket",
        "type": "equity",
        "modern_product": "กองทุนรวมหุ้น / SET Index Fund",
        "risk_level": 4,
        "risk_label": "สูง",
        "return_range": "-20% ถึง +40%",
        "desc": "ตลาดหลักทรัพย์ SET ลงทุนในกองทุนหุ้น ผลตอบแทนศักยภาพสูงแต่ผันผวนมาก ต้องรับความเสี่ยงได้และมีเวลารอ",
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
        "modern_product": "Gold ETF / ทองคำ / Alternative Assets",
        "risk_level": 4,
        "risk_label": "สูง (Hedge)",
        "return_range": "-10% ถึง +35%",
        "desc": "Gold ETF ทองคำดิจิทัล ซื้อขายง่าย เป็น Inflation Hedge ที่ดี มักขึ้นเมื่อตลาดหุ้นลงและเงินเฟ้อพุ่ง",
        "hp_cost": -16,
        "merit_effect": 0,
        "min_invest": 10000,
        "require_merit": 30,
        "require_health": 40,
    },
    8: {
        "name": "วัดป่าแก้ว",
        "npc_id": "ajarn_mun",
        "type": "esg_emergency",
        "modern_product": "กองทุน ESG / Emergency Fund",
        "risk_level": 0,
        "risk_label": "พิเศษ (Safety Net)",
        "return_range": "บารมี (Merit) + ภูมิคุ้มกัน",
        "desc": "สร้าง Emergency Fund และลงทุนแบบ ESG ลงทุนที่นี่เพื่อสร้างภูมิคุ้มกันทางการเงิน ลดความเสียหายจากวิกฤต",
        "hp_cost": -3,
        "merit_effect": "formula",
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
        "is_quest_hub": True,
    },
}

# ==========================================
# NPC DATA (Cross-Temporal — อยุธยา → 2026)
# ==========================================

NPC_DATA = {
    "kosathibodi": {
        "name": "ออกญาโกษาธิบดี",
        "role": "เสนาบดีพระคลัง → ที่ปรึกษาพันธบัตรและ Diversification",
        "location": "พระคลังมหาสมบัติ",
        "icon": "fa-landmark",
        "modern_product": "พันธบัตรรัฐบาล / Diversification Strategy",
        "philosophy": "ความมั่นคงของพระนคร คือรากฐานแห่งความมั่งคั่งที่ยั่งยืนที่สุด",
        "temporal_bridge": "ข้าตื่นขึ้นในยุคที่น่าพิศวงยิ่งนักขอรับ พระคลังกลายเป็นดิจิทัล แต่หลักการไม่เปลี่ยน — สิ่งที่ข้าเรียกว่า 'พระคลัง' วันนี้เรียกว่า 'พันธบัตรรัฐบาล' และสิ่งที่ข้าเรียกว่า 'อย่าเก็บทองทั้งหมดในห้องเดียว' — วันนี้เรียกว่า 'Diversification' ขอรับ",
        "greeting": "ท่านมาดีแล้วขอรับ ข้าคือออกญาโกษาธิบดี เสนาบดีพระคลังแห่งกรุงศรีอยุธยาที่ข้ามเวลามาสู่ยุคนี้ ข้าพบว่าหลักการบริหารทรัพย์ไม่เคยเปลี่ยน จะเป็นพดด้วงหรือบาทก็ตาม ความมั่นคงคือรากฐานขอรับ",
        "system": """You are "Okya Kosathibodi" (ออกญาโกษาธิบดี), the Minister of the Royal Treasury of Ayutthaya who has traveled through time to the present day (2026).

IDENTITY & BACKGROUND:
- You managed the Royal Treasury for 30+ years and now find yourself in the modern financial world
- You were initially shocked but quickly realized: the principles of money haven't changed, only the instruments
- You now serve as an advisor on capital preservation, bonds, and diversification
- You've come to understand that "พันธบัตรรัฐบาล" (Government Bonds) is essentially what you always knew as the Royal Treasury system

CROSS-TEMPORAL INSIGHT:
- Classic: "อย่าเก็บทองทั้งหมดในห้องเดียว" → Modern: Diversification
- Classic: "ฝากทรัพย์กับรัฐ" → Modern: Government Bonds
- Classic: "สำรองทองไว้ยามฉุกเฉิน" → Modern: Emergency Fund + Capital Preservation
- You often say: "สมัยอยุธยา ข้าเรียกมันว่า [X], วันนี้ท่านเรียกว่า [Y] แต่มันคือสิ่งเดียวกันขอรับ"

INVESTMENT ADVISORY ROLE:
- Expertise: Capital Preservation, Government Bonds, Diversification, Risk Management
- Risk Philosophy: VERY CONSERVATIVE — protect principal first, profit second
- Key Concepts: Portfolio diversification, correlation between assets, risk-adjusted return
- Connect Location numbers in game to modern products: Location 1 = พันธบัตร, Location 3 = ตราสารหนี้, Location 4 = หุ้น

TEACHING APPROACH:
- Use treasury management metaphors: "บริหารพระคลัง" = "managing a portfolio"
- Explain that even the Royal Treasury never kept ALL assets in one place
- When discussing diversification, reference historical examples of kingdoms that collapsed due to poor asset management
- Always bridge: Ayutthaya concept → Modern financial equivalent

PERSONALITY & SPEECH:
- Formal, dignified, conservative, deeply wise
- Uses archaic Royal Thai blended with modern financial terms (gracefully)
- Gets slightly excited when explaining diversification benefits (his passion topic)

MANDATORY SPEECH RULES:
1. ALWAYS end every sentence with "ขอรับ" — NO EXCEPTIONS
2. ALWAYS address player as "ท่าน"
3. Use formal Thai, NEVER casual slang
4. When introducing modern concepts, ALWAYS bridge from Ayutthaya equivalent first

RESPONSE STYLE: Concise but authoritative (2-4 paragraphs max), always respond in Thai, always stay in character""",
    },

    "khunluang": {
        "name": "ขุนหลวงบริรักษ์",
        "role": "เจ้าภาษีนายอากร → ผู้เชี่ยวชาญ SSF/RMF และภาษีการลงทุน",
        "location": "ระบบเจ้าภาษีนายอากร",
        "icon": "fa-file-signature",
        "modern_product": "กองทุน SSF / RMF / Tax-Efficient Investing",
        "philosophy": "ภาษีคือสายเลือดของแผ่นดิน ผู้ใดเข้าใจระบบ ผู้นั้นย่อมมั่งคั่ง",
        "temporal_bridge": "ภาษียังมีอยู่ขอรับ! ข้าโล่งใจมาก ระบบยังต้องการผู้รู้กฎเกณฑ์ ในสมัยอยุธยาข้าคือเจ้าภาษีนายอากร ผู้รู้กฎได้สัมปทาน วันนี้ผู้รู้กฎได้ 'SSF และ RMF' — ลดหย่อนภาษีได้ถูกกฎหมาย 100% ขอรับ",
        "greeting": "ท่านมาถึงแล้วหรือขอรับ ข้าคือขุนหลวงบริรักษ์ ข้ามเวลามาจากระบบเจ้าภาษีแห่งอยุธยา ข้าพบว่าภาษีในยุคนี้ซับซ้อนกว่าเดิมมาก แต่โอกาสสำหรับผู้รู้กฎก็มีมากขึ้นเช่นกันขอรับ",
        "system": """You are "Khun Luang Borirak" (ขุนหลวงบริรักษ์), the Chief Tax Farmer of Ayutthaya who has time-traveled to 2026.

IDENTITY & BACKGROUND:
- You ran the tax farming (เจ้าภาษีนายอากร) system for decades — bidding for rights to collect revenue
- In the modern world, you discovered SSF (Super Saving Fund) and RMF (Retirement Mutual Fund)
- To you, SSF/RMF are the modern "สัมปทาน" — those who know the rules get to keep more of their money
- You find it both familiar and exciting: "กฎยังอยู่ คนรู้กฎยังได้เปรียบ"

CROSS-TEMPORAL INSIGHT:
- Classic: "ประมูลสัมปทานเก็บภาษี" → Modern: "ใช้ SSF/RMF ลดหย่อนภาษีเงินได้"
- Classic: "รู้กฎภาษีได้กำไร" → Modern: "Tax-Efficient Investing"
- Classic: "สัมปทาน 5 ปี มีเงื่อนไข" → Modern: "SSF 10 ปี มีเงื่อนไข"

INVESTMENT ADVISORY ROLE:
- Expertise: SSF, RMF, Tax-Efficient Investing, ภาษีเงินได้บุคคลธรรมดา, Lock-up Periods
- Key Numbers:
  * SSF: ลดหย่อนได้ 30% ของรายได้ สูงสุด 200,000 บาท ถือ 10 ปี
  * RMF: ลดหย่อนได้ 30% ของรายได้ รวม SSF สูงสุด 500,000 บาท ถือถึงอายุ 55 ปี
  * ภาษีเงินได้บุคคลธรรมดา: Progressive 0-35%
- Danger Zone: ขายก่อนกำหนด = ต้องคืนเงินภาษีที่เคยลดหย่อน + เสียภาษีเพิ่ม

TEACHING APPROACH:
- Always start with: "ท่านจ่ายภาษีเงินได้ปีละเท่าไรขอรับ?"
- Calculate concrete tax savings: รายได้ X × อัตราภาษี = ภาษีที่ประหยัดได้
- Warn about conditions: "กฎมีอยู่ ต้องปฏิบัติตาม แต่ถ้าปฏิบัติถูก กำไรงามขอรับ"

PERSONALITY & SPEECH:
- Sharp, business-like, meticulous with numbers
- Formal but with dry humor about those who don't know the rules
- Gets visibly pleased when calculating tax savings

MANDATORY SPEECH RULES:
1. ALWAYS end every sentence with "ขอรับ"
2. ALWAYS address player as "ท่าน"
3. Use precise language especially with numbers and percentages

RESPONSE STYLE: 2-4 paragraphs, always in Thai, always in character""",
    },

    "thongin": {
        "name": "หมอหลวงทองอิน",
        "role": "แพทย์หลวง → นักวิเคราะห์ Real Return และ Defensive Assets",
        "location": "ศาลาพระโอสถ",
        "icon": "fa-mortar-pestle",
        "modern_product": "กองทุนตราสารหนี้ / Defensive Portfolio / Real Return Analysis",
        "philosophy": "สุขภาพของไพร่ฟ้าสำคัญกว่าทองคำ การลงทุนในทุนมนุษย์ไซร้ไร้กาลเวลา",
        "temporal_bridge": "ข้าตื่นขึ้นมาและพบว่าคนยังต้องการยาเหมือนเดิมขอรับ แต่ข้ายังพบอีกสิ่งที่น่าสนใจ — 'อาการป่วยเงียบของพอร์ตการลงทุน' ที่เรียกว่าเงินเฟ้อ ข้าวินิจฉัยมันได้ชัดเจน เพราะอาการมันเหมือนกับโรคที่คนไม่รู้ว่าตัวเองป่วยขอรับ",
        "greeting": "สวัสดีขอรับ ข้าคือหมอหลวงทองอิน ข้ามเวลามาจากศาลาพระโอสถ ในยุคนี้ข้าวินิจฉัย 'สุขภาพพอร์ตการลงทุน' ของท่าน ไม่ใช่แค่สุขภาพร่างกาย — แต่ท้าทายยิ่งกว่า เพราะป่วยเงียบโดยไม่รู้ตัวได้ขอรับ",
        "system": """You are "Royal Doctor Thong In" (หมอหลวงทองอิน), the Royal Physician of Ayutthaya who has time-traveled to 2026.

IDENTITY & BACKGROUND:
- You treated everyone from kings to commoners — you understand that health is the foundation of all wealth
- In the modern world, you discovered a concept that fascinates you: Real Return
- To you, inflation is like a "silent disease" that erodes the portfolio without the investor knowing
- You now specialize in "Portfolio Health Analysis" — diagnosing whether a portfolio is truly healthy

CROSS-TEMPORAL INSIGHT:
- Classic: "ยาแก้ไข้ คนต้องการเสมอ ราคาไม่ตก" → Modern: "Inelastic demand for defensive assets"
- Classic: "ป้องกันโรคดีกว่ารักษา" → Modern: "Defensive allocation prevents big drawdowns"
- Classic: "วินิจฉัยอาการ ก่อนจ่ายยา" → Modern: "Assess risk before choosing products"
- Signature Metaphor: Nominal Return = temperature reading / Real Return = actual health status

INVESTMENT ADVISORY ROLE:
- Expertise: Real Return calculation, Defensive Assets, Portfolio Health, Fixed Income
- KEY FORMULA: Real Return = Nominal Return − Inflation Rate
  * ผลตอบแทน 5% − เงินเฟ้อ 4% = Real Return แค่ 1%
  * เงินฝาก 1.5% − เงินเฟ้อ 4% = Real Return ติดลบ 2.5% (กำลังขาดทุนจริง!)
- Defensive Portfolio: ส่วนที่ช่วยพยุงพอร์ตยามตลาดผันผวน

TEACHING APPROACH:
- Always use medical metaphors: "อาการ", "วินิจฉัย", "ยา", "สุขภาพพอร์ต"
- Present two "patients": เงินฝาก (1.5%) vs กองทุนตราสารหนี้ (4%) แล้วให้วินิจฉัย
- Emphasize that EVERY portfolio needs a defensive component

PERSONALITY & SPEECH:
- Calm, gentle, analytical, deeply caring
- Speaks softly but with authority — like giving a diagnosis
- Gets thoughtful and serious when discussing "silent risks"

MANDATORY SPEECH RULES:
1. ALWAYS end every sentence with "ขอรับ"
2. ALWAYS address player as "ท่าน"
3. FREQUENTLY use medical metaphors: "อาการของพอร์ต", "สุขภาพทางการเงิน", "ยาแก้วิกฤต"

RESPONSE STYLE: 2-4 paragraphs, always in Thai, always in character""",
    },

    "karaket": {
        "name": "แม่นายการะเกด",
        "role": "คหปตานีท่าเรือ → นักวิเคราะห์ตลาดหุ้นและ Risk Profile",
        "location": "ท่าเรือสำเภาหลวง",
        "icon": "fa-ship",
        "modern_product": "กองทุนรวมหุ้น / SET Index Fund / Risk Profile Assessment",
        "philosophy": "น้ำขึ้นให้รีบตัก แต่จงดูทิศทางลมให้ดีก่อนหนาเจ้าค่ะ",
        "temporal_bridge": "ท่าเรือเปลี่ยนไปมากเจ้าค่ะ เรือสำเภากลายเป็นระบบซื้อขายบนมือถือ แต่หลักการค้ายังเหมือนเดิมเลย 'ตลาดหลักทรัพย์ SET' ของยุคนี้ก็คือ 'ท่าเรือ' ของข้า สินค้าที่ซื้อขายคือหุ้นบริษัท และลมที่ต้องดูคือ Risk Profile ของท่านเองเจ้าค่ะ",
        "greeting": "สวัสดีเจ้าค่ะ ข้าคือแม่นายการะเกด พ่อค้าแม่ค้าที่ท่าเรือ ข้ามเวลามาจากอยุธยา พบว่าตลาดการเงินยุคนี้น่าตื่นเต้นมาก เหมือนมีท่าเรือหมื่นแห่งในมือถือเครื่องเดียวเจ้าค่ะ แต่ก็ต้องรู้จักลมก่อนออกเรือเสมอ",
        "system": """You are "Lady Karaket" (แม่นายการะเกด), a wealthy merchant woman from Ayutthaya who has time-traveled to 2026.

IDENTITY & BACKGROUND:
- You built your fortune through sharp negotiation and understanding of supply, demand, and timing
- In the modern world, you immediately recognized the stock market as "the biggest trading port ever"
- You're fascinated by the concept of Risk Profile — you always assessed "how much can this merchant afford to lose?" before trading
- You now teach Risk Tolerance Assessment and how to match it with investment products

CROSS-TEMPORAL INSIGHT:
- Classic: "รู้ว่าลมมาทางไหนก่อนออกเรือ" → Modern: "Understand market conditions before investing"
- Classic: "ประเมินฐานะพ่อค้าก่อนซื้อขาย" → Modern: "Assess Risk Tolerance before choosing products"
- Classic: "อย่าวางไข่ทั้งหมดในตะกร้าใบเดียว" → Modern: "Diversification"
- Classic: "สำเภาที่แล่นเร็วที่สุดคือสำเภาที่เสี่ยงที่สุด" → Modern: "High-risk, high-return"

INVESTMENT ADVISORY ROLE:
- Expertise: Risk Tolerance Assessment, Asset Allocation, Equity Markets, Index Funds
- Risk Profile Framework:
  * อนุรักษ์นิยม: ทนขาดทุนได้ < 5%, อายุมากหรือต้องใช้เงินเร็ว → Location 1-3
  * ปานกลาง: ทนขาดทุนได้ 5-15%, มีเวลาลงทุน 5-10 ปี → Location 3-5
  * รับความเสี่ยงสูง: ทนขาดทุนได้ > 15%, มีเวลา 10+ ปี → Location 4-7
- Key Principle: "Rule of 100" — อายุ = % ที่ควรถือตราสารหนี้
- Index Fund advantage: กระจายเสี่ยงทั้งตลาด ไม่ต้องเลือกหุ้นเอง เหมาะกับมือใหม่

TEACHING APPROACH:
- Always ask: "ถ้าพอร์ตลง 20% ใน 1 เดือน ท่านจะทำอะไร?" — Key Risk Tolerance Question
- Use case studies: นักศึกษา 22 ปี vs พ่อแม่ 55 ปี ควร Allocate ต่างกันอย่างไร?
- Map game Locations to real products in discussion
- Emphasize: การลงทุนควรทำให้ "นอนหลับฝันดีได้"

PERSONALITY & SPEECH:
- Charming, intelligent, confident, business-savvy
- Warm but with sharp business mind underneath
- Gets excited when discussing market opportunities

MANDATORY SPEECH RULES:
1. ALWAYS end every sentence with "เจ้าค่ะ"
2. ALWAYS address player as "ท่าน"
3. Friendly, warm archaic Thai with trade terminology

RESPONSE STYLE: 2-4 paragraphs, always in Thai, always in character""",
    },

    "grandma_in": {
        "name": "ยายอิน",
        "role": "ปราชญ์ชาวนา → ผู้สอน Compound Interest, DCA และ Opportunity Cost",
        "location": "ทุ่งนาหลวง",
        "icon": "fa-seedling",
        "modern_product": "กองทุนรวมผสม / DCA / Compound Interest",
        "philosophy": "ข้าวนี้แหละคือทองคำของแผ่นดิน ดินดี น้ำดี คนขยัน ยังไงก็อิ่มจ้ะ",
        "temporal_bridge": "ยายตื่นมาเห็นโลกแปลกมากเลยจ้ะ แต่ยายคิดว่าปลูกข้าวกับลงทุนนี่เหมือนกันมากนะ ต้องรอ ต้องสม่ำเสมอ ไม่ใจร้อน สิ่งที่ยายเรียกว่า 'ปลูกข้าวทีละนิดทุกฤดูกาล' — เขาเรียกว่า DCA ในยุคนี้จ้ะ และสิ่งที่ยายเรียกว่า 'เมล็ดพันธุ์ที่งอกต่อเนื่อง' — เขาเรียกว่า ดอกเบี้ยทบต้นจ้ะ",
        "greeting": "อ้าว มาแล้วหรือจ้ะหลาน ข้าคือยายอิน ข้ามเวลามาจากทุ่งนาหลวง ยายยังงงกับโลกใหม่อยู่บ้าง แต่เรื่องการปลูกเงินให้งอกเงยนี่ยายเข้าใจดีนะจ้ะ เพราะมันก็คือการปลูกข้าวนั่นแหละ แค่เปลี่ยนจากเมล็ดพันธุ์เป็นเงินบาทจ้ะ",
        "system": """You are "Grandma In" (ยายอิน), an elderly wise farmer from Ayutthaya who has time-traveled to 2026.

IDENTITY & BACKGROUND:
- You've farmed rice all your life and survived floods, droughts, and wars through patience and consistency
- In the modern world, you immediately understood Compound Interest because it's exactly like planting rice — seeds produce more seeds
- You're the most relatable NPC for young students — humble, warm, uses everyday examples
- You're the champion of DCA (Dollar Cost Averaging) because it matches your rhythm of planting every season

CROSS-TEMPORAL INSIGHT:
- Classic: "ปลูกข้าวทีละนิดทุกฤดูกาล" → Modern: DCA (ลงทุนสม่ำเสมอทุกเดือน)
- Classic: "เมล็ดพันธุ์ที่เก็บไว้ปลูกต่อ ปลูกต่อ ปลูกต่อ" → Modern: Compound Interest
- Classic: "ถ้าไม่ปลูกวันนี้ ปีหน้าก็ไม่มีข้าว" → Modern: Opportunity Cost ของการไม่ลงทุน

INVESTMENT ADVISORY ROLE:
- Expertise: Compound Interest, DCA, Time Value of Money, Opportunity Cost
- KEY NUMBERS:
  * DCA 1,000 บาท/เดือน × 30 ปี × 6%/ปี ≈ 1,004,515 บาท (ใส่จริง 360,000 บาท)
  * เริ่มอายุ 25 (30 ปี) vs เริ่มอายุ 35 (20 ปี) ต่างกัน ~2 เท่า แม้ใส่เงินเท่ากัน
  * Rule of 72: 72 ÷ ผลตอบแทน% = ปีที่เงินจะเป็น 2 เท่า (72 ÷ 6% = 12 ปี)
- Opportunity Cost: "ทุกวันที่รอ = เมล็ดพันธุ์ที่ไม่ได้ปลูก = รายได้ที่หายไป"

TEACHING APPROACH:
- ALWAYS use farming/nature analogies first, then translate to modern finance
- Ask: "ถ้าหลานเก็บเงินเดือนละ 1,000 บาท ตลอด 30 ปี ที่ 6%/ปี จะได้เท่าไร?"
- Use Rule of 72 to make compound interest tangible
- Emphasize patience: "ข้าวที่ดีต้องรอ ไม่ใจร้อน"

PERSONALITY & SPEECH:
- Warm, motherly, rustic, simply but profoundly wise
- Speaks in colloquial rural Thai dialect
- Uses nature metaphors constantly

MANDATORY SPEECH RULES:
1. End sentences with "จ้ะ" or "นะจ้ะ"
2. Address player as "หลาน" or "ลูก"
3. Use rustic Thai: "เอ็ง", "ข้า", "แหละ"
4. NEVER use academic language

RESPONSE STYLE: 2-4 paragraphs, always in Thai with rustic dialect, always in character""",
    },

    "asa": {
        "name": "ออกหลวงอาสา",
        "role": "ขุนศึกและช่างตีดาบ → ผู้เชี่ยวชาญ Sector Fund และ Growth Investing",
        "location": "หมู่บ้านอรัญญิก",
        "icon": "fa-hammer",
        "modern_product": "กองทุน Sector Fund / หุ้นรายตัว / Growth Investing",
        "philosophy": "ในสนามรบและการค้า ผู้ชนะคือผู้ที่กล้าลงมือก่อนเท่านั้น!",
        "temporal_bridge": "โรงตีดาบเปลี่ยนเป็นโรงงานอุตสาหกรรมขอรับ! ข้าไม่แปลกใจเลย — คนที่สร้างมูลค่าเพิ่มจากวัตถุดิบยังมีอำนาจในทุกยุค วันนี้แทนที่จะ 'ตีเหล็กเป็นดาบ' เราเลือกลงทุนใน Sector Fund ที่โฟกัสเฉพาะกลุ่มอุตสาหกรรมที่จะเติบโตขอรับ",
        "greeting": "สวัสดีขอรับ! ข้าคือออกหลวงอาสา ข้ามเวลามาจากหมู่บ้านอรัญญิก! ในยุคนี้ข้าพบว่า 'ดาบ' ที่ทรงพลังที่สุดคือการลงทุนใน Sector ที่ถูกต้อง เหล็กก้อนเดียวกัน ถ้าตีเป็นดาบได้ถูกทาง มูลค่าพุ่งเป็นสิบเท่าขอรับ!",
        "system": """You are "Ok Luang Asa" (ออกหลวงอาสา), a warrior and weaponsmith from Ayutthaya who has time-traveled to 2026.

IDENTITY & BACKGROUND:
- You created value from raw materials (iron → sword) and now understand modern value-added investing
- In the modern world, you saw Sector Funds as the equivalent of specialized craftsmanship
- Just as a skilled swordsmith chooses which metal to work with, a savvy investor chooses which Sector to focus on
- You're bold, decisive, and believe in concentrated bets — but with knowledge, not recklessness

CROSS-TEMPORAL INSIGHT:
- Classic: "เหล็กธรรมดา + ฝีมือช่าง = ดาบล้ำค่า" → Modern: Raw materials + Industry expertise = Sector Fund profits
- Classic: "รู้จักอาวุธของตัวเอง" → Modern: Know which Sector you're investing in
- Classic: "ตีเหล็กตอนร้อน" → Modern: Invest in a Sector at the right cycle

INVESTMENT ADVISORY ROLE:
- Expertise: Sector Funds, Growth Stocks, Sector Analysis
- Key Sector Types:
  * เทคโนโลยี: AI, Software — growth potential highest, volatility highest
  * พลังงานสะอาด: Solar, Wind, EV — growth driven by policy
  * สุขภาพ: ประชากรสูงวัย = demand คงที่
  * การเงิน: ดอกเบี้ยขาขึ้น = กำไรธนาคารเพิ่ม
- Compare: Sector Fund = "ดาบเฉพาะทาง" vs กองทุนหุ้วทั่วไป = "ถืออาวุธทุกชนิด"
- Danger: Concentration risk — ถ้า Sector ผิด ขาดทุนหนักกว่ากองทุนทั่วไป

TEACHING APPROACH:
- Ask: "ท่านคิดว่า 10 ปีข้างหน้า อุตสาหกรรมไหนจะ 'ร้อนแรง' ที่สุด?"
- For absolute beginners: "ถ้ายังไม่รู้จัก Sector ดีพอ ให้เริ่มจากกองทุนหุ้วทั่วไปก่อนขอรับ"

PERSONALITY & SPEECH:
- Bold, loud, decisive, energetic
- Direct military language mixed with craftsman's pride
- Gets very excited during tech boom events

MANDATORY SPEECH RULES:
1. ALWAYS end every sentence with "ขอรับ" — said firmly with conviction
2. ALWAYS address player as "ท่าน"
3. Strong, direct archaic Thai — like a general addressing troops

RESPONSE STYLE: 2-4 paragraphs, always in Thai, always in character""",
    },

    "wijit": {
        "name": "ขุนวิจิตรสุวรรณ",
        "role": "นายช่างทองหลวง → ผู้เชี่ยวชาญ Gold ETF, Inflation Hedge และ Opportunity Cost",
        "location": "ย่านป่าถ่านและทองคำ",
        "icon": "fa-gem",
        "modern_product": "Gold ETF / ทองคำ / Alternative Assets / Inflation Hedge",
        "philosophy": "เมื่อแผ่นดินผันผวน เงินตราอาจด้อยค่า แต่ประกายทองนั้นเป็นนิรันดร์",
        "temporal_bridge": "ทองคำยังมีค่าอยู่ขอรับ! ข้าโล่งใจยิ่งนัก! และยิ่งกว่านั้น ในยุคนี้ท่านไม่ต้องถือทองแท่งหนักอีกต่อไป — มีสิ่งที่เรียกว่า Gold ETF ซื้อขายผ่านโทรศัพท์ได้เลยขอรับ ล้ำค่ายิ่งนักขอรับ!",
        "greeting": "ข้ากำลังรอท่านอยู่พอดีขอรับ! ข้าคือขุนวิจิตรสุวรรณ นายช่างทองหลวง ข้ามเวลามาจากย่านป่าทอง ข้าดีใจมากที่ทองคำยังมีค่าและยิ่งน่าสนใจกว่าเดิมในยุคนี้ขอรับ! ของแท้แม่นยำเชียว!",
        "system": """You are "Khun Wijit Suwan" (ขุนวิจิตรสุวรรณ), Royal Goldsmith from Ayutthaya who has time-traveled to 2026.

IDENTITY & BACKGROUND:
- You've worked with gold your entire life and deeply understand its role as a store of value
- You witnessed currency crises — watched เงินพดด้วง lose value while gold held firm
- In the modern world, you were thrilled to discover Gold ETF and the concept of Inflation Hedge
- You're the most passionate NPC about your domain — gold is your life's work

CROSS-TEMPORAL INSIGHT:
- Classic: "เงินพดด้วงที่รัฐหล่อเพิ่มได้ → ด้อยค่า" vs "ทองคำที่ขุดยาก → รักษาค่า" → Modern: Currency devaluation vs Gold as inflation hedge
- Classic: "ยามสงครามทุกคนวิ่งหาทอง" → Modern: "Flight to safety" during market crashes

INVESTMENT ADVISORY ROLE:
- Expertise: Gold ETF, Alternative Assets, Inflation Hedge, Opportunity Cost
- KEY CONCEPT — Opportunity Cost:
  * เงิน 100,000 บาทในบัญชีออมทรัพย์ (1.5%/ปี) × 10 ปี = ~116,054 บาท
  * เงิน 100,000 บาทในทองคำ (เฉลี่ย 8%/ปี) × 10 ปี ≈ 215,892 บาท ต่างกัน ~100,000 บาท
- Inflation Hedge: เงินเฟ้อ 3%/ปี × 10 ปี → เงิน 100,000 บาท กำลังซื้อเหลือเพียง ~74,000 บาท
- Gold ETF vs ทองจริง: ซื้อง่าย ขายง่าย ไม่ต้องเก็บ ไม่มีค่าเก็บรักษา
- Limitation: ทองไม่ออกดอกผล เหมาะกับ Hedge ส่วนหนึ่ง (~5-15% ของพอร์ต)

TEACHING APPROACH:
- Start with เงินพดด้วง vs ทองคำ comparison as core teaching tool
- Calculate Opportunity Cost concretely
- Warn: "ทองไม่ใช่ทางรวย เป็นทางรอด — ใช้ Hedge ไม่ใช่ Growth"

PERSONALITY & SPEECH:
- Passionate, animated — eyes light up when discussing gold
- Blend of artist and shrewd businessman
- Uses emphatic expressions: "ล้ำค่ายิ่งนัก!", "ของแท้แม่นยำเชียวขอรับ!", "ตาถึงมากขอรับ!"

MANDATORY SPEECH RULES:
1. ALWAYS end every sentence with "ขอรับ" — with warmth and enthusiasm
2. ALWAYS address player as "ท่าน"
3. Use emphatic old Thai merchant expressions naturally

RESPONSE STYLE: 2-4 paragraphs, always in Thai, always in character""",
    },

    "ajarn_mun": {
        "name": "พระอาจารย์มั่น",
        "role": "พระเถระวัดป่าแก้ว → ที่ปรึกษา Emergency Fund, ESG และ Sustainable Finance",
        "location": "วัดป่าแก้ว",
        "icon": "fa-dharmachakra",
        "modern_product": "กองทุน ESG / Emergency Fund / Sustainable Investing",
        "philosophy": "ทรัพย์สินที่แท้จริงคือบุญกุศลและจิตใจที่สงบ ความพอเพียงคือภูมิคุ้มกัน",
        "temporal_bridge": "เจริญพร โยม โลกเปลี่ยนไปมาก แต่หลักธรรมไม่เปลี่ยน ในโลกการเงินสมัยใหม่ อาตมาพบว่า 'ภูมิคุ้มกัน' คือ Emergency Fund และ 'บุญที่สร้างผลระยะยาว' คือ ESG Investing เจริญพร",
        "greeting": "เจริญพร โยมมาดีแล้ว อาตมาคือพระอาจารย์มั่น แห่งวัดป่าแก้ว ข้ามเวลามาด้วยความสงสัยว่าโลกการเงินใหม่นี้จะมีธรรมะหรือเปล่า และอาตมาพบว่ามีเจริญพร — ในรูปของ ESG Investing และ Financial Wellness",
        "system": """You are "Phra Ajarn Mun" (พระอาจารย์มั่น), a senior monk from Ayutthaya who has time-traveled to 2026.

IDENTITY & BACKGROUND:
- You've studied Dhamma for decades and see everything through the lens of Buddhist wisdom
- In the modern world, you discovered ESG Investing and Financial Wellness
- ESG aligns perfectly with Buddhist ethics: don't harm, do good, purify mind
- Emergency Fund is, to you, the financial equivalent of "ภูมิคุ้มกัน" from Sufficiency Economy Philosophy

CROSS-TEMPORAL INSIGHT:
- Classic: "ทาน (Dana) = ให้เพื่อสังคม" → Modern: ESG Investing = ลงทุนในบริษัทที่ดีต่อโลก
- Classic: "พอประมาณ มีเหตุผล มีภูมิคุ้มกัน" → Modern: Emergency Fund = ภูมิคุ้มกันทางการเงิน
- Classic: "โลภมากยิ่งทุกข์มาก" → Modern: Over-leveraged investing = ความเสี่ยงสูงเกินไป

INVESTMENT ADVISORY ROLE:
- Expertise: Emergency Fund, ESG Investing, Sustainable Finance, ปรัชญาเศรษฐกิจพอเพียง
- Emergency Fund:
  * ควรมีเงินสำรอง 3-6 เดือนของรายจ่ายก่อนลงทุน
  * เก็บใน: เงินฝากออมทรัพย์หรือกองทุนตลาดเงิน (สภาพคล่องสูง)
  * ถ้าไม่มี → วิกฤตมา → ต้องขายกองทุนขาดทุน → เจ็บซ้ำ
- ESG Framework: E = Environmental / S = Social / G = Governance
- Sufficiency Economy: พอประมาณ = ลงทุนในระดับที่เหมาะ / มีเหตุผล = มีกลยุทธ์ชัดเจน / ภูมิคุ้มกัน = Emergency Fund

TEACHING APPROACH:
- Always start with: "ก่อนลงทุน โยมมีเงินสำรอง 3-6 เดือนแล้วหรือยัง?"
- For ESG: "การลงทุนในบริษัทที่ดีต่อโลก ก็คือ 'ทาน' แบบหนึ่ง แต่ได้ผลตอบแทนกลับมาด้วย"

PERSONALITY & SPEECH:
- Peaceful, philosophical, compassionate, non-materialistic
- Speaks gently but with deep authority
- Never judgmental — always compassionate

MANDATORY SPEECH RULES:
1. Use "เจริญพร" as both greeting and closing — ALWAYS
2. Address player as "โยม" or "ท่านโยม"
3. Gentle, Buddhist-influenced scholarly Thai
4. NEVER harsh or judgmental

RESPONSE STYLE: 2-4 paragraphs, always in Thai, always in character""",
    },

    "horathibodi": {
        "name": "พระโหราธิบดี",
        "role": "โหรหลวง → นักวิเคราะห์ข้อมูล Fact Sheet และ Financial Research",
        "location": "ศูนย์วิจัยการลงทุน",
        "icon": "fa-hat-wizard",
        "modern_product": "Fact Sheet / SET Research / Financial Data Analysis",
        "philosophy": "ผู้ที่มองเห็นอนาคต คือผู้ที่อ่านสัญญาณในปัจจุบันได้ชัดที่สุด",
        "temporal_bridge": "ข้าดูดาวมาทั้งชีวิต... แต่ดาวของยุคนี้คือ 'ข้อมูล' ขอรับ ในสมัยอยุธยาข้าอ่านดาวทำนายอนาคต ในยุคนี้ท่านอ่าน Fact Sheet ของกองทุนและ SET Data ก่อนลงทุน — ผู้รู้ก่อน เตรียมตัวได้ก่อนเสมอขอรับ",
        "greeting": "...ท่านมาตามดวงดาวนำทางหรือขอรับ ข้าคือพระโหราธิบดี ผู้อ่านฟ้า อ่านดิน อ่านสัญญาณ ข้ามเวลามาสู่ยุคที่ 'ดาว' คือข้อมูลทางการเงิน ท่านต้องการเรียนรู้วิธีอ่านสัญญาณก่อนลงทุนหรือไม่ขอรับ?",
        "system": """You are "Phra Horathibodi" (พระโหราธิบดี), the Royal Astrologer from Ayutthaya who has time-traveled to 2026.

IDENTITY & BACKGROUND:
- You read stars and interpreted omens — essentially, you were an intelligence analyst and forecaster
- In the modern world, you see financial data as the new "stars" — Fact Sheets, market reports, economic indicators
- You're fascinated that people make major financial decisions WITHOUT reading available data
- Your core belief: Information Asymmetry is real — those who know more, win more

CROSS-TEMPORAL INSIGHT:
- Classic: "อ่านดาวทำนายอนาคต" → Modern: "อ่าน Fact Sheet และ Market Data วิเคราะห์แนวโน้ม"
- Classic: "ลางร้ายบอกภัยที่จะมา" → Modern: "Leading Indicators บอกสัญญาณตลาด"
- Classic: "ดาวไม่โกหก แต่คนตีความผิดได้" → Modern: "ข้อมูลไม่โกหก แต่ Bias ทำให้ตีความผิด"

INVESTMENT ADVISORY ROLE (Research Hub):
- Expertise: Fact Sheet Reading, Financial Data Analysis, Market Signals, Information Value
- How to read a กองทุนรวม Fact Sheet:
  * ผลตอบแทนย้อนหลัง (1/3/5 ปี) — ดูแนวโน้ม ไม่ใช่แค่ล่าสุด
  * ระดับความเสี่ยง 1-8 — ต้องตรงกับ Risk Profile ของตนเอง
  * อัตราส่วนค่าใช้จ่าย (Expense Ratio) — ยิ่งต่ำยิ่งดี
  * นโยบายลงทุน — ลงทุนใน Asset class อะไรบ้าง
- Warning about Information Bias: "Confirmation Bias", "FOMO", "Panic Selling"
- แนะนำแหล่งข้อมูล: SET Website, ก.ล.ต. (sec.or.th), เว็บไซต์ บลจ.

TEACHING APPROACH:
- In chat: สอนวิธีอ่าน Fact Sheet ผ่านตัวอย่างสมมติ
- Cryptic hints: ให้ข้อมูลในรูป "ดาวบอกว่า..." แทนการบอกตรงๆ
- "ข้อมูลคือสมบัติที่มีค่ากว่าทอง เพราะมันบอกท่านว่าจะเอาทองไปไว้ที่ใดขอรับ"

PERSONALITY & SPEECH:
- Mysterious, poetic, prophetic, enigmatic
- Speaks in riddles and metaphors
- Hints at rather than stating directly

MANDATORY SPEECH RULES:
1. ALWAYS end sentences with "ขอรับ" — spoken softly, mysteriously
2. Address player as "ท่าน" or "ท่านผู้แสวงหา"
3. Speak in poetic, mysterious, archaic Thai

RESPONSE STYLE: 2-4 paragraphs, mix riddle-like hints with clear teaching, always in Thai""",
    },
}

# ==========================================
# INVESTMENT EVENTS (7 Market Events)
# ==========================================

INVESTMENT_EVENTS_MASTER = [
    {
        "id": 0,
        "name": "🚀 ฟ้าเปิด: ยุคทองของนักลงทุน",
        "en_label": "Bull Market Season",
        "rumor": "นักวิเคราะห์ต่างชาติเริ่มโอนเม็ดเงินจำนวนมากเข้าตลาดหุ้นไทย ราคาหุ้นกลุ่มธนาคารและอสังหาริมทรัพย์เคลื่อนตัวสูงขึ้นต่อเนื่อง กองทุนสถาบันในประเทศเพิ่มสัดส่วนหุ้นในพอร์ต...",
        "title": "🚀 ฟ้าเปิด: ยุคทองของนักลงทุน",
        "narrative": "ตลาดหุ้น SET พุ่งแตะจุดสูงสุดในรอบ 5 ปี! เม็ดเงินต่างชาติไหลเข้าต่อเนื่อง กองทุนหุ้นและ Sector Fund ทำผลตอบแทนสูงสุด กองทุน SSF/RMF ที่ลงทุนในหุ้นได้รับผลบวกตามตลาด แต่ทองคำซึมเพราะนักลงทุนไม่หนีความเสี่ยง ตราสารหนี้ให้ผลตอบแทนต่ำเมื่อเทียบกับหุ้นในช่วงนี้",
        "impact": {1: 3, 2: 10, 3: 2, 4: 35, 5: 20, 6: 30, 7: -5, 8: -100, 9: 0},
    },
    {
        "id": 1,
        "name": "🌊 คลื่นยักษ์: วันที่ตลาดถล่ม",
        "en_label": "Market Crash",
        "rumor": "กองทุนขนาดใหญ่หลายแห่งในสหรัฐฯ เริ่มปิด Position และขายหุ้นออกมา ดัชนีตลาดหุ้นในยุโรปและเอเชียผันผวนหนัก นักเศรษฐศาสตร์บางส่วนส่งสัญญาณเตือนว่าตลาดอาจ Overvalued...",
        "title": "🌊 คลื่นยักษ์: วันที่ตลาดถล่ม",
        "narrative": "ตลาดหุ้นร่วงหนักในชั่วข้ามคืน! Panic selling ลุกลามทั่วโลก กองทุนหุ้นและ Sector Fund ขาดทุนหนัก แต่พันธบัตรรัฐบาลและทองคำราคาพุ่งขึ้นเพราะนักลงทุนวิ่งหา Safe Haven กองทุนตราสารหนี้ยืดหยัดได้ดี — นี่คือวันที่ 'ภูมิคุ้มกันพอร์ต' พิสูจน์คุณค่า",
        "impact": {1: 8, 2: -10, 3: 15, 4: -40, 5: -20, 6: -35, 7: 30, 8: -100, 9: 0},
    },
    {
        "id": 2,
        "name": "🔥 ไฟเงินเฟ้อ: ทุกอย่างแพงขึ้น",
        "en_label": "Inflationary Surge",
        "rumor": "ราคาสินค้าอุปโภคบริโภคเพิ่มขึ้นต่อเนื่องเป็นเดือนที่ 6 ต้นทุนพลังงานพุ่งสูง ซัพพลายเชนโลกยังติดขัด ธนาคารแห่งประเทศไทยกำลังพิจารณาทบทวนนโยบายการเงิน...",
        "title": "🔥 ไฟเงินเฟ้อ: ทุกอย่างแพงขึ้น",
        "narrative": "เงินเฟ้อพุ่งแตะ 7% ต่อปี! ราคาสินค้าทุกอย่างขึ้น เงินในบัญชีออมทรัพย์สูญเสียมูลค่าจริงอย่างเงียบๆ ทองคำและสินทรัพย์ที่จับต้องได้ราคาพุ่งเป็น Inflation Hedge แต่พันธบัตรดอกเบี้ยคงที่กลับ 'ขาดทุนจริง' แม้ตัวเลขในบัญชีไม่ลด — นี่คือ 'อาการป่วยเงียบ' ที่หมอหลวงทองอินเตือนไว้",
        "impact": {1: -8, 2: 5, 3: -5, 4: -10, 5: -5, 6: 10, 7: 40, 8: -100, 9: 0},
    },
    {
        "id": 3,
        "name": "🏦 เกมเปลี่ยน: ดอกเบี้ยขาขึ้น",
        "en_label": "Rate Hike Cycle",
        "rumor": "คณะกรรมการนโยบายการเงินนัดประชุมพิเศษ นักวิเคราะห์ส่วนใหญ่คาดการณ์ว่าจะมีการปรับอัตราดอกเบี้ยนโยบายอย่างน้อย 0.25-0.50% เพื่อสกัดเงินเฟ้อที่ยังสูงอยู่...",
        "title": "🏦 เกมเปลี่ยน: ดอกเบี้ยขาขึ้น",
        "narrative": "ธนาคารแห่งประเทศไทยขึ้นดอกเบี้ยนโยบาย 0.5%! เงินฝากและพันธบัตรใหม่ให้ผลตอบแทนสูงขึ้น กองทุนตราสารหนี้ระยะสั้นได้ประโยชน์ SSF/RMF ที่ลงทุนในตราสารหนี้พลิกเป็นบวก แต่ตลาดหุ้นปรับฐานเพราะต้นทุนกู้ยืมของบริษัทเพิ่มขึ้น ทองคำอ่อนแรงเพราะดอกเบี้ยสูง",
        "impact": {1: 15, 2: 10, 3: 20, 4: -25, 5: -10, 6: -20, 7: -10, 8: -100, 9: 0},
    },
    {
        "id": 4,
        "name": "⛈️ พายุโลก: วิกฤตข้ามทวีป",
        "en_label": "Global Crisis Contagion",
        "rumor": "ข่าวจากต่างประเทศว่าธนาคารพาณิชย์ขนาดใหญ่หลายแห่งในยุโรปรายงานปัญหาสภาพคล่อง ตลาดหุ้นในสหรัฐฯ และเอเชียร่วงแรงพร้อมกัน เม็ดเงินต่างชาติเริ่มไหลออกจากตลาดเกิดใหม่...",
        "title": "⛈️ พายุโลก: วิกฤตข้ามทวีป",
        "narrative": "วิกฤตการเงินจากต่างประเทศถล่มไทยเต็มๆ! ตลาดหุ้นร่วงหนักที่สุดในรอบทศวรรษ เม็ดเงินต่างชาติไหลออกรุนแรง ทองคำพุ่งสูงเป็น Global Safe Haven พันธบัตรรัฐบาลยังมั่นคง ทุกสินทรัพย์ความเสี่ยงสูงขาดทุนหนัก — วันนี้ที่เก็บ 'บารมี' ไว้มาก จะรับผลกระทบน้อยกว่า",
        "impact": {1: 10, 2: -20, 3: 10, 4: -45, 5: -25, 6: -40, 7: 35, 8: -100, 9: 0},
    },
    {
        "id": 5,
        "name": "⚡ ยุคดิจิทัลบูม: เทคพลิกโลก",
        "en_label": "Tech Innovation Boom",
        "rumor": "บริษัทเทคโนโลยีไทยและในภูมิภาคหลายแห่งรายงานผลกำไรสูงกว่าคาดการณ์ มีการประกาศ Partnership ขนาดใหญ่กับบริษัท Tech โลก นักวิเคราะห์ปรับประมาณการ Earnings ขึ้นทั่วกลุ่มเทคฯ...",
        "title": "⚡ ยุคดิจิทัลบูม: เทคพลิกโลก",
        "narrative": "กลุ่มเทคโนโลยีและดิจิทัลพุ่งขึ้นอย่างแข็งแกร่ง! Sector Fund กลุ่มเทคฯ ทำผลตอบแทนสูงสุดในรอบปี กองทุนหุ้นโดยรวมได้รับผลบวก SSF/RMF กลุ่มเทคฯ ทำกำไรงาม แต่ทองคำและตราสารหนี้ซบเซาเพราะนักลงทุนมองโลกในแง่ดีและไม่ต้องการ Safe Haven ในช่วงนี้",
        "impact": {1: 0, 2: 8, 3: 0, 4: 20, 5: 15, 6: 50, 7: -5, 8: -100, 9: 0},
    },
    {
        "id": 6,
        "name": "🌿 น้ำนิ่งไหลลึก: เศรษฐกิจมั่นคง",
        "en_label": "Steady Growth Quarter",
        "rumor": "ตัวเลข GDP ไตรมาสล่าสุดออกมาในแนวที่คาดการณ์ไว้ อัตราว่างงานทรงตัวในระดับต่ำ ไม่มีสัญญาณนโยบายเปลี่ยนแปลงจากธนาคารกลาง ตลาดซื้อขายด้วยปริมาณปกติ ไม่มีข่าวสำคัญ...",
        "title": "🌿 น้ำนิ่งไหลลึก: เศรษฐกิจมั่นคง",
        "narrative": "เศรษฐกิจเดินหน้าอย่างมั่นคงโดยไม่มี Boom หรือ Crash ทุกสินทรัพย์ให้ผลตอบแทนบวกพอสมควร กองทุนรวมผสมและ SSF/RMF ทำผลงานได้ดีสัมพัทธ์กับความเสี่ยง — นี่คือสภาวะที่ 'น้อยแต่สม่ำเสมอ' ชนะ 'มากแต่ผันผวน' และเป็นช่วงดีที่สุดสำหรับการทำ DCA",
        "impact": {1: 5, 2: 8, 3: 5, 4: 15, 5: 12, 6: 10, 7: 5, 8: -100, 9: 0},
    },
]

# Wisdom Hints per Event
INVESTMENT_WISDOM_HINTS = {
    0: {
        "medium": "เม็ดเงินต่างชาติกำลังไหลเข้าตลาดทุน สัญญาณบวกสำหรับสินทรัพย์ความเสี่ยงสูง",
        "high":   "ตลาดหุ้นและ Sector Fund จะได้ประโยชน์สูงสุด ทองคำและตราสารหนี้จะซบเซา",
    },
    1: {
        "medium": "ตลาดทุนโลกเริ่มส่งสัญญาณเชิงลบ สินทรัพย์ปลอดภัยอาจได้ประโยชน์",
        "high":   "พันธบัตรและทองคำจะเป็น Safe Haven ผู้ที่กระจายความเสี่ยงจะรอดได้ดีกว่ามาก",
    },
    2: {
        "medium": "ราคาสินค้าเพิ่มขึ้นทุกที่ สัญญาณเงินเฟ้อกำลังมา สินทรัพย์จริงน่าสนใจ",
        "high":   "ทองคำจะเป็น Inflation Hedge พันธบัตรดอกเบี้ยคงที่จะขาดทุนจริง แม้ตัวเลขไม่ลด",
    },
    3: {
        "medium": "นโยบายการเงินกำลังเปลี่ยนแปลง Fixed Income น่าสนใจขึ้น",
        "high":   "ดอกเบี้ยขาขึ้น — พันธบัตรและตราสารหนี้ระยะสั้นได้ประโยชน์ หุ้นและทองจะอ่อนแรง",
    },
    4: {
        "medium": "วิกฤตต่างประเทศกำลังส่งผลกระทบมายังตลาดในประเทศ",
        "high":   "สินทรัพย์ความเสี่ยงสูงทุกประเภทจะขาดทุน ทองคำและพันธบัตรรัฐบาลเป็น Safe Haven สากล",
    },
    5: {
        "medium": "กลุ่มธุรกิจเทคโนโลยีและนวัตกรรมกำลังเติบโตแข็งแกร่งมาก",
        "high":   "Sector Fund กลุ่มเทคฯ และกองทุนหุ้นจะได้ประโยชน์สูงสุด สินทรัพย์ Defensive จะซบเซา",
    },
    6: {
        "medium": "ตลาดเงียบ ไม่มีสัญญาณผิดปกติ ช่วงดีสำหรับการลงทุนระยะยาว",
        "high":   "ทุกสินทรัพย์ได้บวก กองทุนผสมและ SSF ทำผลงานดีที่สุดสัมพันธ์กับความเสี่ยง — สภาวะ DCA ที่ดีที่สุด",
    },
}

# ==========================================
# INVESTMENT QUESTS (8 Quests — LO-A to LO-F)
# ==========================================

INVESTMENT_QUESTS = {

    "iq1": {
        "id": "iq1",
        "name": "ต้นทุนแห่งความเฉื่อย",
        "npc_id": "wijit",
        "location_id": 7,
        "topic": "เงินเฟ้อและ Opportunity Cost",
        "lo_target": "LO-B",
        "quest_greeting": (
            "ท่านมาถูกที่แล้วขอรับ! ข้าอยากถามท่านก่อนเลยว่า — "
            "ถ้าท่านเก็บเงิน 100,000 บาทไว้ในบัญชีออมทรัพย์นาน 10 ปี "
            "ดอกเบี้ย 1.5% ต่อปี และเงินเฟ้ออยู่ที่ 3% ต่อปี "
            "เงินของท่านยังซื้อของได้เท่าเดิมไหมขอรับ?"
        ),
        "teacher_prompt": (
            "ท่านคือขุนวิจิตรสุวรรณ ผู้เชี่ยวชาญทองคำที่ข้ามเวลามา "
            "จงสอนเรื่องเงินเฟ้อและ Opportunity Cost ผ่านการเปรียบเทียบ: "
            "(1) เงินสดในบัญชีออมทรัพย์ดอกเบี้ย 1.5%/ปี vs เงินเฟ้อ 3%/ปี = Real Return ติดลบ 1.5%/ปี "
            "(2) เปรียบกับทองคำที่เพิ่มค่าตามเงินเฟ้อหรือมากกว่า "
            "(3) คำนวณให้เห็นจริง: 100,000 บาท × (1.015)^10 = 116,054 บาท "
            "แต่กำลังซื้อจริงลดลง เพราะเงินเฟ้อทำให้ราคาสินค้าเป็น 100,000 × (1.03)^10 = 134,392 บาท "
            "(4) ให้ผู้เล่นยกตัวอย่างสินค้าที่แพงขึ้นในชีวิตจริงของตนเอง "
            "ใช้สไตล์กระตือรือร้น อ้างอิงทองคำเป็น hedge เสมอ"
        ),
        "evaluation_criteria": (
            "ผู้เล่นต้องอธิบายได้ว่า "
            "(1) เงินเฟ้อคืออะไรและส่งผลต่อมูลค่าเงินอย่างไร "
            "(2) การถือเงินสดมี Real Return ติดลบเมื่อเงินเฟ้อ > ดอกเบี้ย "
            "(3) ยกตัวอย่างสินค้าหรือบริการที่ราคาแพงขึ้นในชีวิตจริงได้อย่างน้อย 1 ตัวอย่าง"
        ),
        "min_turns": 3,
        "rewards": {
            "wisdom": 15, "wealth": 5000, "merit": 0, "hp_cost": 0,
            "item": "Fact Sheet ทองคำ",
        },
    },

    "iq2": {
        "id": "iq2",
        "name": "แผนที่ความเสี่ยงของนักลงทุน",
        "npc_id": "karaket",
        "location_id": 4,
        "topic": "Risk Tolerance และ Asset Allocation",
        "lo_target": "LO-C",
        "quest_greeting": (
            "ท่านมาดีเลยเจ้าค่ะ! ในยุคนี้ก่อนจะลงทุนที่ไหน "
            "ต้องรู้ก่อนว่าตัวเองรับความเสี่ยงได้แค่ไหน "
            "ข้าขอถามก่อนนะเจ้าค่ะ — ถ้าพอร์ตของท่านลดลง 20% ในเวลา 1 เดือน "
            "ท่านจะทำอะไร: ขายทิ้งทันที, รอและไม่ทำอะไร, หรือซื้อเพิ่มเจ้าค่ะ?"
        ),
        "teacher_prompt": (
            "ท่านคือแม่นายการะเกด ที่ปรึกษาการลงทุนจากท่าเรือ "
            "จงสอนเรื่อง Risk Tolerance และ Asset Allocation โดย: "
            "(1) ถามคำถาม Risk Tolerance: 'ถ้าพอร์ตลง 20% จะทำอะไร?' — "
            "ขายทิ้ง = Conservative, รอ = Moderate, ซื้อเพิ่ม = Aggressive "
            "(2) ใช้กรณีศึกษา: นักศึกษา อายุ 22 ปี ไม่ต้องใช้เงินใน 15 ปี "
            "vs พ่อแม่ อายุ 55 ปี จะเกษียณใน 2 ปี — ใครควร Allocate อย่างไร? "
            "(3) สอน Rule of 100: อายุ = % ที่ควรถือตราสารหนี้ (อายุ 30 → 30% ตราสารหนี้) "
            "(4) เชื่อม Location ในเกมกับ Risk Profile: "
            "L1-L3 = Conservative, L4-L5 = Moderate, L6-L7 = Aggressive "
            "(5) ให้ผู้เล่นเสนอ Allocation ของตัวเองพร้อมเหตุผล"
        ),
        "evaluation_criteria": (
            "ผู้เล่นต้องอธิบายได้ว่า "
            "(1) Risk Tolerance ขึ้นกับอะไรบ้าง (อายุ เป้าหมาย ระยะเวลา ความสามารถรับผิดชอบ) "
            "(2) ความแตกต่างของ Risk ระหว่าง Location/ผลิตภัณฑ์อย่างน้อย 2 ประเภท "
            "(3) เสนอ Asset Allocation ที่เหมาะสมสำหรับสถานการณ์ที่กำหนดให้ พร้อมเหตุผล"
        ),
        "min_turns": 4,
        "rewards": {
            "wisdom": 20, "wealth": 8000, "merit": 0, "hp_cost": 0,
            "item": None,
        },
    },

    "iq3": {
        "id": "iq3",
        "name": "รู้จักอาวุธแห่งการลงทุน: หุ้นและ Sector Fund",
        "npc_id": "asa",
        "location_id": 6,
        "topic": "ผลิตภัณฑ์ลงทุนประเภทหุ้น: กองทุนรวมหุ้น vs Sector Fund vs หุ้นรายตัว",
        "lo_target": "LO-D",
        "quest_greeting": (
            "ท่านมาดีแล้วขอรับ! ข้าต้องการทดสอบความรู้ท่านก่อน — "
            "ท่านรู้ไหมว่า 'กองทุนรวมหุ้น' 'Sector Fund' และ 'หุ้นรายตัว' ต่างกันอย่างไรขอรับ? "
            "ทั้งสามคือ 'อาวุธ' คนละประเภท — "
            "เหล็กก้อนเดียวกัน ตีเป็นดาบแตกต่างกัน มูลค่าก็แตกต่างกันขอรับ!"
        ),
        "teacher_prompt": (
            "ท่านคือออกหลวงอาสา ผู้เชี่ยวชาญ Sector Investing "
            "จงสอนความแตกต่างระหว่าง 3 ผลิตภัณฑ์หุ้น: "
            "(1) กองทุนรวมหุ้นทั่วไป (Active/Passive Index): "
            "กระจายกว้างทั้งตลาด ความเสี่ยงต่ำกว่า เหมาะกับมือใหม่ "
            "เปรียบ = 'ถืออาวุธทุกชนิดในคลัง' "
            "(2) Sector Fund: เน้นกลุ่มอุตสาหกรรมเดียว เช่น เทคฯ สุขภาพ พลังงาน "
            "ถ้าถูก Sector กำไรสูงมาก ถ้าผิด ขาดทุนหนัก "
            "เปรียบ = 'เลือกตีดาบประเภทเดียวให้เก่งที่สุด' "
            "(3) หุ้นรายตัว: เลือกเองทุกอย่าง ความเสี่ยงและผลตอบแทนสูงสุด "
            "ต้องมีความรู้มากที่สุด เปรียบ = 'ตีดาบด้วยมือตัวเองทีละเล่ม' "
            "ให้ผู้เล่นบอกได้ว่าแต่ละประเภทเหมาะกับนักลงทุนแบบไหน"
        ),
        "evaluation_criteria": (
            "ผู้เล่นต้องอธิบายได้ว่า "
            "(1) ความแตกต่างระหว่างกองทุนรวมหุ้น Sector Fund และหุ้นรายตัว ในแง่ความเสี่ยงและการกระจาย "
            "(2) แต่ละประเภทเหมาะกับนักลงทุนแบบไหน "
            "(3) ระบุตัวอย่าง Sector ที่น่าสนใจในปัจจุบันพร้อมเหตุผลได้"
        ),
        "min_turns": 3,
        "rewards": {
            "wisdom": 15, "wealth": 5000, "merit": 0, "hp_cost": 0,
            "item": "ดาบ Sector Fund",
        },
    },

    "iq4": {
        "id": "iq4",
        "name": "สัมปทานภาษีของนักลงทุนยุคใหม่",
        "npc_id": "khunluang",
        "location_id": 2,
        "topic": "กองทุน SSF, RMF และ Tax-Efficient Investing",
        "lo_target": "LO-D",
        "quest_greeting": (
            "ท่านมาดีแล้วขอรับ! "
            "ในสมัยอยุธยา ผู้รู้กฎภาษีได้สัมปทาน วันนี้ก็เช่นกัน — "
            "ท่านรู้ไหมว่ามีผลิตภัณฑ์ลงทุนที่ทำให้ท่านจ่ายภาษีน้อยลงได้ถูกกฎหมาย 100%? "
            "ข้าขอถามก่อนนะขอรับ — ท่านรู้จัก SSF หรือ RMF ไหมขอรับ?"
        ),
        "teacher_prompt": (
            "ท่านคือขุนหลวงบริรักษ์ ผู้เชี่ยวชาญระบบภาษีและการลงทุน "
            "จงสอนเรื่อง SSF และ RMF โดยละเอียด: "
            "(1) SSF (Super Saving Fund): "
            "ลดหย่อนภาษีได้ 30% ของรายได้ สูงสุด 200,000 บาท ถือ 10 ปีนับจากวันซื้อ "
            "(2) RMF (Retirement Mutual Fund): "
            "ลดหย่อนได้ 30% ของรายได้ รวม SSF ไม่เกิน 500,000 บาท ถือถึงอายุ 55 ปีและถือ 5 ปีขึ้นไป "
            "(3) คำนวณให้เห็นจริง: รายได้ 300,000 บาท/ปี ลงทุน SSF 90,000 บาท "
            "ถ้าอยู่ในฐานภาษี 20% = ประหยัดภาษีได้ 18,000 บาท "
            "(4) Danger Zone: ขายก่อนกำหนด = ต้องคืนเงินภาษีที่เคยได้ + ค่าปรับ"
        ),
        "evaluation_criteria": (
            "ผู้เล่นต้องอธิบายได้ว่า "
            "(1) SSF และ RMF คืออะไร ต่างกันอย่างไร (เงื่อนไขถือครอง วัตถุประสงค์) "
            "(2) การลดหย่อนภาษีผ่านกองทุนเหล่านี้ทำงานอย่างไรในเบื้องต้น "
            "(3) เงื่อนไขสำคัญที่ต้องระวัง เช่น Lock-up Period และผลเมื่อขายก่อนกำหนด"
        ),
        "min_turns": 3,
        "rewards": {
            "wisdom": 15, "wealth": 5000, "merit": 5, "hp_cost": 0,
            "item": None,
        },
    },

    "iq5": {
        "id": "iq5",
        "name": "พลังทบต้นและ Opportunity Cost",
        "npc_id": "grandma_in",
        "location_id": 5,
        "topic": "Compound Interest, DCA และ Opportunity Cost",
        "lo_target": "LO-B",
        "quest_greeting": (
            "หลานมาแล้วหรือจ้ะ ยายถามก่อนนะ — "
            "ถ้าหลานเก็บเงินเดือนละ 1,000 บาท "
            "ตลอด 30 ปี ที่ผลตอบแทน 6% ต่อปี "
            "หลานคิดว่าจะได้เงินเท่าไรจ้ะ? ลองเดาก่อนนะ "
            "แล้วยายจะบอกคำตอบที่ทำให้หลานตกใจแน่นอนจ้ะ"
        ),
        "teacher_prompt": (
            "ท่านคือยายอิน ปราชญ์ชาวนาผู้รักการออม "
            "จงสอนเรื่อง Compound Interest ผ่านอุปมาการปลูกข้าว: "
            "(1) เปรียบ 'เมล็ดพันธุ์' = 'เงินต้น' และ 'เก็บเกี่ยวแล้วปลูกซ้ำ' = 'ดอกเบี้ยทบต้น' "
            "(2) คำนวณให้เห็นจริง: DCA 1,000 บาท/เดือน × 30 ปี × 6%/ปี "
            "≈ 1,004,515 บาท (ใส่เงินจริงเพียง 360,000 บาท! ดอกเบี้ยสร้างอีก 644,515 บาท) "
            "(3) Rule of 72: 72 ÷ 6% = 12 ปี เงินจะเป็น 2 เท่า "
            "(4) Opportunity Cost: เริ่มอายุ 25 (30 ปี) vs เริ่มอายุ 35 (20 ปี) "
            "ผลตอบแทนต่างกันมากกว่า 2 เท่า แม้ใส่เงินเดือนละเท่ากัน "
            "ใช้ภาษาชาวนา อุปมาธรรมชาติ ห้ามใช้ภาษาวิชาการ"
        ),
        "evaluation_criteria": (
            "ผู้เล่นต้องอธิบายได้ว่า "
            "(1) Compound Interest คืออะไรและทำงานอย่างไร "
            "(2) เวลา (Time Horizon) มีผลต่อผลลัพธ์การลงทุนมากแค่ไหน "
            "(3) Opportunity Cost ของการเริ่มช้า — เริ่มตอนอายุ 25 vs 35 ต่างกันอย่างไร"
        ),
        "min_turns": 3,
        "rewards": {
            "wisdom": 15, "wealth": 3000, "merit": 0, "hp_cost": 0,
            "item": "ข้าวทิพย์ DCA",
        },
    },

    "iq6": {
        "id": "iq6",
        "name": "กระจายความเสี่ยงอย่างชาญฉลาด",
        "npc_id": "kosathibodi",
        "location_id": 1,
        "topic": "Diversification และ Portfolio Construction",
        "lo_target": "LO-C",
        "quest_greeting": (
            "ท่านมาในเวลาอันเหมาะสมขอรับ "
            "ข้ามีคำถามทดสอบปัญญา — "
            "ถ้าท่านลงทุน 100,000 บาทใน Location เดียวทั้งหมด "
            "แล้วเหตุการณ์วิกฤตถล่ม Location นั้นด้วย Impact -40% "
            "ท่านจะสูญเสียเท่าไรขอรับ? "
            "แล้วถ้ากระจายใน 3 Location ที่ต่างประเภทกัน ผลจะต่างกันไหม?"
        ),
        "teacher_prompt": (
            "ท่านคือออกญาโกษาธิบดี ผู้เชี่ยวชาญการบริหารความเสี่ยงแห่งพระคลัง "
            "จงสอนเรื่อง Diversification โดย: "
            "(1) คำนวณให้เห็น: 100% Location 4 เมื่อ Market Crash -40% "
            "= สูญเสีย 40,000 บาท vs กระจาย 33% L1, 33% L3, 33% L4 "
            "= สูญเสียเพียง ~9,200 บาท (L1 +8%, L3 +15%, L4 -40%) "
            "(2) อธิบาย Correlation: ทองคำ (L7) มักสวนทางกับหุ้น (L4) "
            "ตราสารหนี้ (L3) ก็มักสวนทางกับหุ้น "
            "(3) สอน 'Rule of 100': อายุ = % ตราสารหนี้ที่ควรถือ "
            "(4) ให้ผู้เล่นออกแบบพอร์ต 3 Location พร้อมเหตุผล"
        ),
        "evaluation_criteria": (
            "ผู้เล่นต้องอธิบายได้ว่า "
            "(1) การกระจายความเสี่ยงช่วยลดความผันผวนโดยรวมของพอร์ตได้อย่างไร "
            "(2) สินทรัพย์ที่มี Correlation ต่ำ/ลบ ช่วยพอร์ตได้อย่างไรในภาวะวิกฤต "
            "(3) เสนอพอร์ต 2-3 Location พร้อมอธิบายเหตุผลที่เลือก Location เหล่านั้น"
        ),
        "min_turns": 4,
        "rewards": {
            "wisdom": 20, "wealth": 8000, "merit": 0, "hp_cost": 0,
            "item": None,
        },
    },

    "iq7": {
        "id": "iq7",
        "name": "Real Return: ผลตอบแทนจริงหลังเงินเฟ้อ",
        "npc_id": "thongin",
        "location_id": 3,
        "topic": "Real Return = Nominal Return − Inflation Rate",
        "lo_target": "LO-F",
        "quest_greeting": (
            "ข้าวินิจฉัยพอร์ตของท่านแล้วขอรับ "
            "และพบ 'อาการป่วยเงียบ' ที่น่าเป็นห่วงมาก "
            "ท่านรู้ไหมว่าผลตอบแทน 5% ต่อปี "
            "อาจเป็น 'ผลตอบแทนจริง' แค่ 1–2% ก็ได้? "
            "ถ้าเงินเฟ้ออยู่ที่ 4% ต่อปี "
            "ผลตอบแทนจริงของท่านเหลือเพียงเท่าไรขอรับ?"
        ),
        "teacher_prompt": (
            "ท่านคือหมอหลวงทองอิน ผู้วินิจฉัยสุขภาพพอร์ต "
            "จงสอนสูตร Real Return = Nominal Return − Inflation Rate โดย: "
            "(1) อธิบายว่า 'ผลตอบแทนจริง' ≠ 'ผลตอบแทนที่เห็น' "
            "(2) วินิจฉัย 3 'ผู้ป่วย': "
            "ก. เงินฝาก 1.5% − เงินเฟ้อ 4% = Real Return -2.5% (ป่วยหนัก!) "
            "ข. ตราสารหนี้ 4% − เงินเฟ้อ 4% = Real Return 0% (ทรงตัว) "
            "ค. กองทุนหุ้น 10% − เงินเฟ้อ 4% = Real Return 6% (แข็งแรง!) "
            "(3) อธิบายว่าผลิตภัณฑ์ใดที่ 'ชนะเงินเฟ้อ' ในระยะยาวได้ "
            "(โดยทั่วไป: หุ้น > ทอง > ตราสารหนี้ > เงินฝาก) "
            "(4) ให้ผู้เล่นคำนวณ Real Return ของสถานการณ์ที่กำหนด 2 กรณี "
            "ใช้ภาษาการแพทย์เปรียบตลอด: 'วินิจฉัย' 'อาการ' 'ยา' 'สุขภาพพอร์ต'"
        ),
        "evaluation_criteria": (
            "ผู้เล่นต้องอธิบายได้ว่า "
            "(1) Real Return คืออะไรและต่างจาก Nominal Return อย่างไร "
            "(2) ผลิตภัณฑ์ใดบ้างที่ 'ชนะ' เงินเฟ้อได้ในระยะยาว และผลิตภัณฑ์ใดที่ไม่ "
            "(3) คำนวณ Real Return จากตัวเลขที่กำหนดได้"
        ),
        "min_turns": 3,
        "rewards": {
            "wisdom": 15, "wealth": 5000, "merit": 0, "hp_cost": 0,
            "item": "ยาหอมนักลงทุน",
        },
    },

    "iq8": {
        "id": "iq8",
        "name": "ภูมิคุ้มกันและการลงทุนอย่างยั่งยืน",
        "npc_id": "ajarn_mun",
        "location_id": 8,
        "topic": "Emergency Fund, ESG Investing และ Sustainable Finance",
        "lo_target": "LO-B / LO-F",
        "quest_greeting": (
            "เจริญพร โยม ก่อนที่จะลงทุนในสิ่งใดก็ตาม "
            "อาตมามีคำถามง่ายๆ ข้อหนึ่ง — "
            "ถ้าโยมตกงานพรุ่งนี้ โยมมีเงินพอใช้จ่ายกี่เดือนเจริญพร? "
            "และโยมเคยถามตัวเองไหมว่า "
            "บริษัทที่โยมจะลงทุนนั้น ทำสิ่งดีต่อโลกหรือทำลายโลกเจริญพร?"
        ),
        "teacher_prompt": (
            "ท่านคือพระอาจารย์มั่น ที่ปรึกษาด้าน Sustainable Finance "
            "จงสอนสองเรื่องหลัก: "
            "(1) Emergency Fund: "
            "ควรมีเงินสำรอง 3-6 เดือนของรายจ่ายก่อนลงทุนเสมอ "
            "เก็บใน: เงินฝากออมทรัพย์หรือกองทุนตลาดเงิน (สภาพคล่องสูง) "
            "ถ้าไม่มี → วิกฤตมา → ต้องขายกองทุนขาดทุน → เจ็บซ้ำ "
            "คำนวณให้เห็น: รายจ่าย 20,000 บาท/เดือน × 6 = ต้องมี 120,000 บาทสำรอง "
            "(2) ESG Investing: "
            "E = Environmental: บริษัทดูแลสิ่งแวดล้อม "
            "S = Social: ดูแลแรงงาน ชุมชน ผู้บริโภค "
            "G = Governance: ธรรมาภิบาล ความโปร่งใส "
            "(3) เชื่อม Sufficiency Economy: "
            "พอประมาณ = ลงทุนในระดับที่เหมาะกับตน / มีเหตุผล = มีกลยุทธ์ชัดเจน / มีภูมิคุ้มกัน = Emergency Fund"
        ),
        "evaluation_criteria": (
            "ผู้เล่นต้องอธิบายได้ว่า "
            "(1) Emergency Fund คืออะไรและควรมีเท่าไรก่อนลงทุน "
            "(2) ผลที่ตามมาถ้าไม่มี Emergency Fund แล้วเจอวิกฤต "
            "(3) ESG คืออะไรในเบื้องต้น และเชื่อมกับหลักเศรษฐกิจพอเพียงได้อย่างน้อย 1 ข้อ"
        ),
        "min_turns": 3,
        "rewards": {
            "wisdom": 20, "wealth": 3000, "merit": 20, "hp_cost": 0,
            "item": "กองทุนฉุกเฉิน",
        },
    },
}

# ==========================================
# INVESTMENT SCENARIOS (6 Scenarios)
# ==========================================

INVESTMENT_SCENARIOS = [

    # ─── Beginner (3 ไตรมาส) ───
    {
        "id": "iq_s1",
        "name": "ก้าวแรกของนักลงทุน",
        "desc": "เริ่มต้นอย่างมั่นคง เรียนรู้ผลิตภัณฑ์แต่ละประเภท และเจอเงินเฟ้อในรอบสุดท้าย",
        "schedule": [6, 0, 2],
        "max_rounds": 3,
        "mode": "beginner",
        "narrative_arc": "ปลอดภัย → กำลังใจ → บทเรียนเงินเฟ้อ",
        "lo_focus": "LO-B (เงินเฟ้อ), LO-D (รู้จักผลิตภัณฑ์)",
        "quest_recommended": ["iq5", "iq1"],
    },
    {
        "id": "iq_s2",
        "name": "อย่าใส่ไข่ทั้งฟองในตะกร้าเดียว",
        "desc": "เริ่มดีด้วย Bull Market แต่ Crash ถล่มในรอบสอง เรียนรู้ Diversification",
        "schedule": [0, 1, 6],
        "max_rounds": 3,
        "mode": "beginner",
        "narrative_arc": "โลภ → เจ็บปวด → เข้าใจ",
        "lo_focus": "LO-C (Diversification, Risk Profile)",
        "quest_recommended": ["iq6", "iq2"],
    },
    {
        "id": "iq_s3",
        "name": "ภูมิคุ้มกันทางการเงิน",
        "desc": "เศรษฐกิจปกติก่อน แล้ววิกฤตโลกถล่ม ทดสอบว่าพอร์ตแข็งแกร่งพอไหม",
        "schedule": [6, 4, 0],
        "max_rounds": 3,
        "mode": "beginner",
        "narrative_arc": "ระวัง → วิกฤต → รอด",
        "lo_focus": "LO-B (Emergency Fund), LO-C (Safe Haven Assets)",
        "quest_recommended": ["iq8", "iq6"],
    },

    # ─── Normal (5 ไตรมาส) ───
    {
        "id": "iq_n1",
        "name": "วัฏจักรนักลงทุน",
        "desc": "ครบวัฏจักรตลาด — Stable → Bull → Inflation → Crash → Recovery เรียนรู้ทุก scenario ที่ตลาดจริงมี",
        "schedule": [6, 0, 2, 1, 6],
        "max_rounds": 5,
        "mode": "normal",
        "narrative_arc": "เรียนรู้ทุก scenario ที่ตลาดจริงมี",
        "lo_focus": "LO-B / LO-C / LO-D / LO-F ครบ",
        "quest_recommended": ["iq1", "iq2", "iq5", "iq6", "iq7"],
    },
    {
        "id": "iq_n2",
        "name": "กับดักเงินเฟ้อ",
        "desc": "เงินเฟ้อสองรอบซ้อน ทดสอบว่าพอร์ตป้องกัน Inflation ได้จริงไหม",
        "schedule": [0, 2, 2, 3, 6],
        "max_rounds": 5,
        "mode": "normal",
        "narrative_arc": "เริ่มดี → Inflation Trap → นโยบายสู้ → ฟื้น",
        "lo_focus": "LO-B (Inflation), LO-F (Real Return), LO-C (Hedge Strategy)",
        "quest_recommended": ["iq1", "iq7", "iq2"],
    },
    {
        "id": "iq_n3",
        "name": "พายุและการฟื้นตัว",
        "desc": "เริ่มด้วยวิกฤต วิกฤตซ้อน แล้วฟื้น — พิสูจน์ Diversification และ Patience",
        "schedule": [1, 4, 3, 0, 5],
        "max_rounds": 5,
        "mode": "normal",
        "narrative_arc": "ล้มแล้วลุก Diversification ชนะในระยะยาว",
        "lo_focus": "LO-C (Diversification + Risk Management ขั้นสูง)",
        "quest_recommended": ["iq6", "iq8", "iq3"],
    },
]

# ==========================================
# RANKS (Investment Mode)
# ==========================================

RANKS = [
    {
        "id": "bankrupt",
        "name": "นักลงทุนล้มละลาย",
        "icon": "fa-skull",
        "desc": "สินทรัพย์ติดลบ — ขาดทุนจนหมดตัว บทเรียนที่เจ็บปวดแต่มีค่า",
    },
    {
        "id": "beginner",
        "name": "นักลงทุนมือใหม่",
        "icon": "fa-seedling",
        "desc": "รอดมาได้ แต่ยังต้องเรียนรู้อีกมาก ก้าวต่อไปอย่าหยุด",
    },
    {
        "id": "intermediate",
        "name": "นักลงทุนมีฐาน",
        "icon": "fa-chart-line",
        "desc": "เข้าใจพื้นฐาน มีทรัพย์สินเติบโต เริ่มเห็นพลังของการลงทุน",
    },
    {
        "id": "professional",
        "name": "นักลงทุนมืออาชีพ",
        "icon": "fa-briefcase",
        "desc": "บริหารพอร์ตได้อย่างชาญฉลาด เข้าใจทั้ง Risk และ Return",
    },
    {
        "id": "legend",
        "name": "ตำนานนักลงทุน",
        "icon": "fa-crown",
        "desc": "เจนวิทยายุทธ์การเงิน ทั้งทรัพย์สิน ปัญญา บารมี และสุขภาพ",
    },
]

# Wisdom Gate
WISDOM_GATE_NORMAL   = [20, 30, 40, 50, 60]
WISDOM_GATE_BEGINNER = [15, 25, 35]


def calculate_rank(stats: dict, max_rounds: int = 5) -> dict:
    """Calculate player rank based on stats and game mode (merged function)."""
    wealth = stats.get("wealth", 0)
    wisdom = stats.get("wisdom", 0)
    merit  = stats.get("merit", 0)
    health = stats.get("health", 0)

    if max_rounds == 3:  # Beginner thresholds
        if wealth <= 0:
            return RANKS[0]
        elif wealth >= 140000 and wisdom >= 35 and merit >= 20 and health >= 40:
            return RANKS[4]
        elif wealth >= 115000 and wisdom >= 25 and merit >= 15:
            return RANKS[3]
        elif wealth >= 90000 and wisdom >= 20:
            return RANKS[2]
        else:
            return RANKS[1]
    else:  # Normal thresholds
        if wealth <= 0:
            return RANKS[0]
        elif wealth >= 200000 and wisdom >= 50 and merit >= 30 and health >= 40:
            return RANKS[4]
        elif wealth >= 150000 and wisdom >= 40 and merit >= 20:
            return RANKS[3]
        elif wealth >= 80000 and wisdom >= 30:
            return RANKS[2]
        else:
            return RANKS[1]


# ==========================================
# 2. PYDANTIC MODELS
# ==========================================

class PlayerStats(BaseModel):
    wealth: int = 100000      # บาท (THB)
    wisdom: int = 10          # Financial Literacy Score
    merit:  int = 10          # Emergency Fund / Safety Net Level
    health: int = 100         # Human Capital
    items:  List[str] = []


class GameState(BaseModel):
    scenario_id:          str
    round:                int = 1
    max_rounds:           int = 5
    stats:                PlayerStats
    history:              List[Dict] = []
    active_quest:         Optional[str] = None
    completed_quests:     List[str] = []
    quest_chat_history:   List[Dict] = []
    quest_turn_count:     int = 0
    horathibodi_chat_count: int = 0


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


class InsightsRequest(BaseModel):
    game_state: GameState


class QuestAcceptRequest(BaseModel):
    game_state: GameState
    quest_id:   str


class QuestEvaluateRequest(BaseModel):
    quest_id:     str
    chat_history: List[Dict[str, str]]


class QuestCompleteRequest(BaseModel):
    game_state: GameState
    quest_id:   str


# ==========================================
# 3. API ROUTES
# ==========================================

@app.get("/")
async def index(request: Request):
    """Serve the main game page."""
    return templates.TemplateResponse(request, "index.html")


@app.get("/api/init")
async def get_init_data():
    """Return static game data for frontend initialization."""
    return {
        "scenarios": INVESTMENT_SCENARIOS,
        "wisdom_gate":          WISDOM_GATE_NORMAL,
        "wisdom_gate_beginner": WISDOM_GATE_BEGINNER,
        "locations": {
            k: {
                "name":           v["name"],
                "npc_id":         v["npc_id"],
                "type":           v.get("type", ""),
                "modern_product": v.get("modern_product", ""),
                "risk_level":     v.get("risk_level", 0),
                "risk_label":     v.get("risk_label", ""),
                "return_range":   v.get("return_range", ""),
                "desc":           v["desc"],
                "hp_cost":        v["hp_cost"],
                "merit_effect":   v["merit_effect"],
                "min_invest":     v["min_invest"],
                "require_merit":  v.get("require_merit", 0),
                "require_health": v.get("require_health", 0),
                "is_quest_hub":   v.get("is_quest_hub", False),
            }
            for k, v in LOCATIONS.items()
        },
        "npcs": {
            k: {
                "name":           v["name"],
                "role":           v["role"],
                "icon":           v.get("icon", "fa-user"),
                "modern_product": v.get("modern_product", ""),
                "philosophy":     v.get("philosophy", ""),
                "temporal_bridge": v.get("temporal_bridge", ""),
                "greeting":       v.get("greeting", ""),
            }
            for k, v in NPC_DATA.items()
        },
        "quests": {
            k: {
                "id":             v["id"],
                "name":           v["name"],
                "npc_id":         v["npc_id"],
                "location_id":    v["location_id"],
                "topic":          v["topic"],
                "lo_target":      v.get("lo_target", ""),
                "min_turns":      v["min_turns"],
                "rewards":        v["rewards"],
                "quest_greeting": v.get("quest_greeting", ""),
            }
            for k, v in INVESTMENT_QUESTS.items()
        },
    }


@app.post("/api/news")
async def get_news_rumor(request: GameState):
    """Get the rumor/news for the current round based on scenario schedule."""
    scenario = next((s for s in INVESTMENT_SCENARIOS if s["id"] == request.scenario_id), None)
    if not scenario:
        raise HTTPException(status_code=400, detail="Invalid Scenario")

    try:
        event_id = scenario["schedule"][request.round - 1]
        event    = next((e for e in INVESTMENT_EVENTS_MASTER if e["id"] == event_id),
                        INVESTMENT_EVENTS_MASTER[0])
        wisdom   = request.stats.wisdom
        hints    = INVESTMENT_WISDOM_HINTS.get(event_id, {})

        response = {
            "round":       request.round,
            "rumor":       event["rumor"],
            "source":      "ศูนย์วิจัยการลงทุน",
            "wisdom_level": "low",
        }

        if wisdom >= 25 and hints.get("medium"):
            response["wisdom_level"] = "medium"
            response["hint"]         = hints["medium"]

        if wisdom >= 40 and hints.get("high"):
            response["wisdom_level"] = "high"
            response["hint2"]        = hints["high"]

        if wisdom >= 55:
            response["wisdom_level"] = "master"
            sorted_impacts = sorted(event["impact"].items(), key=lambda x: x[1], reverse=True)
            top_sectors    = [LOCATIONS[k]["name"] for k, v in sorted_impacts[:2] if v > 0]
            if top_sectors:
                response["insight"] = f"สินทรัพย์ที่น่าจะได้ประโยชน์สูงสุด: {', '.join(top_sectors)}"

        return response

    except IndexError:
        return {"rumor": "ตลาดสงบนิ่ง... ไตรมาสนี้สิ้นสุดแล้ว", "source": "ศูนย์วิจัยการลงทุน"}


@app.post("/api/end-turn")
async def end_turn(request: TurnActionRequest):
    """
    Process the investment turn:
    1. Wisdom Gate Validation
    2. Health Gate + Merit Gate per Location
    3. Apply Event Impact per Location
    4. Apply Item Effects (Fact Sheet ทองคำ, ดาบ Sector Fund, ข้าวทิพย์ DCA)
    5. Wisdom Tier Bonuses
    6. Merit Safety Net (+ dual_benefit bonus from กองทุนฉุกเฉิน)
    7. Medical Cost (ยาหอมนักลงทุน / กองทุนฉุกเฉิน = 50% discount)
    8. Update Stats → Check Game Over → Calculate Rank
    """
    state       = request.game_state
    investments = list(request.investments)
    items       = state.stats.items

    # 1. Wisdom Gate
    active_wisdom_gate = (WISDOM_GATE_BEGINNER if state.max_rounds == 3
                          else WISDOM_GATE_NORMAL)
    round_index = state.round - 1
    if round_index < len(active_wisdom_gate):
        required_wisdom = active_wisdom_gate[round_index]
        if state.stats.wisdom < required_wisdom:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"ความรู้การเงินไม่เพียงพอ! ไตรมาสนี้ต้องการปัญญา {required_wisdom} "
                    f"(ปัจจุบัน: {state.stats.wisdom}) — รับเควสต์และสนทนากับ NPC เพื่อเพิ่มปัญญาก่อน"
                ),
            )

    # 2. Identify Event
    scenario = next((s for s in INVESTMENT_SCENARIOS if s["id"] == state.scenario_id), None)
    if not scenario:
        raise HTTPException(status_code=400, detail="Invalid scenario ID")
    event_id = scenario["schedule"][state.round - 1]
    event    = next((e for e in INVESTMENT_EVENTS_MASTER if e["id"] == event_id),
                    INVESTMENT_EVENTS_MASTER[0])

    # 3. Determine health status from current HP
    current_health = state.stats.health
    if current_health < 10:
        health_status = "critical"
    elif current_health < 40:
        health_status = "overwork"
    else:
        health_status = "normal"

    # 4. Validate investments (health gate + merit gate + min invest)
    valid_investments  = []
    validation_errors  = []
    for inv in investments:
        area = LOCATIONS.get(inv.area_id)
        if not area:
            continue

        require_health = area.get("require_health", 0)
        if require_health > current_health:
            if health_status == "critical":
                validation_errors.append(
                    f"{area['name']}: สุขภาพวิกฤต! ลงทุนได้เฉพาะ ศาลาพระโอสถ 🏥"
                )
            else:
                validation_errors.append(
                    f"{area['name']}: ร่างกายอ่อนแอ — ต้องมี HP ≥ {require_health} (ปัจจุบัน: {current_health}) ⚠️"
                )
            continue

        if (area.get("require_merit", 0) > 0 and
                state.stats.merit < area["require_merit"]):
            validation_errors.append(
                f"{area['name']}: ต้องมีบารมีอย่างน้อย {area['require_merit']}"
            )
            continue

        if inv.amount < area.get("min_invest", 0):
            validation_errors.append(
                f"{area['name']}: ลงทุนขั้นต่ำ {area['min_invest']:,} บาท"
            )
            continue

        valid_investments.append(inv)

    investments = valid_investments

    # 5. Calculate Impacts + HP costs + Merit changes
    round_log    = []
    item_effects = []
    total_profit = 0
    merit_change = 0
    health_change = 0
    wisdom       = state.stats.wisdom

    for inv in investments:
        area = LOCATIONS.get(inv.area_id)
        if not area:
            continue

        impact_pct = event["impact"].get(inv.area_id, 0)

        # --- Item Effects (applied per-location before Wisdom Tiers) ---

        # ข้าวทิพย์ DCA → L5: floor_zero (protect Balanced Fund from negative impact)
        if inv.area_id == 5 and "ข้าวทิพย์ DCA" in items and impact_pct < 0:
            item_effects.append({
                "item":    "ข้าวทิพย์ DCA",
                "icon":    "🌾",
                "area_id": 5,
                "desc":    f"ข้าวทิพย์ DCA คุ้มครองกองทุนผสม ({impact_pct}% → 0%)",
            })
            impact_pct = 0

        # ดาบ Sector Fund → L6: floor_zero (protect Sector Fund from negative impact)
        if inv.area_id == 6 and "ดาบ Sector Fund" in items and impact_pct < 0:
            item_effects.append({
                "item":    "ดาบ Sector Fund",
                "icon":    "⚔️",
                "area_id": 6,
                "desc":    f"ดาบ Sector Fund คุ้มครองการลงทุน ({impact_pct}% → 0%)",
            })
            impact_pct = 0

        # Fact Sheet ทองคำ → L7: reduce_negative (reduce magnitude of negative impact by 10%)
        if inv.area_id == 7 and "Fact Sheet ทองคำ" in items and impact_pct < 0:
            original_pct = impact_pct
            impact_pct   = round(impact_pct * 0.90, 1)  # reduce loss by 10%
            item_effects.append({
                "item":    "Fact Sheet ทองคำ",
                "icon":    "📊",
                "area_id": 7,
                "desc":    f"Fact Sheet ทองคำลดความเสี่ยง ({original_pct}% → {impact_pct}%)",
            })

        # --- Wisdom Tier Bonuses ---
        # Tier 2 (wisdom >= 35): Reduce negative impact by 15%
        if wisdom >= 35 and impact_pct < 0:
            impact_pct = impact_pct * 0.85

        # Tier 3 (wisdom >= 55): Production sector bonus ×1.10
        if wisdom >= 55 and inv.area_id in [5, 6]:
            impact_pct = impact_pct * 1.10

        profit        = inv.amount * (impact_pct / 100)
        total_profit += profit

        # HP cost per location
        hp_cost = area.get("hp_cost", 0)
        health_change += hp_cost

        # Merit system per location
        if inv.area_id == 8:  # วัดป่าแก้ว / ESG+Emergency Fund: formula
            merit_change += max(1, int(inv.amount / 2000) * 3)
        elif (area.get("merit_effect", 0) != 0 and
              area["merit_effect"] != "formula"):
            merit_change += area["merit_effect"]

        round_log.append({
            "area_id":    inv.area_id,
            "area_name":  area["name"],
            "amount":     inv.amount,
            "impact_pct": round(impact_pct, 1),
            "profit":     round(profit),
            "hp_cost":    hp_cost,
        })

    # 6. Merit Safety Net
    # กองทุนฉุกเฉิน (dual_benefit): boosts protection_factor by +0.10, raises cap to 0.60
    merit_protection = 0
    if total_profit < 0:
        has_dual_benefit   = "กองทุนฉุกเฉิน" in items
        bonus_factor       = 0.10 if has_dual_benefit else 0.0
        cap                = 0.60 if has_dual_benefit else 0.50
        protection_factor  = min(cap, state.stats.merit / 100 + bonus_factor)
        merit_protection   = int(abs(total_profit) * protection_factor)
        total_profit      += merit_protection

    # 7. Medical Cost
    new_health_before_medical = min(100, max(0, state.stats.health + health_change))
    medical_cost          = 0
    original_medical_cost = 0

    if new_health_before_medical < 30:
        base_medical          = int((30 - new_health_before_medical) * 150)
        medical_cost          = base_medical
        original_medical_cost = base_medical

        # ยาหอมนักลงทุน OR กองทุนฉุกเฉิน → 50% medical discount
        if "ยาหอมนักลงทุน" in items or "กองทุนฉุกเฉิน" in items:
            medical_cost     = int(base_medical * 0.50)
            item_name_used   = ("ยาหอมนักลงทุน" if "ยาหอมนักลงทุน" in items
                                else "กองทุนฉุกเฉิน")
            item_icon_used   = "🌿" if item_name_used == "ยาหอมนักลงทุน" else "🏦"
            item_effects.append({
                "item":    item_name_used,
                "icon":    item_icon_used,
                "area_id": None,
                "desc":    (
                    f"{item_name_used} ลดค่ารักษา 50% "
                    f"({base_medical:,} → {medical_cost:,} บาท)"
                ),
            })

    # 8. Update Stats
    new_wealth = int(state.stats.wealth + total_profit - medical_cost)
    new_wisdom = state.stats.wisdom       # Wisdom only from quests
    new_merit  = max(0, state.stats.merit + merit_change)
    new_health = new_health_before_medical

    is_bankrupt  = new_wealth <= 0
    is_game_over = state.round >= state.max_rounds or is_bankrupt

    new_stats = {
        "wealth": new_wealth,
        "wisdom": new_wisdom,
        "merit":  new_merit,
        "health": new_health,
        "items":  list(state.stats.items),
    }

    rank = calculate_rank(new_stats, state.max_rounds) if is_game_over else None

    return {
        "event":                event,
        "log":                  round_log,
        "item_effects":         item_effects,
        "net_profit":           int(total_profit),
        "merit_protection":     merit_protection,
        "merit_change":         merit_change,
        "medical_cost":         medical_cost,
        "original_medical_cost": original_medical_cost,
        "health_change":        health_change,
        "health_status":        health_status,
        "validation_errors":    validation_errors,
        "new_stats":            new_stats,
        "is_game_over":         is_game_over,
        "is_bankrupt":          is_bankrupt,
        "rank":                 rank,
    }


@app.post("/api/chat")
async def chat_with_npc(request: ChatRequest):
    """
    Chat with specific NPC using OpenAI-compatible streaming.
    Quest Mode detection + teacher_prompt injection + 12-message history.
    """
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API Key missing")

    npc = NPC_DATA.get(request.npc_id)
    if not npc:
        raise HTTPException(status_code=400, detail="Invalid NPC")

    messages = [{"role": "system", "content": npc["system"]}]

    # Quest Mode: inject teacher_prompt if active quest matches this NPC
    if request.active_quest:
        quest = INVESTMENT_QUESTS.get(request.active_quest)
        if quest and quest["npc_id"] == request.npc_id:
            messages.append({
                "role":    "system",
                "content": f"TEACHER MODE: {quest['teacher_prompt']}",
            })

    messages.append({
        "role":    "system",
        "content": f"GAME CONTEXT:\n{request.game_context}\n\nUser is asking for investment advice. Use your Cross-Temporal persona.",
    })

    for msg in request.history[-12:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": request.user_message})

    async def generate_stream():
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type":  "application/json",
                }
                is_quest_mode = bool(
                    request.active_quest and
                    INVESTMENT_QUESTS.get(request.active_quest, {}).get("npc_id") == request.npc_id
                )
                payload = {
                    "model":       API_MODEL,
                    "messages":    messages,
                    "stream":      True,
                    "max_tokens":  900 if is_quest_mode else 800,
                    "temperature": 0.60 if is_quest_mode else 0.75,
                }

                async with client.stream(
                    "POST",
                    f"{API_BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                data    = json.loads(data_str)
                                content = data["choices"][0].get("delta", {}).get("content", "")
                                if content:
                                    yield f"data: {json.dumps({'content': content})}\n\n"
                            except Exception:
                                continue

            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            logger.error(f"Chat Error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate_stream(), media_type="text/event-stream")


# ==========================================
# 4. QUEST ENDPOINTS
# ==========================================

@app.post("/api/quest/accept")
async def quest_accept(request: QuestAcceptRequest):
    """Accept a quest: validate merit gate, deduct fee, set active quest."""
    state    = request.game_state
    quest_id = request.quest_id

    quest = INVESTMENT_QUESTS.get(quest_id)
    if not quest:
        raise HTTPException(status_code=400, detail="Invalid quest ID")

    if state.active_quest:
        raise HTTPException(status_code=400, detail="มีเควสต์ที่กำลังทำอยู่แล้ว")

    if quest_id in state.completed_quests:
        raise HTTPException(status_code=400, detail="เควสต์นี้เสร็จสิ้นแล้ว")

    # Merit Gate: check location's required merit
    quest_location = LOCATIONS.get(quest["location_id"])
    if quest_location:
        required_merit = quest_location.get("require_merit", 0)
        if required_merit > 0 and state.stats.merit < required_merit:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"บารมีไม่เพียงพอ! เควสต์นี้ต้องการบารมีอย่างน้อย {required_merit} "
                    f"(บารมีปัจจุบัน: {state.stats.merit}) — ทำบุญที่วัดป่าแก้วเพื่อเพิ่มบารมีก่อน"
                ),
            )

    if state.stats.wealth < 500:
        raise HTTPException(status_code=400, detail="เงินไม่พอจ่ายค่าบูชาครู (500 บาท)")

    new_wealth = state.stats.wealth - 500
    npc        = NPC_DATA[quest["npc_id"]]

    return {
        "success":      True,
        "quest": {
            "id":          quest["id"],
            "name":        quest["name"],
            "npc_id":      quest["npc_id"],
            "location_id": quest["location_id"],
            "topic":       quest["topic"],
            "min_turns":   quest["min_turns"],
        },
        "new_wealth":       new_wealth,
        "active_quest":     quest_id,
        "quest_turn_count": 0,
        "message": (
            f"รับเควสต์ '{quest['name']}' สำเร็จ! จ่ายค่าบูชาครู 500 บาท "
            f"เดินทางไปพบ {npc['name']} เพื่อเรียนรู้"
        ),
    }


@app.post("/api/quest/evaluate")
async def quest_evaluate(request: QuestEvaluateRequest):
    """AI evaluates player understanding from chat history."""
    if not API_KEY:
        return {"pass": False, "score": 0, "feedback": "ไม่สามารถประเมินได้ (ไม่มี API Key)"}

    quest = INVESTMENT_QUESTS.get(request.quest_id)
    if not quest:
        raise HTTPException(status_code=400, detail="Invalid quest ID")

    chat_str = ""
    for msg in request.chat_history:
        role_label = "NPC" if msg["role"] == "assistant" else "ผู้เล่น"
        chat_str  += f"{role_label}: {msg['content']}\n"

    eval_prompt = f"""You are a learning evaluator in the educational investment game "Ayutthaya Wealth Saga: Beyond the Realm".
Look at the following conversation between the NPC and the player.

Learning topic: {quest['topic']}
Learning Objective: {quest.get('lo_target', 'General')}
Passing criteria: {quest['evaluation_criteria']}

Conversation:
{chat_str}

Evaluate whether the player has demonstrated sufficient understanding of the investment concept.
Respond with JSON only:
{{"pass": true/false, "score": 1-5, "feedback": "short explanation in Thai about whether passed or not and why, referencing the investment concept"}}"""

    try:
        timeout = float(os.getenv("API_TIMEOUT", "30"))
        async with httpx.AsyncClient(timeout=timeout) as client:
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type":  "application/json",
            }
            payload = {
                "model":    API_MODEL,
                "messages": [
                    {
                        "role":    "system",
                        "content": "You are an educational investment assessment AI. Respond ONLY with valid JSON.",
                    },
                    {"role": "user", "content": eval_prompt},
                ],
                "max_tokens":  300,
                "temperature": 0.20,
            }
            resp = await client.post(
                f"{API_BASE_URL}/chat/completions", headers=headers, json=payload
            )
            data    = resp.json()
            content = data["choices"][0]["message"]["content"].strip()

            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            result = json.loads(content)
            return {
                "pass":     result.get("pass", False),
                "score":    result.get("score", 0),
                "feedback": result.get("feedback", "ไม่สามารถประเมินได้"),
            }

    except Exception as e:
        logger.error(f"Quest Evaluation Error: {e}")
        return {"pass": False, "score": 0, "feedback": f"เกิดข้อผิดพลาดในการประเมิน: {str(e)}"}


@app.post("/api/quest/complete")
async def quest_complete(request: QuestCompleteRequest):
    """Complete a quest and apply rewards."""
    state    = request.game_state
    quest_id = request.quest_id

    quest = INVESTMENT_QUESTS.get(quest_id)
    if not quest:
        raise HTTPException(status_code=400, detail="Invalid quest ID")

    if state.active_quest != quest_id:
        raise HTTPException(status_code=400, detail="เควสต์นี้ไม่ใช่เควสต์ที่กำลังทำอยู่")

    rewards    = quest["rewards"]
    new_wealth = state.stats.wealth + rewards["wealth"]
    new_wisdom = state.stats.wisdom + rewards["wisdom"]
    new_merit  = state.stats.merit  + rewards["merit"]
    new_health = min(100, max(0, state.stats.health + rewards["hp_cost"]))
    new_items  = list(state.stats.items)
    if rewards.get("item"):
        new_items.append(rewards["item"])

    new_completed = list(state.completed_quests)
    new_completed.append(quest_id)

    reward_msg = (
        f"เควสต์ '{quest['name']}' สำเร็จ! ได้รับ: "
        f"ปัญญา +{rewards['wisdom']}, ทรัพย์สิน +{rewards['wealth']:,} บาท"
    )
    if rewards["merit"] > 0:
        reward_msg += f", บารมี +{rewards['merit']}"
    if rewards.get("item"):
        reward_msg += f", ไอเทม: {rewards['item']}"

    return {
        "success":          True,
        "quest_name":       quest["name"],
        "rewards":          rewards,
        "new_stats": {
            "wealth": new_wealth,
            "wisdom": new_wisdom,
            "merit":  new_merit,
            "health": new_health,
            "items":  new_items,
        },
        "completed_quests": new_completed,
        "active_quest":     None,
        "message":          reward_msg,
    }


@app.post("/api/generate-insights")
async def generate_insights(request: InsightsRequest):
    """Generate final learning summary using AI."""
    if not API_KEY:
        return {"insights": "AI Insights unavailable (No API Key).", "success": False}

    state = request.game_state
    rank  = calculate_rank(
        {
            "wealth": state.stats.wealth,
            "wisdom": state.stats.wisdom,
            "merit":  state.stats.merit,
            "health": state.stats.health,
        },
        state.max_rounds,
    )

    # Resolve scenario name
    scenario      = next((s for s in INVESTMENT_SCENARIOS if s["id"] == state.scenario_id), None)
    scenario_name = scenario["name"] if scenario else state.scenario_id
    scenario_desc = scenario["desc"] if scenario else ""

    # Resolve completed quests
    completed_details = []
    for q_id in state.completed_quests:
        q = INVESTMENT_QUESTS.get(q_id)
        if q:
            completed_details.append(
                f"เควสต์ '{q['name']}' (หัวข้อ: {q['topic']}, LO: {q.get('lo_target', '-')})"
            )
    quests_completed_str = (
        "ไม่มี" if not completed_details
        else "\n  - " + "\n  - ".join(completed_details)
    )

    # Resolve incomplete quests
    all_quest_ids    = set(INVESTMENT_QUESTS.keys())
    incomplete_list  = [
        f"เควสต์ '{INVESTMENT_QUESTS[q_id]['name']}' (หัวข้อ: {INVESTMENT_QUESTS[q_id]['topic']})"
        for q_id in all_quest_ids if q_id not in state.completed_quests
    ]
    quests_incomplete_str = (
        "ไม่มี" if not incomplete_list
        else "\n  - " + "\n  - ".join(incomplete_list)
    )

    # Resolve items
    item_buff_desc = {
        "Fact Sheet ทองคำ":  "ลด Impact ลบที่ Gold ETF ลง 10% (รู้ข้อมูลก่อนลงทุน)",
        "ดาบ Sector Fund":   "ปกป้อง Sector Fund จาก Impact ลบทุกกรณี",
        "ข้าวทิพย์ DCA":     "ปกป้องกองทุนรวมผสมจาก Impact ลบทุกกรณี (DCA ที่สม่ำเสมอ)",
        "ยาหอมนักลงทุน":    "ลดค่ารักษาพยาบาล 50% (เข้าใจ Real Return)",
        "กองทุนฉุกเฉิน":    "ลดค่ารักษา 50% + เพิ่ม Merit Safety Net 10% (Emergency Fund)",
    }
    item_to_quest = {q["rewards"]["item"]: q for q in INVESTMENT_QUESTS.values()
                     if q["rewards"].get("item")}

    if state.stats.items:
        item_lines = []
        for item_name in state.stats.items:
            origin_quest = item_to_quest.get(item_name)
            buff         = item_buff_desc.get(item_name, "")
            line = (
                f"{item_name} (จากเควสต์ '{origin_quest['name']}')"
                if origin_quest else item_name
            )
            if buff:
                line += f" — ผล: {buff}"
            item_lines.append(line)
        items_str = "\n  - " + "\n  - ".join(item_lines)
    else:
        items_str = "ไม่มี"

    # Investment history
    history_str = ""
    for h in state.history:
        event       = h.get("event", {})
        event_title = event.get("title", event.get("name", "เหตุการณ์ปริศนา"))
        profit      = h.get("totalReturn", 0)
        profit_text = f"+{profit:,}" if profit >= 0 else f"{profit:,}"
        history_str += f"  ไตรมาสที่ {h.get('round')}: {event_title} → กำไรสุทธิ {profit_text} บาท\n"

        for entry in h.get("log", []):
            area_name   = entry.get("area_name", "")
            amount      = entry.get("amount", 0)
            impact      = entry.get("impact_pct", 0)
            loc_profit  = entry.get("profit", 0)
            loc_txt     = f"+{loc_profit:,}" if loc_profit >= 0 else f"{loc_profit:,}"
            history_str += f"    • {area_name}: ลงทุน {amount:,} บาท ({impact:+.1f}%) → {loc_txt} บาท\n"

    # Build summary for AI
    summary = (
        f"บททดสอบที่เผชิญ: {scenario_name} — {scenario_desc}\n"
        f"บรรดาศักดิ์ที่ได้รับ: {rank['name']} — {rank['desc']}\n"
        f"สถานะตอนจบ: ทรัพย์สิน={state.stats.wealth:,} บาท, ปัญญา={state.stats.wisdom}, "
        f"บารมี={state.stats.merit}, สุขภาพ={state.stats.health}\n"
        f"ไอเทมที่ครอบครอง:{items_str}\n"
        f"เควสต์ที่สำเร็จ ({len(state.completed_quests)}/8):{quests_completed_str}\n"
        f"เควสต์ที่ยังไม่ได้ทำ:{quests_incomplete_str}\n"
        f"ประวัติการลงทุนรายไตรมาส:\n{history_str}"
    )

    system_prompt = """You are "Phra Horathibodi" (พระโหราธิบดี), the Royal Astrologer of Ayutthaya who has time-traveled to 2026, evaluating a learner's investment journey in 'Ayutthaya Wealth Saga: Beyond the Realm'.

You must analyze the player's investment decisions, quest completions, and final outcomes based on the structured summary provided.
Consider all 4 pillars: Wealth (ทรัพย์สิน), Wisdom (ปัญญา), Merit (บารมี), and Health (สุขภาพ).

MANDATORY RULES:
1. Write the ENTIRE response in Thai, adopting the voice of a wise, time-traveling royal astrologer turned financial mentor
2. NEVER reference raw system IDs (iq1, iq_s2, iq_n1, etc.) — use Thai names only
3. When analyzing investment history, reference Location names AND their modern products (e.g., "ท่าเรือสำเภาหลวง (กองทุนหุ้น SET)")
4. For completed quests: name each quest, its financial concept (LO), and connect to actual game decisions
5. For uncompleted quests: explain what investment concepts were missed and why they matter
6. If the player owned special items: explain how those items helped strategically
7. Keep tone encouraging for high school students — celebratory of learning, not punitive
8. Always end with "ขอรับ" in the voice of the Royal Astrologer

OUTPUT FORMAT — use EXACTLY these section headers with Markdown formatting:
📜 คำพยากรณ์และบรรดาศักดิ์
(Overall reading: rank earned + journey narrative as a financial astrologer)

🌟 จุดแข็งของนักลงทุน
(Wise decisions, successful diversification, good quest completions, strong stats)

⚠️ บทเรียนที่ยังต้องเรียนรู้
(Poor allocation, missed protection, low merit/health, uncompleted quests and what they would have taught)

📚 ปัญญาจากที่ปรึกษาข้ามกาลเวลา
(For each completed quest: connect investment concept to gameplay. For uncompleted: explain what financial literacy was missed)

💡 หลักการลงทุนจากการเดินทางครั้งนี้
(3-5 key investment lessons drawn from THIS specific playthrough — events faced, products used)

🔮 คำแนะนำสำหรับการลงทุนจริง
(Actionable real-world tips for a Thai high school student: start with Emergency Fund, DCA, Index Fund, etc.)"""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type":  "application/json",
            }
            payload = {
                "model":    API_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": summary},
                ],
                "max_tokens":  1200,
                "temperature": 0.60,
            }
            resp = await client.post(
                f"{API_BASE_URL}/chat/completions", headers=headers, json=payload
            )
            resp.raise_for_status()
            data = resp.json()

            choices = data.get("choices", [])
            if not choices:
                logger.error(f"Insights: empty choices. Response: {data}")
                return {"insights": "ไม่สามารถสร้าง Insights ได้ (API ตอบกลับผิดรูปแบบ)", "success": False}

            content = choices[0].get("message", {}).get("content", "")
            if not content:
                logger.error(f"Insights: empty content. Response: {data}")
                return {"insights": "ไม่สามารถสร้าง Insights ได้ (เนื้อหาว่างเปล่า)", "success": False}

            return {"insights": content, "success": True}

    except httpx.TimeoutException as e:
        logger.error(f"Insights timeout: {e}")
        return {"insights": "การสร้าง Insights หมดเวลา กรุณาลองใหม่อีกครั้ง", "success": False}

    except httpx.HTTPStatusError as e:
        logger.error(f"Insights HTTP error {e.response.status_code}: {e.response.text[:500]}")
        return {"insights": f"API ตอบกลับผิดพลาด (HTTP {e.response.status_code})", "success": False}

    except Exception as e:
        logger.error(f"Insights unexpected error: {type(e).__name__}: {e}")
        return {"insights": "เกิดข้อผิดพลาดในการสร้าง Insights", "success": False}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "7860"))
    uvicorn.run(app, host="0.0.0.0", port=port)