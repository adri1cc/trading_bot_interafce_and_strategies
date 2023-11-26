from pyalgotrade import strategy
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross


class SMACrossOver(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, smaPeriod, portfolio):
        super(SMACrossOver, self).__init__(feed, portfolio)
        self.__instrument = instrument
        self.__position = None
        #self.setUseAdjustedValues(True)
        self.__prices = feed[instrument].getPriceDataSeries()
        self.__sma = ma.SMA(self.__prices, smaPeriod)

    def getSMA(self):
        return self.__sma

    def onEnterCanceled(self, position):
        self.__position = None

    def onExitOk(self, position):
        self.__position = None

    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        self.__position.exitMarket()

    def onBars(self, bars):
        # If a position was not opened, check if we should enter a long position.
        if self.__position is None:
            if cross.cross_above(self.__prices, self.__sma) > 0:
                shares = int(self.getBroker().getCash() * 0.9 / bars[self.__instrument].getPrice())
                # Enter a buy market order. The order is good till canceled.
                self.__position = self.enterLong(self.__instrument, shares, True)
        # Check if we have to exit the position.
        elif not self.__position.exitActive() and cross.cross_below(self.__prices, self.__sma) > 0:
            self.__position.exitMarket()

class MyStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, smaPeriod, portfolio):
        super(MyStrategy, self).__init__(feed, portfolio)
        self.__position = None
        self.__instrument = instrument
        self.__smaPeriod = smaPeriod
        self.__sma = ma.SMA(feed[instrument].getPriceDataSeries(), smaPeriod)
        self.__portfolio_values = []  # List to store portfolio values
        self.__last_portfolio_value = None  # To keep track of the last portfolio value

    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()
        self.info("BUY at $%.2f" % (execInfo.getPrice()))

    def onEnterCanceled(self, position):
        self.__position = None

    def onExitOk(self, position):
        execInfo = position.getExitOrder().getExecutionInfo()
        self.info("SELL at $%.2f" % (execInfo.getPrice()))

        # Calculate the new portfolio value and store it
        new_portfolio_value = self.getBroker().getEquity()
        if self.__last_portfolio_value is not None:
            portfolio_change = new_portfolio_value - self.__last_portfolio_value
            self.__portfolio_values.append((execInfo.getDateTime(), new_portfolio_value, portfolio_change))

        self.__last_portfolio_value = new_portfolio_value
        self.__position = None

    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        self.__position.exitMarket()

    def onBars(self, bars):
        #print("Received bars:", bars)
        # Wait for enough bars to be available to calculate a SMA.
        if self.__sma[-1] is None:
            return

        bar = bars[self.__instrument]
        # If a position was not opened, check if we should enter a long position.
        if self.__position is None:
            if bar.getPrice() > self.__sma[-1]:
                # Enter a buy market order for 1 share. The order is good till canceled.
                self.__position = self.enterLong(self.__instrument, 1, True)
        # Check if we have to exit the position.
        elif bar.getPrice() < self.__sma[-1] and not self.__position.exitActive():
            self.__position.exitMarket()

    def getPortfolioValues(self):
        return self.__portfolio_values

    def getSMA(self):
        return self.__sma
    def getName(self):
        return self.__instrument + " " + "Mystrategy" + " " + str(self.__smaPeriod)
    