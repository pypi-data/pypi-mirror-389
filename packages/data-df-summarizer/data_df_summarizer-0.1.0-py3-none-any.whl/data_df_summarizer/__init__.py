import pandas as pd

def summarize(df: pd.DataFrame):
    """
    Prints a quick summary of a pandas DataFrame:
    - Shape (rows, columns)
    - Column names
    - Missing values count
    - Numeric column stats (mean, min, max)
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame")

    print("\nDataFrame Summary")
    print("-" * 40)
    print(f"Shape: {df.shape}")
    print(f"Columns: {', '.join(df.columns)}")

    missing = df.isnull().sum().sum()
    print(f"Missing Values: {missing}")

    num_cols = df.select_dtypes(include=['int', 'float'])
    if not num_cols.empty:
        print("\nNumeric Columns Summary:")
        summary = num_cols.describe().loc[['mean', 'min', 'max']]
        print(summary.round(2))
    else:
        print("\nNo numeric columns found.")

    print("-" * 40)
    print("Summary complete.\n")
