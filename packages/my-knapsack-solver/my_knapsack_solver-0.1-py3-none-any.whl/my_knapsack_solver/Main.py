def knapSack(W, wt, val, n):
    """
    Solves the 0/1 Knapsack problem using dynamic programming.

    Args:
        W (int): Maximum weight capacity of the knapsack.
        wt (list): List of weights of the n items.
        val (list): List of values of the n items.
        n (int): Number of items.

    Returns:
        int: The maximum value that can be put in the knapsack.
    """
    
    # Create a DP table to store results of subproblems
    # K[i][w] will store the maximum value that can be achieved
    # with a capacity of w using the first i items.
    K = [[0 for x in range(W + 1)] for i in range(n + 1)]

    # Build table K[][] in bottom-up manner
    for i in range(n + 1):
        for w in range(W + 1):
            if i == 0 or w == 0:
                # Base case: no items or no capacity
                K[i][w] = 0
            elif wt[i - 1] <= w:
                # If the weight of the i-th item is less than or equal
                # to the current capacity w, we have two choices:
                # 1. Include the item: Add its value and the max value
                #    from remaining capacity and remaining items.
                # 2. Exclude the item: Take the max value from the
                #    previous (i-1) items with the same capacity w.
                K[i][w] = max(val[i - 1] + K[i - 1][w - wt[i - 1]], K[i - 1][w])
            else:
                # If the item's weight is more than the current capacity,
                # we must exclude it.
                K[i][w] = K[i - 1][w]

    # The result is in the bottom-right corner of the table
    return K[n][W]

# --- Example Usage ---
if __name__ == "__main__":
    item_values = [60, 100, 120]
    item_weights = [10, 20, 30]
    knapsack_capacity = 50
    num_items = len(item_values)

    max_value = knapSack(knapsack_capacity, item_weights, item_values, num_items)
    
    print(f"Item Values: {item_values}")
    print(f"Item Weights: {item_weights}")
    print(f"Knapsack Capacity: {knapsack_capacity}")
    print("---------------------------------")
    print(f"Maximum value in knapsack: {max_value}") 
    # Expected output: 220 (by picking items with weight 20 and 30)