"""Интерфейс истории и помощника по несопоставленным операциям."""

from collections import Counter, defaultdict
from datetime import datetime
import logging
import re
import sqlite3

import streamlit as st

from sverka_history import REVIEW_STATES


logger = logging.getLogger(__name__)


def rubles(amount):
    return f"{amount:,.2f}".replace(",", "\u202f").replace(".", ",") + " ₽"


def location(operation):
    if operation.get("page") is not None:
        return f"стр. {operation['page']}, строка текста {operation['line']}"
    if operation.get("row") is not None:
        return f"строка {operation['row']}"
    return f"операция №{operation['source_index'] + 1}"


def document_numbers(text):
    without_dates = re.sub(r"\b(?:\d{2}\.\d{2}\.\d{2,4}|\d{4}-\d{2}-\d{2})\b", " ", text.upper())
    token = r"[А-ЯЁA-Z0-9]+(?:[-/][А-ЯЁA-Z0-9]+)*"
    annotated = re.findall(rf"(?:№|\bНОМЕР\b|\bN\b|\()\s*({token})", without_dates)
    marked = {number for number in annotated if any(char.isdigit() for char in number)}
    if marked:
        return marked
    return set(re.findall(r"(?<![\w.,])[А-ЯЁA-Z]{0,4}[-/]?\d{2,}(?![\w.,])", without_dates))


def format_time(iso_time):
    return datetime.fromisoformat(iso_time).astimezone().strftime("%d.%m.%Y, %H:%M")


def render_history(records, open_review):
    st.header("Мои сверки")
    tabs = st.tabs(["В работе", "Завершённые"])
    for completed, tab in zip((False, True), tabs):
        with tab:
            group = [record for record in records if bool(record["closed_at"]) == completed]
            if not group:
                st.caption("Нет завершённых сверок." if completed else "Нет сверок в работе.")
            for record in group:
                record_id = record["id"]
                with st.container(border=True):
                    details, action = st.columns([4, 1])
                    with details:
                        badge = "Проверено" if completed else "Нужны документы" if record["requested"] else "В работе"
                        st.markdown(f"**Сверка №{record_id} · {badge}**")
                        st.text(f"{record['first_file']} ↔ {record['second_file']}")
                        st.caption(f"Период операций: {record['period']} · Создана {format_time(record['created_at'])}")
                        st.caption(
                            f"К проверке: {record['pending']} · Проверено: {record['checked']} · "
                            f"Запросить документ: {record['requested']}"
                        )
                    with action:
                        st.button("Посмотреть" if completed else "Продолжить", key=f"open-review-{record_id}",
                                  on_click=open_review, args=(record_id,), width="stretch")


def save_mark(store, record_id, case_id, widget):
    try:
        if not store.mark(record_id, case_id, st.session_state[widget]):
            st.session_state["review_notice"] = "Не удалось изменить отметку. Возможно, сверку уже завершили."
    except (sqlite3.Error, ValueError):
        logger.exception("Не удалось сохранить отметку по сверке %s", record_id)
        st.session_state["review_notice"] = "Не удалось сохранить отметку. Попробуйте ещё раз."


def source_details(act, operation, files):
    st.markdown(f"**Акт {act} · {location(operation)}**")
    st.text(files[act - 1])
    st.text(operation["raw_doc"] or "Название не распознано")
    st.caption(f"{operation['date']:%d.%m.%Y} · {rubles(operation['amount'])}")


