import sqlite3
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Tuple


class DatabaseManager:
    def __init__(self, db_path: str = "database/milk_analysis.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных с необходимыми таблицами"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Создание таблицы рационов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS diets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                corn_ratio REAL,
                soybean_ratio REAL,
                alfalfa_ratio REAL,
                other_ratio REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Создание таблицы анализа жирных кислот
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fatty_acid_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                diet_id INTEGER,
                lauric_acid REAL,
                palmitic_acid REAL,
                stearic_acid REAL,
                oleic_acid REAL,
                linoleic_acid REAL,
                linolenic_acid REAL,
                analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (diet_id) REFERENCES diets (id)
            )
        ''')
        
        # Создание таблицы предсказаний
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                diet_id INTEGER,
                predicted_lauric REAL,
                predicted_palmitic REAL,
                predicted_stearic REAL,
                predicted_oleic REAL,
                predicted_linoleic REAL,
                predicted_linolenic REAL,
                prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (diet_id) REFERENCES diets (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_diet(self, name: str, corn_ratio: float, soybean_ratio: float, 
                 alfalfa_ratio: float, other_ratio: float) -> int:
        """Добавление нового рациона в базу данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO diets (name, corn_ratio, soybean_ratio, alfalfa_ratio, other_ratio)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, corn_ratio, soybean_ratio, alfalfa_ratio, other_ratio))
        
        diet_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return diet_id
    
    def update_diet(self, diet_id: int, name: str, corn_ratio: float, 
                   soybean_ratio: float, alfalfa_ratio: float, other_ratio: float):
        """Обновление существующего рациона"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE diets 
            SET name = ?, corn_ratio = ?, soybean_ratio = ?, 
                alfalfa_ratio = ?, other_ratio = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (name, corn_ratio, soybean_ratio, alfalfa_ratio, other_ratio, diet_id))
        
        conn.commit()
        conn.close()
    
    def get_diet(self, diet_id: int) -> Optional[Dict]:
        """Получение конкретного рациона по ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM diets WHERE id = ?', (diet_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'name': result[1],
                'corn_ratio': result[2],
                'soybean_ratio': result[3],
                'alfalfa_ratio': result[4],
                'other_ratio': result[5],
                'created_at': result[6],
                'updated_at': result[7]
            }
        return None
    
    def get_all_diets(self) -> List[Dict]:
        """Получение всех рационов"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM diets ORDER BY created_at DESC')
        results = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'name': row[1],
            'corn_ratio': row[2],
            'soybean_ratio': row[3],
            'alfalfa_ratio': row[4],
            'other_ratio': row[5],
            'created_at': row[6],
            'updated_at': row[7]
        } for row in results]
    
    def add_fatty_acid_analysis(self, diet_id: int, lauric: float, palmitic: float,
                               stearic: float, oleic: float, linoleic: float = None,
                               linolenic: float = None) -> int:
        """Добавление результатов анализа жирных кислот"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO fatty_acid_analysis 
            (diet_id, lauric_acid, palmitic_acid, stearic_acid, oleic_acid, 
             linoleic_acid, linolenic_acid)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (diet_id, lauric, palmitic, stearic, oleic, linoleic, linolenic))
        
        analysis_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return analysis_id
    
    def add_prediction(self, diet_id: int, predicted_values: Dict) -> int:
        """Добавление результатов предсказания"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO predictions 
            (diet_id, predicted_lauric, predicted_palmitic, predicted_stearic,
             predicted_oleic, predicted_linoleic, predicted_linolenic)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (diet_id, predicted_values.get('lauric', 0), predicted_values.get('palmitic', 0),
              predicted_values.get('stearic', 0), predicted_values.get('oleic', 0),
              predicted_values.get('linoleic', 0), predicted_values.get('linolenic', 0)))
        
        prediction_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return prediction_id
    
    def get_predictions_for_diet(self, diet_id: int) -> List[Dict]:
        """Получение всех предсказаний для конкретного рациона"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM predictions WHERE diet_id = ? ORDER BY prediction_date DESC', (diet_id,))
        results = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'diet_id': row[1],
            'predicted_lauric': row[2],
            'predicted_palmitic': row[3],
            'predicted_stearic': row[4],
            'predicted_oleic': row[5],
            'predicted_linoleic': row[6],
            'predicted_linolenic': row[7],
            'prediction_date': row[8]
        } for row in results]
    
    def get_analysis_for_diet(self, diet_id: int) -> List[Dict]:
        """Получение всех результатов анализа для конкретного рациона"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM fatty_acid_analysis WHERE diet_id = ? ORDER BY analysis_date DESC', (diet_id,))
        results = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'diet_id': row[1],
            'lauric_acid': row[2],
            'palmitic_acid': row[3],
            'stearic_acid': row[4],
            'oleic_acid': row[5],
            'linoleic_acid': row[6],
            'linolenic_acid': row[7],
            'analysis_date': row[8]
        } for row in results]
    
    def delete_diet(self, diet_id: int):
        """Удаление рациона и всех связанных данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Сначала удалить связанные предсказания и анализы
        cursor.execute('DELETE FROM predictions WHERE diet_id = ?', (diet_id,))
        cursor.execute('DELETE FROM fatty_acid_analysis WHERE diet_id = ?', (diet_id,))
        cursor.execute('DELETE FROM diets WHERE id = ?', (diet_id,))
        
        conn.commit()
        conn.close()
