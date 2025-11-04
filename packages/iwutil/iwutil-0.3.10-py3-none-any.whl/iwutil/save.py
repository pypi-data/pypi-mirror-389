from pathlib import Path
from json import dump
from functools import singledispatch


def create_folder(filename):
    """
    Create a folder if it does not exist

    Parameters
    ----------
    filename : str
        File name in the folder to create
    """
    Path(filename).parent.mkdir(parents=True, exist_ok=True)


def json(params, filename):
    """
    Save params to a json file

    Parameters
    ----------
    params : dict
        Dictionary of parameters
    filename : str
        Full path and name of the file to save
    """
    create_folder(filename)
    with open(filename, "w") as f:
        dump(params, f, indent=2)


@singledispatch
def csv(df, filename):
    """
    Save df to a csv file

    Parameters
    ----------
    df : pandas.DataFrame or polars.DataFrame
        DataFrame to save
    filename : str
        Full path and name of the file to save
    """
    raise NotImplementedError(f"CSV save not implemented for type {type(df)}")


# Register pandas DataFrame support
try:
    import pandas as pd

    @csv.register
    def _(df: pd.DataFrame, filename):
        """Save pandas DataFrame to CSV"""
        create_folder(filename)
        df.to_csv(filename, index=False)
except ImportError:
    pass

# Register polars DataFrame support
try:
    import polars as pl

    @csv.register
    def _(df: pl.DataFrame, filename):
        """Save polars DataFrame to CSV"""
        create_folder(filename)
        df.write_csv(filename)
except ImportError:
    pass


@singledispatch
def parquet(df, filename):
    """
    Save df to a parquet file

    Parameters
    ----------
    df : pandas.DataFrame or polars.DataFrame
        DataFrame to save
    filename : str
        Full path and name of the file to save
    """
    raise NotImplementedError(f"Parquet save not implemented for type {type(df)}")


# Register pandas DataFrame support
try:
    import pandas as pd

    @parquet.register
    def _(df: pd.DataFrame, filename):
        """Save pandas DataFrame to Parquet"""
        create_folder(filename)
        df.to_parquet(filename)
except ImportError:
    pass

# Register polars DataFrame support
try:
    import polars as pl

    @parquet.register
    def _(df: pl.DataFrame, filename):
        """Save polars DataFrame to Parquet"""
        create_folder(filename)
        df.write_parquet(filename)
except ImportError:
    pass


@singledispatch
def txt(df, filename):
    """
    Save df to a txt file (tab-separated)

    Parameters
    ----------
    df : pandas.DataFrame or polars.DataFrame
        DataFrame to save
    filename : str
        Full path and name of the file to save
    """
    raise NotImplementedError(f"TXT save not implemented for type {type(df)}")


# Register pandas DataFrame support
try:
    import pandas as pd

    @txt.register
    def _(df: pd.DataFrame, filename):
        """Save pandas DataFrame to tab-separated TXT"""
        create_folder(filename)
        df.to_csv(filename, index=False, sep="\t")
except ImportError:
    pass

# Register polars DataFrame support
try:
    import polars as pl

    @txt.register
    def _(df: pl.DataFrame, filename):
        """Save polars DataFrame to tab-separated TXT"""
        create_folder(filename)
        df.write_csv(filename, separator="\t")
except ImportError:
    pass


def fig(fig_to_save, filename):
    """
    Save fig to a file

    Parameters
    ----------
    fig_to_save : matplotlib.figure.Figure
        Figure to save
    filename : str
        Full path and name of the file to save
    """
    create_folder(filename)
    fig_to_save.savefig(filename)
