"""
pandas DataFrame utility functions for data analysis and manipulation.

This module provides utilities for:
- Converting data types within DataFrames
- Analyzing column structures across multiple DataFrames
- Finding and extracting rows/columns with missing or empty data
- Data quality validation and exploration
- Integer allocation using mathematical methods
- Value rebalancing to eliminate negative values

Required dependencies:
    pip install qufe[data]

This installs: pandas>=1.1.0, numpy>=1.17.0
"""

from typing import List, Tuple, Dict, Any, Optional, Union
import warnings


class PandasHandler:
    """
    pandas DataFrame utility handler for data analysis and manipulation.

    Provides methods for converting data types, analyzing column structures,
    finding missing data, data quality validation, and mathematical allocation.

    Args:
        default_exclude_cols: Default columns to exclude from NA/empty checks.
                            Can be overridden in individual method calls.

    Raises:
        ImportError: If pandas is not installed

    Example:
        >>> handler = PandasHandler(default_exclude_cols=['id', 'created_at'])
        >>> result = handler.convert_list_to_tuple_in_df(df)
    """

    def __init__(self, default_exclude_cols: Optional[List[str]] = None):
        """Initialize PandasHandler with dependency validation."""
        self.pd = self._import_pandas()
        self.np = self._import_numpy()
        self.default_exclude_cols = default_exclude_cols or []

    def _import_pandas(self):
        """Lazy import pandas with helpful error message."""
        try:
            import pandas as pd
            return pd
        except ImportError as e:
            raise ImportError(
                "Data processing functionality requires pandas. "
                "Install with: pip install qufe[data]"
            ) from e

    def _import_numpy(self):
        """Lazy import numpy with helpful error message."""
        try:
            import numpy as np
            return np
        except ImportError as e:
            raise ImportError(
                "Data processing functionality requires numpy. "
                "Install with: pip install qufe[data]"
            ) from e

    def _validate_dataframe(self, df) -> None:
        """
        Validate that input is a pandas DataFrame.

        Args:
            df: Object to validate

        Raises:
            TypeError: If input is not a pandas DataFrame
        """
        if not isinstance(df, self.pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame")

    def help(self) -> None:
        """
        Display help information for pandas DataFrame utilities.

        Shows installation instructions, available methods, and usage examples.
        """
        print("qufe.pdhandler.PandasHandler - pandas DataFrame Utilities")
        print("=" * 60)
        print()
        print("✓ Dependencies: INSTALLED")
        print()

        print("AVAILABLE METHODS:")
        print("  • convert_list_to_tuple_in_df(): Convert list values to tuples in DataFrame")
        print("  • show_col_names(): Compare column names across multiple DataFrames")
        print("  • show_all_na(): Extract rows and columns containing NA values")
        print("  • show_all_na_or_empty_rows(): Find rows with NA or empty string values")
        print("  • show_all_na_or_empty_columns(): Find columns with NA or empty string values")
        print("  • allocate_integer_remainder(): Allocate fractional values as integers")
        print("  • rebalance_negative_values(): Redistribute to eliminate negative values")
        print("  • calculate_cumulative_balance(): Calculate running balance with segment resets")
        print()

        print("USAGE EXAMPLES:")
        print("  from qufe.pdhandler import PandasHandler")
        print("  ")
        print("  # Initialize handler")
        print("  handler = PandasHandler(default_exclude_cols=['id'])")
        print("  ")
        print("  # Compare columns across DataFrames")
        print("  col_dict, comparison_df = handler.show_col_names([df1, df2, df3])")
        print("  ")
        print("  # Find all NA values in subset")
        print("  na_subset = handler.show_all_na(df)")
        print("  ")
        print("  # Find problematic rows/columns")
        print("  problem_rows = handler.show_all_na_or_empty_rows(df)")
        print("  ")
        print("  # Integer allocation")
        print("  result = handler.allocate_integer_remainder(df, 'group', 'value')")
        print("  ")
        print("  # Rebalance negative values")
        print("  result = handler.rebalance_negative_values(df, 'group', 'amount')")
        print("  ")
        print("  # Cumulative balance calculation")
        print("  result = handler.calculate_cumulative_balance(")
        print("      df, 'initial', 'inflow', 'outflow', 'new_segment'")
        print("  )")

    def convert_list_to_tuple_in_df(self, df) -> object:
        """
        Convert list values to tuples in DataFrame object columns.

        Preserves None values and other data types unchanged.
        Only processes columns with object dtype that contain list values.

        Args:
            df: Input DataFrame to process (pandas.DataFrame)

        Returns:
            DataFrame with list values converted to tuples

        Raises:
            TypeError: If input is not a pandas DataFrame

        Example:
            >>> handler = PandasHandler()
            >>> df = pd.DataFrame({'col1': [[1, 2], [3, 4]], 'col2': ['a', 'b']})
            >>> result = handler.convert_list_to_tuple_in_df(df)
            >>> print(result['col1'].iloc[0])
            (1, 2)
        """
        self._validate_dataframe(df)

        df_copy = df.copy()

        for col in df_copy.columns:
            if df_copy[col].dtype == "object" and df_copy[col].map(type).eq(list).any():
                df_copy[col] = df_copy[col].apply(lambda x: tuple(x) if isinstance(x, list) else x)

        return df_copy

    def show_col_names(self, dfs: List, print_result: bool = False) -> Tuple[Dict[str, List[str]], object]:
        """
        Compare column names across multiple DataFrames.

        Creates a comprehensive view of all columns present in the input DataFrames,
        showing which columns exist in each DataFrame.

        Args:
            dfs: List of DataFrames to compare (List[pandas.DataFrame])
            print_result: Whether to print the comparison table. Defaults to False.

        Returns:
            Tuple containing:
            - Dictionary mapping DataFrame names to column lists
            - Comparison DataFrame showing column presence across DataFrames

        Raises:
            TypeError: If input is not a list of DataFrames

        Example:
            >>> handler = PandasHandler()
            >>> df1 = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
            >>> df2 = pd.DataFrame({'B': [5, 6], 'C': [7, 8]})
            >>> col_dict, comparison_df = handler.show_col_names([df1, df2])
        """
        if not isinstance(dfs, list) or not all(isinstance(df, self.pd.DataFrame) for df in dfs):
            raise TypeError("Input must be a list of pandas DataFrames")

        # Create dictionary mapping each DataFrame to its column list
        all_df = {f'df_{idx + 1}': df.columns.to_list() for (idx, df) in enumerate(dfs)}

        # Get all unique column names across all DataFrames
        all_cols = list(set(col for df_cols in all_df.values() for col in df_cols))
        all_cols = sorted(all_cols)

        # Create comparison dictionary
        df_cols = {'All': all_cols}
        df_cols.update({
            df_name: [col if col in df_columns else '' for col in all_cols]
            for (df_name, df_columns) in all_df.items()
        })

        # Convert to DataFrame for easy viewing
        df_check = self.pd.DataFrame(data=df_cols)

        if print_result:
            print(df_check)

        return (df_cols, df_check)

    def show_all_na(self, df) -> object:
        """
        Extract rows and columns that contain NA values.

        Returns a subset of the original DataFrame containing only:
        - Rows that have at least one NA value
        - Columns that have at least one NA value

        Args:
            df: Input DataFrame to analyze (pandas.DataFrame)

        Returns:
            Subset containing only rows and columns with NA values

        Raises:
            TypeError: If input is not a DataFrame

        Example:
            >>> handler = PandasHandler()
            >>> import numpy as np
            >>> df = pd.DataFrame({'A': [1, np.nan], 'B': [3, 4], 'C': [np.nan, 6]})
            >>> na_subset = handler.show_all_na(df)
        """
        self._validate_dataframe(df)

        # Find rows with any NA values
        df_rows_na = df[df.isna().any(axis='columns')]

        # Find columns with any NA values
        df_cols_na = df.columns[df.isna().any()].to_list()

        # Return intersection: rows with NA values, showing only columns with NA values
        df_na = df_rows_na[df_cols_na]

        return df_na

    def show_all_na_or_empty_rows(self, df, exclude_cols: Optional[List[str]] = None) -> object:
        """
        Find rows containing NA values or empty strings.

        Identifies rows that have NA values or empty strings ('') in any column,
        with option to exclude specific columns from the check.

        Args:
            df: Input DataFrame to analyze (pandas.DataFrame)
            exclude_cols: Columns to exclude from NA/empty check.
                        If None, uses default_exclude_cols from initialization.

        Returns:
            Rows containing NA values or empty strings, with all original columns

        Raises:
            TypeError: If input is not a DataFrame

        Example:
            >>> handler = PandasHandler(default_exclude_cols=['id'])
            >>> df = pd.DataFrame({'A': [1, ''], 'B': [3, 4], 'id': ['x', 'y']})
            >>> problem_rows = handler.show_all_na_or_empty_rows(df)
        """
        self._validate_dataframe(df)

        if exclude_cols is None:
            exclude_cols = self.default_exclude_cols

        # Select columns to check (excluding specified columns)
        cols_to_check = [col for col in df.columns if col not in exclude_cols]
        df_check = df[cols_to_check]

        # Create mask for rows with NA values or empty strings
        mask_row = df_check.isna().any(axis=1) | (df_check == '').any(axis=1)

        # Return complete rows that match the criteria
        df_na_rows = df[mask_row]

        return df_na_rows

    def show_all_na_or_empty_columns(self, df, exclude_cols: Optional[List[str]] = None) -> object:
        """
        Find columns containing NA values or empty strings.

        Identifies columns that have NA values or empty strings ('') in any row,
        with option to exclude specific columns from the check.

        Args:
            df: Input DataFrame to analyze (pandas.DataFrame)
            exclude_cols: Columns to exclude from NA/empty check.
                        If None, uses default_exclude_cols from initialization.

        Returns:
            All rows, but only columns that contain NA values or empty strings

        Raises:
            TypeError: If input is not a DataFrame

        Example:
            >>> handler = PandasHandler(default_exclude_cols=['id'])
            >>> df = pd.DataFrame({'A': [1, 2], 'B': ['', 'x'], 'id': ['y', 'z']})
            >>> problem_cols = handler.show_all_na_or_empty_columns(df)
        """
        self._validate_dataframe(df)

        if exclude_cols is None:
            exclude_cols = self.default_exclude_cols

        # Select columns to check (excluding specified columns)
        cols_to_check = [col for col in df.columns if col not in exclude_cols]

        # Create mask for columns with NA values or empty strings
        mask_col = df[cols_to_check].isna().any(axis=0) | (df[cols_to_check] == '').any(axis=0)

        # Return all rows but only problematic columns
        df_na_cols = df.loc[:, mask_col.index[mask_col]]

        return df_na_cols

    def allocate_integer_remainder(
            self,
            df,
            group_cols: Union[str, List[str]],
            value_col: str,
            result_col: str = 'allocated',
            keep_intermediate: bool = False
    ) -> object:
        """
        Allocate fractional values to integers using the Largest Remainder Method.

        Also known as Hamilton's Method or Hare-Niemeyer method, this is a
        standard mathematical approach for proportional integer allocation while
        preserving group totals.

        The method works by:
        1. Taking the floor of each fractional value as the base allocation
        2. Distributing remaining units to items with largest fractional parts
        3. Ensuring the sum of allocated integers equals the floor of group sum

        Args:
            df: Input DataFrame containing the data to allocate
            group_cols: Column(s) to group by for allocation (str or list of str)
            value_col: Column containing fractional values to be allocated
            result_col: Name for the result column containing integer allocations.
                       Defaults to 'allocated'.
            keep_intermediate: If True, keep intermediate calculation columns.
                             Defaults to False.

        Returns:
            DataFrame with integer allocations in the result column

        Raises:
            TypeError: If input is not a pandas DataFrame
            KeyError: If specified columns don't exist in DataFrame

        References:
            .. [1] Hamilton, A. (1792). "Report on Apportionment"
            .. [2] Balinski, M. L., & Young, H. P. (2001). "Fair Representation:
                   Meeting the Ideal of One Man, One Vote"

        Example:
            >>> handler = PandasHandler()
            >>> data = pd.DataFrame({
            ...     'group': ['A', 'A', 'B', 'B'],
            ...     'value': [2.7, 1.8, 3.3, 2.2]
            ... })
            >>> result = handler.allocate_integer_remainder(data, 'group', 'value')
            >>> print(result[['group', 'value', 'allocated']])
        """
        self._validate_dataframe(df)

        # Input validation
        df = df.copy()
        if isinstance(group_cols, str):
            group_cols = [group_cols]

        # Check if columns exist
        missing_cols = set(group_cols + [value_col]) - set(df.columns)
        if missing_cols:
            raise KeyError(f"Columns not found in DataFrame: {missing_cols}")

        # Calculate group sum
        df['_group_sum'] = df.groupby(group_cols)[value_col].transform('sum')

        # Calculate base allocation (floor) and fractional remainder
        df['_base'] = self.np.floor(df[value_col]).astype('int32')
        df['_fraction'] = df[value_col] - df['_base']

        # Calculate allocated base sum and remaining units to distribute
        df['_base_sum'] = df.groupby(group_cols)['_base'].transform('sum')
        df['_remainder'] = self.np.floor(df['_group_sum']).astype('int32') - df['_base_sum']

        # Rank by fractional part (largest first) within groups
        df['_rank'] = df.groupby(group_cols)['_fraction'].rank(
            method='first',
            ascending=False
        )

        # Allocate: base + 1 if ranked within remainder count
        df[result_col] = (
                df['_base'] +
                (df['_rank'] <= df['_remainder']).astype('int32')
        ).astype('int32')

        # Clean up intermediate columns if requested
        if not keep_intermediate:
            intermediate_cols = [
                '_group_sum', '_base', '_fraction',
                '_base_sum', '_remainder', '_rank'
            ]
            df = df.drop(columns=intermediate_cols)

        return df

    def rebalance_negative_values(
            self,
            df,
            group_cols: Union[str, List[str]],
            value_col: str,
            result_col: str = 'rebalanced',
            use_offset: bool = False,
            keep_intermediate: bool = False
    ) -> object:
        """
        Redistribute values within groups to eliminate negatives while preserving totals.

        This function redistributes group totals to eliminate negative values while
        maintaining proportional relationships among positive values. It implements
        a weighted redistribution algorithm with optional offset handling.

        Args:
            df: Input DataFrame containing values to rebalance
            group_cols: Column(s) defining groups for rebalancing (str or list of str)
            value_col: Column containing values to rebalance (may include negatives)
            result_col: Name for the result column containing rebalanced values.
                       Defaults to 'rebalanced'.
            use_offset: If True, use offset method to include negative values in
                       weight calculation. If False, only positive values contribute
                       to redistribution weights. Defaults to False.
            keep_intermediate: If True, keep intermediate calculation columns.
                             Defaults to False.

        Returns:
            DataFrame with rebalanced values in the result column

        Raises:
            TypeError: If input is not a pandas DataFrame
            KeyError: If specified columns don't exist in DataFrame

        Notes:
            - Groups with negative total sum cannot be rebalanced (values unchanged)
            - Groups where all values are equal receive equal distribution
            - The offset method shifts all values by the minimum to calculate weights

        Example:
            >>> handler = PandasHandler()
            >>> data = pd.DataFrame({
            ...     'group': ['A', 'A', 'A', 'B', 'B'],
            ...     'value': [10, -5, 15, 20, -10]
            ... })
            >>> result = handler.rebalance_negative_values(data, 'group', 'value')
            >>> print(result[['group', 'value', 'rebalanced']])
        """
        self._validate_dataframe(df)

        # Input validation
        df = df.copy()
        if isinstance(group_cols, str):
            group_cols = [group_cols]

        # Check if columns exist
        missing_cols = set(group_cols + [value_col]) - set(df.columns)
        if missing_cols:
            raise KeyError(f"Columns not found in DataFrame: {missing_cols}")

        # Calculate group sum
        df['_sum'] = df.groupby(group_cols)[value_col].transform('sum').astype('int32')

        # Calculate weights for redistribution
        if use_offset:
            # Offset method: shift by minimum to make all values positive
            df['_min'] = df.groupby(group_cols)[value_col].transform('min').astype('int32')
            df['_offset'] = (-df['_min']).clip(lower=0).astype('int32')
            df['_weight'] = (df[value_col] + df['_offset']).astype('int32')
        else:
            # Standard method: use only non-negative values as weights
            df['_weight'] = self.np.maximum(df[value_col], 0).astype('int32')

        # Calculate weight sum per group
        df['_weight_sum'] = df.groupby(group_cols)['_weight'].transform('sum').astype('int32')

        # Calculate proportional allocation
        mask_valid = df['_weight_sum'] > 0
        df['_ratio'] = 0.0
        df.loc[mask_valid, '_ratio'] = (
                df.loc[mask_valid, '_weight'] / df.loc[mask_valid, '_weight_sum']
        )

        # Calculate ideal fractional allocation
        df['_ideal'] = df['_sum'] * df['_ratio']

        # Apply integer allocation using largest remainder method
        df['_base'] = self.np.floor(df['_ideal']).astype('int32')
        df['_fraction'] = df['_ideal'] - df['_base']

        # Calculate remainder to distribute
        df['_base_sum'] = df.groupby(group_cols)['_base'].transform('sum').astype('int32')
        df['_remainder'] = df['_sum'] - df['_base_sum']

        # Rank by fractional part for remainder distribution
        df['_rank'] = df.groupby(group_cols)['_fraction'].rank(
            method='first',
            ascending=False
        )

        # Final redistribution
        df[result_col] = (
                df['_base'] +
                (df['_rank'] <= df['_remainder']).astype('int32')
        ).astype('int32')

        # Handle special cases
        # Case 1: Zero weight sum (all weights are zero)
        mask_zero_weight = df['_weight_sum'] == 0
        df.loc[mask_zero_weight, result_col] = 0

        # Case 2: Negative group sum (cannot rebalance)
        mask_negative_sum = df['_sum'] < 0
        df.loc[mask_negative_sum, result_col] = df.loc[mask_negative_sum, value_col]

        # Clean up intermediate columns if requested
        if not keep_intermediate:
            intermediate_cols = [
                '_sum', '_weight', '_weight_sum', '_ratio', '_ideal',
                '_base', '_fraction', '_base_sum', '_remainder', '_rank'
            ]
            if use_offset:
                intermediate_cols.extend(['_min', '_offset'])

            existing_cols = [col for col in intermediate_cols if col in df.columns]
            df = df.drop(columns=existing_cols)

        return df

    def calculate_cumulative_balance(
            self,
            df,
            initial_col: str,
            inflow_col: str,
            outflow_col: str,
            segment_marker_col: str,
            result_col: str = 'balance',
            group_cols: Optional[Union[str, List[str]]] = None,
            keep_intermediate: bool = False
    ) -> object:
        """
        Calculate cumulative balance with segment-based reinitialization.

        Computes running balance where each segment (marked by a flag column) starts
        with an initial value and accumulates inflows minus outflows. This is commonly
        used for tracking any cumulative flow with periodic resets.

        The calculation follows these rules:
        - When segment marker is 1: balance = initial + inflow - outflow
        - When segment marker is 0: balance = previous_balance + inflow - outflow
        - Each group (if specified) is calculated independently

        This method uses vectorized operations for efficient computation on large datasets,
        avoiding explicit loops through clever use of cumulative sums and groupby operations.

        Args:
            df: Input DataFrame with flow data (must be pre-sorted)
            initial_col: Column containing initial values for each segment start
            inflow_col: Column containing inflow amounts (additions)
            outflow_col: Column containing outflow amounts (subtractions)
            segment_marker_col: Column with 0/1 values marking segment starts (1=start)
            result_col: Name for the result column. Defaults to 'balance'.
            group_cols: Optional column(s) to group by for independent calculations.
                       Can be string or list of strings. Defaults to None.
            keep_intermediate: If True, keep intermediate calculation columns.
                              Defaults to False.

        Returns:
            DataFrame with cumulative balance in the result column

        Raises:
            TypeError: If input is not a pandas DataFrame
            KeyError: If specified columns don't exist in DataFrame
            ValueError: If segment_marker_col contains values other than 0 or 1

        Notes:
            - DataFrame must be pre-sorted in the desired order
            - Segment markers must be 0 or 1 (1 indicates segment start)
            - Each group's first row should have segment_marker = 1
            - Uses pandas cumsum and groupby for vectorized computation

        Example:
            >>> handler = PandasHandler()
            >>> # Simple cumulative flow tracking
            >>> data = pd.DataFrame({
            ...     'initial': [100, 0, 0, 150, 0],
            ...     'inflow': [10, 20, 15, 10, 25],
            ...     'outflow': [5, 30, 10, 20, 15],
            ...     'new_segment': [1, 0, 0, 1, 0]
            ... })
            >>> result = handler.calculate_cumulative_balance(
            ...     data,
            ...     initial_col='initial',
            ...     inflow_col='inflow',
            ...     outflow_col='outflow',
            ...     segment_marker_col='new_segment'
            ... )
            >>> print(result[['balance']])

            >>> # Multi-entity tracking with groups
            >>> data = pd.DataFrame({
            ...     'entity': ['A', 'A', 'A', 'B', 'B', 'B'],
            ...     'period': [1, 2, 3, 1, 2, 3],
            ...     'initial': [100, 0, 0, 200, 0, 0],
            ...     'additions': [50, 30, 40, 60, 70, 80],
            ...     'deductions': [20, 45, 35, 50, 65, 75],
            ...     'period_start': [1, 0, 0, 1, 0, 0]
            ... })
            >>> result = handler.calculate_cumulative_balance(
            ...     data,
            ...     initial_col='initial',
            ...     inflow_col='additions',
            ...     outflow_col='deductions',
            ...     segment_marker_col='period_start',
            ...     group_cols='entity'
            ... )

        Algorithm Details:
            The method uses a segment-based approach where:
            1. Net flow (delta) = inflow - outflow
            2. Segments are identified by cumulative sum of markers
            3. Initial value propagates through each segment
            4. Cumulative delta within segments gives final balance

            This achieves O(n) complexity without explicit loops.
        """
        self._validate_dataframe(df)

        # Input validation
        df = df.copy()

        # Normalize group_cols to list
        if group_cols is None:
            group_cols = []
        elif isinstance(group_cols, str):
            group_cols = [group_cols]

        # Check if all required columns exist
        required_cols = [initial_col, inflow_col, outflow_col, segment_marker_col] + group_cols
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            raise KeyError(f"Columns not found in DataFrame: {missing_cols}")

        # Validate segment marker values
        unique_markers = df[segment_marker_col].unique()
        if not set(unique_markers).issubset({0, 1}):
            invalid_values = set(unique_markers) - {0, 1}
            raise ValueError(
                f"Segment marker column '{segment_marker_col}' contains invalid values: {invalid_values}. "
                f"Only 0 and 1 are allowed."
            )

        # Calculate net flow (inflow - outflow)
        df['_delta'] = df[inflow_col] - df[outflow_col]

        # Create segment identifiers
        if group_cols:
            # For grouped data, segment numbers restart for each group
            df['_segment'] = df.groupby(group_cols)[segment_marker_col].cumsum()

            # Extract initial values at segment starts
            df['_initial_at_segment'] = self.np.where(
                df[segment_marker_col].astype(bool),
                df[initial_col],
                self.np.nan
            )

            # Propagate initial values through each segment
            df['_segment_initial'] = (
                df.groupby(group_cols + ['_segment'])['_initial_at_segment']
                .transform('first')
            )

            # Calculate cumulative delta within each segment
            df['_cumulative_delta'] = (
                df.groupby(group_cols + ['_segment'])['_delta']
                .cumsum()
            )
        else:
            # For ungrouped data, simpler calculation
            df['_segment'] = df[segment_marker_col].cumsum()

            # Extract initial values at segment starts
            df['_initial_at_segment'] = self.np.where(
                df[segment_marker_col].astype(bool),
                df[initial_col],
                self.np.nan
            )

            # Propagate initial values through each segment
            df['_segment_initial'] = (
                df.groupby('_segment')['_initial_at_segment']
                .transform('first')
            )

            # Calculate cumulative delta within each segment
            df['_cumulative_delta'] = (
                df.groupby('_segment')['_delta']
                .cumsum()
            )

        # Calculate final balance: segment initial + cumulative delta
        df[result_col] = df['_segment_initial'] + df['_cumulative_delta']

        # Handle edge case: if first row has no segment marker
        if group_cols:
            # Check each group's first row
            first_rows = df.groupby(group_cols).head(1)
            if (first_rows[segment_marker_col] == 0).any():
                warnings.warn(
                    f"Some groups have first row with {segment_marker_col}=0. "
                    f"These rows will have NaN in {result_col}. "
                    f"Consider ensuring each group starts with {segment_marker_col}=1.",
                    UserWarning
                )
        else:
            # Check overall first row
            if df.iloc[0][segment_marker_col] == 0:
                warnings.warn(
                    f"First row has {segment_marker_col}=0. "
                    f"This row will have NaN in {result_col}. "
                    f"Consider ensuring data starts with {segment_marker_col}=1.",
                    UserWarning
                )

        # Clean up intermediate columns if requested
        if not keep_intermediate:
            intermediate_cols = [
                '_delta', '_segment', '_initial_at_segment',
                '_segment_initial', '_cumulative_delta'
            ]
            existing_cols = [col for col in intermediate_cols if col in df.columns]
            df = df.drop(columns=existing_cols)

        return df
