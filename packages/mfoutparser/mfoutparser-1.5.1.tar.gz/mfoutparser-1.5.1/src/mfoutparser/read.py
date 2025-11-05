# coding: utf-8
import re
import sys
import pandas as pd
from pandas import DataFrame as pd_DataFrame
import numpy as np
from collections import OrderedDict

### A custom class to handle display and formatting of data during output

class DataFrame(pd_DataFrame):
    """Custom DataFrame for Model-Free output parsing.

    - Filters out NaN values when displaying in Jupyter/IPython.
    - Has a _print_format attribute for tracking float formatting.
    """

    _metadata = ['_print_format']

    @property
    def _constructor(self):
        return DataFrame

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._print_format = dict()

    def __finalize__(self, other, method=None, **kwargs):
        if isinstance(other, pd.core.generic.NDFrame):
            for name in self._metadata:
                val = getattr(other, name, None)
                if method is None:
                    object.__setattr__(self, name, val)
                elif method == 'copy' and hasattr(val, 'copy'):
                    object.__setattr__(self, name, val.copy())
                else:
                    object.__setattr__(self, name, val)
        return self

    def _repr_html_(self):
        # Display with NaNs replaced by ''
        return super(DataFrame, self.replace(np.nan, ''))._repr_html_()

    def copy(self, deep=True):
        cp = super().copy(deep=deep)
        return cp.__finalize__(self, method='copy')

    def to_csv(self, filename, preserve_format=True,
               sep='\t', na_rep='', index=None, *args, **kwargs):
        dataframe = self
        if index is None:
            index = True
            if ((None in self.index.names) and (len(self.index.names) == 1)):
                index = False

        if preserve_format and hasattr(self, '_print_format'):
            format_dict = self._print_format.copy()
            dataframe = self.copy()
            if index:
                dataframe = dataframe.reset_index()
                index = False
            if isinstance(na_rep, (int, float)):
                dataframe = dataframe.replace(np.nan, na_rep)
            for key, format_string in format_dict.items():
                if key in dataframe.columns:
                    dataframe[key] = dataframe[key].apply(lambda x: format_string.format(x) if pd.notna(x) else na_rep)
            if isinstance(na_rep, str):
                dataframe = dataframe.replace(r"[Nn][Aa][Nn]", na_rep, regex=True)
        super(DataFrame, dataframe).to_csv(filename, sep=sep, na_rep=na_rep, index=index, *args, **kwargs)

def parse_mfout(mfoutfilename):
    """Parse a ModelFree output file. Returns tag_dict and loop_dict."""
    tag_data_dict = _parse_mfoutfile(mfoutfilename)

    tag_dict = OrderedDict()
    loop_dict = OrderedDict()

    for key, text_list in tag_data_dict.items():
        text_loops, text_tags = _split_loop_and_tag_text(text_list)
        if text_tags:
            text_dict_tags = _convert_tags_to_dict(text_tags)
            text_df_tags = _convert_tags_to_df(text_dict_tags)
            tag_dict[key] = text_df_tags
        if text_loops:
            text_df_loops = _convert_loops_to_df(text_loops)
            loop_dict[key] = text_df_loops

    loop_dict = _clean_up_loop_dict(loop_dict)
    tag_dict = _clean_up_tag_dict_tags(tag_dict)
    loop_dict = _clean_up_table_column_names(loop_dict)
    tag_dict = _coerce_and_store_data_types(tag_dict)
    loop_dict = _coerce_and_store_data_types(loop_dict)

    # Remove 'data_' prefix from keys
    tag_dict = OrderedDict((k.replace('data_', ''), v) for k, v in tag_dict.items())
    loop_dict = OrderedDict((k.replace('data_', ''), v) for k, v in loop_dict.items())

    return tag_dict, loop_dict

def _parse_mfoutfile(mfoutfilename):
    """Read ModelFree file and split into tag dictionary."""
    with open(mfoutfilename, 'r') as f:
        file_string = f.read()

    file_string = re.sub(r'\r\n', '\n', file_string)
    file_string = re.sub(r'(^\s?#.+|^\s?)\n', '', file_string, flags=re.MULTILINE)
    file_string = re.sub(r'\n{2,}', '\n', file_string)
    file_string = file_string.strip()
    split_list = re.split(r'\n(?=data_.+?\n)', file_string, flags=re.MULTILINE | re.DOTALL)
    tag_data_list = [re.search(r'(data_.+?)\n(.+)', x, flags=re.MULTILINE | re.DOTALL)
                     for x in split_list]
    tag_data_dict = OrderedDict(
        (x.group(1).strip(), x.group(2))
        for x in tag_data_list if x is not None
    )
    return tag_data_dict

