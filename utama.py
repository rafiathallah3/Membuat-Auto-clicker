import sys, threading, time

from pynput.keyboard import Key, KeyCode, Listener as KeyboardListener
from pynput.mouse import Controller, Button, Listener as MouseListnener
from PyQt5 import QtCore, QtGui, QtWidgets

#src: https://stackoverflow.com/questions/61859385/keypressevent-without-focus
class KeyMouseMonitor(QtCore.QObject):
    keyPressed = QtCore.pyqtSignal(KeyCode)
    clickPressed = QtCore.pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.Keyboardlistener = KeyboardListener(on_release=self.on_release)
        self.Mouselistener = MouseListnener(on_click=self.on_click)

    def on_release(self, key):
        #Masalah
        self.keyPressed.emit(key.value if hasattr(key, 'value') else key)

    def on_click(self, x,y,button,pressed):
        if not pressed and button == Button.left:
            self.clickPressed.emit([x,y])

    def stop_monitoring(self):
        self.Keyboardlistener.stop()
        self.Mouselistener.stop()

    def start_monitoring(self):
        self.Keyboardlistener.start()
        self.Mouselistener.start()

class WindowUtama():
    def __init__(self, MainWindow: QtWidgets.QMainWindow, MosController):
        self.MainWindow = MainWindow
        self.MosController = MosController
        self.threadMouse = None

        self._Mulai = False
        self._ApakahGantiKeybind = False
        self.AmbilLokasi = False
        self.Keybind = "F6"

        self.data = {
            "WaktuKlik": [0, 0, 0, .1], #Jam menit detik milidetik
            "Opsi": {
                "TombolMouse": (4, 2, 0),
                "TipeMouse": "Sekali"
            },
            "Perulangan": {
                "DiulangSampaiBerhenti": True,
                "BerapaKaliUlang": 1
            },
            "Posisi": {
                "LokasiSama": True,
                "PosisiLokasi": [0,0]
            }
        }

        self.monitor = KeyMouseMonitor()
        self.monitor.keyPressed.connect(self.keyMonitorFunc)
        self.monitor.clickPressed.connect(self.klikMonitorFunc)
        self.monitor.start_monitoring()

    def selesaiInputWaktu(self):
        def DeteksiInput(InputEdit: QtWidgets.QLineEdit) -> str:
            if not InputEdit.text() or not InputEdit.text().isdecimal(): return 0
            return int(InputEdit.text()) # Kalau ada nol di character pertama maka dihilangin dengan int function

        for i,v in enumerate([self.waktuJamInput, self.waktuMenitInput, self.waktuDetikInput, self.waktuMilidetikInput]):
            hasil = DeteksiInput(v)
            self.data["WaktuKlik"][i] = hasil
            v.setText(str(hasil))

        self.data["WaktuKlik"][3] = 100 if self.data["WaktuKlik"][3] < 10 else self.data["WaktuKlik"][3]
        self.waktuMilidetikInput.setText(str(self.data["WaktuKlik"][3]))

        WaktuKlikTime = str(self.data["WaktuKlik"][3])
        WaktuKlikTime = f'{"0" if WaktuKlikTime.count("0") < 2 else ""}{WaktuKlikTime}'
        self.data["WaktuKlik"][3] = float("."+WaktuKlikTime)

    def OpsiComboBox(self):
        self.data["Opsi"]["TombolMouse"] = (4, 2, 0) if self.TombolMouseComboBox.currentText() == "Kiri" else (16, 8, 0)
        self.data["Opsi"]["TipeMouse"] = self.TipeMouseComboBox.currentText()

    def radioUlangValueChanged(self):
        self.data["Perulangan"]["DiulangSampaiBerhenti"] = self.radioUlangBerhenti.isChecked()
        self.data["Perulangan"]["BerapaKaliUlang"] = self.berapaKaliUlang.value()

    def radioLokasiValueChanged(self):
        def DeteksiInput(EditPosisi: list[QtWidgets.QLineEdit]) -> list[QtWidgets.QLineEdit]:
            for i,v in enumerate(EditPosisi):
                EditPosisi[i] = 0 if not v.text() or not v.text().isdecimal() else str(int(v.text()))

            return EditPosisi

        self.data["Posisi"]["LokasiSama"] = self.radioLokasiSama.isChecked()
        self.data["Posisi"]["PosisiLokasi"] = DeteksiInput([self.EditPosisiX, self.EditPosisiY])

    def MulaiAutoClicker(self, delay):
        def Perulang():
            time.sleep(delay)

            if not self.data["Posisi"]["LokasiSama"]: self.MosController.position = self.data["Posisi"]["PosisiLokasi"]
            self.MosController.click(Button(self.data["Opsi"]["TombolMouse"]), 2 if self.data["Opsi"]["TipeMouse"] == "Dua kali" else 1)

        while self.data["Perulangan"]["DiulangSampaiBerhenti"]:
            if not self.Mulai: break
            Perulang()
        else:
            for _ in range(self.data["Perulangan"]["BerapaKaliUlang"]):
                if not self.Mulai: break
                Perulang()
            self.Mulai = False
                
        print("Stop clicker")

    def keyMonitorFunc(self, key):
        print(key.from_char(key))
        if self.ApakahGantiKeybind:
            self.Keybind = key.value
            self.ApakahGantiKeybind = False

        if key == Key.f6.value:
            self.Mulai = not self.Mulai

    def klikMonitorFunc(self, pos: list[int, int]):
        if self.AmbilLokasi:
            self.data["Posisi"]["PosisiLokasi"] = pos
            
            self.EditPosisiX.setText(str(pos[0]))
            self.EditPosisiY.setText(str(pos[1]))
            
            self.AmbilLokasi = False

    @property
    def Mulai(self):
        return self._Mulai

    @Mulai.setter
    def Mulai(self, value):
        self._Mulai = value
        
        self.TombolMulai.setEnabled(not value)
        self.TombolStop.setEnabled(value)

        if value:
            delay = self.data["WaktuKlik"][0]**60 + self.data["WaktuKlik"][1]*60 + self.data["WaktuKlik"][2] + self.data["WaktuKlik"][3]

            x = threading.Thread(target=self.MulaiAutoClicker, args=(delay,))
            x.start()

    @property
    def ApakahGantiKeybind(self):
        return self._ApakahGantiKeybind

    @ApakahGantiKeybind.setter
    def ApakahGantiKeybind(self, value):
        self._ApakahGantiKeybind = value

        self.KeybindLabel.setText("Silahkan di tekan key" if value else self.Keybind)
        self.TombolSettingHotkey.setText("Batal" if value else "Ganti Start/Stop")

    def setupUi(self):
        self.MainWindow.setObjectName("MainWindow")
        self.MainWindow.resize(569, 469)
        self.MainWindow.setFixedSize(self.MainWindow.size())
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("ui\\../icon/mouse.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.MainWindow.setWindowIcon(icon)
        
        self.centralwidget = QtWidgets.QWidget(self.MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        
        font = QtGui.QFont()
        font.setFamily("Ebrima")
        font.setPointSize(10)
        self.groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox.setGeometry(QtCore.QRect(20, 10, 531, 71))
        self.groupBox.setFont(font)
        self.groupBox.setObjectName("groupBox")
        
        self.waktuJamInput = QtWidgets.QLineEdit(self.groupBox)
        self.waktuJamInput.setGeometry(QtCore.QRect(40, 30, 51, 21))
        self.waktuJamInput.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.waktuJamInput.setObjectName("waktuJamInput")
        self.waktuJamInput.setMaxLength(2)
        
        self.waktuJamLabel = QtWidgets.QLabel(self.groupBox)
        self.waktuJamLabel.setGeometry(QtCore.QRect(90, 30, 47, 21))
        self.waktuJamLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.waktuJamLabel.setObjectName("waktuJamLabel")
        
        self.waktuMenitInput = QtWidgets.QLineEdit(self.groupBox)
        self.waktuMenitInput.setGeometry(QtCore.QRect(160, 30, 51, 21))
        self.waktuMenitInput.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.waktuMenitInput.setObjectName("waktuMenitInput")
        self.waktuMenitInput.setMaxLength(2)
        
        self.waktuMenitLabel = QtWidgets.QLabel(self.groupBox)
        self.waktuMenitLabel.setGeometry(QtCore.QRect(210, 30, 47, 21))
        self.waktuMenitLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.waktuMenitLabel.setObjectName("waktuMenitLabel")
        
        self.waktuDetikInput = QtWidgets.QLineEdit(self.groupBox)
        self.waktuDetikInput.setGeometry(QtCore.QRect(280, 30, 51, 21))
        self.waktuDetikInput.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.waktuDetikInput.setObjectName("waktuDetikInput")
        self.waktuDetikInput.setMaxLength(2)

        self.waktuDetikLabel = QtWidgets.QLabel(self.groupBox)
        self.waktuDetikLabel.setGeometry(QtCore.QRect(330, 30, 47, 21))
        self.waktuDetikLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.waktuDetikLabel.setObjectName("waktuDetikLabel")
        
        self.waktuMilidetikInput = QtWidgets.QLineEdit(self.groupBox)
        self.waktuMilidetikInput.setGeometry(QtCore.QRect(400, 30, 51, 21))
        self.waktuMilidetikInput.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.waktuMilidetikInput.setObjectName("waktuMilidetikInput")
        self.waktuMilidetikInput.setMaxLength(3)

        self.waktuMilidetiLabel = QtWidgets.QLabel(self.groupBox)
        self.waktuMilidetiLabel.setGeometry(QtCore.QRect(450, 30, 61, 21))
        self.waktuMilidetiLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.waktuMilidetiLabel.setObjectName("waktuMilidetiLabel")
        
        font = QtGui.QFont()
        font.setFamily("Ebrima")
        font.setPointSize(10)
        self.groupBox_2 = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_2.setGeometry(QtCore.QRect(20, 90, 241, 131))
        self.groupBox_2.setFont(font)
        self.groupBox_2.setObjectName("groupBox_2")
        
        self.TombolMauseLabel = QtWidgets.QLabel(self.groupBox_2)
        self.TombolMauseLabel.setGeometry(QtCore.QRect(20, 30, 91, 16))
        self.TombolMauseLabel.setObjectName("TombolMauseLabel")
        
        self.TombolMouseComboBox = QtWidgets.QComboBox(self.groupBox_2)
        self.TombolMouseComboBox.setGeometry(QtCore.QRect(150, 30, 71, 22))
        self.TombolMouseComboBox.setObjectName("TombolMouseComboBox")
        self.TombolMouseComboBox.addItem("")
        self.TombolMouseComboBox.addItem("")
        
        self.TipeMouseLabel = QtWidgets.QLabel(self.groupBox_2)
        self.TipeMouseLabel.setGeometry(QtCore.QRect(20, 70, 91, 16))
        self.TipeMouseLabel.setObjectName("TipeMouseLabel")
        
        self.TipeMouseComboBox = QtWidgets.QComboBox(self.groupBox_2)
        self.TipeMouseComboBox.setGeometry(QtCore.QRect(150, 70, 71, 22))
        self.TipeMouseComboBox.setObjectName("TipeMouseComboBox")
        self.TipeMouseComboBox.addItem("")
        self.TipeMouseComboBox.addItem("")
        
        font = QtGui.QFont()
        font.setFamily("Ebrima")
        font.setPointSize(10)
        self.groupBox_3 = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_3.setGeometry(QtCore.QRect(310, 90, 241, 131))
        self.groupBox_3.setFont(font)
        self.groupBox_3 = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_3.setGeometry(QtCore.QRect(310, 90, 241, 131))
        self.groupBox_3.setObjectName("groupBox_3")
        
        self.radioUlang = QtWidgets.QRadioButton(self.groupBox_3)
        self.radioUlang.setGeometry(QtCore.QRect(20, 30, 82, 17))
        self.radioUlang.setObjectName("radioUlang")
        
        self.radioUlangBerhenti = QtWidgets.QRadioButton(self.groupBox_3)
        self.radioUlangBerhenti.setGeometry(QtCore.QRect(20, 70, 161, 17))
        self.radioUlangBerhenti.setObjectName("radioUlangBerhenti")
        self.radioUlangBerhenti.setChecked(True)
        
        self.berapaKaliUlang = QtWidgets.QSpinBox(self.groupBox_3)
        self.berapaKaliUlang.setGeometry(QtCore.QRect(100, 30, 42, 22))
        self.berapaKaliUlang.setObjectName("berapaKaliUlang")
        self.berapaKaliUlang.setValue(1)
        
        self.berapaKaliLabel = QtWidgets.QLabel(self.groupBox_3)
        self.berapaKaliLabel.setGeometry(QtCore.QRect(150, 30, 47, 21))
        self.berapaKaliLabel.setObjectName("berapaKaliLabel")
        
        font = QtGui.QFont()
        font.setFamily("Ebrima")
        font.setPointSize(10)
        self.groupBox_4 = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_4.setGeometry(QtCore.QRect(20, 230, 531, 71))
        self.groupBox_4.setFont(font)
        self.groupBox_4.setObjectName("groupBox_4")
        
        self.radioLokasiSama = QtWidgets.QRadioButton(self.groupBox_4)
        self.radioLokasiSama.setGeometry(QtCore.QRect(10, 30, 91, 17))
        self.radioLokasiSama.setObjectName("radioButton")
        self.radioLokasiSama.setChecked(True)
        
        self.radioPilihLokasi = QtWidgets.QRadioButton(self.groupBox_4)
        self.radioPilihLokasi.setGeometry(QtCore.QRect(280, 27, 20, 20))
        self.radioPilihLokasi.setText("")
        self.radioPilihLokasi.setObjectName("radioPilihLokasi")
        
        self.TombolPilihLokasi = QtWidgets.QPushButton(self.groupBox_4)
        self.TombolPilihLokasi.setGeometry(QtCore.QRect(300, 20, 81, 41))
        self.TombolPilihLokasi.setObjectName("TombolPilihLokasi")
        
        self.EditPosisiX = QtWidgets.QLineEdit(self.groupBox_4)
        self.EditPosisiX.setGeometry(QtCore.QRect(412, 30, 41, 20))
        self.EditPosisiX.setObjectName("EditPosisiX")
        self.EditPosisiX.setMaxLength(3)
        
        self.labelX = QtWidgets.QLabel(self.groupBox_4)
        self.labelX.setGeometry(QtCore.QRect(390, 30, 21, 16))
        self.labelX.setAlignment(QtCore.Qt.AlignCenter)
        self.labelX.setObjectName("labelX")
        
        self.labelY = QtWidgets.QLabel(self.groupBox_4)
        self.labelY.setGeometry(QtCore.QRect(458, 30, 21, 16))
        self.labelY.setAlignment(QtCore.Qt.AlignCenter)
        self.labelY.setObjectName("labelY")
        
        self.EditPosisiY = QtWidgets.QLineEdit(self.groupBox_4)
        self.EditPosisiY.setGeometry(QtCore.QRect(480, 30, 41, 20))
        self.EditPosisiY.setObjectName("EditPosisiY")
        self.EditPosisiY.setMaxLength(3)
        
        font = QtGui.QFont()
        font.setFamily("Ebrima")
        font.setPointSize(12)
        self.TombolMulai = QtWidgets.QPushButton(self.centralwidget)
        self.TombolMulai.setGeometry(QtCore.QRect(20, 310, 241, 51))
        self.TombolMulai.setFont(font)
        self.TombolMulai.setObjectName("TombolMulai")
        
        font = QtGui.QFont()
        font.setFamily("Ebrima")
        font.setPointSize(12)
        self.TombolStop = QtWidgets.QPushButton(self.centralwidget)
        self.TombolStop.setGeometry(QtCore.QRect(310, 310, 241, 51))
        self.TombolStop.setFont(font)
        self.TombolStop.setObjectName("TombolStop")
        self.TombolStop.setEnabled(False)

        font = QtGui.QFont()
        font.setFamily("Ebrima")
        font.setPointSize(12)
        self.TombolSettingHotkey = QtWidgets.QPushButton(self.centralwidget)
        self.TombolSettingHotkey.setGeometry(QtCore.QRect(20, 370, 241, 51))
        self.TombolSettingHotkey.setFont(font)
        self.TombolSettingHotkey.setObjectName("TombolSettingHotkey")
        
        font = QtGui.QFont()
        font.setFamily("Ebrima")
        font.setPointSize(16)
        self.KeybindLabel = QtWidgets.QLineEdit(self.centralwidget)
        self.KeybindLabel.setGeometry(QtCore.QRect(310, 370, 241, 51))
        self.KeybindLabel.setFont(font)
        self.KeybindLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.KeybindLabel.setReadOnly(True)
        self.KeybindLabel.setObjectName("KeybindLabel")
        
        self.MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(self.MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 569, 21))
        self.menubar.setObjectName("menubar")
        self.MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(self.MainWindow)
        self.statusbar.setObjectName("statusbar")
        self.MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self.MainWindow)

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.MainWindow.setWindowTitle(_translate("MainWindow", "Auto Clicker"))
        self.groupBox.setTitle(_translate("MainWindow", "Waktu Klik"))
        self.waktuJamInput.setText(_translate("MainWindow", "0"))
        self.waktuJamLabel.setText(_translate("MainWindow", "Jam"))
        self.waktuMenitInput.setText(_translate("MainWindow", "0"))
        self.waktuMenitLabel.setText(_translate("MainWindow", "Menit"))
        self.waktuDetikInput.setText(_translate("MainWindow", "0"))
        self.waktuDetikLabel.setText(_translate("MainWindow", "Detik"))
        self.waktuMilidetikInput.setText(_translate("MainWindow", "100"))
        self.waktuMilidetiLabel.setText(_translate("MainWindow", "mili detik"))
        self.groupBox_2.setTitle(_translate("MainWindow", "Opsi Klik"))
        self.TombolMauseLabel.setText(_translate("MainWindow", "Tombol Mause"))
        self.TombolMouseComboBox.setItemText(0, _translate("MainWindow", "Kiri"))
        self.TombolMouseComboBox.setItemText(1, _translate("MainWindow", "Kanan"))
        self.TipeMouseLabel.setText(_translate("MainWindow", "Tipe Mouse"))
        self.TipeMouseComboBox.setItemText(0, _translate("MainWindow", "Sekali"))
        self.TipeMouseComboBox.setItemText(1, _translate("MainWindow", "Dua kali"))
        self.groupBox_3.setTitle(_translate("MainWindow", "Perulangan"))
        self.radioUlang.setText(_translate("MainWindow", "Ulang"))
        self.radioUlangBerhenti.setText(_translate("MainWindow", "Ulang sampai berhenti"))
        self.berapaKaliLabel.setText(_translate("MainWindow", "Kali"))
        self.groupBox_4.setTitle(_translate("MainWindow", "Posisi"))
        self.radioLokasiSama.setText(_translate("MainWindow", "Lokasi sama"))
        self.TombolPilihLokasi.setText(_translate("MainWindow", "Pilih Lokasi"))
        self.EditPosisiX.setText(_translate("MainWindow", "0"))
        self.labelX.setText(_translate("MainWindow", "X"))
        self.labelY.setText(_translate("MainWindow", "Y"))
        self.EditPosisiY.setText(_translate("MainWindow", "0"))
        self.TombolMulai.setText(_translate("MainWindow", "Start"))
        self.TombolStop.setText(_translate("MainWindow", "Stop"))
        self.TombolSettingHotkey.setText(_translate("MainWindow", "Ganti Start/Stop"))
        self.KeybindLabel.setText(_translate("MainWindow", "F6"))

        self.waktuJamInput.editingFinished.connect(self.selesaiInputWaktu)
        self.waktuMenitInput.editingFinished.connect(self.selesaiInputWaktu)
        self.waktuDetikInput.editingFinished.connect(self.selesaiInputWaktu)
        self.waktuMilidetikInput.editingFinished.connect(self.selesaiInputWaktu)

        self.TombolMouseComboBox.activated.connect(self.OpsiComboBox)
        self.TipeMouseComboBox.activated.connect(self.OpsiComboBox)

        self.radioUlang.toggled.connect(self.radioUlangValueChanged)
        self.radioUlangBerhenti.toggled.connect(self.radioUlangValueChanged)

        self.radioLokasiSama.toggled.connect(self.radioLokasiValueChanged)

        self.TombolMulai.clicked.connect(lambda: setattr(self, "Mulai", True))
        self.TombolStop.clicked.connect(lambda: setattr(self, "Mulai", False))
        self.TombolPilihLokasi.clicked.connect(lambda: setattr(self, "AmbilLokasi", True))
        self.TombolSettingHotkey.clicked.connect(lambda: setattr(self, "ApakahGantiKeybind", not self.ApakahGantiKeybind))

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    mosController = Controller()

    ui = WindowUtama(MainWindow, mosController)
    ui.setupUi()

    MainWindow.show()
    sys.exit(app.exec_())