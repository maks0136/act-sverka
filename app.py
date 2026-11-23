import logging
import os
import re
import sqlite3
from datetime import datetime, date
from pathlib import Path

import pandas as pd
import streamlit as st

from sverka_history import ReconciliationHistory
from sverka_review import render_assistant, render_history

# -------------------- Оформление --------------------
st.set_page_config(page_title="ACT SVERKA | Сверка актов", page_icon="📑", layout="wide", initial_sidebar_state="collapsed")

STATS_DB = Path(os.getenv("ACT_SVERKA_STATS_DB", str(Path(__file__).with_name("sverka_stats.sqlite3"))))
logger = logging.getLogger(__name__)
HISTORY = ReconciliationHistory(STATS_DB)


def show_header(slot, total):
    display_total = "—" if total is None else f"{total:,}".replace(",", "\u202f")
    slot.html(f"""
<header id="sverka-header">
  <div class="screen-brand"><span class="screen-logo" aria-hidden="true">≋</span> ACT SVERKA</div>
  <figure class="screen-tagline">
    <blockquote>«Ни@уя, сошлось!»</blockquote>
    <figcaption>— комментарий Алины после сверки</figcaption>
  </figure>
  <div class="screen-counter">
    <span>Всего сверок</span><strong>{display_total}</strong>
  </div>
</header>
""")


