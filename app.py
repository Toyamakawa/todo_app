import streamlit as st
import json
import os
from datetime import datetime

DATA_DIR = "data"


def get_data_file(user_id: str) -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, f"user_{user_id}.json")


def load_todos(user_id: str) -> list:
    path = get_data_file(user_id)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_todos(user_id: str, todos: list) -> None:
    path = get_data_file(user_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)


def login_page() -> None:
    st.set_page_config(page_title="ToDoアプリ ログイン", page_icon="✅", layout="centered")
    st.title("✅ ToDoアプリ")
    st.subheader("ユーザーコードを入力してください")
    st.info("ユーザーコードごとに専用のToDoリストが作成されます。\n同じコードを入力すると、前回のデータが表示されます。")

    with st.form("login_form"):
        user_id = st.text_input(
            "ユーザーコード",
            placeholder="例: 1234, abc, myname ...",
            max_chars=50,
        )
        submitted = st.form_submit_button("ログイン", use_container_width=True)

    if submitted:
        uid = user_id.strip()
        if not uid:
            st.error("ユーザーコードを入力してください。")
        else:
            st.session_state.user_id = uid
            st.session_state.todos = load_todos(uid)
            st.rerun()


def todo_page() -> None:
    user_id: str = st.session_state.user_id

    st.set_page_config(page_title="ToDoアプリ", page_icon="✅", layout="centered")

    col_title, col_logout = st.columns([4, 1])
    with col_title:
        st.title("✅ ToDoアプリ")
        st.caption(f"ユーザー: **{user_id}**")
    with col_logout:
        st.write("")
        if st.button("ログアウト", type="secondary"):
            del st.session_state.user_id
            del st.session_state.todos
            st.rerun()

    # --- タスク追加フォーム ---
    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            new_task = st.text_input("新しいタスク", placeholder="タスクを入力してください...")
        with col2:
            priority = st.selectbox("優先度", ["普通", "高", "低"])
        submitted = st.form_submit_button("追加", use_container_width=True)

        if submitted and new_task.strip():
            st.session_state.todos.append(
                {
                    "id": datetime.now().isoformat(),
                    "task": new_task.strip(),
                    "done": False,
                    "priority": priority,
                    "created_at": datetime.now().strftime("%Y/%m/%d %H:%M"),
                }
            )
            save_todos(user_id, st.session_state.todos)
            st.success(f"「{new_task.strip()}」を追加しました！")

    st.divider()

    # --- フィルター ---
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        status_filter = st.radio("表示", ["すべて", "未完了", "完了済み"], horizontal=True)
    with filter_col2:
        priority_filter = st.selectbox("優先度フィルター", ["すべて", "高", "普通", "低"])

    # --- タスク一覧 ---
    todos = st.session_state.todos

    filtered = [
        t for t in todos
        if (
            status_filter == "すべて"
            or (status_filter == "未完了" and not t["done"])
            or (status_filter == "完了済み" and t["done"])
        )
        and (priority_filter == "すべて" or t.get("priority", "普通") == priority_filter)
    ]

    priority_icon = {"高": "🔴", "普通": "🟡", "低": "🟢"}

    if not filtered:
        st.info("タスクがありません。")
    else:
        for todo in filtered:
            actual_idx = next(j for j, t in enumerate(todos) if t["id"] == todo["id"])
            cols = st.columns([0.5, 4, 1, 1])

            with cols[0]:
                done = st.checkbox("", value=todo["done"], key=f"done_{todo['id']}")
                if done != todo["done"]:
                    st.session_state.todos[actual_idx]["done"] = done
                    save_todos(user_id, st.session_state.todos)
                    st.rerun()

            with cols[1]:
                icon = priority_icon.get(todo.get("priority", "普通"), "🟡")
                label = f"~~{todo['task']}~~" if todo["done"] else todo["task"]
                st.markdown(f"{icon} {label}")
                st.caption(todo.get("created_at", ""))

            with cols[2]:
                new_priority = st.selectbox(
                    "",
                    ["高", "普通", "低"],
                    index=["高", "普通", "低"].index(todo.get("priority", "普通")),
                    key=f"pri_{todo['id']}",
                    label_visibility="collapsed",
                )
                if new_priority != todo.get("priority", "普通"):
                    st.session_state.todos[actual_idx]["priority"] = new_priority
                    save_todos(user_id, st.session_state.todos)
                    st.rerun()

            with cols[3]:
                if st.button("削除", key=f"del_{todo['id']}", type="secondary"):
                    st.session_state.todos.pop(actual_idx)
                    save_todos(user_id, st.session_state.todos)
                    st.rerun()

    # --- フッター統計 ---
    if todos:
        st.divider()
        total = len(todos)
        done_count = sum(1 for t in todos if t["done"])
        undone_count = total - done_count
        c1, c2, c3 = st.columns(3)
        c1.metric("合計", total)
        c2.metric("未完了", undone_count)
        c3.metric("完了済み", done_count)

        if undone_count == 0 and total > 0:
            st.balloons()
            st.success("すべてのタスクが完了しました！🎉")

        if done_count > 0:
            if st.button("完了済みをすべて削除", type="primary"):
                st.session_state.todos = [t for t in todos if not t["done"]]
                save_todos(user_id, st.session_state.todos)
                st.rerun()


def main() -> None:
    if "user_id" not in st.session_state:
        login_page()
    else:
        todo_page()


if __name__ == "__main__":
    main()
