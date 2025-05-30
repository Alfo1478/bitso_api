# Bitso Order Book Analysis & Slippage Simulator

A lightweight Python toolkit to fetch and analyze Bitso order‐book data, plot market depth, and simulate market‐order slippage and monetary loss for arbitrary trade sizes.

---

## 🚀 Features

- **Fetch & parse** Bitso public REST order‐book (no API key required)
- **Build a Pandas DataFrame** with bids/asks, prices, volumes
- **Zoomed depth chart** around the best bid/ask (± X% window)
- **Slippage simulation** for market orders of any size (buy or sell)
- **Money‐loss calculation**: extra cost or shortfall vs. top‐of‐book execution
- **Human‐friendly report** summarizing average price, slippage %, and loss

---

![Screenshot 2025-05-30 at 4 05 25 p m](https://github.com/user-attachments/assets/37086555-95e4-484d-ad21-26c5166e1341)
