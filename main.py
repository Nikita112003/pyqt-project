import datetime as dt
import sqlite3
import sys
from PyQt5.QtCore import Qt, QTimer
from PyQt5 import QtGui
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import *
from main_interface import Ui_MainWindow
from add_city import Ui_Dialog as add_city_window
from set_alarm import Ui_Dialog as set_alarm_clock_window
from set_timer import Ui_Dialog as set_timer_window

DAYS_LIST = ['понедельник', 'вторник', 'среда', 'четверг',
             'пятница', 'суббота', 'воскресенье']
CITIES = {
    ('Остров Бейкер (США)', 'Остров Хауленд (США)'): dt.timedelta(hours=-15),
    ('Американское Самоа (США)',): dt.timedelta(hours=-14),
    ('Гавайи (США)',): dt.timedelta(hours=-13),
    ('Джуно (США)',): dt.timedelta(hours=-12),
    ('Сан-Франциско (США)', 'Лос-Анджелес (США)'): dt.timedelta(hours=-11),
    ('Денвер (США)',): dt.timedelta(hours=-10),
    ('Виннипег (Канада)', 'Чикаго (США)', 'Мехико (Мексика)'): dt.timedelta(hours=-9),
    ('Оттава (Канада)', 'Нью-Йорк (США)', 'Майами (США)',
     'Богота (Колумбия)', 'Лима (Перу)'): dt.timedelta(hours=-8),
    ('Каракас (Венесуэла)', 'Ла-Пас (Боливия)', 'Сантьяго (Чили)'): dt.timedelta(hours=-7),
    ('Гренландия (Дания)', 'Рио-де-Жанейро (Бразилия)', 'Буэнос-Айрес (Аргентина)'):
        dt.timedelta(hours=-6),
    ('Лондон (Великобритания)', 'Лиссабон (Португалия)',
     'Алжир (Алжир)', 'Монровия (Либерия)'): dt.timedelta(hours=-3),
    ('Париж (Франция)', 'Рим (Италия)', 'Лагос (Нигерия)', 'Киншаса (ДРК)'): dt.timedelta(hours=-2),
    ('Калиниград (Россия)', 'Хельсинки (Финляндия)',
     'Каир (Египет)', 'Кейптаун (ЮАР)'): dt.timedelta(hours=-1),
    ('Москва (Россия)', 'Анкара (Турция)', 'Аддис-Абеба (Эфиопия)'): dt.timedelta(hours=0),
    ('Самара (Россия)', 'Маврикий', 'Реюньон (Франция)'): dt.timedelta(hours=1),
    ('Екатеринбург (Россия)', 'Бишкек (Киргизия)', 'Кергелен (Франция)'): dt.timedelta(hours=2),
    ('Нью-Дели',): dt.timedelta(hours=2, minutes=30),
    ('Омск (Россия)',): dt.timedelta(hours=3),
    ('Красноярск (Россия)', 'Бангкок (Таиланд)', 'Джакарта (Индонезия)'): dt.timedelta(hours=4),
    ('Иркутск (Россия)', 'Пекин (Китай)', 'Манила (Филиппины)',
     'Перт (Австралия)'): dt.timedelta(hours=5),
    ('Якутск (Россия)', 'Токио (Япония)'): dt.timedelta(hours=6),
    ('Владивосток (Россия)', 'Сидней (Австралия)', 'Мельбурн (австралия)'): dt.timedelta(hours=7),
    ('Магадан (Россия)',): dt.timedelta(hours=9),
    ('Петропавловск-Камчатский (Россия)', 'Фиджи', 'Веллингтон (Новая Зеландия)'):
        dt.timedelta(hours=10),
    ('Острова Феникс (Кирибати)',): dt.timedelta(hours=11),
    ('Остров Рождества (Кирибати)',): dt.timedelta(hours=12)

}