def _split_loop_and_tag_text(text_list):
    """Split text into loop and tag lists."""
    text_list = text_list.split('\n')
    text_df = pd.DataFrame(text_list, columns=['text'])
    text_df['text'] = text_df['text'].str.strip()
    text_df['tag'] = text_df['text'].str.contains(r'_\w+', regex=True)
    text_df['loop'] = text_df['text'].str.contains('loop_')
    # The line below the tag is always part of the tag group
    tag_indices = text_df.index[text_df['loop']]
    text_df.loc[tag_indices + 1, 'loop'] = True
    text_df.loc[(~text_df['tag']) & (~text_df['loop']), 'loop'] = True
    text_df_tags = text_df.loc[~text_df['loop'], 'text'].tolist()
    text_df_loop = text_df.loc[text_df['loop'], 'text'].tolist()
    return text_df_loop, text_df_tags

def _convert_tags_to_dict(text_list_tags):
    """Convert tag lines to a dictionary."""
    out = []
    for row in text_list_tags:
        m = re.findall(r'\s*_(\w+)\s+(.+?)\s*$', row)
        if m:
            out.append(m[0])
    return OrderedDict(out)

def _convert_tags_to_df(text_dict_tags):
    """Convert tag dict to DataFrame."""
    return DataFrame({'tag': [item[0] for item in text_dict_tags.items()],
                      'value': [item[1] for item in text_dict_tags.items()]})

def _clean_up_tag_dict_tags(tag_dict):
    """Make all tag labels lowercase and remove leading underscore."""
    for key in tag_dict:
        tag_dict[key]['tag'] = tag_dict[key]['tag'].str.lower()
        tag_dict[key]['tag'] = tag_dict[key]['tag'].str.replace(r'^_', '', regex=True)
    return tag_dict

def _convert_loops_to_df(text_loops):
    """Classify all data and convert to DataFrame."""
    df_loop = DataFrame(text_loops, columns=['text'])
    df_loop = _set_loops(df_loop)
    df_loop = _set_labels(df_loop)
    df_loop = _set_stops(df_loop)
    df_loop = _set_values(df_loop)
    df_list = _extract_loop_data(df_loop)
    return df_list

def _clean_up_loop_dict(loop_dict):
    """Handle data_header entries in loop_dict."""
    if 'data_header' in loop_dict:
        header_df_list = loop_dict.pop('data_header')
        if isinstance(header_df_list, list):
            for idx, df in enumerate(header_df_list):
                loop_dict[f'data_header_{idx+1}'] = df
        else:
            loop_dict['data_header_1'] = header_df_list
    return loop_dict

def _clean_up_table_column_names(loop_dict):
    """Make column names lowercase, remove leading underscores."""
    for key in loop_dict:
        rename_dict = {x: re.sub(r'^_', '', x.lower()) for x in loop_dict[key].columns}
        loop_dict[key].rename(columns=rename_dict, inplace=True)
    return loop_dict

def _set_loops(loop_data):
    loop_data['loop'] = 0
    loop_data.loc[loop_data['text'].str.contains('loop_'), 'loop'] = 1
    old_columns = loop_data.columns
    loop_data = loop_data.reset_index(drop=False)
    index_column = list(set(loop_data.columns) - set(old_columns))
    loop_index = loop_data.index[loop_data['loop'] == 1]
    loop_diff = loop_index[1:] - loop_index[:-1]
    depth = 0
    for idx, diff in zip(loop_index[:-1], loop_diff):
        if diff <= 2:
            depth += 1
            loop_data.loc[idx, 'loop'] += depth
        else:
            depth = 0
    loop_data.set_index(index_column, drop=True)
    if 'index' in loop_data.columns:
        loop_data = loop_data.drop(['index'], axis=1)
    return loop_data

