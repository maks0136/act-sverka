import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Универсальная сверка актов", layout="wide")
st.title("Автоматическое сравнение актов сверки")

col1, col2 = st.columns(2)
with col1:
    file1 = st.file_uploader("Первый акт", type=["xls", "xlsx"])
with col2:
    file2 = st.file_uploader("Второй акт", type=["xls", "xlsx"])

# -------------------- Парсеры --------------------
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

def auto_detect_columns_letters(df):
    """
    Улучшенное определение колонок с проверкой наличия данных в каждой паре.
    """
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
        return None

    # Собираем все колонки с ключевыми словами
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

    # Если не нашли дебет/кредит, проверим следующую строку
    if not debit_cols or not credit_cols:
        if header_row + 1 < len(df):
            for idx, val in df.iloc[header_row + 1].items():
                if pd.notna(val):
                    val_str = str(val).lower()
                    if 'дебет' in val_str and idx not in debit_cols:
                        debit_cols.append(idx)
                    elif 'кредит' in val_str and idx not in credit_cols:
                        credit_cols.append(idx)

    # Если всё ещё не нашли, ищем по числам
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

    # Если есть несколько пар, проверяем наличие данных
    def has_data(date_idx, doc_idx, debit_idx, credit_idx):
        for i in range(header_row + 1, len(df)):
            row = df.iloc[i]
            if len(row) <= max(date_idx, doc_idx, debit_idx, credit_idx):
                continue
            dt = parse_date(row[date_idx])
            if dt is None:
                continue
            # Проверяем наличие числа хотя бы в одной из колонок дебета или кредита
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

    # Сортируем колонки
    date_cols.sort()
    doc_cols.sort()
    debit_cols.sort()
    credit_cols.sort()

    # Пробуем самую правую пару (последние элементы)
    if date_cols and doc_cols and debit_cols and credit_cols:
        # Правая пара
        d_idx = date_cols[-1]
        doc_idx = doc_cols[-1]
        deb_idx = debit_cols[-1]
        cred_idx = credit_cols[-1]
        if has_data(d_idx, doc_idx, deb_idx, cred_idx):
            return (index_to_letter(d_idx), index_to_letter(doc_idx),
                    index_to_letter(deb_idx), index_to_letter(cred_idx))
        # Левая пара (если есть)
        if len(date_cols) > 1:
            d_idx = date_cols[-2]
            doc_idx = doc_cols[-2]
            deb_idx = debit_cols[-2]
            cred_idx = credit_cols[-2]
            if has_data(d_idx, doc_idx, deb_idx, cred_idx):
                return (index_to_letter(d_idx), index_to_letter(doc_idx),
                        index_to_letter(deb_idx), index_to_letter(cred_idx))
        # Если ни одна не подходит, берём первую попавшуюся
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

# -------------------- Основная часть --------------------
if file1 and file2:
    df1 = pd.read_excel(file1, header=None)
    df2 = pd.read_excel(file2, header=None)

    # Показываем структуру
    st.subheader("Просмотр структуры файлов (первые 10 строк)")
    col_struct1, col_struct2 = st.columns(2)
    with col_struct1:
        st.write("Первый файл")
        st.dataframe(df1.head(10))
    with col_struct2:
        st.write("Второй файл")
        st.dataframe(df2.head(10))

    # Автоматическое определение
    detected1 = auto_detect_columns_letters(df1)
    detected2 = auto_detect_columns_letters(df2)

    # Если не удалось, используем fallback
    if detected1 is None:
        # Проверяем, есть ли две таблицы (по наличию фразы "По данным")
        has_two_tables = any('по данным' in str(cell).lower() for cell in df1.iloc[0:10, 0])
        if has_two_tables:
            date1_def, doc1_def, debit1_def, credit1_def = 'A', 'B', 'D', 'F'
        else:
            date1_def, doc1_def, debit1_def, credit1_def = 'A', 'B', 'G', 'H'
    else:
        date1_def, doc1_def, debit1_def, credit1_def = detected1

    if detected2 is None:
        has_two_tables = any('по данным' in str(cell).lower() for cell in df2.iloc[0:10, 0])
        if has_two_tables:
            date2_def, doc2_def, debit2_def, credit2_def = 'A', 'B', 'G', 'H'
        else:
            date2_def, doc2_def, debit2_def, credit2_def = 'A', 'B', 'G', 'H'
    else:
        date2_def, doc2_def, debit2_def, credit2_def = detected2

    st.info("Автоматически определены колонки. Если они неверны, измените буквы ниже и нажмите «Сравнить».")

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

        # Если в первом файле не найдено операций, пробуем альтернативные колонки (левая таблица)
        if len(ops1) == 0:
            # Пробуем левую таблицу для первого файла (A, B, D, F)
            ops1_alt = extract_ops(df1, letter_to_idx('A'), letter_to_idx('B'), letter_to_idx('D'), letter_to_idx('F'))
            if len(ops1_alt) > 0:
                ops1 = ops1_alt
                # Обновляем отображаемые буквы (чтобы пользователь видел)
                date1, doc1, debit1, credit1 = 'A', 'B', 'D', 'F'
                st.info("Для первого файла автоматически выбрана левая таблица (A, B, D, F).")

        # Если во втором файле не найдено операций, пробуем альтернативные колонки
        if len(ops2) == 0:
            # Пробуем стандартные колонки для второго файла (A, B, G, H)
            ops2_alt = extract_ops(df2, letter_to_idx('A'), letter_to_idx('B'), letter_to_idx('G'), letter_to_idx('H'))
            if len(ops2_alt) > 0:
                ops2 = ops2_alt
                date2, doc2, debit2, credit2 = 'A', 'B', 'G', 'H'
                st.info("Для второго файла автоматически выбраны колонки (A, B, G, H).")

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

        # Сравнение
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

        # Отдельно корректировки
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
