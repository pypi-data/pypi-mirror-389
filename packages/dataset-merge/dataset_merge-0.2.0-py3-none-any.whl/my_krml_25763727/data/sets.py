import pandas as pd
from typing import List, Union

def merge_datasets(df1: pd.DataFrame, df2: pd.DataFrame, on_field: str, how: str = "inner") -> pd.DataFrame:
    """
    Merge two datasets on a user-specified field.
    """
    if on_field not in df1.columns or on_field not in df2.columns:
        raise ValueError(f"'{on_field}' must exist in both datasets")
    
    merged_df = pd.merge(df1, df2, on=on_field, how=how)
    return merged_df


def convert_to_csv(input_path: str, output_path: str) -> None:
    """
    Convert a semicolon-delimited file (with or without quotes) to a standard comma-delimited CSV file.
    Cleans up unnecessary quotes around values.
    """
    try:
        df = pd.read_csv(
            input_path,
            sep=';',
            quotechar='"',
            skipinitialspace=True,
            engine='python'
        )
        # Clean any stray quotes in string cells
        df = df.applymap(lambda x: x.strip('"') if isinstance(x, str) else x)

        df.to_csv(output_path, index=False)
        print(f"Converted '{input_path}' to standard CSV format at '{output_path}'")

    except Exception as e:
        raise RuntimeError(f"Error converting file '{input_path}': {e}")

def union_datasets(datasets: List[Union[str, pd.DataFrame]]) -> pd.DataFrame:
    """
    Union (concatenate) multiple datasets into one.
    Accepts a list of file paths or pandas DataFrames.
    """
    dfs = []
    for data in datasets:
        if isinstance(data, str):
            df = pd.read_csv(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise TypeError("Each dataset must be a file path or a pandas DataFrame.")
        dfs.append(df)

    # Align columns automatically
    combined_df = pd.concat(dfs, ignore_index=True, sort=False)
    print(f"Union completed. Combined shape: {combined_df.shape}")
    return combined_df
