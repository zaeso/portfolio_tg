import sqlite3
from config import DATABASE  # Assuming you have a config.py file with DATABASE defined

skills = [(_,) for _ in (['Python', 'SQL', 'API', 'Telegram', 'Discord'])]
statuses = [(_,) for _ in (['На этапе проектирования', 'В процессе разработки', 'Разработан. Готов к использованию.', 'Обновлен', 'Завершен. Не поддерживается'])]

import sqlite3
from config import DATABASE  # Assuming you have a config.py file with DATABASE defined

skills = [(_,) for _ in (['Python', 'SQL', 'API', 'Telegram', 'Discord'])]
statuses = [(_,) for _ in (['На этапе проектирования', 'В процессе разработки', 'Разработан. Готов к использованию.', 'Обновлен', 'Завершен. Не поддерживается'])]

class DB_Manager:
    def __init__(self, database):
        self.database = database

    def create_tables(self):
        conn = sqlite3.connect(self.database)
        with conn:
            try:
                conn.execute('''CREATE TABLE projects (
                    project_id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    project_name TEXT NOT NULL,
                    description TEXT,
                    url TEXT,
                    status_id INTEGER,
                    photo TEXT,  -- Измените "#" на "--" 
                    FOREIGN KEY(status_id) REFERENCES status(status_id)
                )''')
                conn.execute('''CREATE TABLE skills (
                    skill_id INTEGER PRIMARY KEY,
                    skill_name TEXT
                )''')
                conn.execute('''CREATE TABLE project_skills (
                    project_id INTEGER,
                    skill_id INTEGER,
                    FOREIGN KEY(project_id) REFERENCES projects(project_id),
                    FOREIGN KEY(skill_id) REFERENCES skills(skill_id)
                )''')
                conn.execute('''CREATE TABLE status (
                    status_id INTEGER PRIMARY KEY,
                    status_name TEXT
                )''')
                print("База данных успешно создана.")
            except sqlite3.OperationalError as e:
                if "already exists" in str(e):
                    print("Таблицы уже существуют.")
                else:
                    print(f"Ошибка при создании таблиц: {e}")
        conn.commit()


    def __executemany(self, sql, data):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.executemany(sql, data)
        conn.commit()

    def __select_data(self, sql, data=tuple()):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute(sql, data)
            return cur.fetchall()

    def default_insert(self):
        sql = 'INSERT OR IGNORE INTO skills (skill_name) values(?)'
        data = skills
        self.__executemany(sql, data)

        sql = 'INSERT OR IGNORE INTO status (status_name) values(?)'
        data = statuses
        self.__executemany(sql, data)

    def insert_project(self, user_id, project_name, description, url, status_name, photo=None):
        status_id = self.get_status_id(status_name)
        data = [(user_id, project_name, description, url, status_id, photo)]
        sql = """INSERT INTO projects (user_id, project_name, description, url, status_id, photo) values(?, ?, ?, ?, ?, ?)"""
        self.__executemany(sql, data)

    def insert_skill(self, user_id, project_name, skill):
        project_id = self.get_project_id(project_name, user_id)
        skill_id = self.__select_data('SELECT skill_id FROM skills WHERE skill_name = ?', (skill,))[0][0]
        data = [(project_id, skill_id)]
        sql = 'INSERT OR IGNORE INTO project_skills VALUES(?, ?)'
        self.__executemany(sql, data)

    def get_statuses(self):
        sql = "SELECT status_name from status"
        return self.__select_data(sql)

    def get_status_id(self, status_name):
        sql = 'SELECT status_id FROM status WHERE status_name = ?'
        res = self.__select_data(sql, (status_name,))
        if res:
            return res[0][0]
        else:
            return None

    def get_projects(self, user_id):
        sql="""SELECT * FROM projects WHERE user_id = ?"""
        return self.__select_data(sql, data = (user_id,))

    def get_project_id(self, project_name, user_id):
        return self.__select_data(sql='SELECT project_id FROM projects WHERE project_name = ? AND user_id = ? ', data = (project_name, user_id,))[0][0]

    def get_skills(self):
        return self.__select_data(sql='SELECT * FROM skills')

    def get_project_skills(self, project_name):
        res = self.__select_data(sql='''SELECT skill_name FROM projects JOIN project_skills ON projects.project_id = project_skills.project_id JOIN skills ON skills.skill_id = project_skills.skill_id WHERE project_name = ?''', data = (project_name,) )
        return ', '.join([x[0] for x in res])

    def get_project_info(self, user_id, project_name):
        sql = """ SELECT project_name, description, url, status_name FROM projects JOIN status ON status.status_id = projects.status_id WHERE project_name=? AND user_id=? """
        return self.__select_data(sql=sql, data = (project_name, user_id))

    def update_projects(self, param, data):
        sql = f"""UPDATE projects SET {param} = ? WHERE project_name = ? AND user_id = ?"""
        self.__executemany(sql, [data])

    def delete_project(self, user_id, project_id):
        sql = """DELETE FROM projects WHERE user_id = ? AND project_id = ? """
        self.__executemany(sql, [(user_id, project_id)])

    def delete_skill(self, project_id, skill_id):
        sql = """DELETE FROM project_skills WHERE project_id = ? AND skill_id = ? """
        self.__executemany(sql, [(project_id, skill_id)])

    def update_skills(self, project_id, skill_name, new_skill_name):
        """Обновление навыков в таблице project_skills"""
        skill_id = self.__select_data('SELECT skill_id FROM skills WHERE skill_name = ?', (new_skill_name,))[0][0]
        sql = """UPDATE project_skills SET skill_id = ? WHERE project_id = ? AND skill_id = (SELECT skill_id FROM skills WHERE skill_name = ?)"""
        self.__executemany(sql, [(skill_id, project_id, skill_name)])

    def insert_new_skill(self, skill_name):
        """Добавление нового навыка в таблицу skills"""
        sql = """INSERT INTO skills (skill_name) VALUES (?)"""
        self.__executemany(sql, [(skill_name,)])

    def update_status(self, status_id, new_status_name):
        """Обновление статуса проекта"""
        sql = """UPDATE status SET status_name = ? WHERE status_id = ?"""
        self.__executemany(sql, [(new_status_name, status_id)])

    def delete_status(self, status_id):
        """Удаление статуса из таблицы status"""
        sql = """DELETE FROM status WHERE status_id = ?"""
        self.__executemany(sql, [(status_id,)])

    def add_photo_column(self):
        """Добавление столбца для фото в таблицу projects."""
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        try:
            alter_query = "ALTER TABLE projects ADD COLUMN photo TEXT"
            cursor.execute(alter_query)
            conn.commit()
            conn.close()
            print("Столбец 'photo' добавлен в таблицу 'projects'")
        except sqlite3.OperationalError as e:
            if "already exists" in str(e):
                print("Столбец 'photo' уже существует.")
            else:
                print(f"Ошибка при добавлении столбца: {e}")