def _set_labels(loop_data):
    old_columns = loop_data.columns
    loop_data = loop_data.reset_index(drop=False)
    index_column = list(set(loop_data.columns) - set(old_columns))
    tag_values = loop_data['loop'][loop_data['loop'] != 0].tolist()
    tag_index = loop_data.index[loop_data['loop'] != 0] + 1
    loop_data['tag'] = 0
    loop_data.loc[tag_index, 'tag'] = tag_values
    loop_data.set_index(index_column, drop=True)
    if 'index' in loop_data.columns:
        loop_data = loop_data.drop(['index'], axis=1)
    return loop_data

def _set_stops(loop_data):
    loop_data['stop'] = 0
    loop_data.loc[loop_data['text'].str.contains('stop_'), 'stop'] = 1
    return loop_data

def _set_values(loop_data):
    value_indexes = loop_data.index[(loop_data['loop'] == 0) & (loop_data['tag'] == 0) & (loop_data['stop'] == 0)]
    loop_data['value'] = 0
    loop_data.loc[value_indexes, 'value'] = 1
    value_indexes_begin = (value_indexes - 1)[loop_data['value'][value_indexes - 1] == 0] + 1
    loop_max = loop_data['loop'].max()
    loop_range = np.arange(loop_max-1, -1, -1)
    for idx in value_indexes_begin:
        loop_data.loc[idx:idx+len(loop_range)-1, 'value'] += loop_range
    return loop_data

def _extract_loop_data(loop_data):
    max_level = loop_data['loop'].max()
    loop_index_begin = loop_data.index[loop_data['loop'] == max_level]
    loop_index_end = np.append(loop_index_begin[1:] - 1, [len(loop_data)])
    outer_df_list = []
    for lim in zip(loop_index_begin, loop_index_end):
        level_data = loop_data.loc[lim[0]:lim[1]]
        level_data_index = level_data.index[level_data['value'] == 1]
        inner_df_list = []
        inner_df_columns = []
        for level in range(max_level, 0, -1):
            tag_list = level_data['text'][level_data['tag'] == level].apply(lambda x: re.split(r'\s+', x))
            value_list = level_data['text'][level_data['value'] == level].apply(lambda x: re.split(r'\s+', x))
            if len(tag_list) == 0 or len(value_list) == 0:
                continue
            inner_df = pd.DataFrame(value_list.tolist(), columns=tag_list.tolist()[0], index=value_list.index)
            inner_df_list.append(inner_df)
            inner_df_columns += tag_list.tolist()[0]
        if inner_df_list:
            outer_df = pd.concat(inner_df_list).sort_index().ffill()
            outer_df = outer_df.loc[level_data_index]
            outer_df = DataFrame(outer_df, columns=inner_df_columns).reset_index(drop=True)
            outer_df_list.append(outer_df)
    if len(outer_df_list) == 1:
        return outer_df_list[0]
    else:
        return outer_df_list

def to_numeric_safe(x):
    try:
        return pd.to_numeric(x)
    except ValueError:
        return x

def _coerce_and_store_data_types(tag_loop_dict):
    regex_format = re.compile(r'\d*\.(?P<decimal>\d+)(?:[Ee]?[+-]?(?P<exponent>\d?))')
    for key in tag_loop_dict:
        if 'data_header' not in key:
            tmp = tag_loop_dict[key].copy()
            # tag_loop_dict[key] = tag_loop_dict[key].apply(lambda x: pd.to_numeric(x, errors='coerce'))
            tag_loop_dict[key] = tag_loop_dict[key].apply(lambda x: to_numeric_safe(x))
            float_cols = [x for x in tag_loop_dict[key].columns if pd.api.types.is_float_dtype(tag_loop_dict[key][x])]
            decimal_format = {}
            exponent_format = {}
            for col in float_cols:
                decimals = tmp[col].apply(lambda x: len(re.search(regex_format, str(x)).group('decimal')) if re.search(regex_format, str(x)) else 0)
                decimal_format[col] = decimals.max()
                exponents = tmp[col].apply(lambda x: len(re.search(regex_format, str(x)).group('exponent')) if re.search(regex_format, str(x)) else 0)
                exponent_format[col] = exponents.max()
            number_format = {col: 'f' if exponent_format[col] == 0 else 'E' for col in float_cols}
            formatter = {col: '{:.' + str(decimal_format[col]) + number_format[col] + '}' for col in float_cols}
            tag_loop_dict[key]._print_format = formatter
    return tag_loop_dict