class AlarmClock:
    def __init__(self, hours, minutes, days, active=True):
        self.hours = hours
        self.minutes = minutes
        self.days = [n for n, day in enumerate(days) if day]
        self.active = active

    def is_active(self):
        if self.active:
            return 'Включен'
        return 'Выключен'

    def is_time_to_ring(self):
        now = dt.datetime.now()
        return self.active and now.time().hour == self.hours and \
            now.time().minute == self.minutes and now.date().weekday() in self.days

    def on_off(self):
        self.active = not self.active

    def str_days(self):
        days = [DAYS_LIST[n] for n in self.days]
        return ', '.join(days).capitalize()


class MainWidget(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWidget, self).__init__()
        self.setupUi(self)
        self.secondWindow = None
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('icon.ico'))

        self.alarm_clocks = []
        self.timer_messages = ''

        self.alarm_clocks_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cities_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.laps_table.setEditTriggers(QTableWidget.NoEditTriggers)

        # loading settings
        self.con = sqlite3.connect('settings.db')
        self.cur = self.con.cursor()
        try:
            self.cur.execute('SELECT * FROM cities')
        except sqlite3.OperationalError:
            self.cur.execute('''CREATE TABLE cities (
    id   INTEGER PRIMARY KEY AUTOINCREMENT
                 UNIQUE
                 NOT NULL,
    city TEXT    NOT NULL
);''')
            self.con.commit()
        else:
            result = self.cur.execute('SELECT city FROM cities').fetchall()
            for city in result:
                self.add_city(city[0])

        try:
            self.cur.execute('SELECT * FROM alarm_clocks;')
        except sqlite3.OperationalError:
            self.cur.execute('''CREATE TABLE alarm_clocks (
    id     INTEGER PRIMARY KEY AUTOINCREMENT
                   UNIQUE
                   NOT NULL,
    time  TEXT    NOT NULL,
    days   TEXT    NOT NULL,
    active BOOLEAN NOT NULL
);''')
            self.con.commit()
        else:
            result = self.cur.execute('SELECT time, days, active FROM alarm_clocks').fetchall()
            for alarm_clock in result:
                self.add_alarm_clock(
                    AlarmClock(int(alarm_clock[0].split(':')[0]),
                               int(alarm_clock[0].split(':')[1]),
                               [str(_) in alarm_clock[1] for _ in range(7)],
                               bool(alarm_clock[2])))

        # timers
        clock_timer = QTimer(self)
        clock_timer.setInterval(1000)
        clock_timer.timeout.connect(self.program_timer)
        clock_timer.start()
        self.timer_timer = QTimer(self)
        self.timer_timer.setInterval(1000)
        self.timer_timer.timeout.connect(self.timer)
        self.stopwatch_timer = QTimer(self)
        self.stopwatch_timer.setInterval(10)
        self.stopwatch_timer.timeout.connect(self.stopwatch)

        # laps for stopwatch
        self.lap = dt.datetime.strptime('00:00:00', '%M:%S:%f')
        self.lap_n = 1

        # signals
        self.add_alarm_clock_btn.clicked.connect(lambda: self.open_new_dialog(AddAlarmClock))
        self.add_city_btn.clicked.connect(lambda: self.open_new_dialog(AddCity))
        self.alarm_clocks_table.cellDoubleClicked.connect(
            lambda: self.open_new_dialog(
                ChangeAlarmClock,
                self.alarm_clocks[self.alarm_clocks_table.selectedIndexes()[0].row()],
                self.alarm_clocks_table.selectedIndexes()[0].row()))
        self.alarm_clocks_table.itemSelectionChanged.connect(self.alarm_clocks_table_clicked)
        self.change_alarm_clock_btn.clicked.connect(
            lambda: self.open_new_dialog(
                ChangeAlarmClock,
                self.alarm_clocks[self.alarm_clocks_table.selectedIndexes()[0].row()],
                self.alarm_clocks_table.selectedIndexes()[0].row()))
        self.cities_table.itemSelectionChanged.connect(self.cities_table_clicked)
        self.delete_alarm_clock_btn.clicked.connect(self.delete_alarm_clock)
        self.delete_city_btn.clicked.connect(self.delete_city)
        self.lap_btn.clicked.connect(self.add_lap)
        self.on_off_alarm_clock_btn.clicked.connect(self.on_off_alarm_clock)
        self.reset_stopwatch_btn.clicked.connect(self.reset_stopwatch)
        self.reset_timer_btn.clicked.connect(self.reset_timer)
        self.set_timer_btn.clicked.connect(lambda: self.open_new_dialog(SetTimer))
        self.start_stop_stopwatch_btn.clicked.connect(self.start_stop_stopwatch)
        self.start_stop_timer_btn.clicked.connect(self.start_stop_timer)

    def program_timer(self):
        # show current time
        time = dt.datetime.now().time()
        if self.h24_btn.isChecked():
            time = time.strftime('%H:%M:%S')
        else:
            time = time.strftime('%I:%M:%S %p')
        self.time_label.setText(time)

        # show current time of cities
        for row in range(self.cities_table.rowCount()):
            city = self.cities_table.item(row, 0).text()
            date = dt.datetime.now()
            city_delta = [CITIES[city_] for city_ in CITIES.keys() if city in city_][0]
            time = (date + city_delta)
            if self.h24_btn.isChecked():
                time_str = time.strftime('%H:%M')
            else:
                time_str = time.strftime('%I:%M %p')
            if date.weekday() > time.weekday():
                time_str += ', вчера'
            elif date.weekday() < time.weekday():
                time_str += ', завтра'
            self.cities_table.setItem(row, 1, QTableWidgetItem(time_str))
            self.cities_table.resizeColumnsToContents()

        # check alarm clock
        if dt.datetime.now().time().second == 0:
            for alarm_clock in self.alarm_clocks:
                if alarm_clock.is_time_to_ring():
                    self.tray_icon.setVisible(True)
                    self.tray_icon.showMessage('Будильник',
                                               f'Будильник на {dt.datetime.now().strftime("%H:%M")}'
                                               f' сработал',
                                               QSystemTrayIcon.Information)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.cur.execute('DELETE FROM cities;')
        for i in range(self.cities_table.rowCount()):
            self.cur.execute(f'INSERT INTO cities(city) VALUES (\'{self.cities_table.item(i, 0).text()}\')')
        self.cur.execute('DELETE FROM alarm_clocks')
        for alarm_clock in self.alarm_clocks:
            time = f'{alarm_clock.hours}:{alarm_clock.minutes}'
            days = ''.join(str(_) for _ in alarm_clock.days)
            active = alarm_clock.active
            self.cur.execute(f'''INSERT INTO alarm_clocks(time, days, active)
VALUES (\'{time}\', \'{days}\', {int(active)})''')
        self.con.commit()
        self.con.close()

    def keyPressEvent(self, a0: QtGui.QKeyEvent) -> None:
        if int(a0.modifiers()) == Qt.AltModifier:
            if a0.key() == Qt.Key_1:
                self.tabWidget.setCurrentIndex(0)
            elif a0.key() == Qt.Key_2:
                self.tabWidget.setCurrentIndex(1)
            elif a0.key() == Qt.Key_3:
                self.tabWidget.setCurrentIndex(2)
            elif a0.key() == Qt.Key_4:
                self.tabWidget.setCurrentIndex(3)

    def open_new_dialog(self, dialog, *args):
        self.secondWindow = dialog(self, *args)
        self.secondWindow.exec()

    # world time methods
    def add_city(self, city):
        for row in range(self.cities_table.rowCount()):
            if self.cities_table.item(row, 0).text() == city:
                break
        else:
            self.cities_table.setRowCount(self.cities_table.rowCount() + 1)
            self.cities_table.setItem(self.cities_table.rowCount() - 1, 0, QTableWidgetItem(city))
            self.cities_table.sortItems(0)
            self.cities_table.resizeColumnsToContents()

    def cities_table_clicked(self):
        if len(self.cities_table.selectedIndexes()) == 1:
            self.delete_city_btn.setEnabled(True)
        else:
            self.delete_city_btn.setEnabled(False)

    def delete_city(self):
        row = self.cities_table.selectedIndexes()[0].row()
        self.cities_table.removeRow(row)
        self.cities_table.resizeColumnsToContents()

    # alarm clock methods
    def add_alarm_clock(self, alarm_clock: AlarmClock):
        self.alarm_clocks.append(alarm_clock)
        self.alarm_clocks_table.setRowCount(self.alarm_clocks_table.rowCount() + 1)
        self.alarm_clocks_table.setItem(self.alarm_clocks_table.rowCount() - 1, 0,
                                        QTableWidgetItem(
                                            f'{alarm_clock.hours:02}:{alarm_clock.minutes:02}'))
        self.alarm_clocks_table.setItem(self.alarm_clocks_table.rowCount() - 1, 1,
                                        QTableWidgetItem(alarm_clock.str_days()))
        if alarm_clock.active:
            self.alarm_clocks_table.setItem(self.alarm_clocks_table.rowCount() - 1, 2,
                                            QTableWidgetItem('Включен'))
        else:
            self.alarm_clocks_table.setItem(self.alarm_clocks_table.rowCount() - 1, 2,
                                            QTableWidgetItem('Выключен'))
        self.alarm_clocks_table.resizeColumnsToContents()

    def alarm_clocks_table_clicked(self):
        if len(self.alarm_clocks_table.selectedIndexes()) == 1:
            self.change_alarm_clock_btn.setEnabled(True)
            self.delete_alarm_clock_btn.setEnabled(True)
            self.on_off_alarm_clock_btn.setEnabled(True)
            if self.alarm_clocks_table.item(self.alarm_clocks_table.selectedIndexes()
                                            [0].row(), 2).text() == 'Включен':
                self.on_off_alarm_clock_btn.setText('Выключить')
            else:
                self.on_off_alarm_clock_btn.setText('Включить')
        else:
            self.change_alarm_clock_btn.setEnabled(False)
            self.delete_alarm_clock_btn.setEnabled(False)
            self.on_off_alarm_clock_btn.setEnabled(False)
            self.on_off_alarm_clock_btn.setText('Включить')

    def change_alarm_clock(self, alarm_clock, n):
        self.alarm_clocks[n] = alarm_clock
        self.alarm_clocks_table.setItem(n, 0, QTableWidgetItem(
            f'{alarm_clock.hours:02}:{alarm_clock.minutes:02}'))
        self.alarm_clocks_table.setItem(n, 1, QTableWidgetItem(alarm_clock.str_days()))
        self.alarm_clocks_table.setItem(n, 2, QTableWidgetItem(alarm_clock.is_active()))
        self.alarm_clocks_table.resizeColumnsToContents()

    def delete_alarm_clock(self):
        row = self.alarm_clocks_table.selectedIndexes()[0].row()
        self.alarm_clocks_table.removeRow(row)
        del self.alarm_clocks[row]
        self.alarm_clocks_table.resizeColumnsToContents()

    def on_off_alarm_clock(self):
        row = self.alarm_clocks_table.selectedIndexes()[0].row()
        self.alarm_clocks[row].on_off()
        if self.on_off_alarm_clock_btn.text() == 'Включить':
            self.alarm_clocks_table.setItem(row, 2, QTableWidgetItem('Включен'))
            self.on_off_alarm_clock_btn.setText('Выключить')
        else:
            self.alarm_clocks_table.setItem(row, 2, QTableWidgetItem('Выключен'))
            self.on_off_alarm_clock_btn.setText('Включить')

    # stopwatch methods
    def add_lap(self):
        lap = self.lap.strftime('%M:%S:%f')[:-4]
        self.laps_table.setRowCount(self.laps_table.rowCount() + 1)
        self.laps_table.setItem(self.lap_n - 1, 0, QTableWidgetItem(f'Отрезок {self.lap_n}'))
        self.laps_table.setItem(self.lap_n - 1, 1, QTableWidgetItem(lap))
        self.laps_table.setItem(self.lap_n - 1, 2, QTableWidgetItem(self.stopwatch_time_label.text()))
        self.laps_table.resizeColumnsToContents()

        self.lap_n += 1
        self.lap = dt.datetime.strptime('00:00:00', '%M:%S:%f')

    def reset_stopwatch(self):
        self.stopwatch_timer.stop()
        self.stopwatch_time_label.setText('00:00:00')
        self.start_stop_stopwatch_btn.setText('Старт')

        self.lap_n = 0
        self.laps_table.setRowCount(0)
        self.lap = dt.datetime.strptime('00:00:00', '%M:%S:%f')

        self.lap_btn.setEnabled(False)
        self.reset_stopwatch_btn.setEnabled(False)

    def start_stop_stopwatch(self):
        if not self.stopwatch_timer.isActive():
            self.start_stop_stopwatch_btn.setText('Стоп')
            self.lap_btn.setEnabled(True)
            self.reset_stopwatch_btn.setEnabled(True)
            self.stopwatch_timer.start()
        else:
            self.start_stop_timer_btn.setText('Старт')
            self.stopwatch_timer.stop()
            self.lap_btn.setEnabled(False)

    def stopwatch(self):
        time = dt.datetime.strptime(self.stopwatch_time_label.text(), '%M:%S:%f')
        time += dt.timedelta(milliseconds=10)
        self.lap += dt.timedelta(milliseconds=10)
        time_format = time.strftime('%M:%S:%f')[:-4]
        self.stopwatch_time_label.setText(time_format)

    # timer methods
    def reset_timer(self):
        self.timer_timer.stop()
        self.timer_time_label.setText('--:--:--')
        self.start_stop_timer_btn.setText('Старт')

        self.start_stop_timer_btn.setEnabled(False)
        self.reset_timer_btn.setEnabled(False)

    def set_timer(self, hours, minutes, seconds, message):
        self.timer_timer.stop()
        self.start_stop_timer_btn.setText('Старт')
        self.reset_timer_btn.setEnabled(False)

        self.timer_time_label.setText(f'{hours:02}:{minutes:02}:{seconds:02}')
        self.start_stop_timer_btn.setEnabled(True)
        self.timer_messages = message

    def start_stop_timer(self):
        if not self.timer_timer.isActive():
            self.start_stop_timer_btn.setText('Стоп')
            self.reset_timer_btn.setEnabled(True)
            self.timer_timer.start()
        else:
            self.start_stop_timer_btn.setText('Старт')
            self.timer_timer.stop()

    def timer(self):
        time = dt.datetime.strptime(self.timer_time_label.text(), '%H:%M:%S')
        time -= dt.timedelta(seconds=1)
        time_format = time.strftime('%H:%M:%S')
        self.timer_time_label.setText(time_format)
        if time_format == '00:00:00':
            self.tray_icon.setVisible(True)
            self.tray_icon.showMessage('Таймер', self.timer_messages, QSystemTrayIcon.Information)
            self.timer_timer.stop()
            self.start_stop_timer_btn.setText('Старт')
            self.start_stop_timer_btn.setEnabled(False)
            self.reset_timer_btn.setEnabled(False)