# Стили действуют на всю страницу, включая настройки и результаты.
st.html("""<style>
.stApp {
  isolation: isolate;
  --sverka-ink: light-dark(#231d35, #f5effa);
  --sverka-muted: light-dark(#5d556b, #c9bfd5);
  --sverka-panel: light-dark(#fff, #251f2e);
  --sverka-line: light-dark(#e5dff0, #453a53);
  --sverka-accent: light-dark(#5946b7, #c3b4ff);
  --sverka-amber: light-dark(#7c4208, #ffdfab);
  --sverka-amber-bg: light-dark(#fff0dc, #553915);
  background:
    radial-gradient(ellipse at 0% 26%, light-dark(#d7e9ff, #273952), transparent 58%),
    radial-gradient(ellipse at 100% 72%, light-dark(#e3d6fa, #422b56), transparent 56%),
    light-dark(#f1eef8, #21192d);
}
[data-testid="stHeader"] { background: transparent; }
.stMainBlockContainer {
  max-width: 1180px;
  padding: 3.5rem clamp(1rem, 6vw, 5rem) 3rem;
}

#sverka-screen { color: var(--sverka-ink); display: grid; gap: 16px; }
#sverka-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  align-items: center;
  gap: 7px 12px;
  padding: 11px clamp(12px, 3vw, 26px);
  background: var(--sverka-panel);
  color: var(--sverka-ink);
  border: 1px solid var(--sverka-line);
  border-radius: 14px;
}
#sverka-header .screen-brand {
  display: inline-flex; align-items: center; gap: 9px;
  font-size: 13px; font-weight: 800; letter-spacing: .09em; white-space: nowrap;
}
#sverka-header .screen-logo {
  display: grid; place-items: center; width: 31px; height: 31px;
  background: #6350c6; color: #fff; border-radius: 9px; font-size: 22px; line-height: 1;
}
#sverka-header .screen-tagline {
  grid-column: 2; justify-self: center; min-width: 0; margin: 0;
  display: flex; flex-wrap: wrap; align-items: baseline; justify-content: center;
  gap: 2px 6px; text-align: center;
  color: var(--sverka-accent); font-size: 14px; font-weight: 750;
}
#sverka-header .screen-tagline blockquote { margin: 0; padding: 0; border: 0; font: inherit; color: inherit; }
#sverka-header .screen-tagline figcaption { margin: 0; color: var(--sverka-muted); font-size: 11px; font-weight: 500; }
#sverka-header .screen-counter {
  grid-column: 3; justify-self: end; display: inline-flex; flex-wrap: wrap;
  align-items: baseline; justify-content: flex-end; gap: 2px 8px;
  padding: 5px 10px; border: 1px solid var(--sverka-line); border-radius: 8px;
  background: light-dark(#f4efff, #382c4d); color: var(--sverka-muted); font-size: 12px;
}
#sverka-header .screen-counter strong {
  color: var(--sverka-accent); font-size: 16px; font-variant-numeric: tabular-nums;
}

#sverka-banner {
  display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.07fr);
  align-items: center; gap: 24px; padding: clamp(18px, 3.2vw, 30px);
  border: 1px solid var(--sverka-line); border-radius: 22px;
  background: radial-gradient(ellipse at 95% 12%, light-dark(#e9dfff, #392854), transparent 65%),
    light-dark(#faf8ff, #1e192b);
}
#sverka-banner h1 {
  margin: 0 0 8px; padding: 0; font-size: clamp(26px, 4.5vw, 40px);
  line-height: 1.1; letter-spacing: -.04em; color: var(--sverka-ink);
}
#sverka-banner p { margin: 0; font-size: 14px; line-height: 1.5; color: var(--sverka-muted); }
#sverka-banner .illustration { display: grid; gap: 13px; min-width: 0; }
#sverka-banner .acts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
#sverka-banner .act {
  position: relative; overflow: hidden; padding: 11px 9px;
  background: var(--sverka-panel); border: 1px solid var(--sverka-line);
  border-radius: 12px; box-shadow: 0 7px 18px light-dark(#4e386a14, #0003);
}
#sverka-banner .act h3 { margin: 0 0 8px; padding: 0; font-size: 12px; color: var(--sverka-muted); }
#sverka-banner .amount {
  padding: 6px 2px; border-top: 1px solid var(--sverka-line); text-align: right;
  font-size: clamp(11px, 1.9vw, 14px); font-variant-numeric: tabular-nums; white-space: nowrap;
}
#sverka-banner :is(.different, .difference) { background: var(--sverka-amber-bg); color: var(--sverka-amber); font-weight: 700; }
#sverka-banner .different { border-top-color: transparent; border-radius: 4px; }
#sverka-banner .difference { justify-self: center; border-radius: 999px; padding: 5px 10px; font-size: 12px; }
#sverka-banner .scan {
  position: absolute; inset: 0 6px auto; height: 2px; opacity: 0; pointer-events: none;
  background: var(--sverka-accent); box-shadow: 0 0 9px var(--sverka-accent);
}

#sverka-screen .feature-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
#sverka-screen .feature {
  display: flex; gap: 9px; align-items: flex-start; padding: 12px;
  background: var(--sverka-panel); border: 1px solid var(--sverka-line); border-radius: 12px;
}
#sverka-screen .feature-icon { color: var(--sverka-accent); font-size: 18px; line-height: 1; }
#sverka-screen .feature h3 { padding: 0; margin: 0; font-size: 13px; color: var(--sverka-ink); }
#sverka-screen .feature p { margin: 3px 0 0; font-size: 12px; color: var(--sverka-muted); }
#sverka-screen .upload-title { margin: 0; padding: 0; font-size: 17px; color: var(--sverka-ink); }

.stApp :is([data-testid="stFileUploader"], [data-testid="stMetric"], [data-testid="stExpander"], [data-testid="stDataFrame"]) {
  background: var(--sverka-panel); border-radius: 12px;
}
.stApp :is([data-testid="stFileUploader"], [data-testid="stMetric"]) {
  border: 1px solid var(--sverka-line); padding: 12px 14px;
}
.stApp [data-testid="stFileUploaderDropzone"] { border: 1px dashed var(--sverka-line); border-radius: 8px; }
.stApp [data-testid="stDataFrame"] { overflow: hidden; }
.stApp .stButton button[kind="primary"] {
  background: light-dark(#5946b7, #c3b4ff);
  border-color: transparent;
  color: light-dark(#fff, #24173c);
}
.stApp .site-footer {
  padding: 26px 6px; border-top: 1px solid var(--sverka-line);
  display: flex; justify-content: space-between; gap: 18px; flex-wrap: wrap; color: var(--sverka-muted); font-size: .82rem;
}

@media (max-width: 780px) {
  #sverka-header { grid-template-columns: minmax(0, 1fr) auto; }
  #sverka-header .screen-tagline { grid-area: 2 / 1 / 3 / -1; }
  #sverka-header .screen-counter { grid-area: 1 / 2; }
}
@media (max-width: 360px) {
  #sverka-header .screen-counter { gap: 2px 4px; padding-inline: 6px; }
}
@media (max-width: 590px) {
  #sverka-screen .feature-grid { grid-template-columns: 1fr; gap: 6px; }
  #sverka-screen .feature { padding: 8px 10px; }
  #sverka-banner { grid-template-columns: 1fr; gap: 15px; }
}

.stApp .paper-stage {
    position: fixed;
    inset: 0;
    overflow: hidden;
    z-index: -1;
    pointer-events: none;
  }
  .stApp .floating-paper {
    position: absolute;
    box-sizing: border-box;
    width: calc(clamp(90px, 15vw, 145px) * var(--paper-size, 1));
    height: calc(clamp(116px, 18vw, 178px) * var(--paper-size, 1));
    padding: 11px 9px;
    border: 1px solid light-dark(#8366b268, #c9adf66b);
    border-radius: 10px;
    color: light-dark(#695190, #d5bdf7);
    background: light-dark(#fff7, #b28ce31b);
    box-shadow: 0 10px 26px light-dark(#65568d24, #120a2570);
    font-size: 10px;
    font-weight: 720;
    letter-spacing: .08em;
    opacity: var(--paper-opacity, .95);
    animation: sverka-paper-float var(--paper-duration) ease-in-out infinite alternate;
  }
  .stApp .floating-paper span {
    display: block;
    height: 1px;
    margin-top: 12px;
    background: currentColor;
    opacity: .36;
  }
  .stApp .floating-paper span:last-child { width: 57%; }
  .stApp .paper-act {
    left: -10px; top: 20%;
    --paper-duration: 12s; --tilt-start: -17deg; --tilt-end: -4deg; --rise: -64px; --bend: 15px; --drift: 34px;
    animation-delay: -3s;
  }
  .stApp .paper-invoice {
    right: 0; top: 13%;
    --paper-duration: 14s; --tilt-start: 9deg; --tilt-end: 22deg; --rise: 63px; --bend: -13px; --drift: 24px;
    animation-delay: -11s;
  }
  .stApp .paper-delivery {
    right: -13px; bottom: -6%;
    --paper-duration: 11s; --tilt-start: 15deg; --tilt-end: -6deg; --rise: -64px; --bend: -20px; --drift: 12px;
    animation-delay: -4s;
  }
  .stApp .paper-payment {
    left: -15px; top: 47%;
    --paper-size: .8; --paper-opacity: .68;
    --paper-duration: 15s; --tilt-start: 12deg; --tilt-end: -18deg; --rise: 58px; --bend: 27px; --drift: -12px;
    animation-delay: -9s;
  }
  .stApp .paper-statement {
    right: -10px; top: 46%;
    --paper-size: .92; --paper-opacity: .78;
    --paper-duration: 13s; --tilt-start: -15deg; --tilt-end: 5deg; --rise: -52px; --bend: 16px; --drift: -28px;
    animation-delay: -8s;
  }
  .stApp .paper-register {
    left: 2%; bottom: -12%;
    --paper-size: .86; --paper-opacity: .88;
    --paper-duration: 16s; --tilt-start: -20deg; --tilt-end: -3deg; --rise: -74px; --bend: -15px; --drift: 24px;
    animation-delay: -13s;
  }
  .stApp .paper-invoice-copy {
    left: 20%; top: -13%;
    --paper-size: .75; --paper-opacity: .6;
    --paper-duration: 13s; --tilt-start: 20deg; --tilt-end: 5deg; --rise: 39px; --bend: 25px; --drift: 68px;
    animation-delay: -9s;
  }
  .stApp .paper-act-copy {
    right: 25%; bottom: -15%;
    --paper-size: .78; --paper-opacity: .68;
    --paper-duration: 15s; --tilt-start: -10deg; --tilt-end: 13deg; --rise: -42px; --bend: -17px; --drift: -65px;
    animation-delay: -7s;
  }
  @keyframes sverka-paper-float {
    from { transform: translate(0, 0) rotate(var(--tilt-start)); }
    48% { transform: translate(var(--bend), calc(var(--rise) * .52)) rotate(calc(var(--tilt-start) * .6)); }
    to { transform: translate(var(--drift), var(--rise)) rotate(var(--tilt-end)); }
  }

#sverka-banner { --scan-cycle: 6s; }
  #sverka-banner .scan { animation: sverka-periodic-scan var(--scan-cycle) ease-in-out infinite; }
  #sverka-banner .different, #sverka-banner .difference {
    animation: sverka-periodic-highlight var(--scan-cycle) ease-in-out infinite;
  }
  @keyframes sverka-periodic-scan {
    0% { top: 91%; opacity: 0; }
    3% { opacity: .95; }
    23% { top: 18%; opacity: .95; }
    46% { top: 91%; opacity: .95; }
    49%, 100% { top: 91%; opacity: 0; }
  }
  @keyframes sverka-periodic-highlight {
    0%, 49% { background: transparent; }
    53%, 96% { background: var(--sverka-amber-bg); }
    100% { background: transparent; }
  }
  #sverka-banner .difference { animation-name: sverka-periodic-result; }
  @keyframes sverka-periodic-result {
    0%, 49% { opacity: 0; }
    53%, 96% { opacity: 1; }
    100% { opacity: 0; }
  }
</style>""")

PAPER_BACKGROUND = """
<div class="paper-stage" aria-hidden="true">
  <div class="floating-paper paper-act">АКТ СВЕРКИ<span></span><span></span><span></span><span></span></div>
  <div class="floating-paper paper-invoice">СЧЁТ<span></span><span></span><span></span><span></span></div>
  <div class="floating-paper paper-delivery">НАКЛАДНАЯ<span></span><span></span><span></span><span></span></div>
  <div class="floating-paper paper-payment">ПЛАТЁЖНОЕ<br>ПОРУЧЕНИЕ<span></span><span></span><span></span></div>
  <div class="floating-paper paper-statement">ВЫПИСКА<span></span><span></span><span></span><span></span></div>
  <div class="floating-paper paper-register">РЕЕСТР<span></span><span></span><span></span><span></span></div>
  <div class="floating-paper paper-invoice-copy">СЧЁТ<span></span><span></span><span></span><span></span></div>
  <div class="floating-paper paper-act-copy">АКТ СВЕРКИ<span></span><span></span><span></span><span></span></div>
</div>
"""

