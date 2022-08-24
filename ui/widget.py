import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget
from PyQt5.QtChart import QLineSeries, QChart
from PyQt5.QtWidgets import QTableWidgetItem, QProgressBar
from PyQt5.QtCore import Qt


class ChartWidget(QWidget):
    def __init__(self, parent=None, ticker="BTC"):
        super().__init__(parent)
        uic.loadUi("test.ui", self)
        self.ticker = ticker
        for idx, coin in enumerate(["BTC", "ETH", "SOL", "ADA", "DOGE"]):
            item_0, premium, back_premium = QTableWidgetItem(coin), QTableWidgetItem("5%"), QTableWidgetItem("-1%")
            item_0.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            premium.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            back_premium.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.premium.setItem(1, idx, item_0)
            self.premium.setItem(0, idx, premium)
            self.premium.setItem(2, idx, back_premium)

            item_2 = QProgressBar(self.premium)
            item_2.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            item_2.setStyleSheet("""
                QProgressBar {background-color : rgba(0, 0, 0, 0%);border : 1}
                QProgressBar::Chunk {background-color : rgba(255, 0, 0, 50%);border : 1}
            """)
            # self.premium.setCellWidget(i, 2, item_2)



if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    cw = ChartWidget()
    cw.show()
    exit(app.exec_())

