-- Створення таблиць в Supabase

-- Таблиця модулів (наборів слів)
CREATE TABLE modules (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    source_language VARCHAR(50),
    target_language VARCHAR(50),
    category VARCHAR(100),
    class VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Індекс для швидкого пошуку публічних модулів
CREATE INDEX idx_modules_public ON modules(is_public, source_language, target_language, category);
CREATE INDEX idx_modules_user ON modules(user_id);

-- Таблиця слів
CREATE TABLE words (
    id BIGSERIAL PRIMARY KEY,
    module_id BIGINT REFERENCES modules(id) ON DELETE CASCADE,
    word TEXT NOT NULL,
    translation TEXT NOT NULL,
    example TEXT,
    position INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_words_module ON words(module_id);

-- Таблиця прогресу користувача
CREATE TABLE user_progress (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    module_id BIGINT REFERENCES modules(id) ON DELETE CASCADE,
    word_id BIGINT REFERENCES words(id) ON DELETE CASCADE,
    status VARCHAR(20) CHECK (status IN ('new', 'learning', 'learned')) DEFAULT 'new',
    last_reviewed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    review_count INTEGER DEFAULT 0,
    UNIQUE(user_id, module_id, word_id)
);

CREATE INDEX idx_user_progress_user ON user_progress(user_id, module_id);

-- Таблиця прогресу навчання
CREATE TABLE learning_progress (
    user_id BIGINT NOT NULL,
    module_id BIGINT REFERENCES modules(id) ON DELETE CASCADE,
    current_batch INTEGER DEFAULT 0,
    current_word_index INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, module_id)
);

-- Таблиця бібліотеки користувача (додані публічні модулі)
CREATE TABLE user_library (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    module_id BIGINT REFERENCES modules(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, module_id)
);

CREATE INDEX idx_user_library_user ON user_library(user_id);

-- Таблиця посилань на додавання модулів
CREATE TABLE module_invites (
    id BIGSERIAL PRIMARY KEY,
    module_id BIGINT REFERENCES modules(id) ON DELETE CASCADE,
    invite_code VARCHAR(50) UNIQUE NOT NULL,
    created_by BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    max_uses INTEGER,
    uses_count INTEGER DEFAULT 0
);

CREATE INDEX idx_module_invites_code ON module_invites(invite_code);

-- Таблиця для розсилок
CREATE TABLE broadcasts (
    id BIGSERIAL PRIMARY KEY,
    admin_id BIGINT NOT NULL,
    message_text TEXT NOT NULL,
    image_url TEXT,
    button_text VARCHAR(100),
    button_url TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    recipients_count INTEGER DEFAULT 0
);

-- Функція для оновлення updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Тригери для автоматичного оновлення
CREATE TRIGGER update_modules_updated_at 
    BEFORE UPDATE ON modules 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_learning_progress_updated_at 
    BEFORE UPDATE ON learning_progress 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ВИПРАВЛЕНІ RLS Політики безпеки (без auth.uid())
ALTER TABLE modules ENABLE ROW LEVEL SECURITY;
ALTER TABLE words ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_library ENABLE ROW LEVEL SECURITY;
ALTER TABLE module_invites ENABLE ROW LEVEL SECURITY;
ALTER TABLE broadcasts ENABLE ROW LEVEL SECURITY;

-- Політики для modules (публічний доступ для читання публічних модулів)
CREATE POLICY "Всі можуть бачити публічні модулі" ON modules
    FOR SELECT USING (is_public = true);

-- Політики для words (публічний доступ до слів публічних модулів)
CREATE POLICY "Всі можуть бачити слова публічних модулів" ON words
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM modules 
            WHERE modules.id = words.module_id 
            AND modules.is_public = true
        )
    );

-- Політики для module_invites (публічний доступ)
CREATE POLICY "Всі можуть переглядати запрошення" ON module_invites
    FOR SELECT USING (true);

-- Примітка: Оскільки ми використовуємо Telegram ID, а не Supabase Auth,
-- ми не використовуємо RLS для обмеження запису/оновлення/видалення.
-- Натомість, перевірка прав доступу буде виконуватись на рівні додатку
-- через перевірку user_id в запитах.

-- Додаємо політики для модифікації даних (дозволяємо всі операції через API ключ)
CREATE POLICY "API може створювати модулі" ON modules
    FOR INSERT WITH CHECK (true);

CREATE POLICY "API може оновлювати модулі" ON modules
    FOR UPDATE USING (true);

CREATE POLICY "API може видаляти модулі" ON modules
    FOR DELETE USING (true);

CREATE POLICY "API може додавати слова" ON words
    FOR INSERT WITH CHECK (true);

CREATE POLICY "API може оновлювати слова" ON words
    FOR UPDATE USING (true);

CREATE POLICY "API може видаляти слова" ON words
    FOR DELETE USING (true);

CREATE POLICY "API може змінювати прогрес" ON user_progress
    FOR ALL USING (true);

CREATE POLICY "API може змінювати прогрес навчання" ON learning_progress
    FOR ALL USING (true);

CREATE POLICY "API може змінювати бібліотеку" ON user_library
    FOR ALL USING (true);

CREATE POLICY "API може створювати запрошення" ON module_invites
    FOR INSERT WITH CHECK (true);

CREATE POLICY "API може змінювати запрошення" ON module_invites
    FOR UPDATE USING (true);

CREATE POLICY "API може створювати розсилки" ON broadcasts
    FOR ALL USING (true);