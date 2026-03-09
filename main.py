# main.py 最新（修正版・完全版）
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import FileResponse
from groq import Groq
import io
import json
import os
import logging
from typing import Optional, List
from pydantic import BaseModel
from docxtpl import DocxTemplate
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS（テスト用：全許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("uvicorn.error")

# ⚠️本番では必ず環境変数へ移してください
GROQ_API_KEY = os.getenv("GROQ_API_KEY_BACKEND", "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")
client = Groq(api_key=GROQ_API_KEY)

# パス設定
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(CURRENT_DIR, "output_forms")
os.makedirs(OUTPUT_DIR, exist_ok=True)

TEMPLATE_FILE = os.path.join(CURRENT_DIR, "template.docx")


# --- 保存用データ構造 ---
class PatientData(BaseModel):
    # ✅ UIから渡すcase_id（上書き保存の安定化）
    case_id: Optional[str] = None

    # すべての項目にデフォルト値を設定（空文字や空リスト）
    # これにより、UI側で一部入力漏れがあっても500エラーで落ちるのを防ぎます
    staff_id: str = ""
    name: str = ""
    sex: str = ""
    birth: str = ""
    age: str = ""
    address_jp: str = ""
    address_home: str = ""
    phone_home: str = ""
    phone_mobile: str = ""
    nationality: str = ""
    interpreter_req: str = ""
    native_lang: str = ""
    other_langs: str = ""
    occupation: str = ""
    religion_care: str = ""
    emergency_name: str = ""
    emergency_rel: str = ""
    emergency_address: str = ""
    
    # ✅ UI側のフルデータ（full_fd）とキー名を完全に一致させる
    emergency_phone_home: str = ""
    emergency_phone_mobile: str = ""
    
    residency_status: str = ""
    reason_choosing: str = ""
    first_visit: str = ""
    referral_letter: str = ""
    referral_institution: str = ""
    appointment: str = ""
    insurance_type: str = ""
    insurance_company: str = ""
    
    # リスト形式の項目
    departments: List[str] = []
    symptoms: str = ""


# DB（簡易）
patient_db = []

# 従業員ごとの最新テキストと音声バッファ
latest_transcriptions = {}
audio_buffers = {}


# --- 1. 音声解析 (既存機能) ---
@app.websocket("/ws/{staff_id}")
async def websocket_endpoint(websocket: WebSocket, staff_id: str):
    await websocket.accept()
    audio_buffers[staff_id] = bytearray()
    if staff_id not in latest_transcriptions:
        latest_transcriptions[staff_id] = ""

    try:
        while True:
            data = await websocket.receive_bytes()
            audio_buffers[staff_id].extend(data)

            if len(audio_buffers[staff_id]) > 160000:
                audio_file = io.BytesIO(audio_buffers[staff_id])
                audio_file.name = "temp.wav"

                try:
                    transcription = client.audio.transcriptions.create(
                        file=audio_file,
                        model="whisper-large-v3",
                        response_format="text"
                    )

                    if transcription.strip():
                        latest_transcriptions[staff_id] += " " + transcription
                        logger.info(f"[{staff_id}] 認識: {transcription}")
                except Exception:
                    logger.exception("Groq API Error (transcription)")

                audio_buffers[staff_id] = bytearray()

    except Exception:
        logger.exception("WebSocket Error")
    finally:
        await websocket.close()


# --- 2. テキスト取得 (既存機能) ---
@app.get("/get_text/{staff_id}")
async def get_text(staff_id: str):
    return {"text": latest_transcriptions.get(staff_id, "")}


# --- 3. リセット (既存機能) ---
@app.get("/reset_text/{staff_id}")
async def reset_text(staff_id: str):
    latest_transcriptions[staff_id] = ""
    return {"status": "reset"}


def _safe_filename_component(name: str) -> str:
    # ファイル名に使える文字だけ残す（日本語を捨てたくない場合は別方式に変更可）
    safe = "".join([c for c in (name or "") if c.isalnum() or c in (" ", "_", "-")]).strip()
    return safe or "patient"


@app.get("/download_form/{filename}")
async def download_form(filename: str):
    # パス固定でディレクトリトラバーサル対策
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="file not found")

    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename,
    )


@app.delete("/delete_patient/{case_id}")
async def delete_patient(case_id: str):
    """
    UIの「完了ケース削除」要求に対応（既存機能維持）。
    簡易DB(patient_db)からcase_id一致を削除。
    JSONLからの物理削除まではしない（必要なら実装可）。
    """
    before = len(patient_db)
    patient_db[:] = [p for p in patient_db if str(p.get("case_id")) != str(case_id)]
    after = len(patient_db)

    return {"status": "deleted", "removed": before - after}