START_SCREEN = """
<div id="sverka-screen">
<section id="sverka-banner" aria-label="Баннер ACT SVERKA">
    <div>
      <h1>Два акта.<br>Видно, где разница.</h1>
      <p>Сверка операций в Excel и PDF</p>
    </div>
    <div class="illustration" role="img" aria-label="Пример сверки. Суммы 12 450 и 12 540 рублей отличаются на 90 рублей.">
      <div class="acts">
        <div class="act">
          <h3>Акт № 1</h3>
          <div class="amount">8 700,00 ₽</div>
          <div class="amount">3 680,00 ₽</div>
          <div class="amount different">12 450,00 ₽</div>
          <div class="scan" aria-hidden="true"></div>
        </div>
        <div class="act">
          <h3>Акт № 2</h3>
          <div class="amount">8 700,00 ₽</div>
          <div class="amount">3 680,00 ₽</div>
          <div class="amount different">12 540,00 ₽</div>
          <div class="scan" aria-hidden="true"></div>
        </div>
      </div>
      <div class="difference">Разница 90,00 ₽</div>
    </div>
  </section>
<section class="feature-grid" aria-label="Возможности сервиса">
      <div class="feature"><span class="feature-icon" aria-hidden="true">⇄</span><div><h3>Сравнение актов</h3><p>Операции, которые остались без пары.</p></div></div>
      <div class="feature"><span class="feature-icon" aria-hidden="true">✧</span><div><h3>Умный поиск</h3><p>Подсказки по расхождениям в суммах.</p></div></div>
      <div class="feature"><span class="feature-icon" aria-hidden="true">▤</span><div><h3>Готовый результат</h3><p>Список расхождений с датами и суммами.</p></div></div>
    </section>
<h2 class="upload-title" id="sverka-upload-title">Загрузите два акта</h2>
</div>
"""


# -------------------- Универсальное чтение файлов (Excel + PDF) --------------------
def read_pdf_tables(file):
    try:
        import pdfplumber
    except ImportError:
        st.error("Библиотека pdfplumber не установлена. Выполните: pip install pdfplumber")
        return pd.DataFrame()

    rows = []
    try:
        with pdfplumber.open(file) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if not text: continue
                
                lines = text.split('\n')
                current_date = None
                current_doc = []
                current_amt = None
                current_location = None
                pre_buffer = [] # Буфер для текста, идущего до даты

                for line_number, line in enumerate(lines, start=1):
                    line = line.strip()
                    if not line: continue
                    
                    # Игнорируем шапку
                    if any(k in line.lower() for k in ['акт сверки', 'между ооо', 'между общество', 'по данным', 'сальдо начальное', 'сальдо конечное', 'обороты за период']):
                        continue
                    
                    # Ищем даты в формате ДД.ММ.ГГ (строго 2 цифры года)
                    dates = list(re.finditer(r'(?<!\d)(\d{2}\.\d{2}\.\d{2})(?!\d)', line))
                    
                    if dates:
                        # Если дат две (левая и правая таблица), отрезаем правую часть
                        if len(dates) > 1:
                            line = line[:dates[1].start()].strip()
                            dates = list(re.finditer(r'(?<!\d)(\d{2}\.\d{2}\.\d{2})(?!\d)', line))
                        
                        if dates:
                            # Сохраняем предыдущую операцию
                            if current_date:
                                final_doc = " ".join(current_doc).strip()
                                rows.append([current_date, final_doc if final_doc else "Документ (не распознан)", current_amt if current_amt else "", current_location])
                                current_date = None
                                current_doc = []
                                current_amt = None
                                
                            current_date = dates[0].group(1)
                            current_location = {"page": page_number, "line": line_number}
                            rest = line[dates[0].end():].strip()
                            
                            # Очистка от дат в скобках, слова "от" и самих скобок
                            rest = re.sub(r'от\s+\d{2}\.\d{2}\.\d{2,4}', '', rest)
                            rest = re.sub(r'\b\d{2}\.\d{2}\.\d{4}\b', '', rest)
                            rest = re.sub(r'[\(\)]', ' ', rest)
                            rest = re.sub(r'\s+', ' ', rest).strip()
                            
                            # ЖЕСТКИЙ поиск суммы: только в конце строки, с копейками, не привязан к другим цифрам
                            amount_match = re.search(r'(?<!\d)(-?\d{1,3}(?:[\s\u00A0]\d{3})*[.,]\d{2})$', rest)
                            if amount_match:
                                current_amt = amount_match.group(1).strip()
                                doc_part = rest[:amount_match.start()].strip()
                                if doc_part: current_doc.append(doc_part)
                                
                                if pre_buffer:
                                    current_doc = pre_buffer + current_doc
                                    pre_buffer = []
                                    
                                final_doc = " ".join(current_doc).strip()
                                rows.append([current_date, final_doc if final_doc else "Документ (не распознан)", current_amt, current_location])
                                current_date = None
                                current_doc = []
                                current_amt = None
                            else:
                                if pre_buffer:
                                    current_doc = pre_buffer + current_doc
                                    pre_buffer = []
                                if rest: current_doc.append(rest)
                    else:
                        # Нет даты в строке
                        if current_date:
                            line_clean = re.sub(r'от\s+\d{2}\.\d{2}\.\d{2,4}', '', line)
                            line_clean = re.sub(r'\b\d{2}\.\d{2}\.\d{4}\b', '', line_clean)
                            line_clean = re.sub(r'[\(\)]', ' ', line_clean)
                            line_clean = re.sub(r'\s+', ' ', line_clean).strip()
                            
                            # ЖЕСТКИЙ поиск суммы
                            amount_match = re.search(r'(?<!\d)(-?\d{1,3}(?:[\s\u00A0]\d{3})*[.,]\d{2})$', line_clean)
                            if amount_match:
                                current_amt = amount_match.group(1).strip()
                                doc_part = line_clean[:amount_match.start()].strip()
                                if doc_part: current_doc.append(doc_part)
                                
                                final_doc = " ".join(current_doc).strip()
                                rows.append([current_date, final_doc if final_doc else "Документ (не распознан)", current_amt, current_location])
                                current_date = None
                                current_doc = []
                                current_amt = None
                            else:
                                current_doc.append(line_clean)
                        else:
                            # Сохраняем в буфер только текст, похожий на название документа
                            if any(k in line.lower() for k in ['продажа', 'приход', 'оплата', 'претензия', 'корректировка', 'счет-фактура', 'возврат']):
                                pre_buffer.append(line)
                                if len(pre_buffer) > 5: pre_buffer.pop(0)
                            else:
                                pre_buffer = []
                                
                if current_date:
                    final_doc = " ".join(current_doc).strip()
                    rows.append([current_date, final_doc if final_doc else "Документ (не распознан)", current_amt if current_amt else "", current_location])
                    
    except Exception as e:
        st.error(f"Не удалось прочитать PDF: {e}")
        return pd.DataFrame()

    if not rows: return pd.DataFrame()

    final_rows = []
    source_locations = []
    for r in rows:
        d, doc, amt, source_location = r
        if not parse_date(d): continue
        source_locations.append(source_location)
        
        # Финальная очистка названия
        doc = re.sub(r'\s+', ' ', doc).strip()
        if not doc: doc = "Документ (не распознан)"
        
        if amt:
            amt_clean = amt.replace(' ', '').replace(',', '.')
            try:
                val = float(amt_clean)
                if val < 0:
                    final_rows.append([d, doc, amt, ""])
                else:
                    final_rows.append([d, doc, "", amt])
            except:
                final_rows.append([d, doc, amt, ""])
        else:
            final_rows.append([d, doc, "", ""])

    df = pd.DataFrame(final_rows, columns=['date', 'doc', 'debit_str', 'credit_str'])
    # Возвращаем с колонками 0, 1, 2, 3, чтобы избежать ошибки KeyError
    result_df = df[['date', 'doc', 'debit_str', 'credit_str']].copy()
    result_df.columns = [0, 1, 2, 3]
    result_df.attrs["source_locations"] = source_locations
    return result_df

