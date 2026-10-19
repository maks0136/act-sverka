import streamlit as st
import pandas as pd
import re
from datetime import datetime, date

# -------------------- Оформление (CSS) --------------------
st.set_page_config(
    page_title="Универсальная сверка актов",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    html, body, .stApp {
        background-color: #ffc0cb !important;
        background-image: linear-gradient(135deg, #ffc0cb 0%, #ffe4e1 100%) !important;
        min-height: 100vh;
    }
    .stApp > div {
        background-color: rgba(255, 255, 255, 0.92) !important;
        border-radius: 16px;
        padding: 25px;
        margin: 15px auto;
        max-width: 1200px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }
    .stFileUploader > div { background: transparent !important; }
    .stFileUploader label { background: transparent !important; }
    h1 { text-align: center; color: #4a1a4a; font-weight: 700; margin-bottom: 0.2rem; }
    .centered-text { text-align: center; font-size: 1.1rem; color: #5a2a5a; margin-top: -0.5rem; margin-bottom: 1.5rem; }
    .stButton button {
        background-color: #d63384; color: white; font-weight: bold;
        border-radius: 8px; border: none; padding: 0.5rem 2rem;
        transition: 0.3s; width: 100%;
    }
    .stButton button:hover { background-color: #a02070; box-shadow: 0 4px 12px rgba(214, 51, 132, 0.3); transform: scale(1.02); }
    .centered-message {
        text-align: center; font-weight: bold; padding: 12px 20px;
        border-radius: 10px; margin: 10px auto; max-width: 80%; font-size: 1.05rem;
    }
    .centered-message.success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    .centered-message.error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    .centered-message.warning { background-color: #fff3cd; color: #856404; border: 1px solid #ffc107; }
    .centered-message.info { background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
    .stMetric { background: rgba(255,255,255,0.7); border-radius: 12px; padding: 10px; }
    .stDataFrame { border-radius: 12px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

st.title("📊 Универсальная сверка актов")
st.markdown('<p class="centered-text">Автоматическое сравнение актов сверки (Excel + PDF)</p>', unsafe_allow_html=True)

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

    if st.button("Сравнить"):
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

        st.write(f"Всего операций в первом акте: **{len(ops1)}**")
        st.write(f"Всего операций во втором акте: **{len(ops2)}**")

        with st.expander("Извлечённые операции (первый акт)"): st.dataframe(pd.DataFrame(ops1))
        with st.expander("Извлечённые операции (второй акт)"): st.dataframe(pd.DataFrame(ops2))

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

        if not only1 and not only2:
            st.success("✅ Все операции совпадают!")
