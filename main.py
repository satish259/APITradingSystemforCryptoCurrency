# import click
import logging
import pprint
from RequestHandler import RequestHandler

logger = logging.getLogger(__name__)


# @click.command("Primitive Text Based Trading Tool for ")
# @click.option("--instrument", default="BTCUSD.SPOT", help="Which instrument do you want to trade?")
# @click.option("--side", default="buy", help="Do you want to buy or sell them?")
# @click.option("--quantity", default=1, help="How many units to trade?")
# def main(instrument, side, quantity):
def main():
    try:
        print('Welcome to Text Based Trading Tool for .')
        instrument = input("Which instrument do you want to trade?")
        side = input("Do you want to buy or sell them?")
        quantity = input("How many units to trade?")
        rH = RequestHandler()
        rfq = rH.RFQ(instrument, side, quantity)
        pprint.pprint(rfq)
        inTrade = input("Do you wish to trade? (y/n)")
        if inTrade.lower() in ['y', 'yes']:
            trade = rH.trade()
            pprint.pprint(trade)
            print("Trade was successful. New balance below.")
            pprint.pprint(rH.getBalances())
            print("You are now rich. Goodbye!")
        else:
            print('Thank you for trading. Goodbye!')
    except RuntimeError as e:
        logger.critical("Trade failed: %s" % e)


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger("").setLevel(logging.INFO)
    main()
