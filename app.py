import streamlit as st
import pandas as pd
import re
from datetime import datetime, date

# -------------------- Оформление (CSS) --------------------
st.set_page_config(page_title="ACT SVERKA | Сверка актов", page_icon="📑", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
:root {color-scheme:light;}
.stApp{background:radial-gradient(ellipse 55% 38% at 4% 2%,rgba(145,201,255,.38),transparent 75%),radial-gradient(ellipse 48% 40% at 98% 13%,rgba(182,157,255,.38),transparent 78%),radial-gradient(ellipse 48% 32% at 45% 90%,rgba(207,231,255,.32),transparent 80%),#f8faff;color:#17233d;}
[data-testid="stHeader"]{background:transparent!important;}
.block-container{max-width:1180px;padding-top:1.5rem;padding-bottom:3rem;}
h1,h2,h3{color:#1d2843!important;letter-spacing:-.035em;}
h2{font-size:1.45rem!important;}
.site-nav{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:16px 22px;background:rgba(255,255,255,.77);border:1px solid rgba(255,255,255,.95);border-radius:20px;box-shadow:0 10px 35px rgba(66,84,145,.08);backdrop-filter:blur(16px);margin-bottom:24px;}
.site-brand{display:flex;align-items:center;gap:11px;font-weight:850;letter-spacing:.08em;font-size:1rem;color:#1b2949;}
.site-logo{width:36px;height:36px;border-radius:12px;background:linear-gradient(140deg,#5878ee,#9778f7);display:grid;place-items:center;color:#fff;font-size:22px;box-shadow:0 5px 16px rgba(92,101,222,.24);}
.site-nav-right{color:#72809d;font-size:.83rem;white-space:nowrap;}
.site-nav-joke{flex:1;text-align:center;color:#6266a7;font-size:.88rem;font-weight:600;padding:0 14px;}
.hero{position:relative;isolation:isolate;overflow:hidden;display:grid;grid-template-columns:1.25fr .75fr;gap:24px;min-height:290px;padding:38px 40px;border-radius:28px;background:linear-gradient(120deg,#ffffff 0%,#f3f5ff 65%,#ecebff 100%);border:1px solid white;box-shadow:0 22px 60px rgba(87,98,162,.10);margin-bottom:19px;}
.hero:before{content:"";position:absolute;width:360px;height:360px;right:-110px;top:-150px;border-radius:50%;background:linear-gradient(145deg,rgba(135,183,255,.36),rgba(172,135,255,.3));z-index:-1;}
.hero-tag{display:inline-flex;align-items:center;gap:8px;font-size:.76rem;color:#5465c4;font-weight:800;letter-spacing:.09em;text-transform:uppercase;background:#e9ecff;border:1px solid #dfe3ff;padding:8px 12px;border-radius:100px;}
.hero-title{font-size:clamp(2.2rem,4vw,3.6rem);line-height:1.09;letter-spacing:-.055em;font-weight:850;color:#1c2b4c;margin:20px 0 14px;max-width:650px;}
.hero-title em{font-style:normal;background:linear-gradient(100deg,#5273df,#9674df);-webkit-background-clip:text;background-clip:text;color:transparent;}
.hero-desc{font-size:1.01rem;line-height:1.7;color:#697792;max-width:590px;}
.hero-art{position:relative;min-height:220px;display:flex;align-items:center;justify-content:center;}
.art-card{width:260px;background:rgba(255,255,255,.94);border:1px solid #fff;border-radius:20px;box-shadow:0 24px 50px rgba(70,88,157,.18);padding:20px;transform:rotate(-5deg);}
.art-title{font-size:.83rem;color:#27375a;font-weight:800;margin-bottom:16px;}
.art-row{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:10px 0;font-size:.74rem;color:#67738c;}
.art-line{height:9px;border-radius:10px;background:#e7ecfa;width:65%;}
.art-line.short{width:43%;}
.art-pill{background:#e6f7ef;color:#23986c;border-radius:50px;padding:5px 8px;font-weight:800;}
.art-pill.warn{background:#fff0e5;color:#d48045;}
.art-float{position:absolute;right:4%;bottom:12%;background:#fff;border-radius:13px;padding:10px 13px;box-shadow:0 12px 30px rgba(81,95,157,.15);font-size:.77rem;color:#5364a5;font-weight:800;transform:rotate(7deg);}
.features{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:0 0 31px;}
.feature{background:rgba(255,255,255,.83);border:1px solid #e7eafb;border-radius:18px;padding:19px 20px;box-shadow:0 8px 28px rgba(81,97,151,.045);transition:transform .2s,box-shadow .2s;}
.feature:hover{transform:translateY(-3px);box-shadow:0 14px 35px rgba(81,97,151,.10);}
.feature-icon{display:inline-grid;place-items:center;width:36px;height:36px;border-radius:12px;background:#eef1ff;color:#6776d9;font-size:19px;margin-bottom:11px;}
.feature strong{display:block;color:#263553;font-size:.93rem;margin-bottom:6px;}
.feature span{color:#75819a;font-size:.82rem;line-height:1.5;}
.section-label{font-size:.83rem;color:#66769b;font-weight:800;letter-spacing:.08em;text-transform:uppercase;margin:0 0 14px;}
[data-testid="stFileUploader"]{background:rgba(255,255,255,.9);border:1px solid #e0e6f6;border-radius:19px;padding:16px;box-shadow:0 10px 28px rgba(65,82,145,.045);}
[data-testid="stFileUploaderDropzone"]{background:#f7f9ff;border:1px dashed #cbd6f0;border-radius:14px;}
[data-testid="stMetric"]{background:rgba(255,255,255,.95);border:1px solid #e0e6f6;border-radius:17px;padding:19px;box-shadow:0 8px 25px rgba(65,82,145,.06);}
[data-testid="stMetricLabel"]{color:#75829c;}
[data-testid="stMetricValue"]{color:#26365b;}
.stButton button[kind="primary"],.stButton button{background:linear-gradient(110deg,#526ee3,#7965d9)!important;border:0!important;border-radius:12px!important;color:#fff!important;font-weight:750!important;min-height:46px;box-shadow:0 7px 17px rgba(89,103,218,.19);}
.stButton button:hover{background:linear-gradient(110deg,#415bcd,#6651c7)!important;color:white!important;transform:translateY(-1px);}
[data-testid="stTextArea"] textarea{background:#fff!important;border:1px solid #dfe5f4!important;border-radius:13px!important;font-family:Consolas,monospace;line-height:1.6;}
[data-testid="stExpander"]{background:rgba(255,255,255,.85);border:1px solid #e0e6f5;border-radius:13px;}
[data-testid="stDataFrame"]{border-radius:13px;overflow:hidden;}
[data-testid="stTextInput"] input{border-radius:10px;}
.site-footer{margin-top:48px;padding:26px 6px;border-top:1px solid #dce3f3;display:flex;justify-content:space-between;gap:18px;flex-wrap:wrap;color:#7a87a0;font-size:.82rem;}
@media(max-width:800px){.hero{grid-template-columns:1fr;padding:28px 23px}.hero-art{display:none}.features{grid-template-columns:1fr}.site-nav-right{display:none}.site-nav-joke{font-size:.75rem;padding:0 2px}.block-container{padding-top:1rem}}
/* Ненавязчивый бухгалтерский паттерн на фоне */
.stApp:before{content:"";position:fixed;inset:0;pointer-events:none;opacity:.38;background-image:linear-gradient(rgba(118,145,220,.09) 1px,transparent 1px),linear-gradient(90deg,rgba(118,145,220,.09) 1px,transparent 1px);background-size:48px 48px;mask-image:linear-gradient(to bottom,#000,transparent 72%);z-index:0}
.block-container{position:relative;z-index:1}
.hero{min-height:345px;grid-template-columns:1.1fr .9fr;align-items:center;background:linear-gradient(115deg,#fff 0%,#f7faff 48%,#f0efff 100%)}
.hero:after{content:"";position:absolute;width:230px;height:230px;left:-100px;bottom:-165px;border-radius:50%;background:rgba(158,202,255,.24);pointer-events:none}
.hero-art{min-height:260px;isolation:isolate}
.doc-visual{position:relative;width:100%;height:250px;max-width:380px}
.doc-sheet{position:absolute;width:215px;height:210px;padding:19px 17px;border:1px solid #e2e8f7;border-radius:17px;background:rgba(255,255,255,.94);box-shadow:0 20px 44px rgba(75,90,151,.16)}
.doc-sheet.first{left:2%;top:8px;transform:rotate(-10deg)}
.doc-sheet.second{right:0;top:35px;transform:rotate(8deg)}
.doc-head{display:flex;align-items:center;gap:8px;font-size:12px;font-weight:800;color:#2b3a60;margin-bottom:18px}
.doc-icon{display:grid;place-items:center;width:25px;height:29px;border-radius:7px;background:#e8efff;color:#5a76d8;font-size:16px}
.doc-line{height:9px;border-radius:8px;background:#e8edf8;margin:12px 0}
.doc-line.sm{width:62%}.doc-line.md{width:82%}
.doc-amount{display:flex;justify-content:space-between;font-size:11px;color:#7c8aa7;margin-top:18px}
.doc-amount b{color:#40557c}
.compare-bubble{position:absolute;z-index:3;left:45%;top:44%;width:56px;height:56px;display:grid;place-items:center;border-radius:18px;background:linear-gradient(140deg,#5578e7,#9573e9);box-shadow:0 13px 26px rgba(88,99,204,.32);color:#fff;font-size:27px;border:4px solid #fff}
.difference-chip{position:absolute;z-index:4;right:-3%;bottom:0;background:#fff;border:1px solid #e9e5ff;border-radius:13px;box-shadow:0 10px 28px rgba(80,94,159,.15);padding:10px 13px;font-size:12px;color:#7a6b9b;font-weight:700}
.difference-chip strong{color:#7557c9}
.compatibility{margin-top:13px;display:inline-flex;gap:7px;align-items:center;color:#6b7696;font-size:.81rem}
.compatibility b{font-weight:700;color:#5664b4}
@media(max-width:800px){.hero-art{display:flex;min-height:230px}.doc-visual{transform:scale(.82);transform-origin:center}.hero{gap:0}.hero-title{font-size:2.25rem}}
.why-section{margin-top:34px;padding:30px 34px;border:1px solid #dfe4f6;border-radius:24px;background:linear-gradient(115deg,rgba(255,255,255,.96),rgba(239,239,255,.78));box-shadow:0 14px 40px rgba(86,103,177,.08)}
.why-kicker{font-size:.74rem;font-weight:800;letter-spacing:.12em;color:#777cc4;margin-bottom:12px}
.why-section h3{font-size:1.5rem;color:#222c4c;margin:0 0 12px;font-weight:800}
.why-section p{font-size:1.02rem;color:#53617d;line-height:1.75;max-width:780px;margin:0 0 16px}
.why-note{font-size:.84rem;color:#68738e;background:rgba(238,241,255,.8);padding:12px 15px;border-radius:12px;line-height:1.6}
</style>
""",unsafe_allow_html=True)

st.markdown("""<div class="site-nav"><div class="site-brand"><div class="site-logo">≋</div>ACT SVERKA</div><div class="site-nav-joke">Сводим дебет с кредитом. И людей с ума не сводим 😎</div><div class="site-nav-right">Сверка документов · Excel / PDF</div></div>
<section class="hero"><div><div class="hero-tag">✦ Для тех, кто устал сверять вручную</div><div class="hero-title">Два акта. Одна правда.<br><em>И никаких поисков по 300 строкам.</em></div><div class="hero-desc">Сервис сравнивает операции в двух актах сверки, находит несовпадения по суммам и датам и помогает разобраться, где именно возникла разница.</div><div class="compatibility">◈ Excel и PDF · Выгрузки из <b>1С</b> · Поиск возможных ошибок до 1 000 ₽</div></div>
<div class="hero-art"><div class="doc-visual" aria-hidden="true"><div class="doc-sheet first"><div class="doc-head"><span class="doc-icon">▤</span> АКТ №1</div><div class="doc-line md"></div><div class="doc-line"></div><div class="doc-line sm"></div><div class="doc-amount"><span>Операция</span><b>12 450,00 ₽</b></div></div><div class="doc-sheet second"><div class="doc-head"><span class="doc-icon">▤</span> АКТ №2</div><div class="doc-line"></div><div class="doc-line sm"></div><div class="doc-line md"></div><div class="doc-amount"><span>Операция</span><b>12 450,00 ₽</b></div></div><div class="compare-bubble">⇄</div><div class="difference-chip">✦ Поиск расхождений <strong>до 1 000 ₽</strong></div></div></div></section>
<div class="features"><div class="feature"><div class="feature-icon">⇄</div><strong>Сравнение актов</strong><span>Проверим операции и покажем, какие документы не нашли пару.</span></div><div class="feature"><div class="feature-icon">✧</div><strong>Умный поиск</strong><span>Подскажем, где возможна ошибка в сумме. Даже 11 копеек не спрячутся.</span></div><div class="feature"><div class="feature-icon">▤</div><strong>Готовый результат</strong><span>Список расхождений с документами, датами и суммами. Без ручной перепечатки.</span></div></div>
<div class="section-label">01 / Загрузите два акта. Остальное — наша забота.</div>""",unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    file1 = st.file_uploader("Первый акт", type=["xls", "xlsx", "pdf"])
with col2:
    file2 = st.file_uploader("Второй акт", type=["xls", "xlsx", "pdf"])

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
            for page in pdf.pages:
                text = page.extract_text()
                if not text: continue
                
                lines = text.split('\n')
                current_date = None
                current_doc = []
                current_amt = None
                pre_buffer = [] # Буфер для текста, идущего до даты

                for line in lines:
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
                                rows.append([current_date, final_doc if final_doc else "Документ (не распознан)", current_amt if current_amt else ""])
                                current_date = None
                                current_doc = []
                                current_amt = None
                                
                            current_date = dates[0].group(1)
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
                                rows.append([current_date, final_doc if final_doc else "Документ (не распознан)", current_amt])
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
                                rows.append([current_date, final_doc if final_doc else "Документ (не распознан)", current_amt])
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
                    rows.append([current_date, final_doc if final_doc else "Документ (не распознан)", current_amt if current_amt else ""])
                    
    except Exception as e:
        st.error(f"Не удалось прочитать PDF: {e}")
        return pd.DataFrame()

    if not rows: return pd.DataFrame()

    final_rows = []
    for r in rows:
        d, doc, amt = r
        if not parse_date(d): continue
        
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
    for _, row in df.iterrows():
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
        
        ops.append({'date': dt, 'doc': doc, 'amount': abs(amount), 'sign': sign, 'raw_doc': doc, 'change': amount})
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

# -------------------- Основная часть --------------------
if file1 and file2:
    df1 = read_any_file(file1)
    df2 = read_any_file(file2)

    if df1.empty or df2.empty:
        st.error("Один или оба файла не удалось прочитать.")
        st.stop()

    contractors1 = get_contractors(df1)
    contractors2 = get_contractors(df2)
    skip_check = st.checkbox("Пропустить проверку контрагентов (если не совпадают)", value=False)

    if not skip_check and contractors1 and contractors2:
        if contractors1 != contractors2:
            st.markdown('<div class="centered-message error">❌ Акты относятся к разным контрагентам! Проверьте файлы.</div>', unsafe_allow_html=True)
            st.stop()
        else:
            st.markdown('<div class="centered-message success">✅ Контрагенты совпадают. Продолжаем сравнение.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="centered-message warning">⚠️ Проверка контрагентов пропущена.</div>', unsafe_allow_html=True)

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

    if st.button("🔎 Найти, где не сходится"):
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


        st.write(f"Всего операций в первом акте: **{len(ops1)}**")
        st.write(f"Всего операций во втором акте: **{len(ops2)}**")

        with st.expander("Извлечённые операции (первый акт)"): st.dataframe(pd.DataFrame(ops1))
        with st.expander("Извлечённые операции (второй акт)"): st.dataframe(pd.DataFrame(ops2))

        total_unmatched = len(only1) + len(only2)
        if total_unmatched:
            st.warning(
                f"🧐 Кажется, кто-то не договорился. Нашли {total_unmatched} "
                f"записей без пары: {len(only1)} в первом акте и {len(only2)} во втором. "
                "Одна операция может попасть в оба списка — проверьте подсказки ниже."
            )
        else:
            st.success("🎉 Красота! Расхождений не обнаружено. Бухгалтер может выдохнуть.")

        st.subheader("Результаты сравнения")
        st.metric("Совпало операций", len(matched))
        st.metric("Только в первом акте", len(only1))
        st.metric("Только во втором акте", len(only2))

        if only1:
            st.error(f"Операции, отсутствующие во втором акте ({len(only1)} шт.):")
            st.dataframe(pd.DataFrame(only1)[['date', 'raw_doc', 'amount', 'sign']])
        if only2:
            st.error(f"Операции, отсутствующие в первом акте ({len(only2)} шт.):")
            st.dataframe(pd.DataFrame(only2)[['date', 'raw_doc', 'amount', 'sign']])

        corr_only1 = [op for op in only1 if is_correction(op['doc'])]
        corr_only2 = [op for op in only2 if is_correction(op['doc'])]
        if corr_only1 or corr_only2:
            st.subheader("🔍 Не совпавшие корректировки/претензии")
            if corr_only1:
                st.error(f"В первом акте есть, во втором нет ({len(corr_only1)}):")
                st.dataframe(pd.DataFrame(corr_only1)[['date', 'raw_doc', 'amount', 'sign']])
            if corr_only2:
                st.error(f"Во втором акте есть, в первом нет ({len(corr_only2)}):")
                st.dataframe(pd.DataFrame(corr_only2)[['date', 'raw_doc', 'amount', 'sign']])

        # -------------------- ДОПОЛНИТЕЛЬНЫЙ УМНЫЙ АНАЛИЗ --------------------
        # Основной алгоритм выше НЕ ИЗМЕНЯЕТСЯ.
        st.divider()
        st.subheader("🧠 Умный анализ: ищем подозрительные суммы")
        st.caption("Возможно, здесь закралась опечатка. Проверим подозрительные суммы. Это подсказки, а не подтверждённые ошибки.")

        hints, warnings, different_types = smart_analyze(
            matched, only1, only2, ops1, ops2
        )
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
            st.dataframe(pd.DataFrame(hints), hide_index=True, use_container_width=True)
        else:
            st.info("Похожих сумм с разницей до 1 000 рублей среди несопоставленных операций не обнаружено.")

        def show_missing(title, items):
            st.markdown(f"#### {title} — {len(items)}")
            if items:
                rows = [{
                    "Дата": op['date'].strftime('%d.%m.%Y'),
                    "Документ": op['raw_doc'],
                    "Сумма, ₽": round(op['amount'], 2),
                    "Категория": smart_category(op['doc'])
                } for op in items]
                st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
            else:
                st.success("Нет записей без пары.")

        show_missing("Только в первом акте", only1)
        show_missing("Только во втором акте", only2)

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
                st.dataframe(pd.DataFrame(uneven), hide_index=True, use_container_width=True)
            else:
                st.write("Не найдено повторяющихся сумм с разным количеством записей.")
            if different_types:
                st.write("Пары, сопоставленные по сумме, но с разными типами документов:")
                st.dataframe(pd.DataFrame(different_types), hide_index=True, use_container_width=True)
            else:
                st.write("Явных различий типов в сопоставленных парах не выявлено.")
            st.caption("Даже одинаковое количество повторений не гарантирует правильное соответствие номеров документов.")

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
            key="copy_differences"
        )

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
