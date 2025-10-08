#!/usr/bin/env python3
"""
Десктопное приложение для анализа жирнокислотного состава молока (PyQt6)
Конвертировано из Streamlit в PyQt6
"""

import os
import sys

# Принудительно устанавливаем платформу Qt
os.environ['QT_QPA_PLATFORM'] = 'xcb'
if sys.platform == 'darwin':
    os.environ['QT_QPA_PLATFORM'] = 'cocoa'

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import numpy as np
import matplotlib

matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from datetime import datetime
from database import DatabaseManager
from utils import validate_diet_ratios
from utils.constants import FATTY_ACID_NAMES, ingredient_names, nutrient_names
from preprocessing import (
    parse_pdf_diet,
    INGREDIENT_FEATURES,
    NUTRIENT_FEATURES,
    map_nutrients_to_features,
)
from parameters.model import MilkFattyAcidPredictor, create_sample_data


class MplCanvas(FigureCanvasQTAgg):
    """Холст matplotlib для встраивания графиков"""

    def __init__(self, parent=None, width=8, height=6, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.model = MilkFattyAcidPredictor()
        self.current_diet_data = {}
        self.current_analysis_data = {}

        self.setWindowTitle("Анализ жирнокислотного состава молока")
        self.setGeometry(100, 100, 1400, 900)

        # Хранилище для предсказаний и ID рациона
        self.current_predictions = {}
        self.current_diet_id = None

        self.init_ui()

    def init_ui(self):
        """Инициализация интерфейса"""
        # Главный виджет
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # Главный layout
        main_layout = QVBoxLayout(main_widget)

        # Заголовок
        title = QLabel("Анализ жирнокислотного состава молока")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # Вкладки
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Создание всех вкладок
        self.create_loading_tab()  # Переименовано из analysis_tab
        self.create_predictions_tab()
        self.create_results_tab()  # Переименовано из data_management_tab
        self.create_about_tab()

        # Статус бар
        self.statusBar().showMessage("Готов к работе")

    def create_loading_tab(self):
        """Вкладка загрузки данных"""
        tab = QWidget()
        self.tabs.addTab(tab, "Загрузка")

        layout = QHBoxLayout(tab)

        # Левая панель - ввод
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Загрузка файлов
        file_group = QGroupBox("Загрузка файлов")
        file_layout = QVBoxLayout()

        pdf_btn = QPushButton("Загрузить PDF файл")
        pdf_btn.clicked.connect(self.load_pdf)
        file_layout.addWidget(pdf_btn)

        file_group.setLayout(file_layout)
        left_layout.addWidget(file_group)

        # Ручной ввод
        manual_group = QGroupBox("Ручной ввод данных")
        manual_layout = QVBoxLayout()

        # Название рациона
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Название рациона:"))
        self.diet_name = QLineEdit("Пользовательский рацион")
        name_layout.addWidget(self.diet_name)
        manual_layout.addLayout(name_layout)

        # Ингредиенты рациона (% СВ - сухого вещества)
        ingr_group = QGroupBox("Ингредиенты рациона (% СВ)")
        ingr_scroll = QScrollArea()
        ingr_scroll.setWidgetResizable(True)
        ingr_widget = QWidget()
        ingr_layout = QGridLayout(ingr_widget)

        self.ingredient_inputs = {}
        ingredient_items = [(code, label, 0.0) for code, label in INGREDIENT_FEATURES]

        for i, (key, label, default) in enumerate(ingredient_items):
            row = i // 2
            col = (i % 2) * 2
            ingr_layout.addWidget(QLabel(f"{label} (% СВ):"), row, col)
            spin = QDoubleSpinBox()
            spin.setRange(0, 100)
            spin.setValue(default)
            spin.setSuffix(" %")
            spin.setMinimumWidth(120)
            spin.setMaximumWidth(150)
            self.ingredient_inputs[key] = spin
            ingr_layout.addWidget(spin, row, col + 1)

        ingr_scroll.setWidget(ingr_widget)
        ingr_scroll.setMinimumHeight(300)
        ingr_scroll.setMaximumHeight(400)

        ingr_group_layout = QVBoxLayout()
        ingr_group_layout.addWidget(ingr_scroll)
        ingr_group.setLayout(ingr_group_layout)
        manual_layout.addWidget(ingr_group)

        # Нутриенты (Value_i признаки)
        nutr_group = QGroupBox("Нутриенты (фичи модели)")
        nutr_layout = QGridLayout()

        self.nutrient_inputs = {}
        nutrient_items = [(feat, feat, 0.0) for feat in NUTRIENT_FEATURES]

        for i, (key, label, default) in enumerate(nutrient_items):
            nutr_layout.addWidget(QLabel(label + ":"), i, 0)
            spin = QDoubleSpinBox()
            spin.setRange(0, 10000)
            spin.setValue(default)
            self.nutrient_inputs[key] = spin
            nutr_layout.addWidget(spin, i, 1)

        nutr_group.setLayout(nutr_layout)
        manual_layout.addWidget(nutr_group)

        # Кнопка сохранения
        save_btn = QPushButton("Сохранить данные")
        save_btn.clicked.connect(self.save_loading_data)
        manual_layout.addWidget(save_btn)

        manual_group.setLayout(manual_layout)
        left_layout.addWidget(manual_group)

        left_layout.addStretch()
        layout.addWidget(left_panel, 1)

        # Правая панель - результаты парсинга
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Таблица результатов загрузки
        results_group = QGroupBox("Результаты загрузки")
        results_layout = QVBoxLayout()

        self.loading_table = QTableWidget()
        self.loading_table.setColumnCount(3)
        self.loading_table.setHorizontalHeaderLabels([
            'Параметр', 'Значение', 'Статус'
        ])
        self.loading_table.horizontalHeader().setStretchLastSection(True)
        results_layout.addWidget(self.loading_table)

        results_group.setLayout(results_layout)
        right_layout.addWidget(results_group)

        layout.addWidget(right_panel, 2)

    def create_predictions_tab(self):
        """Вкладка предсказаний"""
        tab = QWidget()
        self.tabs.addTab(tab, "Предсказания")

        layout = QVBoxLayout(tab)

        # Параметры
        params_group = QGroupBox("Параметры рациона")
        params_layout = QGridLayout()

        self.pred_inputs = {}
        diet_items = [("corn", "Кукуруза", 40.0), ("soybean", "Соя", 25.0),
                      ("alfalfa", "Люцерна", 25.0), ("other", "Прочее", 10.0)]

        for i, (key, label, default) in enumerate(diet_items):
            params_layout.addWidget(QLabel(label + " (%):"), i, 0)
            spin = QDoubleSpinBox()
            spin.setRange(0, 100)
            spin.setValue(default)
            spin.setSuffix("%")
            self.pred_inputs[key] = spin
            params_layout.addWidget(spin, i, 1)

        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        # Кнопка
        pred_btn = QPushButton("Сгенерировать предсказания")
        pred_btn.clicked.connect(self.generate_predictions)
        layout.addWidget(pred_btn)

        # Таблица предсказаний
        pred_group = QGroupBox("Результаты предсказаний")
        pred_layout = QVBoxLayout()

        self.pred_table = QTableWidget()
        self.pred_table.setColumnCount(3)
        self.pred_table.setHorizontalHeaderLabels([
            'Жирная кислота', 'Предсказанное значение (%)', 'Уверенность'
        ])
        self.pred_table.horizontalHeader().setStretchLastSection(True)
        pred_layout.addWidget(self.pred_table)

        pred_group.setLayout(pred_layout)
        layout.addWidget(pred_group)

    def create_results_tab(self):
        """Вкладка управления результатами"""
        tab = QWidget()
        self.tabs.addTab(tab, "Управление результатами")

        layout = QVBoxLayout(tab)

        # Кнопки
        btn_layout = QHBoxLayout()

        export_docx_btn = QPushButton("Экспорт в DOCX")
        export_docx_btn.clicked.connect(self.export_to_docx)
        btn_layout.addWidget(export_docx_btn)

        export_pdf_btn = QPushButton("Экспорт в PDF")
        export_pdf_btn.clicked.connect(self.export_to_pdf)
        btn_layout.addWidget(export_pdf_btn)

        print_btn = QPushButton("Печать")
        print_btn.clicked.connect(self.print_results)
        btn_layout.addWidget(print_btn)

        layout.addLayout(btn_layout)

        # Таблица результатов предсказаний
        results_group = QGroupBox("Результаты предсказаний")
        results_layout = QVBoxLayout()

        self.results_pred_table = QTableWidget()
        self.results_pred_table.setColumnCount(3)
        self.results_pred_table.setHorizontalHeaderLabels([
            'Жирная кислота', 'Значение (%)', 'Уверенность'
        ])
        self.results_pred_table.horizontalHeader().setStretchLastSection(True)
        results_layout.addWidget(self.results_pred_table)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        # График
        graph_group = QGroupBox("Графики")
        graph_layout = QVBoxLayout()

        # Кнопки для графиков
        graph_btn_layout = QHBoxLayout()
        dist_btn = QPushButton("Показать распределение")
        dist_btn.clicked.connect(self.show_distribution)
        graph_btn_layout.addWidget(dist_btn)

        trend_btn = QPushButton("Показать тренды")
        trend_btn.clicked.connect(self.show_trends)
        graph_btn_layout.addWidget(trend_btn)

        graph_layout.addLayout(graph_btn_layout)

        self.canvas = MplCanvas(self, width=10, height=6)
        graph_layout.addWidget(self.canvas)

        graph_group.setLayout(graph_layout)
        layout.addWidget(graph_group)

    def create_about_tab(self):
        """Вкладка о программе"""
        tab = QWidget()
        self.tabs.addTab(tab, "О программе")

        layout = QVBoxLayout(tab)

        # Информация
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setHtml("""
        <h2>Инструмент анализа жирнокислотного состава молока</h2>
        <p>Это приложение помогает анализировать и предсказывать жирнокислотный состав молока на основе параметров рациона.</p>
        <h3>Возможности:</h3>
        <ul>
            <li><b>Загрузка</b>: Загрузка Excel/PDF файлов или ручной ввод данных</li>
            <li><b>Предсказания</b>: Генерация предсказаний с использованием ML моделей</li>
            <li><b>Управление результатами</b>: Визуализация данных с интерактивными графиками, экспорт и печать</li>
        </ul>
        <h3>Технологический стек:</h3>
        <ul>
            <li><b>GUI</b>: PyQt6</li>
            <li><b>База данных</b>: SQLite</li>
            <li><b>Визуализация</b>: Matplotlib</li>
            <li><b>Обработка данных</b>: Pandas, NumPy</li>
        </ul>
        """)
        layout.addWidget(info_text)

        # Кнопка загрузки тестовых данных
        test_btn = QPushButton("Загрузить тестовые данные")
        test_btn.clicked.connect(self.load_test_data)
        layout.addWidget(test_btn)

    # Обработчики событий
    def load_pdf(self):
        """Загрузка PDF файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите PDF файл", "", "PDF files (*.pdf)"
        )
        if file_path:
            try:
                full_data = parse_pdf_diet(file_path)

                # Заполняем поля 4 группами
                for key, value in full_data['ratios'].items():
                    if key in self.pred_inputs:
                        self.pred_inputs[key].setValue(value)

                # Также в форму ингредиентов по кодам
                for code, value in full_data.get('ingredients_by_code', {}).items():
                    if code in self.ingredient_inputs:
                        self.ingredient_inputs[code].setValue(value)

                # Отображаем результаты парсинга
                self.display_loading_results(full_data, "PDF")

                # Валидация
                is_valid, message = validate_diet_ratios(full_data['ratios'])
                if not is_valid:
                    QMessageBox.warning(self, "Валидация", message)
                else:
                    QMessageBox.information(self, "Успех", "PDF файл успешно загружен!")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки: {str(e)}")

    def display_loading_results(self, data, file_type):
        """Отображение результатов парсинга"""
        try:
            # Для Excel (dict жирных кислот)
            if isinstance(data, dict) and 'lauric' in data:
                all_items = list(data.items())
            # Для PDF (полный dict из парсера)
            else:
                # Составляем таблицу: ингредиенты (имя->%), нутриенты (имя->знач), группы
                ingr_items = list(data['ingredients'].items())
                nutr_items = list(data['nutrients'].items())
                ratio_items = [(f"Группа: {k}", v) for k, v in data['ratios'].items()]
                all_items = ingr_items + nutr_items + ratio_items

            self.loading_table.setRowCount(len(all_items))

            # Объединяем названия жирных кислот и ингредиентов
            acid_names = FATTY_ACID_NAMES

            for row, (key, value) in enumerate(all_items):
                param_name = acid_names.get(key, key)
                self.loading_table.setItem(row, 0, QTableWidgetItem(param_name))
                self.loading_table.setItem(row, 1, QTableWidgetItem(f"{value:.2f}"))

                status = "OK" if value > 0 else "Нет данных"
                self.loading_table.setItem(row, 2, QTableWidgetItem(status))

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка отображения: {str(e)}")

    def save_loading_data(self):
        """Сохранение данных из вкладки загрузки"""
        try:
            # Сбор данных из ингредиентов и нутриентов
            self.current_diet_data = {k: v.value() for k, v in self.ingredient_inputs.items()}
            nutrients_data = {k: v.value() for k, v in self.nutrient_inputs.items()}

            # Валидация рациона
            is_valid, message = validate_diet_ratios(self.current_diet_data)
            if not is_valid:
                QMessageBox.warning(self, "Ошибка валидации", message)
                return

            # Сохранение рациона в БД (4 группы)
            # Преобразуем введённые кодовые ингредиенты -> группы через простую эвристику по label
            from preprocessing import feed_types, aggregate_ratios_from_codes
            entered_codes = {code: val for code, val in self.current_diet_data.items() if val > 0}
            ratios = aggregate_ratios_from_codes(entered_codes)
            diet_id = self.db.add_diet(
                name=self.diet_name.text(),
                corn_ratio=ratios.get('corn', 0.0),
                soybean_ratio=ratios.get('soybean', 0.0),
                alfalfa_ratio=ratios.get('alfalfa', 0.0),
                other_ratio=ratios.get('other', 0.0)
            )

            # Сохраняем diet_id для использования в предсказаниях
            self.current_diet_id = diet_id

            QMessageBox.information(self, "Успех",
                                    "Данные сохранены в БД! Теперь можете перейти в вкладку Предсказания.")
            self.statusBar().showMessage(f"Данные сохранены (ID рациона: {diet_id})")

            # Переключаемся на вкладку предсказаний
            self.tabs.setCurrentIndex(1)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения: {str(e)}")

    def generate_predictions(self):
        """Генерация предсказаний"""
        try:
            diet_ratios = {k: v.value() for k, v in self.pred_inputs.items()}

            is_valid, message = self.model.validate_input(diet_ratios)
            if not is_valid:
                QMessageBox.warning(self, "Ошибка валидации", message)
                return

            predictions = self.model.predict_fatty_acids(diet_ratios)
            self.current_predictions = predictions

            # Заполняем таблицу предсказаний
            self.pred_table.setRowCount(len(predictions))

            for row, (acid, value) in enumerate(predictions.items()):
                self.pred_table.setItem(row, 0, QTableWidgetItem(FATTY_ACID_NAMES.get(acid, acid)))
                self.pred_table.setItem(row, 1, QTableWidgetItem(f"{value:.2f}"))
                self.pred_table.setItem(row, 2, QTableWidgetItem(
                    "Высокая" if value > 0.1 else "Средняя"
                ))

            # Сохраняем предсказания в БД, если есть diet_id
            if self.current_diet_id:
                prediction_id = self.db.add_prediction(self.current_diet_id, predictions)
                self.statusBar().showMessage(f"Предсказания сгенерированы и сохранены (ID: {prediction_id})")
            else:
                # Если нет diet_id, создаем новый рацион
                diet_id = self.db.add_diet(
                    name=f"Рацион из предсказаний {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    corn_ratio=diet_ratios['corn'],
                    soybean_ratio=diet_ratios['soybean'],
                    alfalfa_ratio=diet_ratios['alfalfa'],
                    other_ratio=diet_ratios['other']
                )
                self.current_diet_id = diet_id
                prediction_id = self.db.add_prediction(diet_id, predictions)
                self.statusBar().showMessage(
                    f"Предсказания сгенерированы и сохранены (Diet ID: {diet_id}, Prediction ID: {prediction_id})")

            # Также обновляем таблицу результатов
            self.update_results_table()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка предсказаний: {str(e)}")

    def update_results_table(self):
        """Обновление таблицы результатов"""
        try:
            if not self.current_predictions:
                return

            self.results_pred_table.setRowCount(len(self.current_predictions))

            for row, (acid, value) in enumerate(self.current_predictions.items()):
                self.results_pred_table.setItem(row, 0, QTableWidgetItem(FATTY_ACID_NAMES.get(acid, acid)))
                self.results_pred_table.setItem(row, 1, QTableWidgetItem(f"{value:.2f}"))
                self.results_pred_table.setItem(row, 2, QTableWidgetItem(
                    "Высокая" if value > 0.1 else "Средняя"
                ))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка обновления: {str(e)}")

    def export_to_docx(self):
        """Экспорт результатов в DOCX"""
        try:
            if not self.current_predictions:
                QMessageBox.warning(self, "Предупреждение", "Сначала сгенерируйте предсказания!")
                return

            from docx import Document

            file_path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить как", "результаты.docx", "Word files (*.docx)"
            )

            if file_path:
                doc = Document()
                doc.add_heading('Результаты предсказания жирнокислотного состава', 0)

                table = doc.add_table(rows=1, cols=3)
                table.style = 'Light Grid Accent 1'
                hdr_cells = table.rows[0].cells
                hdr_cells[0].text = 'Жирная кислота'
                hdr_cells[1].text = 'Значение (%)'
                hdr_cells[2].text = 'Уверенность'

                for acid, value in self.current_predictions.items():
                    row_cells = table.add_row().cells
                    row_cells[0].text = FATTY_ACID_NAMES.get(acid, acid)
                    row_cells[1].text = f"{value:.2f}"
                    row_cells[2].text = "Высокая" if value > 0.1 else "Средняя"

                doc.save(file_path)
                QMessageBox.information(self, "Успех", f"Экспорт в DOCX завершен: {file_path}")

        except ImportError:
            QMessageBox.critical(self, "Ошибка", "Установите python-docx: pip install python-docx")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка экспорта: {str(e)}")

    def export_to_pdf(self):
        """Экспорт результатов в PDF"""
        try:
            if not self.current_predictions:
                QMessageBox.warning(self, "Предупреждение", "Сначала сгенерируйте предсказания!")
                return

            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
            from reportlab.lib.styles import getSampleStyleSheet

            file_path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить как", "результаты.pdf", "PDF files (*.pdf)"
            )

            if file_path:
                doc = SimpleDocTemplate(file_path, pagesize=letter)
                elements = []

                styles = getSampleStyleSheet()
                elements.append(Paragraph("Результаты предсказания жирнокислотного состава", styles['Title']))

                data = [['Жирная кислота', 'Значение (%)', 'Уверенность']]
                for acid, value in self.current_predictions.items():
                    data.append([
                        FATTY_ACID_NAMES.get(acid, acid),
                        f"{value:.2f}",
                        "Высокая" if value > 0.1 else "Средняя"
                    ])

                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))

                elements.append(table)
                doc.build(elements)

                QMessageBox.information(self, "Успех", f"Экспорт в PDF завершен: {file_path}")

        except ImportError:
            QMessageBox.critical(self, "Ошибка", "Установите reportlab: pip install reportlab")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка экспорта: {str(e)}")

    def print_results(self):
        """Печать результатов"""
        try:
            if not self.current_predictions:
                QMessageBox.warning(self, "Предупреждение", "Сначала сгенерируйте предсказания!")
                return

            from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
            from PyQt6.QtGui import QPainter

            printer = QPrinter()
            dialog = QPrintDialog(printer, self)

            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                painter = QPainter(printer)

                # Простая печать таблицы
                self.results_pred_table.render(painter)

                painter.end()
                QMessageBox.information(self, "Успех", "Печать завершена!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка печати: {str(e)}")

    def show_distribution(self):
        """Показать распределение"""
        try:
            diets = self.db.get_all_diets()
            all_analyses = []
            for diet in diets:
                analyses = self.db.get_analysis_for_diet(diet['id'])
                all_analyses.extend(analyses)

            if not all_analyses:
                self.canvas.axes.clear()
                self.canvas.axes.text(0.5, 0.5, 'Нет данных', ha='center', va='center')
                self.canvas.draw()
                return

            acids = ['lauric_acid', 'palmitic_acid', 'stearic_acid',
                     'oleic_acid', 'linoleic_acid', 'linolenic_acid']
            names = ['Лауриновая', 'Пальмитиновая', 'Стеариновая',
                     'Олеиновая', 'Линолевая', 'Линоленовая']

            data_means = []
            labels = []
            for acid, name in zip(acids, names):
                values = [a[acid] for a in all_analyses if a[acid]]
                if values:
                    data_means.append(np.mean(values))
                    labels.append(name)

            self.canvas.axes.clear()
            self.canvas.axes.bar(labels, data_means, alpha=0.7, color='steelblue')
            self.canvas.axes.set_xlabel('Жирные кислоты')
            self.canvas.axes.set_ylabel('Среднее значение (%)')
            self.canvas.axes.set_title('Распределение жирных кислот')
            self.canvas.axes.tick_params(axis='x', rotation=45)
            self.canvas.figure.tight_layout()
            self.canvas.draw()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка графика: {str(e)}")

    def show_trends(self):
        """Показать тренды"""
        self.canvas.axes.clear()
        self.canvas.axes.text(0.5, 0.5, 'Функция трендов в разработке',
                              ha='center', va='center', fontsize=14)
        self.canvas.draw()

    def load_test_data(self):
        """Загрузка тестовых данных"""
        try:
            sample_data = create_sample_data()
            for diet in sample_data['diets']:
                try:
                    self.db.add_diet(**diet)
                except:
                    pass
            QMessageBox.information(self, "Успех", "Тестовые данные загружены!")
            self.refresh_diets()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки: {str(e)}")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    main()