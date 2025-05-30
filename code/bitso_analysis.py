import os
import requests
import pandas as pd
from dotenv import load_dotenv
import matplotlib.pyplot as plt

# ─── Configuration ─────────────────────────────────────────────────────────────
load_dotenv()  
BASE_URL = "https://api.bitso.com/v3"

# ─── Fetch Function ────────────────────────────────────────────────────────────
def fetch_order_book(book: str, aggregate: bool = False, limit: int = None) -> dict:
    params = {
        "book": book,
        "aggregate": str(aggregate).lower()
    }
    if limit is not None:
        params["limit"] = limit

    resp = requests.get(f"{BASE_URL}/order_book/", params=params)
    resp.raise_for_status()
    return resp.json()["payload"]

# ─── Build DataFrame ───────────────────────────────────────────────────────────
def order_book_df(book: str, aggregate: bool = False, limit: int = None) -> pd.DataFrame:
    payload = fetch_order_book(book, aggregate, limit)
    
    # Each side as its own DataFrame
    bids = pd.DataFrame(payload["bids"])
    bids["side"] = "bid"
    
    asks = pd.DataFrame(payload["asks"])
    asks["side"] = "ask"
    
    # Combine both, keep original ordering if you like
    df = pd.concat([bids, asks], ignore_index=True)
    # Optionally convert numeric columns
    df["price"] = df["price"].astype(float)
    df["amount"] = df["amount"].astype(float)
    
    # And maybe sort by side & price
    df = df.sort_values(["side", "price"], ascending=[False, False]).reset_index(drop=True)
    return df

def custom_order_book_df(df:pd.DataFrame, pct:float):

    # Amount in minor
  df["amount_minor"] = df["amount"]* df["price"]
  
  # Amount in major
  df["amount_major"] =  df["amount"]
  
  # Separate bids and asks
  bids = df[df["side"] == "bid"].sort_values("price", ascending=False)
  asks = df[df["side"] == "ask"].sort_values("price", ascending=True)

  # Compute cumulative depth
  bids["cum_amount_major"] = bids["amount"].cumsum()
  asks["cum_amount_major"] = asks["amount"].cumsum()
  
  bids["cum_amount_minor"] = bids["amount_minor"].cumsum()
  asks["cum_amount_minor"] = asks["amount_minor"].cumsum()
  
  
  # Determine top book prices
  top_bid = df[df["side"] == "bid"]["price"].max()
  top_ask = df[df["side"] == "ask"]["price"].min()

  # Define ±5% bounds
  bid_lower = top_bid * (1 - pct)
  ask_upper = top_ask * (1 + pct)

  # Filter to within bounds
  bids_f = df[(df["side"] == "bid") & (df["price"] >= bid_lower)].sort_values("price", ascending=False)
  asks_f = df[(df["side"] == "ask") & (df["price"] <= ask_upper)].sort_values("price")

  # Compute cumulative depth
  bids_f["cum_amount_major"] = bids_f["amount"].cumsum()
  asks_f["cum_amount_major"] = asks_f["amount"].cumsum()
  

  # Recalculate spread
  spread = ((top_ask - top_bid)/((top_ask + top_bid)/2))*100
  return spread, bids_f, asks_f, bids, asks, top_bid, top_ask


def print_order_book(df: pd.DataFrame, book: str = "usd_mxn"):
  major=book.split("_")[0]
  minor=book.split("_")[1]
  # Values for plot
  spread=df[0]
  bids_f=df[1]
  asks_f=df[2]

  # Plot depth chart zoomed to x%
  plt.figure()
  plt.plot(bids_f["price"], bids_f["cum_amount_major"], label="Bid depth")
  plt.plot(asks_f["price"], asks_f["cum_amount_major"], label="Ask depth")
  plt.xlabel("Rate")
  plt.ylabel(f"Depth in {major.upper()}")
  plt.title(f"Order Book Depth for {book.upper()} (±{percentage*100}% around top levels)\nSpread: {spread:.4f}% / {spread*100:.2f}bp")
  plt.legend()
  plt.grid(True)
  plt.show()

def simulate_slippage(df: pd.DataFrame, size: float, side: str = "buy") -> float:
    """
    Simulate market order execution slippage.
    :param df: order book DataFrame with columns ['price','amount','side']
    :param size: quantity in major currency (e.g., USD) to trade
    :param side: 'buy' or 'sell'
    :return: slippage percentage based on top-of-book price
    """
    # choose asks for buys, bids for sells
    book = df[df["side"] == ("ask" if side=="buy" else "bid")].copy()
    # sort: ascending for asks, descending for bids
    book = book.sort_values("price", ascending=(side=="buy"))
    
    remaining = size
    cost = 0.0
    for _, row in book.iterrows():
        trade_amount = min(remaining, row["amount"])
        cost += trade_amount * row["price"]
        remaining -= trade_amount
        if remaining <= 0:
            break
    if remaining > 0:
        raise ValueError("Order size exceeds available depth")
    
    avg_price = cost / size
    top_price = book["price"].iloc[0]
    slippage = abs((avg_price - top_price) / top_price * 100)
    no_slippage_amount = top_price*size
    if side == "buy":
        money_loss=abs(((top_price - avg_price)*size)/top_price)
    else:
      money_loss=(top_price - avg_price)*size
    return avg_price, slippage, no_slippage_amount, cost, top_price, remaining, money_loss
    
def slippage_scenarios(df: pd.DataFrame, side: str = "buy", multiplier:float=1 ,sizes:list=[]):
  # Simulate for each
  slippage = []
  result_vector = [item * multiplier for item in sizes]
  for s in result_vector:
      simulations=simulate_slippage(df, size=s, side=side)
      r1 = simulations[0]
      r2 = simulations[1]
      r4 = simulations[2]
      r6 = simulations[4]
      r3 = simulations[6]
      slippage.append({"order_size": s,
                      "avg_price": r1,
                      "slippage_pct": r2, 
                      "would_recevied":r4,                  
                      "top_price":r6,                  
                      "money_loss":r3})
  results_df = pd.DataFrame(slippage)
  return results_df

def print_slippage_report(df: pd.DataFrame, side: str = "buy",book: str = "usd_mxn"):
    """
    Print a human‐readable slippage & loss report for each row of df.
    Expects df to have columns: 
      'order_size', 'avg_price', 'slippage_pct', 'money_loss'
    """
    major=book.split("_")[0]
    minor=book.split("_")[1]
    for _, row in df.iterrows():
        size    = row["order_size"]
        avg     = row["avg_price"]
        slip    = row["slippage_pct"]
        loss    = row["money_loss"]
        
        if side.lower() == "buy":
            # loss is money you pay extra (in minor currency, e.g. MXN)
            print(
                f"For an order of {size:,.0f} {major}, the average price would be "
                f"{avg:.4f} {minor}; with slippage of {slip:.2f}%, you would have "
                f"received {loss:,.2f} {major} less for that order size."
            ) 
        else:
            # loss is money you receive extra on a sell
            print(
                f"For an order of {size:,.0f} {major}, the average price would be "
                f"{avg:.4f} {minor}; with slippage of {slip:.2f}%, you would have "
                f"received an extra {loss:,.2f} {minor} for that order size."
            )