def read_any_file(file):
    name = file.name.lower()
    if name.endswith('.pdf'):
        return read_pdf_tables(file)
    else:
        try:
            return pd.read_excel(file, header=None)
        except Exception as e:
            st.error(f"Ошибка чтения Excel: {e}")
            return pd.DataFrame()

# -------------------- Парсеры --------------------
def parse_date(val):
    if pd.isna(val): return None
    if isinstance(val, pd.Timestamp): return val.date()
    if isinstance(val, datetime): return val.date()
    if isinstance(val, date): return val
    if isinstance(val, (int, float)):
        try: return pd.to_datetime(val, unit='D', origin='1899-12-30').date()
        except: return None
    if isinstance(val, str):
        val = val.strip()
        match = re.search(r'(\d{2}\.\d{2}\.\d{2,4}|\d{4}-\d{2}-\d{2})', val)
        if match: val = match.group(1)
        for fmt in ('%d.%m.%y', '%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
            try: return datetime.strptime(val, fmt).date()
            except: continue
    return None

def clean_number(s):
    if pd.isna(s): return 0.0
    s = str(s).strip()
    s = re.sub(r'[^\d\-,\.]', '', s)
    s = s.replace(' ', '').replace(',', '.')
    parts = s.split('.')
    if len(parts) > 1:
        s = ''.join(parts[:-1]) + '.' + parts[-1]
    try: return float(s)
    except: return 0.0

def index_to_letter(idx):
    if idx is None: return ''
    letter = ''
    n = idx + 1
    while n > 0:
        n -= 1
        letter = chr(n % 26 + ord('A')) + letter
        n //= 26
    return letter

def auto_detect_columns_letters(df):
    header_row = None
    for i, row in df.iterrows():
        has_date = False
        has_doc = False
        for cell in row:
            if pd.notna(cell):
                cell_str = str(cell).lower()
                if 'дата' in cell_str: has_date = True
                if 'документ' in cell_str: has_doc = True
        if has_date and has_doc:
            header_row = i
            break
            
    if header_row is None: return None

    date_cols, doc_cols, debit_cols, credit_cols = [], [], [], []
    for idx, val in df.iloc[header_row].items():
        if pd.notna(val):
            val_str = str(val).lower()
            if 'дата' in val_str: date_cols.append(idx)
            elif 'документ' in val_str: doc_cols.append(idx)
            elif 'дебет' in val_str: debit_cols.append(idx)
            elif 'кредит' in val_str: credit_cols.append(idx)

    if not debit_cols or not credit_cols:
        if header_row + 1 < len(df):
            for idx, val in df.iloc[header_row + 1].items():
                if pd.notna(val):
                    val_str = str(val).lower()
                    if 'дебет' in val_str and idx not in debit_cols: debit_cols.append(idx)
                    elif 'кредит' in val_str and idx not in credit_cols: credit_cols.append(idx)

    def has_data(date_idx, doc_idx, debit_idx, credit_idx):
        for i in range(header_row + 1, len(df)):
            row = df.iloc[i]
            if len(row) <= max(date_idx, doc_idx, debit_idx, credit_idx): continue
            if parse_date(row[date_idx]) is None: continue
            if (len(row) > debit_idx and pd.notna(row[debit_idx]) and clean_number(row[debit_idx]) != 0.0) or \
               (len(row) > credit_idx and pd.notna(row[credit_idx]) and clean_number(row[credit_idx]) != 0.0):
                return True
        return False

    date_cols.sort(); doc_cols.sort(); debit_cols.sort(); credit_cols.sort()

    if date_cols and doc_cols:
        valid_docs = [c for c in doc_cols if c not in date_cols]
        if valid_docs: doc_cols = valid_docs

    if date_cols and doc_cols and debit_cols and credit_cols:
        d_idx = date_cols[-1]
        doc_idx = doc_cols[-1]
        deb_idx = debit_cols[-1]
        cred_idx = credit_cols[-1]
        if has_data(d_idx, doc_idx, deb_idx, cred_idx):
            return (index_to_letter(d_idx), index_to_letter(doc_idx), index_to_letter(deb_idx), index_to_letter(cred_idx))
            
        if len(date_cols) > 1:
            d_idx = date_cols[0]
            doc_idx = doc_cols[0]
            deb_idx = debit_cols[0]
            cred_idx = credit_cols[0]
            if has_data(d_idx, doc_idx, deb_idx, cred_idx):
                return (index_to_letter(d_idx), index_to_letter(doc_idx), index_to_letter(deb_idx), index_to_letter(cred_idx))
                
        return (index_to_letter(date_cols[0]), index_to_letter(doc_cols[0]), index_to_letter(debit_cols[0]), index_to_letter(credit_cols[0]))
    return None

def extract_ops(df, date_col, doc_col, debit_col, credit_col):
    ops = []
    source_locations = df.attrs.get("source_locations")
    for index, (_, row) in enumerate(df.iterrows()):
        if len(row) <= max(date_col, doc_col, debit_col, credit_col): continue
        dt = parse_date(row[date_col])
        if dt is None: continue
        
        doc = str(row[doc_col]).strip() if pd.notna(row[doc_col]) else ''
        
        debit = clean_number(row[debit_col] if len(row) > debit_col else None)
        credit = clean_number(row[credit_col] if len(row) > credit_col else None)
        
        if abs(debit) < 0.001 and abs(credit) < 0.001: continue
        
        if abs(credit) > 0.001:
            amount = credit; sign = 1
        elif abs(debit) > 0.001:
            amount = debit; sign = -1
        else: continue
        
        source = source_locations[index] if source_locations is not None else {"row": index + 1}
        ops.append({
            "date": dt, "doc": doc, "amount": abs(amount), "sign": sign, "raw_doc": doc,
            "change": amount, "source_index": index, **source,
        })
    return ops

def is_correction(doc_text):
    kw = ['корректировк', 'претензи', 'возврат', 'перерасчет', 'сторно', 'исправлен']
    return any(k in doc_text.lower() for k in kw)

def get_contractors(df):
    text_lines = []
    for i in range(min(10, len(df))):
        row = df.iloc[i]
        for cell in row:
            if pd.notna(cell): text_lines.append(str(cell))
    full_text = ' '.join(text_lines)

    match = re.search(r'между\s+(.+?)\s+и\s+(.+?)(?:\s*[\(,]|\s*$)', full_text, re.IGNORECASE)
    if match:
        org1, org2 = match.group(1).strip(), match.group(2).strip()
        def extract_key(name):
            q = re.search(r'["“]([^"“]+)["“"]', name)
            if q: return q.group(1).strip().upper()
            words = name.split()
            if words: return re.sub(r'[^\w]', '', words[-1]).upper()
            return name.upper()
        return {extract_key(org1), extract_key(org2)}
    else:
        orgs = set(re.findall(r'ООО\s+"([^"]+)"', full_text, re.IGNORECASE))
        return {o.strip().upper() for o in orgs} if orgs else set()


# -------------------- Проверка реквизитов (отдельно от сверки) --------------------
def get_inns(df):
    """Извлекает только ИНН, явно подписанные в шапке акта.

    В акте часто присутствуют реквизиты обеих сторон, поэтому сравниваются
    наборы ИНН, а не первый найденный номер.
    """
    cells = []
    for row in df.head(18).itertuples(index=False, name=None):
        for cell in row:
            if pd.notna(cell):
                cells.append(str(cell))
    header = ' '.join(cells)
    result = set()
    for value in re.findall(r'(?<![А-Яа-яA-Za-z])ИНН\s*[:№-]?\s*(\d[\d\s]{8,14}\d)', header, re.I):
        number = re.sub(r'\D', '', value)
        if len(number) in (10, 12):
            result.add(number)
    return result


def normalize_contractor(name):
    """Нормализация только для проверки сторон, не для сверки операций."""
    name = str(name).upper().replace('Ё', 'Е')
    name = re.sub(r'[«»"“”„]', ' ', name)
    name = re.sub(r'\b(?:ООО|АО|ПАО|ОАО|ЗАО|ИП|ОБЩЕСТВО|С|ОГРАНИЧЕННОЙ|ОТВЕТСТВЕННОСТЬЮ)\b', ' ', name)
    return re.sub(r'[^А-ЯA-Z0-9]+', '', name)


def compare_contractors(names1, names2, inns1, inns2):
    """Проверка пар участников; к извлечению и сопоставлению операций отношения не имеет."""
    a = {normalize_contractor(x) for x in names1 if normalize_contractor(x)}
    b = {normalize_contractor(x) for x in names2 if normalize_contractor(x)}
    common = a & b
    unique_a, unique_b = a - b, b - a

    if inns1 and inns2:
        if inns1 == inns2:
            return 'match', 'ИНН участников в обоих актах совпадают.'
        if not (inns1 & inns2):
            return 'different', 'В актах не совпадают ИНН участников. Вероятно, выбраны разные контрагенты.'
        if len(inns1) >= 2 and len(inns2) >= 2:
            return 'different', 'Один ИНН совпадает, а второй различается. Вероятно, выбраны акты разных контрагентов.'
        return 'uncertain', 'Найдены общие ИНН, но реквизиты извлечены не полностью.'

    # Когда ИНН одного акта отсутствуют, нельзя считать общий "наш" участник
    # доказательством того, что второй контрагент тот же.
    if a and b:
        if a == b:
            return 'match', 'Названия обеих сторон совпадают (ИНН определены не полностью).'
        if common and unique_a and unique_b:
            return 'different', 'Одна сторона совпадает, но другие участники актов различаются. Вероятно, выбраны акты разных контрагентов.'
        if not common:
            return 'uncertain', 'Не удалось найти общих участников по названиям. Проверьте реквизиты и оформление шапок.'
        return 'uncertain', 'Состав участников определён не полностью. Проверьте реквизиты.'
    return 'uncertain', 'Недостаточно реквизитов для автоматической проверки контрагентов.'


# -------------------- Умный анализ (не меняет алгоритм сверки) --------------------
def smart_category(doc):
    text = str(doc).lower().replace('ё', 'е')
    if any(x in text for x in ('корректиров', 'претензи', 'возврат', 'перерасчет', 'сторно')):
        return 'Возврат / претензия / корректировка'
    if any(x in text for x in ('продажа', 'реализац', 'приход', 'отгрузк', 'поступление товаров')):
        return 'Реализация / приход'
    if any(x in text for x in ('оплата', 'платеж', 'поручени', 'списание с расчетного')):
        return 'Оплата'
    return 'Другой документ'


def smart_analyze(matched, only1, only2, all1, all2):
    """Предположения о расхождениях, без изменения исходных результатов."""
    from collections import Counter
    from difflib import SequenceMatcher

    def doc_numbers(text):
        # Номера документов без дат, чтобы не считать числа даты номерами.
        text = re.sub(r"\b\d{2}\.\d{2}\.\d{2,4}\b", " ", str(text))
        return set(re.findall(r"(?<!\w)[А-ЯA-Z]{0,4}[-/]?\d{2,}(?!\w)", text.upper()))

    def normalize(text):
        text = str(text).lower().replace('ё', 'е')
        text = re.sub(r"\d{2}\.\d{2}\.\d{2,4}", " ", text)
        text = re.sub(r"\b(корректировка|претензия|продажи|счет|фактура|от|номер)\b", " ", text)
        return re.sub(r"\W+", " ", text).strip()

    candidates = []
    for i, a in enumerate(only1):
        for j, b in enumerate(only2):
            ca, cb = smart_category(a['doc']), smart_category(b['doc'])
            if ca != cb or ca == 'Другой документ':
                continue
            difference = round(abs(a['amount'] - b['amount']), 2)
            if not 0.01 <= difference <= 1000.00:
                continue
            days = abs((a['date'] - b['date']).days)
            nums_a, nums_b = doc_numbers(a['raw_doc']), doc_numbers(b['raw_doc'])
            common_number = bool(nums_a & nums_b)
            similarity = SequenceMatcher(None, normalize(a['doc']), normalize(b['doc'])).ratio()
            # Не выводим случайные пары только из-за суммы: нужна близость дат,
            # общий номер или сильное сходство названий.
            if days > 31 and not common_number and similarity < 0.75:
                continue
            score = 0
            reasons = ['совместимый тип операции']
            if common_number:
                score += 45
                reasons.append('совпадает номер документа')
            if days <= 3:
                score += 25
                reasons.append('даты отличаются не более чем на 3 дня')
            elif days <= 10:
                score += 15
                reasons.append('близкие даты')
            elif days <= 31:
                score += 5
            if similarity >= 0.80:
                score += 20
                reasons.append('похожие названия')
            elif similarity >= 0.55:
                score += 10
            if difference <= 1:
                score += 15
            elif difference <= 100:
                score += 10
            else:
                score += 5
            candidates.append((score, difference, i, j, reasons, days))

    # Лучшие кандидаты без дублирования одного документа в нескольких парах.
    candidates.sort(key=lambda x: (-x[0], x[1], x[5]))
    used1, used2, findings = set(), set(), []
    for score, difference, i, j, reasons, days in candidates:
        if i in used1 or j in used2:
            continue
        a, b = only1[i], only2[j]
        competing = sum(1 for x in candidates if x[2] == i or x[3] == j) > 1
        if score >= 65 and not competing:
            confidence = 'Высокая'
        elif score >= 35:
            confidence = 'Средняя'
        else:
            confidence = 'Низкая'
        if competing:
            confidence = 'Неоднозначная' if score < 65 else 'Средняя'
        findings.append({
            'Уверенность': confidence,
            'Документ в акте 1': a['raw_doc'],
            'Сумма акта 1': round(a['amount'], 2),
            'Дата акта 1': a['date'].strftime('%d.%m.%Y'),
            'Документ в акте 2': b['raw_doc'],
            'Сумма акта 2': round(b['amount'], 2),
            'Дата акта 2': b['date'].strftime('%d.%m.%Y'),
            'Разница': difference,
            'Комментарий': '; '.join(reasons) + ('; есть альтернативные кандидаты' if competing else '') + '. Проверить первичные документы.'
        })
        used1.add(i)
        used2.add(j)

    warnings = []
    counts1 = Counter(round(x['amount'], 2) for x in all1)
    counts2 = Counter(round(x['amount'], 2) for x in all2)
    if any(n > 1 for n in counts1.values()) or any(n > 1 for n in counts2.values()):
        warnings.append('Есть повторяющиеся суммы: исходный алгоритм может сопоставить разные документы.')

    mismatched_types = []
    for a, b in matched:
        ca, cb = smart_category(a['doc']), smart_category(b['doc'])
        if ca != cb and ca != 'Другой документ' and cb != 'Другой документ':
            mismatched_types.append({
                'Документ в акте 1': a['raw_doc'],
                'Документ в акте 2': b['raw_doc'],
                'Сумма': round(a['amount'], 2),
                'Тип 1': ca, 'Тип 2': cb
            })
    return findings, warnings, mismatched_types


def smart_summary(only1, only2, hints):
    lines = [
        f'Не найдено пары в акте 2: {len(only1)} операций.',
        f'Не найдено пары в акте 1: {len(only2)} операций.'
    ]
    for label, ops in [('Только акт 1', only1), ('Только акт 2', only2)]:
        for op in ops:
            lines.append(
                f"{label}: {op['date']} | {op['raw_doc']} | "
                f"{op['amount']:,.2f} ₽ | {smart_category(op['doc'])}"
            )
    if hints:
        lines.append(f'Возможных ошибок суммы для проверки: {len(hints)}.')
    return '\n'.join(lines)

def render_comparison_form():
    generation = st.session_state.get("upload_generation", 0)
    col1, col2 = st.columns(2)
    with col1:
        file1 = st.file_uploader("Первый акт", type=["xls", "xlsx", "pdf"], key=f"first-act-{generation}")
    with col2:
        file2 = st.file_uploader("Второй акт", type=["xls", "xlsx", "pdf"], key=f"second-act-{generation}")

    if file1 and file2:
        df1 = read_any_file(file1)
        df2 = read_any_file(file2)

        if df1.empty or df2.empty:
            st.error("Один или оба файла не удалось прочитать.")
            st.stop()

        contractors1 = get_contractors(df1)
        contractors2 = get_contractors(df2)
        inns1 = get_inns(df1)
        inns2 = get_inns(df2)
        skip_check = st.checkbox("Пропустить проверку контрагентов", value=False)
        contractor_status = 'uncertain'
        allow_comparison = True
        if skip_check:
            st.info("Проверка контрагентов отключена по вашему выбору.")
        else:
            contractor_status, message = compare_contractors(contractors1, contractors2, inns1, inns2)
            if contractor_status == 'match':
                st.success(message)
            elif contractor_status == 'different':
                st.error("⚠️ " + message + " Сверка приостановлена до подтверждения.")
                allow_comparison = st.checkbox(
                    "Я проверил контрагентов и всё равно хочу выполнить сверку",
                    value=False,
                    key="confirm_different_contractors",
                )
            else:
                st.warning(message + " Сверка доступна.")
            with st.expander("Какие реквизиты контрагентов обнаружены?"):
                st.write("**Акт 1 — названия:**", ", ".join(sorted(contractors1)) or "не найдены")
                st.write("**Акт 2 — названия:**", ", ".join(sorted(contractors2)) or "не найдены")
                st.write("**Акт 1 — ИНН:**", ", ".join(sorted(inns1)) or "не найдены")
                st.write("**Акт 2 — ИНН:**", ", ".join(sorted(inns2)) or "не найдены")
                st.caption("Проверка предварительная: в файлах могут присутствовать ИНН обеих сторон. На алгоритм сопоставления операций она не влияет.")

        st.markdown("### Настройка сравнения")
        st.caption("Проверьте расположение колонок и параметры поиска совпадений.")
        st.subheader("Просмотр структуры файлов (первые 10 строк)")
        col_struct1, col_struct2 = st.columns(2)
        with col_struct1:
            st.write("Первый файл")
            st.dataframe(df1.head(10))
        with col_struct2:
            st.write("Второй файл")
            st.dataframe(df2.head(10))

        if file1.name.lower().endswith('.pdf'):
            date1_def, doc1_def, debit1_def, credit1_def = '0', '1', '2', '3'
        else:
            detected1 = auto_detect_columns_letters(df1)
            date1_def, doc1_def, debit1_def, credit1_def = detected1 if detected1 else ('A', 'B', 'C', 'D')

        if file2.name.lower().endswith('.pdf'):
            date2_def, doc2_def, debit2_def, credit2_def = '0', '1', '2', '3'
        else:
            detected2 = auto_detect_columns_letters(df2)
            date2_def, doc2_def, debit2_def, credit2_def = detected2 if detected2 else ('A', 'B', 'C', 'D')

        col1_set, col2_set = st.columns(2)
        with col1_set:
            st.subheader("Настройка первого файла")
            date1 = st.text_input("Дата", value=date1_def)
            doc1 = st.text_input("Документ", value=doc1_def)
            debit1 = st.text_input("Дебет", value=debit1_def)
            credit1 = st.text_input("Кредит", value=credit1_def)
        with col2_set:
            st.subheader("Настройка второго файла")
            date2 = st.text_input("Дата (второй)", value=date2_def)
            doc2 = st.text_input("Документ (второй)", value=doc2_def)
            debit2 = st.text_input("Дебет (второй)", value=debit2_def)
            credit2 = st.text_input("Кредит (второй)", value=credit2_def)

        ignore_sign = st.checkbox("Игнорировать знак (претензия = корректировка)", value=True)
        ignore_dates = st.checkbox("Не учитывать даты при сравнении", value=True)
        filter_initial = st.checkbox("Исключить операции до 01.07.2026", value=False)

        if st.button("🔎 Найти, где не сходится", type="primary", disabled=not allow_comparison):
            with st.spinner("🔍 Ищем документы, которые решили пойти своим путём…"):
                def get_col_idx(col_str, df_cols):
                    col_str = str(col_str).strip()
                    if col_str.isdigit():
                        return int(col_str)
                    return ord(col_str.upper()) - 65

                ops1 = extract_ops(df1, get_col_idx(date1, df1.columns), get_col_idx(doc1, df1.columns), get_col_idx(debit1, df1.columns), get_col_idx(credit1, df1.columns))
                ops2 = extract_ops(df2, get_col_idx(date2, df2.columns), get_col_idx(doc2, df2.columns), get_col_idx(debit2, df2.columns), get_col_idx(credit2, df2.columns))

                if filter_initial:
                    start = datetime(2026, 7, 1).date()
                    ops1 = [op for op in ops1 if op['date'] >= start]
                    ops2 = [op for op in ops2 if op['date'] >= start]

                if not ops1 or not ops2:
                    st.error("В одном из файлов нет операций. Проверьте колонки.")
                    st.stop()

                copy1, copy2 = ops1.copy(), ops2.copy()
                matched, only1, only2 = [], [], []

                for op1 in copy1:
                    found = None
                    for idx, op2 in enumerate(copy2):
                        if not ignore_dates and abs((op1['date'] - op2['date']).days) > 1: continue
                        if abs(op1['amount'] - op2['amount']) > 0.01: continue
                        if not ignore_sign and op1['sign'] != op2['sign']: continue
                        found = idx; break
                    if found is not None: matched.append((op1, copy2.pop(found)))
                    else: only1.append(op1)
                only2 = copy2

            first_day = min(operation["date"] for operation in ops1 + ops2)
            last_day = max(operation["date"] for operation in ops1 + ops2)
            period = (f"{first_day:%d.%m.%Y}" if first_day == last_day
                      else f"{first_day:%d.%m.%Y} – {last_day:%d.%m.%Y}")
            hints, warnings, different_types = smart_analyze(matched, only1, only2, ops1, ops2)
            snapshot = {
                "files": [file1.name, file2.name],
                "period": period,
                "ops": [ops1, ops2],
                "only": [[op["source_index"] for op in group] for group in (only1, only2)],
                "pairs": [(a["source_index"], b["source_index"]) for a, b in matched],
                "analysis": [hints, warnings, different_types],
            }
            try:
                record_id = HISTORY.save(snapshot)
            except sqlite3.Error:
                logger.exception("Не удалось сохранить результат сверки")
                st.error("Не удалось сохранить сверку. Проверьте локальную базу и повторите сравнение.")
                return
            open_review(record_id)
            st.rerun()


def render_result(record):
    result = record["result"]
    ops1, ops2 = result["ops"]
    first = {op["source_index"]: op for op in ops1}
    second = {op["source_index"]: op for op in ops2}
    only1 = [first[source] for source in result["only"][0]]
    only2 = [second[source] for source in result["only"][1]]
    matched = result["pairs"]
    status = "Проверено" if record["closed_at"] else "В работе"
    st.header(f"Сверка №{record['id']} · {status}")
    st.text(f"{result['files'][0]} ↔ {result['files'][1]}")
    st.caption(f"Период операций: {result['period']}")

    st.write(f"Всего операций в первом акте: **{len(ops1)}**")
    st.write(f"Всего операций во втором акте: **{len(ops2)}**")

    with st.expander("Извлечённые операции (первый акт)"): st.dataframe(pd.DataFrame(ops1))
    with st.expander("Извлечённые операции (второй акт)"): st.dataframe(pd.DataFrame(ops2))

    total_unmatched = len(only1) + len(only2)
    if total_unmatched:
        st.warning(f"🧐 Кажется, кто-то не договорился! Найдено {total_unmatched} операций без пары. Сейчас покажем, где именно.")
    else:
        st.success("🎉 Красота! Расхождений не обнаружено. Бухгалтер может выдохнуть.")

    st.subheader("Результаты сравнения")
    result_col1, result_col2, result_col3 = st.columns(3)
    with result_col1:
        st.metric("✅ Совпало операций", len(matched))
    with result_col2:
        st.metric("📄 Только в акте №1", len(only1))
    with result_col3:
        st.metric("📄 Только в акте №2", len(only2))
    if total_unmatched:
        st.caption(f"{len(matched)} операций нашли свою пару. {total_unmatched} пока остались в одиночестве. 🙂")
    else:
        st.caption(f"Все {len(matched)} операций нашли свою пару. Идеальная компания! ✨")

    # Каждая операция выводится только один раз, в своей категории.
    st.subheader("Детальный разбор расхождений")
    st.caption("Все документы без пары сгруппированы по типам. Повторного списка претензий нет.")

    def readable_direction(op):
        return "−" if op.get("sign", 1) == -1 else "+"

    def show_grouped_differences(operations, act_label):
        if not operations:
            st.success(f"{act_label}: операций без пары нет.")
            return
        st.markdown(f"#### {act_label} · {len(operations)}")
        groups = {}
        for op in operations:
            group = smart_category(op.get("doc", op.get("raw_doc", "")))
            groups.setdefault(group, []).append(op)
        for group, entries in groups.items():
            st.markdown(f"**{group} — {len(entries)}**")
            rows = [{
                "Дата": op["date"].strftime("%d.%m.%Y") if hasattr(op["date"], "strftime") else str(op["date"]),
                "Документ": op["raw_doc"],
                "Сумма, ₽": round(op["amount"], 2),
                "Направление": readable_direction(op),
            } for op in entries]
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

    show_grouped_differences(only1, "Только в первом акте")
    show_grouped_differences(only2, "Только во втором акте")

    # -------------------- ДОПОЛНИТЕЛЬНЫЙ УМНЫЙ АНАЛИЗ --------------------
    # Основной алгоритм выше НЕ ИЗМЕНЯЕТСЯ.
    st.divider()
    st.subheader("🧠 Умный анализ: ищем подозрительные суммы")
    st.caption("Возможно, здесь закралась опечатка. Проверим подозрительные суммы. Это подсказки, а не подтверждённые ошибки.")

    hints, warnings, different_types = result["analysis"]
    for warning in warnings:
        st.warning(warning)
    c1, c2, c3 = st.columns(3)
    c1.metric("Без пары в акте 1", len(only1))
    c2.metric("Без пары в акте 2", len(only2))
    c3.metric("Возможные ошибки сумм", len(hints))

    st.markdown("#### Заключение")
    st.write(
        f"Найдено **{len(only1) + len(only2)} несопоставленных записей**: "
        f"{len(only1)} в первом акте и {len(only2)} во втором. "
        "Одна хозяйственная операция может присутствовать в обоих списках "
        "с разными суммами или обозначениями."
    )
    if hints:
        st.warning(
            f"Есть {len(hints)} возможных соответствий с расхождением суммы "
            "не более 1 000 рублей. Они требуют проверки по первичным документам."
        )
        st.dataframe(pd.DataFrame(hints), hide_index=True, width="stretch")
    elif not only1 or not only2:
        st.info("Для поиска пар по сумме нужны несопоставленные строки в обоих актах.")
    else:
        st.info("Похожих сумм с разницей до 1 000 рублей среди несопоставленных операций не обнаружено.")

    # Повторения с равным количеством в обоих актах не объявляем ошибкой.
    from collections import Counter
    counts1 = Counter(round(x['amount'], 2) for x in ops1)
    counts2 = Counter(round(x['amount'], 2) for x in ops2)
    uneven = [
        {"Сумма, ₽": amount, "Акт 1": counts1[amount], "Акт 2": counts2[amount]}
        for amount in sorted(set(counts1) | set(counts2))
        if (counts1[amount] > 1 or counts2[amount] > 1)
        and counts1[amount] != counts2[amount]
    ]
    with st.expander("Дополнительные проверки неоднозначных операций"):
        if uneven:
            st.write("Повторяющиеся суммы с разным количеством записей в актах:")
            st.dataframe(pd.DataFrame(uneven), hide_index=True, width="stretch")
        else:
            st.write("Не найдено повторяющихся сумм с разным количеством записей.")
        if different_types:
            st.write("Пары, сопоставленные по сумме, но с разными типами документов:")
            st.dataframe(pd.DataFrame(different_types), hide_index=True, width="stretch")
        else:
            st.write("Явных различий типов в сопоставленных парах не выявлено.")
        st.caption("Даже одинаковое количество повторений не гарантирует правильное соответствие номеров документов.")

    render_assistant(record, HISTORY, smart_category)
    if not record["closed_at"]:
        ready = all(status == "checked" for status in record["marks"].values())
        if not ready:
            st.caption("Для завершения сверки отметьте все строки как «Проверено». Отметки сохраняются автоматически.")
        with st.container(horizontal=True):
            st.button("Сохранить и продолжить позже", on_click=open_history)
            if st.button("Завершить сверку", type="primary", disabled=not ready):
                finish_review(record["id"])

    # Окно для копирования: только несопоставленные документы и суммы.
    copy_lines = []

    if only1:
        copy_lines.append("ТОЛЬКО В ПЕРВОМ АКТЕ:")
        for op in only1:
            copy_lines.append(
                f"{op['date']:%d.%m.%Y} | {op['raw_doc']} | "
                f"{op['amount']:.2f} руб."
            )
        copy_lines.append("")

    if only2:
        copy_lines.append("ТОЛЬКО ВО ВТОРОМ АКТЕ:")
        for op in only2:
            copy_lines.append(
                f"{op['date']:%d.%m.%Y} | {op['raw_doc']} | "
                f"{op['amount']:.2f} руб."
            )
        copy_lines.append("")

    if hints:
        copy_lines.append("ВОЗМОЖНЫЕ РАСХОЖДЕНИЯ В СУММАХ (ТРЕБУЮТ ПРОВЕРКИ):")
        for hint in hints:
            copy_lines.append(
                f"Акт 1: {hint['Документ в акте 1']} — "
                f"{hint['Сумма акта 1']:.2f} руб."
            )
            copy_lines.append(
                f"Акт 2: {hint['Документ в акте 2']} — "
                f"{hint['Сумма акта 2']:.2f} руб."
            )
            copy_lines.append(f"Разница: {hint['Разница']:.2f} руб.")
            copy_lines.append("")

    copy_text = "\n".join(copy_lines).strip()
    if not copy_text:
        copy_text = "Расхождений не найдено."

    st.divider()
    st.subheader("📋 Забрать список расхождений")
    st.caption(
        "Заберите готовый список документов без пары, сумм и возможных ошибок. "
        "Нажмите внутри поля, затем Ctrl+A и Ctrl+C."
    )
    st.text_area(
        "Забрать список расхождений — выделите текст (Ctrl+A) и скопируйте (Ctrl+C)",
        value=copy_text,
        height=350,
        key=f"copy_differences_{record['id']}"
    )


def open_start():
    st.session_state["review_view"] = "start"
    st.session_state["upload_generation"] = st.session_state.get("upload_generation", 0) + 1


def open_history():
    st.session_state["review_view"] = "history"


def open_review(record_id):
    st.session_state["review_view"] = "review"
    st.session_state["active_review"] = record_id


def finish_review(record_id):
    try:
        finished = HISTORY.finish(record_id)
    except sqlite3.Error:
        logger.exception("Не удалось завершить сверку %s", record_id)
        st.error("Не удалось завершить сверку. Попробуйте ещё раз.")
        return
    if not finished:
        st.warning("Сверка уже завершена или в ней остались непроверенные строки. Обновите страницу.")
        return
    open_start()
    st.session_state["home_notice"] = f"Сверка №{record_id} сохранена в «Мои сверки → Завершённые»."
    st.rerun()


def navigation(view):
    with st.container(horizontal=True):
        st.button("Новая сверка", key="nav-start",
                  type="primary" if view == "start" else "secondary", on_click=open_start)
        st.button("Мои сверки", key="nav-history",
                  type="primary" if view == "history" else "secondary", on_click=open_history)


def show_workspace():
    view = st.session_state.get("review_view", "start")
    try:
        total = HISTORY.total()
    except sqlite3.Error:
        logger.exception("Не удалось открыть локальную базу")
        show_header(st.empty(), None)
        st.error("Не удалось открыть локальную базу. Проверьте, что приложение может писать в папку с базой.")
        return

    show_header(st.empty(), total)
    st.html(PAPER_BACKGROUND)
    navigation(view)
    if view == "history":
        try:
            records = HISTORY.list()
        except sqlite3.Error:
            logger.exception("Не удалось загрузить историю")
            st.error("Не удалось загрузить историю сверок. Попробуйте открыть раздел ещё раз.")
            return
        render_history(records, open_review)
        return

    if view == "review":
        try:
            record = HISTORY.load(st.session_state["active_review"])
        except (sqlite3.Error, ValueError, KeyError):
            logger.exception("Не удалось открыть сохранённую сверку")
            st.error("Не удалось прочитать сохранённую сверку.")
            return
        if record is None:
            st.error("Сохранённая сверка не найдена.")
            return
        render_result(record)
        return

    if notice := st.session_state.pop("home_notice", None):
        st.success(notice)
    st.html(START_SCREEN)
    render_comparison_form()


show_workspace()

# Компактная информация в самом низу — без большой отвлекающей карточки.
st.markdown("""
<div class="site-footer" style="margin-top:64px; align-items:flex-start;">
  <div style="max-width:620px;">
    <strong>ACT SVERKA</strong> · Для бухгалтеров, которые ценят время и нервные клетки
    <div style="margin-top:9px;line-height:1.7;font-size:.78rem;opacity:.86;">
      Сравнивать сотни строк вручную — сомнительное развлечение. Сервис помогает найти расхождения,
      но окончательное решение остаётся за человеком, особенно при повторяющихся суммах.
    </div>
  </div>
  <span>Excel / PDF · Умный анализ до 1 000 ₽</span>
</div>
""", unsafe_allow_html=True)