class AddAlarmClock(QDialog, set_alarm_clock_window):
    def __init__(self, parent: MainWidget):
        super(AddAlarmClock, self).__init__()
        self.setupUi(self)
        self.setWindowTitle('Добавить будильник')
        self.parent_ = parent

        self.cancel_btn.clicked.connect(lambda: self.close())
        self.ok_btn.clicked.connect(self.add_alarm_clock)
        self.monday.clicked.connect(self.check_values)
        self.tuesday.clicked.connect(self.check_values)
        self.wendesday.clicked.connect(self.check_values)
        self.thursday.clicked.connect(self.check_values)
        self.friday.clicked.connect(self.check_values)
        self.saturday.clicked.connect(self.check_values)
        self.sunday.clicked.connect(self.check_values)

    def check_values(self):
        if self.monday.isChecked() or self.tuesday.isChecked() or \
                self.wendesday.isChecked() or self.thursday.isChecked() or \
                self.friday.isChecked() or self.saturday.isChecked() or \
                self.sunday.isChecked():
            self.ok_btn.setEnabled(True)
        else:
            self.ok_btn.setEnabled(False)

    def add_alarm_clock(self):
        alarm_clock = AlarmClock(int(self.hours_input.text()), int(self.minutes_input.text()),
                                 [self.monday.isChecked(), self.tuesday.isChecked(),
                                  self.wendesday.isChecked(), self.thursday.isChecked(),
                                  self.friday.isChecked(), self.saturday.isChecked(),
                                  self.sunday.isChecked()])
        self.parent_.add_alarm_clock(alarm_clock)
        self.close()


