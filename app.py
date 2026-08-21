import streamlit as st
import pandas as pd
import re
from datetime import datetime

# -------------------- Оформление (CSS) --------------------
st.set_page_config(
    page_title="Универсальная сверка актов",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* Фон всей страницы — розовый */
    html, body, .stApp {
        background-color: #ffc0cb !important;
        background-image: linear-gradient(135deg, #ffc0cb 0%, #ffe4e1 100%) !important;
        min-height: 100vh;
    }
    /* Основной контейнер — полупрозрачная белая карточка */
    .stApp > div {
        background-color: rgba(255, 255, 255, 0.92) !important;
        border-radius: 16px;
        padding: 25px;
        margin: 15px auto;
        max-width: 1200px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }
    /* Убираем лишние фоны у загрузчиков */
    .stFileUploader > div {
        background: transparent !important;
    }
    .stFileUploader label {
        background: transparent !important;
    }
    /* Заголовок по центру */
    h1 {
        text-align: center;
        color: #4a1a4a;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .centered-text {
        text-align: center;
        font-size: 1.1rem;
        color: #5a2a5a;
        margin-top: -0.5rem;
        margin-bottom: 1.5rem;
    }
    /* Кнопка «Сравнить» */
    .stButton button {
        background-color: #d63384;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 2rem;
        transition: 0.3s;
        width: 100%;
    }
    .stButton button:hover {
        background-color: #a02070;
        box-shadow: 0 4px 12px rgba(214, 51, 132, 0.3);
        transform: scale(1.02);
    }
    /* Центрирование сообщений */
    .centered-message {
        text-align: center;
        font-weight: bold;
        padding: 12px 20px;
        border-radius: 10px;
        margin: 10px auto;
        max-width: 80%;
        font-size: 1.05rem;
    }
    .centered-message.success {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    .centered-message.error {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    .centered-message.warning {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffc107;
    }
    .centered-message.info {
        background-color: #d1ecf1;
        color: #0c5460;
        border: 1px solid #bee5eb;
    }
    /* Метрики */
    .stMetric {
        background: rgba(255,255,255,0.7);
        border-radius: 12px;
        padding: 10px;
    }
    /* Таблицы */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Универсальная сверка актов")
st.markdown('<p class="centered-text">Автоматическое сравнение актов сверки</p>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    file1 = st.file_uploader("Первый акт", type=["xls", "xlsx"])
with col2:
    file2 = st.file_uploader("Второй акт", type=["xls", "xlsx"])

# -------------------- Парсеры (остаются без изменений) --------------------
def parse_date(val):
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        try:
            return pd.to_datetime(val, unit='D', origin='1899-12-30').date()
        except:
            return None
    if isinstance(val, str):
        val = val.strip()
        for fmt in ('%d.%m.%y', '%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
            try:
                return datetime.strptime(val, fmt).date()
            except:
                continue
    return None

def clean_number(s):
    if pd.isna(s):
        return 0.0
    s = str(s).strip()
    s = s.replace(' ', '').replace(',', '.')
    parts = s.split('.')
    if len(parts) > 1:
        s = ''.join(parts[:-1]) + '.' + parts[-1]
    try:
        return float(s)
    except:
        return 0.0

def index_to_letter(idx):
    if idx is None:
        return ''
    letter = ''
    n = idx + 1
    while n > 0:
        n -= 1
        letter = chr(n % 26 + ord('A')) + letter
        n //= 26
    return letter

def letter_to_idx(letter):
    if not letter:
        return 0
    return ord(letter.upper()) - 65

def is_likely_doc_column(col_values, threshold=0.3):
    doc_keywords = ['документ', 'накладная', 'платеж', 'возврат', 'корректировк',
                    'претензи', 'счет-фактура', 'упд', 'счет', 'акт', 'приход', 'продажа']
    vals = [str(v).strip() for v in col_values if pd.notna(v) and str(v).strip() != '']
    if not vals:
        return False
    rub_count = sum(1 for v in vals if v.upper() in ('RUB', 'РУБ', 'RUB.', 'РУБ.'))
    if rub_count / len(vals) > 0.8:
        return False
    kw_count = sum(1 for v in vals if any(kw in v.lower() for kw in doc_keywords))
    if kw_count > 0:
        return True
    unique_texts = set(vals)
    if len(unique_texts) > 1 and all(not v.replace('.', '').replace(',', '').isdigit() for v in unique_texts):
        return True
    return False

def auto_detect_columns_letters(df):
    header_row = None
    for i, row in df.iterrows():
        has_date = False
        has_doc = False
        for cell in row:
            if pd.notna(cell):
                cell_str = str(cell).lower()
                if 'дата' in cell_str:
                    has_date = True
                if 'документ' in cell_str:
                    has_doc = True
        if has_date and has_doc:
            header_row = i
            break
    if header_row is None:
        for i, row in df.iterrows():
            for cell in row:
                if pd.notna(cell) and parse_date(cell) is not None:
                    for j, val in enumerate(row):
                        if pd.notna(val) and clean_number(val) != 0.0:
                            header_row = i - 1
                            break
                    if header_row is not None:
                        break
            if header_row is not None:
                break
        if header_row is None:
            return None

    date_cols = []
    doc_cols = []
    debit_cols = []
    credit_cols = []
    for idx, val in df.iloc[header_row].items():
        if pd.notna(val):
            val_str = str(val).lower()
            if 'дата' in val_str:
                date_cols.append(idx)
            elif 'документ' in val_str:
                doc_cols.append(idx)
            elif 'дебет' in val_str:
                debit_cols.append(idx)
            elif 'кредит' in val_str:
                credit_cols.append(idx)

    if not debit_cols or not credit_cols:
        if header_row + 1 < len(df):
            for idx, val in df.iloc[header_row + 1].items():
                if pd.notna(val):
                    val_str = str(val).lower()
                    if 'дебет' in val_str and idx not in debit_cols:
                        debit_cols.append(idx)
                    elif 'кредит' in val_str and idx not in credit_cols:
                        credit_cols.append(idx)

    if not debit_cols or not credit_cols:
        for i in range(header_row + 1, min(header_row + 10, len(df))):
            numeric_cols = []
            row_data = df.iloc[i]
            for idx, val in row_data.items():
                if pd.notna(val):
                    try:
                        clean_number(val)
                        numeric_cols.append(idx)
                    except:
                        pass
            if len(numeric_cols) >= 2:
                numeric_cols.sort()
                if not debit_cols:
                    debit_cols.append(numeric_cols[0])
                if not credit_cols:
                    credit_cols.append(numeric_cols[-1])
                break

    if not doc_cols:
        excluded = set(date_cols + debit_cols + credit_cols)
        candidate_cols = [c for c in range(len(df.columns)) if c not in excluded]
        for col in candidate_cols:
            col_data = df.iloc[header_row+1:header_row+31, col]
            if is_likely_doc_column(col_data):
                doc_cols.append(col)
                break
        if not doc_cols and date_cols:
            date_col = date_cols[0]
            if date_col + 1 < len(df.columns):
                doc_cols.append(date_col + 1)
            elif date_col - 1 >= 0:
                doc_cols.append(date_col - 1)

    if doc_cols:
        doc_col = doc_cols[0]
        vals = df.iloc[header_row+1:header_row+21, doc_col].dropna().astype(str).str.upper()
        rub_count = sum(1 for v in vals if v in ('RUB', 'РУБ', 'RUB.', 'РУБ.'))
        if len(vals) > 0 and rub_count / len(vals) > 0.8:
            doc_cols = [c for c in doc_cols if c != doc_col]
            excluded = set(date_cols + debit_cols + credit_cols)
            candidate_cols = [c for c in range(len(df.columns)) if c not in excluded and c not in doc_cols]
            for col in candidate_cols:
                col_data = df.iloc[header_row+1:header_row+31, col]
                if is_likely_doc_column(col_data):
                    doc_cols.append(col)
                    break
            if not doc_cols and date_cols:
                date_col = date_cols[0]
                if date_col + 1 < len(df.columns) and date_col + 1 not in excluded:
                    doc_cols.append(date_col + 1)
                elif date_col - 1 >= 0 and date_col - 1 not in excluded:
                    doc_cols.append(date_col - 1)

    date_cols.sort()
    doc_cols.sort()
    debit_cols.sort()
    credit_cols.sort()

    def has_data(date_idx, doc_idx, debit_idx, credit_idx):
        for i in range(header_row + 1, len(df)):
            row = df.iloc[i]
            if len(row) <= max(date_idx, doc_idx, debit_idx, credit_idx):
                continue
            dt = parse_date(row[date_idx])
            if dt is None:
                continue
            has_num = False
            if len(row) > debit_idx and pd.notna(row[debit_idx]):
                try:
                    clean_number(row[debit_idx])
                    has_num = True
                except:
                    pass
            if not has_num and len(row) > credit_idx and pd.notna(row[credit_idx]):
                try:
                    clean_number(row[credit_idx])
                    has_num = True
                except:
                    pass
            if has_num:
                return True
        return False

    if date_cols and doc_cols and debit_cols and credit_cols:
        d_idx = date_cols[-1]
        doc_idx = doc_cols[-1]
        deb_idx = debit_cols[-1]
        cred_idx = credit_cols[-1]
        if has_data(d_idx, doc_idx, deb_idx, cred_idx):
            return (index_to_letter(d_idx), index_to_letter(doc_idx),
                    index_to_letter(deb_idx), index_to_letter(cred_idx))
        if len(date_cols) > 1:
            d_idx = date_cols[-2]
            doc_idx = doc_cols[-2] if len(doc_cols) > 1 else doc_cols[0]
            deb_idx = debit_cols[-2] if len(debit_cols) > 1 else debit_cols[0]
            cred_idx = credit_cols[-2] if len(credit_cols) > 1 else credit_cols[0]
            if has_data(d_idx, doc_idx, deb_idx, cred_idx):
                return (index_to_letter(d_idx), index_to_letter(doc_idx),
                        index_to_letter(deb_idx), index_to_letter(cred_idx))
        return (index_to_letter(date_cols[0]), index_to_letter(doc_cols[0]),
                index_to_letter(debit_cols[0]), index_to_letter(credit_cols[0]))
    else:
        return None

def extract_ops(df, date_col, doc_col, debit_col, credit_col):
    ops = []
    for _, row in df.iterrows():
        if len(row) <= max(date_col, doc_col, debit_col, credit_col):
            continue
        dt = parse_date(row[date_col])
        if dt is None:
            continue
        doc = str(row[doc_col]).strip() if pd.notna(row[doc_col]) else ''
        if not doc:
            continue
        debit = clean_number(row[debit_col] if len(row) > debit_col else None)
        credit = clean_number(row[credit_col] if len(row) > credit_col else None)
        if abs(debit) < 0.001 and abs(credit) < 0.001:
            continue
        if abs(credit) > 0.001:
            amount = credit
            sign = 1
        elif abs(debit) > 0.001:
            amount = debit
            sign = -1
        else:
            continue
        ops.append({
            'date': dt,
            'doc': doc,
            'amount': abs(amount),
            'sign': sign,
            'raw_doc': doc,
            'change': amount
        })
    return ops

def is_correction(doc_text):
    kw = ['корректировк', 'претензи', 'возврат', 'перерасчет', 'сторно', 'исправлен']
    return any(k in doc_text.lower() for k in kw)

# -------------------- Функция извлечения контрагентов --------------------
def get_contractors(df):
    text_lines = []
    for i in range(min(10, len(df))):
        row = df.iloc[i]
        for cell in row:
            if pd.notna(cell):
                text_lines.append(str(cell))
    full_text = ' '.join(text_lines)

    match = re.search(r'между\s+(.+?)\s+и\s+(.+?)(?:\s*[\(,]|\s*$)', full_text, re.IGNORECASE)
    if match:
        org1 = match.group(1).strip()
        org2 = match.group(2).strip()
        def extract_key(name):
            q = re.search(r'["“]([^"“]+)["“"]', name)
            if q:
                return q.group(1).strip().upper()
            words = name.split()
            if words:
                last = re.sub(r'[^\w]', '', words[-1])
                if last:
                    return last.upper()
            return name.upper()
        return {extract_key(org1), extract_key(org2)}
    else:
        orgs = set()
        patterns = [
            r'ООО\s+"([^"]+)"',
            r'Общество\s+с\s+ограниченной\s+ответственностью\s+"([^"]+)"',
            r'Общество\s+с\s+ограниченной\s+ответственностью\s+\(ООО\)\s+"([^"]+)"',
            r'\(ООО\)\s+"([^"]+)"'
        ]
        for pat in patterns:
            matches = re.findall(pat, full_text, re.IGNORECASE)
            for m in matches:
                orgs.add(m.strip().upper())
        if orgs:
            return orgs
        return set()

# -------------------- Основная часть --------------------
if file1 and file2:
    df1 = pd.read_excel(file1, header=None)
    df2 = pd.read_excel(file2, header=None)

    contractors1 = get_contractors(df1)
    contractors2 = get_contractors(df2)

    skip_check = st.checkbox("Пропустить проверку контрагентов (если не совпадают)", value=False)

    # Вывод центрированных сообщений вместо стандартных
    if not skip_check and contractors1 and contractors2:
        if contractors1 != contractors2:
            st.markdown('<div class="centered-message error">❌ Акты относятся к разным контрагентам! Проверьте загруженные файлы. Если вы уверены, что они верны, отметьте "Пропустить проверку" и нажмите "Сравнить" снова.</div>', unsafe_allow_html=True)
            st.stop()
        else:
            st.markdown('<div class="centered-message success">✅ Контрагенты совпадают. Продолжаем сравнение.</div>', unsafe_allow_html=True)
    else:
        if skip_check:
            st.markdown('<div class="centered-message warning">⚠️ Проверка контрагентов пропущена по вашему запросу.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="centered-message info">⚠️ Не удалось определить контрагентов в одном из файлов. Проверка пропущена.</div>', unsafe_allow_html=True)

    st.subheader("Просмотр структуры файлов (первые 10 строк)")
    col_struct1, col_struct2 = st.columns(2)
    with col_struct1:
        st.write("Первый файл")
        st.dataframe(df1.head(10))
    with col_struct2:
        st.write("Второй файл")
        st.dataframe(df2.head(10))

    detected1 = auto_detect_columns_letters(df1)
    detected2 = auto_detect_columns_letters(df2)

    if detected1:
        date1_def, doc1_def, debit1_def, credit1_def = detected1
    else:
        date1_def, doc1_def, debit1_def, credit1_def = 'A', 'B', 'D', 'F'
    if detected2:
        date2_def, doc2_def, debit2_def, credit2_def = detected2
    else:
        date2_def, doc2_def, debit2_def, credit2_def = 'A', 'B', 'G', 'H'

    st.info("Если автоматические буквы неверны, исправьте их вручную и нажмите «Сравнить».")

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
        date_idx1 = letter_to_idx(date1)
        doc_idx1 = letter_to_idx(doc1)
        debit_idx1 = letter_to_idx(debit1)
        credit_idx1 = letter_to_idx(credit1)
        date_idx2 = letter_to_idx(date2)
        doc_idx2 = letter_to_idx(doc2)
        debit_idx2 = letter_to_idx(debit2)
        credit_idx2 = letter_to_idx(credit2)

        ops1 = extract_ops(df1, date_idx1, doc_idx1, debit_idx1, credit_idx1)
        ops2 = extract_ops(df2, date_idx2, doc_idx2, debit_idx2, credit_idx2)

        def has_valid_docs(ops, threshold=0.7):
            if not ops:
                return False
            valid = sum(1 for op in ops if op['doc'] and op['doc'] not in ('RUB', 'руб', 'RUB.', 'руб.'))
            return valid / len(ops) > threshold

        if ops1 and not has_valid_docs(ops1):
            for col in range(len(df1.columns)):
                if col == date_idx1 or col == debit_idx1 or col == credit_idx1:
                    continue
                test_ops = extract_ops(df1, date_idx1, col, debit_idx1, credit_idx1)
                if test_ops and has_valid_docs(test_ops):
                    ops1 = test_ops
                    doc1_def = index_to_letter(col)
                    st.info(f"Для первого файла автоматически выбрана колонка документа {doc1_def}")
                    break
        if ops2 and not has_valid_docs(ops2):
            for col in range(len(df2.columns)):
                if col == date_idx2 or col == debit_idx2 or col == credit_idx2:
                    continue
                test_ops = extract_ops(df2, date_idx2, col, debit_idx2, credit_idx2)
                if test_ops and has_valid_docs(test_ops):
                    ops2 = test_ops
                    doc2_def = index_to_letter(col)
                    st.info(f"Для второго файла автоматически выбрана колонка документа {doc2_def}")
                    break

        if filter_initial:
            start = datetime(2026, 7, 1).date()
            ops1 = [op for op in ops1 if op['date'] >= start]
            ops2 = [op for op in ops2 if op['date'] >= start]

        st.write(f"Всего операций в первом акте: **{len(ops1)}**")
        st.write(f"Всего операций во втором акте: **{len(ops2)}**")

        with st.expander("Извлечённые операции (первый акт)"):
            st.dataframe(pd.DataFrame(ops1))
        with st.expander("Извлечённые операции (второй акт)"):
            st.dataframe(pd.DataFrame(ops2))

        if not ops1 or not ops2:
            st.error("В одном из файлов нет операций. Проверьте правильность введённых букв колонок.")
            st.stop()

        copy1 = ops1.copy()
        copy2 = ops2.copy()
        matched = []
        only1 = []
        only2 = []

        for op1 in copy1:
            found = None
            for idx, op2 in enumerate(copy2):
                if not ignore_dates and abs((op1['date'] - op2['date']).days) > 1:
                    continue
                if abs(op1['amount'] - op2['amount']) > 0.01:
                    continue
                if not ignore_sign and op1['sign'] != op2['sign']:
                    continue
                found = idx
                break
            if found is not None:
                matched.append((op1, copy2.pop(found)))
            else:
                only1.append(op1)
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