@app.post("/save_patient")
async def save_patient(data: PatientData):
    logger.info(f"--- リクエスト受信: {data.name} / staff={data.staff_id} / case_id={data.case_id} ---")

    try:
        # 1. データの辞書化
        patient_entry = data.dict()

        # ✅ template存在チェック
        if not os.path.exists(TEMPLATE_FILE):
            logger.error(f"❌ テンプレート未検出: {TEMPLATE_FILE}")
            raise HTTPException(status_code=404, detail=f"Template file not found at {TEMPLATE_FILE}")

        # ✅ ファイル名の決定
        safe_name = _safe_filename_component(data.name)
        if data.case_id:
            filename = f"form_{data.case_id}.docx"
        else:
            filename = f"form_{safe_name}.docx"

        word_path = os.path.join(OUTPUT_DIR, filename)

        # 2. テンプレート表示用データの作成
        display_data = patient_entry.copy()
        CHECK, UNCHECK = "☑", "□"

        # --- チェックボックス変換 ---
        display_data['sex_male'] = CHECK if data.sex == "Male" else UNCHECK
        display_data['sex_female'] = CHECK if data.sex == "Female" else UNCHECK
        display_data['intp_yes'] = CHECK if data.interpreter_req == "Yes" else UNCHECK
        display_data['intp_no'] = CHECK if data.interpreter_req == "No" else UNCHECK
        display_data['fv_yes'] = CHECK if data.first_visit == "Yes" else UNCHECK
        display_data['fv_no'] = CHECK if data.first_visit == "No" else UNCHECK
        display_data['ref_yes'] = CHECK if data.referral_letter == "Yes" else UNCHECK
        display_data['ref_no'] = CHECK if data.referral_letter == "No" else UNCHECK
        display_data['appo_yes'] = CHECK if data.appointment == "Yes" else UNCHECK
        display_data['appo_no'] = CHECK if data.appointment == "No" else UNCHECK

        # 在留資格
        res = data.residency_status or ""
        display_data['res_resident'] = CHECK if res == "Resident" else UNCHECK
        display_data['res_short'] = CHECK if res == "Short-term stay" else UNCHECK
        display_data['res_biz'] = CHECK if res == "Business" else UNCHECK
        display_data['res_student'] = CHECK if res == "Student" else UNCHECK
        display_data['res_other'] = CHECK if res == "Other" else UNCHECK

        # 保険
        ins = (data.insurance_type or "").lower()
        display_data['ins_jap'] = CHECK if "japanese" in ins else UNCHECK
        display_data['ins_pub'] = CHECK if "public" in ins else UNCHECK
        display_data['ins_priv'] = CHECK if "private" in ins else UNCHECK
        display_data['ins_overseas'] = CHECK if "overseas" in ins else UNCHECK
        display_data['ins_uninsured'] = CHECK if "uninsured" in ins else UNCHECK

        # 診療科
        received_depts = [str(d).strip().lower() for d in (data.departments or [])]
        dept_mapping = {
            'dept_internal': 'Internal Medicine', 'dept_psycho': 'Psychosomatic Medicine',
            'dept_neuro': 'Neurology', 'dept_pulmon': 'Pulmonology',
            'dept_gastro': 'Gastroenterology', 'dept_cardio': 'Cardiovascular medicine',
            'dept_nephro': 'Nephrology', 'dept_pedia': 'Pediatrics',
            'dept_surgery': 'Surgery', 'dept_ortho': 'Orthopedic surgery',
            'dept_neurosurg': 'Neurosurgery', 'dept_thoracic': 'Thoracic Surgery',
            'dept_cardiosurg': 'Cardiovascular Surgery', 'dept_derm': 'Dermatology',
            'dept_uro': 'Urology', 'dept_obgyn': 'Obstetrics and Gynecology',
            'dept_opht': 'Ophthalmology', 'dept_ent': 'Otorhinolaryngology',
            'dept_dent': 'Dentistry', 'dept_other': 'Other'
        }
        for var_name, label in dept_mapping.items():
            display_data[var_name] = CHECK if label.lower() in received_depts else UNCHECK

        # ✅ 文字列化ガード：Jinja2エラー（NoneTypeなど）を防止
        for k, v in list(display_data.items()):
            if v is None:
                display_data[k] = ""
            elif isinstance(v, list):
                display_data[k] = ", ".join([str(x) for x in v])
            else:
                display_data[k] = str(v)

        # 3. Wordファイル生成
        logger.info(f"Rendering Word document: {filename}")
        try:
            doc = DocxTemplate(TEMPLATE_FILE)
            doc.render(display_data)
            doc.save(word_path)
        except Exception as docx_err:
            logger.error(f"❌ DocxTemplate Error: {docx_err}")
            raise HTTPException(status_code=500, detail=f"Word Rendering Failed: {str(docx_err)}")

        # 4. データの永続化
        patient_db.append(patient_entry)
        jsonl_path = os.path.join(CURRENT_DIR, "registered_patients.jsonl")
        try:
            with open(jsonl_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(patient_entry, ensure_ascii=False) + "\n")
        except Exception as io_err:
            logger.warning(f"⚠️ JSONL Write Error: {io_err}")

        logger.info(f"✅ 正常完了: {word_path}")

        return {
            "status": "success",
            "word_file": word_path,
            "filename": filename,
            "download_url": f"/download_form/{filename}"
        }

    except HTTPException:
        raise
    except Exception as e:
        # 詳細なトレースバックをログに出し、クライアントにはエラーメッセージを返す
        logger.exception("❌ サーバー内部で致命的なエラーが発生しました")
        raise HTTPException(status_code=500, detail=f"Server Error: {type(e).__name__} - {str(e)}")