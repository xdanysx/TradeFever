import sys
import random
from typing import Dict

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QSpinBox,
    QGroupBox,
)

import os

def load_config():
    # Ordner finden, in dem main.py liegt
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Pfad zur config.txt im data-Ordner
    config_path = os.path.join(base_dir, "..", "data", "config.txt")

    start_cash = 10000
    fee_rate = 0.01

    try:
        with open(config_path, "r") as f:
            for line in f:
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip().upper()
                value = value.strip()

                if key == "START_CASH":
                    start_cash = float(value)
                elif key == "FEE_RATE":
                    fee_rate = float(value)

    except FileNotFoundError:
        print(f"config.txt nicht gefunden unter: {config_path}")
        print("Standardwerte werden verwendet.")

    return start_cash, fee_rate


START_CASH, FEE_RATE = load_config()

class Stock:
    def __init__(self, symbol: str, name: str, price: float, volatility: float):
        self.symbol = symbol
        self.name = name
        self.price = price
        self.volatility = volatility  # z.B. 0.03 = +/- 3 % pro Sekunde

    def update_price(self):
        # Zufällige prozentuale Änderung
        change_factor = 1 + random.uniform(-self.volatility, self.volatility)
        new_price = self.price * change_factor

        # Kleine Chance auf stärkeren Sprung
        if random.random() < 0.02:  # 2 % Chance auf Event
            event_factor = random.choice([0.8, 0.85, 1.15, 1.2])  # -20 %, -15 %, +15 %, +20 %
            new_price *= event_factor

        # Untere Grenze (kein Preis <= 0)
        self.price = max(new_price, 0.1)


class Market:
    def __init__(self, stocks):
        self.stocks: Dict[str, Stock] = {stock.symbol: stock for stock in stocks}

    def update_prices(self):
        for stock in self.stocks.values():
            stock.update_price()

    def get_stock(self, symbol: str):
        return self.stocks.get(symbol.upper())

    def get_all_stocks(self):
        return list(self.stocks.values())


class Player:
    def __init__(self, name: str, starting_cash: float = 10000.0):
        self.name = name
        self.cash = starting_cash
        # holdings[symbol] = {"amount": int, "avg_price": float}
        self.holdings: Dict[str, Dict[str, float]] = {}

    def portfolio_value(self, market: Market) -> float:
        total = 0.0
        for symbol, data in self.holdings.items():
            amount = data["amount"]
            stock = market.get_stock(symbol)
            if stock:
                total += amount * stock.price
        return total

    def total_value(self, market: Market) -> float:
        return self.cash + self.portfolio_value(market)

    def buy(self, market: Market, symbol: str, amount: int, fee_rate: float):
        stock = market.get_stock(symbol)
        if not stock:
            return False, "Aktie nicht gefunden."

        if amount <= 0:
            return False, "Stückzahl muss positiv sein."

        cost_without_fee = stock.price * amount
        fee = cost_without_fee * fee_rate
        total_cost = cost_without_fee + fee

        if total_cost > self.cash:
            return False, f"Nicht genug Cash. Du brauchst {total_cost:.2f} €, hast aber nur {self.cash:.2f} €."

        self.cash -= total_cost

        if symbol not in self.holdings:
            # Neue Position
            self.holdings[symbol] = {"amount": amount, "avg_price": stock.price}
        else:
            # Durchschnittlichen Kaufpreis neu berechnen (gewichteter Mittelwert)
            old_amount = self.holdings[symbol]["amount"]
            old_avg = self.holdings[symbol]["avg_price"]
            new_amount = old_amount + amount
            new_avg = (old_avg * old_amount + stock.price * amount) / new_amount

            self.holdings[symbol]["amount"] = new_amount
            self.holdings[symbol]["avg_price"] = new_avg

        msg = (
            f"Gekauft: {amount}x {symbol} für {cost_without_fee:.2f} € "
            f"(Gebühr: {fee:.2f} €, Gesamt: {total_cost:.2f} €)."
        )
        return True, msg

    def sell(self, market: Market, symbol: str, amount: int, fee_rate: float):
        stock = market.get_stock(symbol)
        if not stock:
            return False, "Aktie nicht gefunden."

        if amount <= 0:
            return False, "Stückzahl muss positiv sein."

        if symbol not in self.holdings:
            return False, f"Du besitzt keine {symbol}."

        current = self.holdings[symbol]["amount"]
        if amount > current:
            return False, f"Du hast nur {current}x {symbol}, kannst nicht {amount} verkaufen."

        revenue_without_fee = stock.price * amount
        fee = revenue_without_fee * fee_rate
        revenue = revenue_without_fee - fee

        self.cash += revenue
        new_amount = current - amount
        if new_amount == 0:
            # Position komplett verkauft
            del self.holdings[symbol]
        else:
            # Menge reduzieren, avg_price lassen wir wie er ist
            self.holdings[symbol]["amount"] = new_amount

        msg = (
            f"Verkauft: {amount}x {symbol} für {revenue_without_fee:.2f} € "
            f"(Gebühr: {fee:.2f} €, Netto: {revenue:.2f} €)."
        )
        return True, msg


class StockGameWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Mini Aktien Spiel")
        self.resize(1000, 700)

        # --- Mehr Aktien hier definieren ---
        stocks = [
            Stock("TECH", "Techify AG", 150.0, 0.01),
            Stock("GREEN", "GreenCorp SE", 80.0, 0.008),
            Stock("SPACE", "SpaceXplorer", 220.0, 0.015),
            Stock("FOOD", "FoodWorld AG", 45.0, 0.006),
            Stock("BANK", "SafeBank SA", 60.0, 0.005),
            Stock("AUTO", "AutoMotion AG", 95.0, 0.012),
            Stock("ENER", "EnerGen SE", 70.0, 0.011),
            Stock("HEAL", "HealthPlus AG", 55.0, 0.007),
            Stock("GAME", "GameWorld SE", 40.0, 0.02),
            Stock("CLOUD", "Cloudify SA", 130.0, 0.013),
        ]

        self.market = Market(stocks)
        self.player = Player("Spieler", starting_cash=START_CASH)

        # --- UI Aufbau ---
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Info-Leiste (Cash, Portfolio, Gesamt)
        info_layout = QHBoxLayout()
        self.cash_label = QLabel()
        self.portfolio_label = QLabel()
        self.total_label = QLabel()

        for lbl in (self.cash_label, self.portfolio_label, self.total_label):
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        info_layout.addWidget(self.cash_label)
        info_layout.addWidget(self.portfolio_label)
        info_layout.addWidget(self.total_label)

        main_layout.addLayout(info_layout)

        # Markt-Tabelle
        market_group = QGroupBox("Markt")
        market_layout = QVBoxLayout()
        market_group.setLayout(market_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Symbol", "Name", "Preis (€)", "Bestand"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        market_layout.addWidget(self.table)
        main_layout.addWidget(market_group)

        # Portfolio-Tabelle
        portfolio_group = QGroupBox("Dein Portfolio")
        portfolio_layout = QVBoxLayout()
        portfolio_group.setLayout(portfolio_layout)

        self.portfolio_table = QTableWidget()
        # NEU: zusätzliche Spalte "Ø Kaufpreis"
        self.portfolio_table.setColumnCount(6)
        self.portfolio_table.setHorizontalHeaderLabels(
            ["Symbol", "Name", "Stück", "Ø Kaufpreis (€)", "Preis (€)", "Wert (€)"]
        )
        self.portfolio_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.portfolio_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.portfolio_table.setSelectionMode(QTableWidget.NoSelection)

        portfolio_layout.addWidget(self.portfolio_table)
        main_layout.addWidget(portfolio_group)

        # Trade-Bereich
        trade_group = QGroupBox("Handel")
        trade_layout = QHBoxLayout()
        trade_group.setLayout(trade_layout)

        self.amount_spin = QSpinBox()
        self.amount_spin.setMinimum(1)
        self.amount_spin.setMaximum(1_000_000)
        self.amount_spin.setValue(10)

        self.buy_button = QPushButton("Kaufen")
        self.sell_button = QPushButton("Verkaufen")

        trade_layout.addWidget(QLabel("Stückzahl:"))
        trade_layout.addWidget(self.amount_spin)
        trade_layout.addWidget(self.buy_button)
        trade_layout.addWidget(self.sell_button)

        main_layout.addWidget(trade_group)

        # Status / Meldungen
        self.status_label = QLabel()
        main_layout.addWidget(self.status_label)

        # --- Signale ---
        self.buy_button.clicked.connect(self.on_buy_clicked)
        self.sell_button.clicked.connect(self.on_sell_clicked)

        # --- Timer für Kurs-Updates ---
        self.timer = QTimer(self)
        self.timer.setInterval(1000)  # 1 Sekunde
        self.timer.timeout.connect(self.on_timer_tick)
        self.timer.start()

        # Initiale Anzeige
        self.refresh_market_table()
        self.refresh_portfolio_table()
        self.refresh_info_labels()

    # ---- UI-Update-Methoden ----

    def refresh_market_table(self):
        stocks = self.market.get_all_stocks()
        self.table.setRowCount(len(stocks))
        for row, stock in enumerate(stocks):
            symbol_item = QTableWidgetItem(stock.symbol)
            name_item = QTableWidgetItem(stock.name)
            price_item = QTableWidgetItem(f"{stock.price:.2f}")

            holding_amount = 0
            if stock.symbol in self.player.holdings:
                holding_amount = int(self.player.holdings[stock.symbol]["amount"])
            holding_item = QTableWidgetItem(str(holding_amount))

            symbol_item.setTextAlignment(Qt.AlignCenter)
            name_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            holding_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.table.setItem(row, 0, symbol_item)
            self.table.setItem(row, 1, name_item)
            self.table.setItem(row, 2, price_item)
            self.table.setItem(row, 3, holding_item)

        self.table.resizeColumnsToContents()

    def refresh_portfolio_table(self):
        holdings_items = list(self.player.holdings.items())
        self.portfolio_table.setRowCount(len(holdings_items))

        for row, (symbol, data) in enumerate(holdings_items):
            amount = int(data["amount"])
            avg_price = data["avg_price"]
            stock = self.market.get_stock(symbol)
            if not stock:
                continue

            price = stock.price
            value = amount * price

            symbol_item = QTableWidgetItem(symbol)
            name_item = QTableWidgetItem(stock.name)
            amount_item = QTableWidgetItem(str(amount))
            avg_item = QTableWidgetItem(f"{avg_price:.2f}")
            price_item = QTableWidgetItem(f"{price:.2f}")
            value_item = QTableWidgetItem(f"{value:.2f}")

            symbol_item.setTextAlignment(Qt.AlignCenter)
            name_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            avg_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            value_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.portfolio_table.setItem(row, 0, symbol_item)
            self.portfolio_table.setItem(row, 1, name_item)
            self.portfolio_table.setItem(row, 2, amount_item)
            self.portfolio_table.setItem(row, 3, avg_item)
            self.portfolio_table.setItem(row, 4, price_item)
            self.portfolio_table.setItem(row, 5, value_item)

        self.portfolio_table.resizeColumnsToContents()

    def refresh_info_labels(self):
        cash = self.player.cash
        pv = self.player.portfolio_value(self.market)
        tv = self.player.total_value(self.market)

        self.cash_label.setText(f"Cash: {cash:.2f} €")
        self.portfolio_label.setText(f"Portfoliowert: {pv:.2f} €")
        self.total_label.setText(f"Gesamtvermögen: {tv:.2f} €")

    def set_status(self, text: str):
        self.status_label.setText(text)

    def get_selected_symbol(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if not item:
            return None
        return item.text().strip()

    # ---- Slots für Buttons & Timer ----

    def on_buy_clicked(self):
        symbol = self.get_selected_symbol()
        if not symbol:
            self.set_status("Bitte zuerst eine Aktie im Markt auswählen.")
            return

        amount = self.amount_spin.value()
        success, msg = self.player.buy(self.market, symbol, amount, FEE_RATE)
        self.set_status(msg)
        if success:
            self.refresh_market_table()
            self.refresh_portfolio_table()
            self.refresh_info_labels()

    def on_sell_clicked(self):
        symbol = self.get_selected_symbol()
        if not symbol:
            self.set_status("Bitte zuerst eine Aktie im Markt auswählen.")
            return

        amount = self.amount_spin.value()
        success, msg = self.player.sell(self.market, symbol, amount, FEE_RATE)
        self.set_status(msg)
        if success:
            self.refresh_market_table()
            self.refresh_portfolio_table()
            self.refresh_info_labels()

    def on_timer_tick(self):
        # Preise updaten und Anzeige aktualisieren
        self.market.update_prices()
        self.refresh_market_table()
        self.refresh_portfolio_table()
        self.refresh_info_labels()


def main():
    app = QApplication(sys.argv)
    window = StockGameWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
