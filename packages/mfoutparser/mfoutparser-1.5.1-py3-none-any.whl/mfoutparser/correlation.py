# coding: utf-8
from .read import DataFrame

def make_correlation_matrices(dataframe):
    """Convert a dataframe of correlation data into a matrix

       Input: Pandas dataframe containing correlation data

       Output: Pandas dataframe with data manipulated into matrices
    """

    # Group the data by residue then use a pivot table-like function
    # to create correlation matrices
    if 'residue' in dataframe.index.names:
        correlation_group = dataframe.reset_index().groupby('residue')
    else:
        correlation_group = dataframe.groupby('residue')

    # Use .pivot instead of deprecated .pivot_table, and avoid deprecated apply with groupby
    correlation_matrix = correlation_group.apply(
        lambda x: x.pivot(index='model_free_name_1', 
                          columns='model_free_name_2', 
                          values='covariance')
    )

    # Remove deprecated .ix, .as_matrix, etc. (none here)
    # Convert to DataFrame (custom)
    correlation_matrix = DataFrame(correlation_matrix)

    # Pandas groupby doesn't preserve the print formatter
    correlation_matrix = correlation_matrix.__finalize__(dataframe, method='copy')

    # Append columns for each of the parameters in 'model_free_name_2'
    new_col_names = dataframe['model_free_name_2'].unique()

    for col in new_col_names:
        # Use .get to avoid KeyError if 'covariance' absent
        covariance_fmt = correlation_matrix._print_format.get('covariance', '{}')
        correlation_matrix._print_format[col] = covariance_fmt

    return correlation_matrix