if __name__ == '__main__':
    manager = DB_Manager(DATABASE)
    manager.create_tables()
    manager.add_photo_column()  
    manager.default_insert()
    
    
    manager.insert_project(user_id=2, project_name='bot_pokemon', description='Бот пакимогпокемон', url='https://github.com/zaeso/poke-om.git', status_name='Завершен', photo='C:/Users/Серёга/Desktop/bsdp/Снимок экрана (2766).png')  
    manager.insert_skill(user_id=2, project_name='bot_pokemon', skill='Telegram')

    manager.insert_project(user_id=2, project_name='bot_ai', description='AI bot', url='https://github.com/zaeso/bot_ai.git', status_name='Завершен', photo='Снимок экрана (2761).png')
    manager.insert_skill(user_id=2, project_name='bot_ai', skill='Python')
    manager.insert_skill(user_id=2, project_name='bot_ai', skill='Discord')

    manager.insert_project(user_id=2, project_name='бот эко', description='Bot ECO', url='https://github.com/zaeso/eco.git', status_name='Завершен', photo='C:/Users/Серёга/Desktop/bsdp/eco.png')
    manager.insert_skill(user_id=2, project_name='бот эко', skill='Api')
    manager.insert_skill(user_id=2, project_name='бот эко', skill='Python')
    manager.insert_skill(user_id=2, project_name='бот эко', skill='Discord')