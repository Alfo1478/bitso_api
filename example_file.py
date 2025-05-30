# Getting the data
book="usd_mxn"

# This parameter works when showing the depth of the book as follows: the shown depth would be based on top_of_the_book_rate+-percentage
# for instance if the top of the book is 19.50 with a percentage=0.1 (10%) then the depth would consider the amounts within (17.55 - 21.45)
percentage=0.05

# Calling the order book
df = order_book_df(book=book, aggregate=False)

# Printing the order book
results=custom_order_book_df(df, pct=percentage)
print_order_book(results, book)

# slippage simulation
multiplier=100000
sizes = [1,2,3,4,5]
side="sell"
results_df=slippage_scenarios(df, side=side, multiplier=multiplier, sizes=sizes)
print_slippage_report(results_df,side=side,book=book)
