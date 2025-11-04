import pandas as pd
from pathlib import Path

def fetch_mumbai_housing(as_frame=True):
    """
    Fetch the Mumbai housing dataset.

    Parameters
    ----------
    as_frame : bool, default=True
        If True, returns a dictionary with pandas DataFrame and Series.
        If False, returns numpy arrays.

    Returns
    -------
    dataset : dict
        A dictionary containing:
        - 'data': pandas DataFrame of features
        - 'target': pandas Series of target (price)
        - 'feature_names': list of feature column names
        - 'DESCR': short description of the dataset
    """
    # Step 1: Locate CSV file inside data folder
    data_path = Path(__file__).resolve().parent / "data" / "mumbai_housing.csv"

    # Step 2: Read dataset
    df = pd.read_csv(data_path)

    # Step 3: Define target and features
    target = df["price"]
    features = df.drop("price", axis=1)

    # Step 4: Create description
    description = (
        "Mumbai Housing Dataset\n\n"
        "Features include price per sqft, total sqft, BHK, floor number, and location.\n"
        "Target variable: price (in INR)\n"
        "Source: Synthetic Housing Data - Mumbai Apartments"
    )

    # Step 5: Return in sklearn-style format
    if as_frame:
        return {
            "data": features,
            "target": target,
            "feature_names": features.columns.tolist(),
            "DESCR": description
        }
    else:
        return features.values, target.values
