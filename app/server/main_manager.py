import sqlite3
from datetime import datetime
from pathlib import Path
import json

# from app.server.utills.utills import log
# from app.server.search.search import
from openai import OpenAI
from markdown import markdown
from dotenv import load_dotenv
import os
import pytz

now = datetime.now(pytz.timezone("Asia/Kolkata"))

load_dotenv()


BASE_DIR = Path(__file__).resolve().parent


class GenMan:
    def __init__(
        self,
        think=False,
        search=False,
        session=None,
        user_input="",
        file_path="",
        model="gemini-2.5-flash",
    ):
        self.think = think
        self.search = search  # fixed typo too
        self.session = (
            session if session else f"S{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        )
        self.user_input = user_input
        self.file_path = file_path
        self.model = model

        self.api_key = "AIzaSyCfioIDHSTocnfXPXwvAdtoECBxXotGIsQ"

        self.database = BASE_DIR.parent / "data" / "database.db"
        self.session_info = BASE_DIR.parent / "data" / "session_info.db"

        self.now = datetime.now()

        # self.result = {}

        self.system_instructions = f"""
        ## Informations
        Current date: {now.strftime("%A, %B %d, %Y")},
        Current time: {now.strftime("%I:%M %p")} IST (UTC+5:30)
        Think: {'Enabled' if think else 'Disabled'}
        Search: {'Enabled' if search else 'Disabled'}

        ## Rules
        1. If the user's query requires real-time information, news, dates, scores, or events from this month, but 'Live Search: Disabled' is active, you MUST NOT guess or hallucinate. 
    - Instead, stop immediately and output a clean message asking the user to enable the **Search** toggle so can provide latest updates based on internet, because you don't have access to searching agents until user enable **search** mode.
        2. If the user's query requires complex calculation, coding logic, deep reasoning, or debugging, but 'Think Mode: Disabled' is active:
        - Output a clean message asking the user to enable the **Think** toggle for a better response so you can think in more detail about query.
        3. Keep the request polite, concise, and professional. Do not add any other placeholder conversational text."""

    def get_db(self, path):
        connect = sqlite3.connect(path, timeout=10)
        connect.execute("PRAGMA journal_mode=WAL")  # allows concurrent reads
        return connect

    def check_session(self):
        from server import session_name_gen

        """
        it checks session exist or not, and create one and save its info.
        """

        # session_exists = None
        # from server import send.mode
        # check session table exist is True or False
        connect = connect = self.get_db(self.database)
        cursor = connect.cursor()

        result = {}

        cursor.execute(f"PRAGMA table_info({self.session})")
        exist = cursor.fetchone()
        connect.close()

        if not exist:
            connect = connect = self.get_db(self.database)
            cursor = connect.cursor()

            # if False, create session table
            cursor.execute(f"""
                CREATE TABLE {self.session} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role VARCHAR(10),
                    content TEXT,
                    thought TEXT,
                    source TEXT
                )
                """)

            connect.commit()
            connect.close()

            # save session info
            connect = sqlite3.connect(self.session_info)
            cursor = connect.cursor()

            session_name = session_name_gen(self.user_input)

            cursor.execute(
                "INSERT INTO info (session_id, session_name, date_created, date_last_commit) VALUES(?,?,?,?)",
                (self.session, session_name, f"{self.now}", f"{self.now}"),
            )

            connect.commit()
            connect.close()

            print("creating new session")

            result["new_session"] = {
                "session_name": session_name,
                "session_id": self.session,
            }

        result["session_exist"] = bool(exist)

        result["results"] = {"session_id": self.session}

        # self.save_into_session("model", model_response(messages = self.load_contents(), think=self.think, search = self.search))

        return result

    def load_contents(self):
        # save user input
        # self.save_into_session("user", {'response':self.user_input, 'thought':""})

        contents_list = [
            {"role": "system", "content": self.system_instructions},
        ]

        connect = connect = self.get_db(self.database)
        cursor = connect.cursor()

        cursor.execute(f"SELECT * FROM {self.session}")

        rows = cursor.fetchall()

        connect.commit()
        connect.close()

        for row in rows:
            role = row[1]

            parts = row[2]

            new_part = {"role": role, "content": parts}

            contents_list.append(new_part)

        return contents_list

    def save_into_session(self, data):

        connect = connect = self.get_db(self.database)
        cursor = connect.cursor()

        cursor.execute(
            f"INSERT INTO {self.session} (role, content, thought, source) VALUES(?,?,?,?)",
            (data["role"], data["content"], data["thought"], data["sources"]),
        )

        connect.commit()
        connect.close()

        connect = sqlite3.connect(self.session_info)
        cursor = connect.cursor()

        cursor.execute(
            f"UPDATE info SET date_last_commit = ? WHERE session_id = ?",
            (f"{self.now}", self.session),
        )

        connect.commit()
        connect.close()

    def all_session(self):
        session_pairs = {}

        connect = connect = self.get_db(self.database)
        cursor = connect.cursor()

        cursor.execute("SELECT name FROM sqlite_schema WHERE type = 'table'")

        rows = cursor.fetchall()

        connect.commit()
        connect.close()

        # get corresponding name
        connect = sqlite3.connect(self.session_info)
        cursor = connect.cursor()

        cursor.execute("SELECT * FROM info")

        rowws = cursor.fetchall()

        connect.commit()
        connect.close()

        for row in rows:
            for roww in rowws:
                if row[0] == roww[0]:
                    session_pairs[row[0]] = {
                        "id": roww[0],
                        "session_name": roww[1],
                        "date_created": roww[2],
                        "date_last_commit": roww[3],
                    }

        # just for curiosity!
        # with open("test/t.json", 'w') as file:
        #     json.dump(session_pairs, file)

        return session_pairs


# Gen(user_input="what is birds? in 10 words").check_session()
# Gen(user_input="what is fox? in 10 words", think=True, search=False).check_session()
# Gen(user_input="what is fireFox? in 10 words", think=True).check_session()
# Gen(user_input="what is dart? in 10 words", think=True).check_session()
# Gen(user_input="what is python rehex? in 10 words", think=True).check_session()


class Man(GenMan):
    def __init__(self, session):
        super().__init__(session=session)
        self.session = session
        self.session_conversation = {}

    def load_conversation(self):
        contents_list = []

        connect = connect = self.get_db(self.database)
        cursor = connect.cursor()

        cursor.execute(f"SELECT * FROM {self.session}")

        rows = cursor.fetchall()

        connect.commit()
        connect.close()

        for row in rows:
            id = row[0]

            role = row[1]

            content = row[2]

            thought = row[3]

            source = row[4]

            new_part = {
                "id": id,
                "role": role,
                "content": content,
                "thought": thought,
                "source": source,
            }

            contents_list.append(new_part)

        self.session_conversation[f"{self.session}"] = contents_list
        return self.session_conversation


# with open("w.json", 'w') as file:
#     json.dump(Man(session='S20260517030614927216').load_conversation(), file)


# Gen(session ='S20260516044027833344',user_input="how many color they have?", think=True, search=False).check_session()
