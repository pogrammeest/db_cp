-- ========== STRUCTURE ==========

DROP TABLE IF EXISTS task_comments, task_assignees, messages, chat_members, chats, tasks, projects, users, roles, user_profiles CASCADE;

CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE RESTRICT
);

CREATE TABLE user_profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    full_name VARCHAR(100),
    bio TEXT,
    avatar_url TEXT
);

CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'open',
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date DATE
);

CREATE TABLE task_assignees (
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (task_id, user_id)
);

CREATE TABLE task_comments (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE chats (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    is_private BOOLEAN DEFAULT FALSE,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE chat_members (
    chat_id INTEGER REFERENCES chats(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (chat_id, user_id)
);

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    chat_id INTEGER REFERENCES chats(id) ON DELETE CASCADE,
    sender_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========== DATA ==========

-- Роли
INSERT INTO roles (name) VALUES
    ('admin'),
    ('manager'),
    ('user');

-- Пользователи
INSERT INTO users (username, email, password_hash, role_id) VALUES
    ('admin', 'admin@example.com', 'hashed_pwd_1', 1),
    ('alice', 'alice@example.com', 'hashed_pwd_2', 2),
    ('bob', 'bob@example.com', 'hashed_pwd_3', 3),
    ('carol', 'carol@example.com', 'hashed_pwd_4', 3);

-- Профили
INSERT INTO user_profiles (user_id, full_name, bio, avatar_url) VALUES
    (1, 'Admin User', 'System administrator', NULL),
    (2, 'Alice Manager', 'Project manager', NULL),
    (3, 'Bob Dev', 'Backend developer', NULL),
    (4, 'Carol QA', 'Quality assurance', NULL);

-- Проекты
INSERT INTO projects (name, description, created_by) VALUES
    ('Tracker Core', 'Internal task tracker platform', 1),
    ('Website Redesign', 'Marketing site revamp', 2);

-- Задачи
INSERT INTO tasks (title, description, status, project_id, created_by, due_date) VALUES
    ('Setup PostgreSQL DB', 'Create schema for task tracker', 'in_progress', 1, 3, '2025-07-20'),
    ('Design Landing Page', 'Create new layout in Figma', 'open', 2, 4, '2025-07-15'),
    ('Implement Auth', 'JWT and roles', 'open', 1, 3, '2025-07-25');

-- Назначение задач
INSERT INTO task_assignees (task_id, user_id) VALUES
    (1, 3), -- Bob
    (2, 4), -- Carol
    (3, 3),
    (3, 4); -- совместная задача

-- Комментарии
INSERT INTO task_comments (task_id, user_id, message) VALUES
    (1, 3, 'Создал таблицы и связи.'),
    (2, 4, 'Начала работу над прототипом.'),
    (3, 3, 'Добавлю авторизацию через JWT сегодня.');

-- Чаты
INSERT INTO chats (name, is_private, created_by) VALUES
    ('General Chat', FALSE, 1),
    ('Dev Team', TRUE, 3),
    ('QA Room', TRUE, 4);

-- Участники чатов
INSERT INTO chat_members (chat_id, user_id) VALUES
    (1, 1), (1, 2), (1, 3), (1, 4),
    (2, 1), (2, 3),
    (3, 1), (3, 4);

-- Сообщения
INSERT INTO messages (chat_id, sender_id, content) VALUES
    (1, 1, 'Добро пожаловать в систему!'),
    (1, 2, 'Рада присоединиться!'),
    (2, 3, 'Работаю над базой данных.'),
    (3, 4, 'Тестирование интерфейса начну завтра.');