class AddCity(QDialog, add_city_window):
    def __init__(self, parent: MainWidget):
        super(AddCity, self).__init__()
        self.setupUi(self)
        self.parent_ = parent

        cities = []
        for city in CITIES:
            cities.extend(city)
        cities.sort()
        for city in cities:
            self.city_choice.addItem(city)

        self.ok_btn.clicked.connect(self.add_city)
        self.cancel_btn.clicked.connect(lambda: self.close())

    def add_city(self):
        self.parent_.add_city(self.city_choice.currentText())
        self.close()


class ChangeAlarmClock(QDialog, set_alarm_clock_window):
    def __init__(self, parent: MainWidget, alarm_clock: AlarmClock, n):
        super(ChangeAlarmClock, self).__init__()
        self.setupUi(self)
        self.setWindowTitle('Изменить будильник')
        self.parent_ = parent
        self.n = n

        self.alarm_clock = alarm_clock
        self.hours_input.setValue(self.alarm_clock.hours)
        self.minutes_input.setValue(self.alarm_clock.minutes)
        self.monday.setChecked(0 in self.alarm_clock.days)
        self.tuesday.setChecked(1 in self.alarm_clock.days)
        self.wendesday.setChecked(2 in self.alarm_clock.days)
        self.thursday.setChecked(3 in self.alarm_clock.days)
        self.friday.setChecked(4 in self.alarm_clock.days)
        self.saturday.setChecked(5 in self.alarm_clock.days)
        self.sunday.setChecked(6 in self.alarm_clock.days)

        self.cancel_btn.clicked.connect(lambda: self.close())
        self.ok_btn.setEnabled(True)
        self.ok_btn.clicked.connect(self.change_alarm_clock)
        self.monday.clicked.connect(self.check_values)
        self.tuesday.clicked.connect(self.check_values)
        self.wendesday.clicked.connect(self.check_values)
        self.thursday.clicked.connect(self.check_values)
        self.friday.clicked.connect(self.check_values)
        self.saturday.clicked.connect(self.check_values)
        self.sunday.clicked.connect(self.check_values)

    def check_values(self):
        if self.monday.isChecked() or self.tuesday.isChecked() or \
                self.wendesday.isChecked() or self.thursday.isChecked() or \
                self.friday.isChecked() or self.saturday.isChecked() or \
                self.sunday.isChecked():
            self.ok_btn.setEnabled(True)
        else:
            self.ok_btn.setEnabled(False)

    def change_alarm_clock(self):
        self.parent_.change_alarm_clock(AlarmClock(
            int(self.hours_input.text()), int(self.minutes_input.text()),
            [self.monday.isChecked(), self.tuesday.isChecked(),
             self.wendesday.isChecked(), self.thursday.isChecked(),
             self.friday.isChecked(), self.saturday.isChecked(), self.sunday.isChecked()],
            self.alarm_clock.active), self.n)
        self.close()


class SetTimer(QDialog, set_timer_window):
    def __init__(self, parent: MainWidget):
        super(SetTimer, self).__init__()
        self.setupUi(self)
        self.parent_ = parent

        self.cancel_btn.clicked.connect(lambda: self.close())
        self.ok_btn.clicked.connect(self.set_timer)
        self.hours.valueChanged.connect(self.check_values)
        self.minutes.valueChanged.connect(self.check_values)
        self.seconds.valueChanged.connect(self.check_values)

    def check_values(self):
        if not (self.hours.text() == '0' and self.minutes.text() == '0' and self.seconds.text() == '0'):
            self.ok_btn.setEnabled(True)
        else:
            self.ok_btn.setEnabled(False)

    def set_timer(self):
        self.parent_.set_timer(int(self.hours.text()), int(self.minutes.text()),
                               int(self.seconds.text()), self.message_input.text())
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = MainWidget()
    widget.show()
    sys.exit(app.exec())