def render_assistant(record, store, category):
    result = record["result"]
    record_id = record["id"]
    operations = [{op["source_index"]: op for op in group} for group in result["ops"]]
    cases = [(act, index) for act, indices in enumerate(result["only"], start=1) for index in indices]
    status = record["marks"]
    st.subheader("Помощник по расхождениям")
    if notice := st.session_state.pop("review_notice", None):
        st.warning(notice)
    if not cases:
        st.success("Строк без пары нет. Сверку можно завершить.")
        return

    counts = Counter(status.values())
    st.caption(f"К проверке: {counts['pending']} · Проверено: {counts['checked']} · Запросить документ: {counts['request']}")
    by_number = [defaultdict(set), defaultdict(set)]
    for act, group in enumerate(operations):
        for index, op in group.items():
            for number in document_numbers(op["raw_doc"]):
                by_number[act][number].add(index)
    paired = [dict(result["pairs"]), {right: left for left, right in result["pairs"]}]
    periods = [(min(op["date"] for op in group.values()), max(op["date"] for op in group.values()))
               for group in operations]

    page_size = 10
    pages = (len(cases) + page_size - 1) // page_size
    page = st.selectbox("Страница разбора", range(1, pages + 1), key=f"review-page-{record_id}") if pages > 1 else 1
    for act, index in cases[(page - 1) * page_size:page * page_size]:
        op = operations[act - 1][index]
        case_id = f"{act}:{index}"
        other_act = 3 - act
        other = operations[other_act - 1]
        numbers = document_numbers(op["raw_doc"])
        found = set().union(*(by_number[other_act - 1].get(number, set()) for number in numbers))
        ranked = sorted(found, key=lambda i: (category(op["doc"]) != category(other[i]["doc"]),
                                               abs((op["date"] - other[i]["date"]).days),
                                               abs(op["amount"] - other[i]["amount"]), i))
        with st.container(border=True):
            context, controls = st.columns([3, 2])
            with context:
                st.text(op["raw_doc"] or "Документ без названия")
                st.caption(f"Акт {act} · {location(op)} · {op['date']:%d.%m.%Y} · {rubles(op['amount'])}")
                if ranked:
                    candidate = other[ranked[0]]
                    diff = rubles(abs(candidate["amount"] - op["amount"]))
                    st.write(f"Совпадения по номеру в акте {other_act}: {len(ranked)}. Разница с первым кандидатом: {diff}.")
                    if ranked[0] in paired[other_act - 1]:
                        st.write("Кандидат уже сопоставлен. Сверьте обе записи и текущую пару по первичным документам.")
                    else:
                        st.write("Сверьте дату, сумму и тип операции по первичному документу.")
                elif not numbers:
                    st.write("Номер не удалось извлечь. Проверьте название документа по исходной строке.")
                elif not periods[other_act - 1][0] <= op["date"] <= periods[other_act - 1][1]:
                    st.write(f"Номер в акте {other_act} не найден. Дата за пределами дат прочитанных операций в нём. Проверьте период выгрузки.")
                else:
                    st.write(f"Номер в акте {other_act} не найден. Проверьте оригинал документа или запросите копию.")
            with controls:
                if record["closed_at"]:
                    st.caption(f"Статус: {REVIEW_STATES[status[case_id]]}")
                else:
                    widget = f"review-mark-{record_id}-{case_id}"
                    st.session_state[widget] = status[case_id]
                    st.selectbox(
                        "Статус проверки", list(REVIEW_STATES), format_func=REVIEW_STATES.__getitem__,
                        key=widget, on_change=save_mark, args=(store, record_id, case_id, widget),
                    )
            with st.expander(f"Показать исходные строки · акт {act}, {location(op)}"):
                if not ranked:
                    source_details(act, op, result["files"])
                    continue
                def candidate_label(source):
                    candidate = other[source]
                    return f"{location(candidate)} · {candidate['raw_doc']} · {rubles(candidate['amount'])}"
                selected = ranked[0] if len(ranked) == 1 else st.selectbox(
                    f"Кандидат из акта {other_act}", ranked, format_func=candidate_label,
                    key=f"candidate-{record_id}-{case_id}",
                )
                left, right = st.columns(2)
                for panel, side, row in ((left, act, op), (right, other_act, other[selected])):
                    with panel:
                        source_details(side, row, result["files"])
                active_pair = paired[other_act - 1].get(selected)
                if active_pair is not None:
                    pair = operations[act - 1][active_pair]
                    st.caption(f"Текущая пара кандидата: акт {act}, {location(pair)}")
                    st.text(pair["raw_doc"])
