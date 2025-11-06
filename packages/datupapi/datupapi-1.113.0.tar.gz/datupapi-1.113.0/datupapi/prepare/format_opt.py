import os
import polars as pl
import pandas as pd
import re
from datupapi.configure.config import Config


class FormatOptimized(Config):
    """
    Optimized Format class using Polars for efficient data resampling operations.
    This class provides the same interface as Format but with improved performance
    through Polars' efficient processing capabilities.
    """

    def __init__(self, config_file, logfile, log_path, *args, **kwargs):
        Config.__init__(self, config_file=config_file, logfile=logfile)
        self.log_path = log_path

    def _convert_frequency_to_polars(self, frequency: str) -> str:
        """
        Convert pandas frequency notation to Polars notation.
        
        :param frequency: Pandas frequency string (e.g., 'M', 'W', 'D', 'Q', '2M', '3W')
        :return: Polars frequency string (e.g., '1mo', '1w', '1d', '1q', '2mo', '3w')
        """
        # Mapping of pandas frequency codes to Polars
        freq_map = {
            'D': 'd',   # Day
            'W': 'w',   # Week
            'M': 'mo',  # Month
            'Q': 'q',   # Quarter
            'Y': 'y',   # Year
            'H': 'h',   # Hour
            'T': 'm',   # Minute (T in pandas, m in polars)
            'S': 's',   # Second
        }
        
        # Extract number prefix if exists (e.g., '2M' -> '2', 'M')
        match = re.match(r'^(\d*)([A-Z]+)$', frequency.upper())
        
        if not match:
            raise ValueError(f"Invalid frequency format: {frequency}")
        
        number = match.group(1) or '1'
        freq_code = match.group(2)
        
        if freq_code not in freq_map:
            raise ValueError(f"Unsupported frequency code: {freq_code}")
        
        polars_freq = freq_map[freq_code]
        
        return f"{number}{polars_freq}"

    def reorder_cols(self, df, first_cols):
        """
        Return a dataframe with columns specified in first_col at the leading positions
        
        :param df: Dataframe to reorder
        :param first_cols: Leading columns to appear in the dataframe
        :return df: Dataframe reordered
        
        >>> df = reorder_cols(df, first_cols)
        >>> df =
                        var1    var2    var3
                idx0     1       2       3
        """
        cols = list(df.columns)
        for col in reversed(first_cols):
            if col in cols:
                cols.remove(col)
                cols.insert(0, col)
        df = df[cols]
        return df

    def resample_dataset(self, df, date_col=None, item_col=None, frequency=None, agg_dict=None, use_lazy=True):
        """
        Return a dataframe resampling the date dimension to the specified frequency using Polars.
        
        This optimized version:
        - Converts pandas to Polars for faster processing
        - Uses lazy evaluation for optimal query planning (when use_lazy=True)
        - Uses group_by_dynamic for efficient resampling
        - Fills missing date ranges with 0
        - Adjusts dates to the last day of each month
        - Returns a pandas DataFrame
        
        :param df: Pandas DataFrame to be resampled
        :param date_col: Name of the date column
        :param item_col: Name of the item column
        :param frequency: Target frequency to resample the data (e.g., 'M' for monthly, 'W' for weekly)
        :param agg_dict: Aggregation dictionary including column as key and operation as value
        :param use_lazy: Use lazy evaluation for better performance (default: True)
        :return df_out: Pandas DataFrame resampled
        
        >>> df_out = resample_dataset(df, date_col='timestamp', item_col='item_id',
        ...                           frequency='M', agg_dict={'demand': 'sum'})
        >>> df_out =
                                timestamp  item_id  demand
                        0      2021-01-31     sku1      23
                        1      2021-02-28     sku1     543
        """
        try:
            # Convert pandas frequency to Polars frequency
            polars_frequency = self._convert_frequency_to_polars(frequency)
            
            # Convert pandas DataFrame to Polars (lazy if requested)
            if use_lazy:
                df_pl = pl.from_pandas(df).lazy()
            else:
                df_pl = pl.from_pandas(df)
            
            # Build the lazy query
            df_lazy = (
                df_pl
                # Ensure date column is datetime type
                .with_columns(
                    pl.col(date_col).cast(pl.Datetime)
                )
                # Sort by date column
                .sort(date_col)
            )
            
            # Collect to perform group_by_dynamic (not supported in lazy mode)
            if use_lazy:
                df_collected = df_lazy.collect()
            else:
                df_collected = df_lazy
            
            # Perform dynamic grouping and resampling
            df_resampled = (
                df_collected.group_by_dynamic(
                    index_column=date_col,
                    every=polars_frequency,
                    closed="left",  # Left-closed interval
                    by=[item_col]
                )
                .agg([getattr(pl.col(col), func)().alias(col) for col, func in agg_dict.items()])
            )
            
            # Continue with lazy operations
            if use_lazy:
                df_out_lazy = df_resampled.lazy()
            else:
                df_out_lazy = df_resampled
            
            # Adjust to the last day of the month
            df_out_lazy = df_out_lazy.with_columns(
                pl.col(date_col).dt.month_end().alias(date_col)
            )
            
            # Collect to get min/max dates for range creation
            if use_lazy:
                df_temp = df_out_lazy.collect()
            else:
                df_temp = df_out_lazy
            
            # Fill missing date ranges with 0
            # Get all unique items
            items = df_temp.select(item_col).unique()
            
            # Get date range from min to max
            min_date = df_temp.select(pl.col(date_col).min()).item()
            max_date = df_temp.select(pl.col(date_col).max()).item()
            
            # Create complete date range at month end
            date_range = pl.datetime_range(
                min_date,
                max_date,
                interval=polars_frequency,
                eager=True
            ).dt.month_end()
            
            # Create a complete grid of dates and items
            complete_grid = items.join(
                pl.DataFrame({date_col: date_range}),
                how="cross"
            )
            
            # Build final lazy query for joins and fills
            if use_lazy:
                complete_grid_lazy = complete_grid.lazy()
                df_temp_lazy = df_temp.lazy()
                
                df_out_lazy = (
                    complete_grid_lazy
                    .join(
                        df_temp_lazy,
                        on=[date_col, item_col],
                        how="left"
                    )
                )
                
                # Fill null values with 0 for aggregated columns
                for col in agg_dict.keys():
                    df_out_lazy = df_out_lazy.with_columns(
                        pl.col(col).fill_null(0)
                    )
                
                # Reorder columns: date_col, item_col, then others
                other_cols = [c for c in df_temp.columns if c not in [date_col, item_col]]
                df_out_lazy = df_out_lazy.select(
                    [pl.col(date_col), pl.col(item_col)] + [pl.col(c) for c in other_cols]
                )
                
                # Collect the final result
                df_out = df_out_lazy.collect()
            else:
                # Join with resampled data and fill nulls with 0
                df_out = complete_grid.join(
                    df_temp,
                    on=[date_col, item_col],
                    how="left"
                )
                
                # Fill null values with 0 for aggregated columns
                for col in agg_dict.keys():
                    df_out = df_out.with_columns(
                        pl.col(col).fill_null(0)
                    )
                
                # Reorder columns: date_col, item_col, then others
                other_cols = [c for c in df_out.columns if c not in [date_col, item_col]]
                df_out = df_out.select(
                    [pl.col(date_col), pl.col(item_col)] + [pl.col(c) for c in other_cols]
                )
            
            # Convert back to pandas
            df_pandas = df_out.to_pandas()
            
            # Reorder columns using the class method
            df_pandas = self.reorder_cols(df_pandas, first_cols=[date_col, item_col])
            
        except KeyError as err:
            self.logger.exception(f'Columns for index, item or qty not found. Please check spelling: {err}')
            raise
        
        return df_pandas

    def resample_dataset_with_location(self, df, date_col_=None, item_col_=None, location_col_=None, frequency_=None, agg_dict_=None, use_lazy=True):
        """
        Return a dataframe resampling the date dimension to the specified frequency using Polars,
        including location grouping.
        
        This optimized version:
        - Converts pandas to Polars for faster processing
        - Uses lazy evaluation for optimal query planning (when use_lazy=True)
        - Uses group_by_dynamic for efficient resampling with location
        - Fills missing date ranges with 0
        - Adjusts dates to the last day of each month
        - Returns a pandas DataFrame
        
        :param df: Pandas DataFrame to be resampled
        :param date_col_: Name of the date column
        :param item_col_: Name of the item column
        :param location_col_: Name of the location column
        :param frequency_: Target frequency to resample the data (e.g., 'M' for monthly, 'W' for weekly)
        :param agg_dict_: Aggregation dictionary including column as key and operation as value
        :param use_lazy: Use lazy evaluation for better performance (default: True)
        :return df_out: Pandas DataFrame resampled
        
        >>> df_out = resample_dataset_with_location(df, date_col_='timestamp',
        ...                                         item_col_='item_id', location_col_='location',
        ...                                         frequency_='M', agg_dict_={'demand': 'sum'})
        """
        try:
            # Convert pandas frequency to Polars frequency
            polars_frequency = self._convert_frequency_to_polars(frequency_)
            
            # Convert pandas DataFrame to Polars (lazy if requested)
            if use_lazy:
                df_pl = pl.from_pandas(df).lazy()
            else:
                df_pl = pl.from_pandas(df)
            
            # Build the lazy query
            df_lazy = (
                df_pl
                # Ensure date column is datetime type
                .with_columns(
                    pl.col(date_col_).cast(pl.Datetime)
                )
                # Sort by date column
                .sort(date_col_)
            )
            
            # Collect to perform group_by_dynamic (not supported in lazy mode)
            if use_lazy:
                df_collected = df_lazy.collect()
            else:
                df_collected = df_lazy
            
            # Perform dynamic grouping and resampling
            df_resampled = (
                df_collected.group_by_dynamic(
                    index_column=date_col_,
                    every=polars_frequency,
                    closed="left",  # Left-closed interval
                    by=[location_col_, item_col_]
                )
                .agg([getattr(pl.col(col), func)().alias(col) for col, func in agg_dict_.items()])
            )
            
            # Continue with lazy operations
            if use_lazy:
                df_out_lazy = df_resampled.lazy()
            else:
                df_out_lazy = df_resampled
            
            # Adjust to the last day of the month
            df_out_lazy = df_out_lazy.with_columns(
                pl.col(date_col_).dt.month_end().alias(date_col_)
            )
            
            # Collect to get min/max dates for range creation
            if use_lazy:
                df_temp = df_out_lazy.collect()
            else:
                df_temp = df_out_lazy
            
            # Fill missing date ranges with 0
            # Get all unique combinations of location and item
            location_items = df_temp.select([location_col_, item_col_]).unique()
            
            # Get date range from min to max
            min_date = df_temp.select(pl.col(date_col_).min()).item()
            max_date = df_temp.select(pl.col(date_col_).max()).item()
            
            # Create complete date range at month end
            date_range = pl.datetime_range(
                min_date,
                max_date,
                interval=polars_frequency,
                eager=True
            ).dt.month_end()
            
            # Create a complete grid of dates, locations, and items
            complete_grid = location_items.join(
                pl.DataFrame({date_col_: date_range}),
                how="cross"
            )
            
            # Build final lazy query for joins and fills
            if use_lazy:
                complete_grid_lazy = complete_grid.lazy()
                df_temp_lazy = df_temp.lazy()
                
                df_out_lazy = (
                    complete_grid_lazy
                    .join(
                        df_temp_lazy,
                        on=[date_col_, location_col_, item_col_],
                        how="left"
                    )
                )
                
                # Fill null values with 0 for aggregated columns
                for col in agg_dict_.keys():
                    df_out_lazy = df_out_lazy.with_columns(
                        pl.col(col).fill_null(0)
                    )
                
                # Reorder columns: date_col, item_col, location_col, then others
                other_cols = [c for c in df_temp.columns if c not in [date_col_, item_col_, location_col_]]
                df_out_lazy = df_out_lazy.select(
                    [pl.col(date_col_), pl.col(item_col_), pl.col(location_col_)] + [pl.col(c) for c in other_cols]
                )
                
                # Collect the final result
                df_out = df_out_lazy.collect()
            else:
                # Join with resampled data and fill nulls with 0
                df_out = complete_grid.join(
                    df_temp,
                    on=[date_col_, location_col_, item_col_],
                    how="left"
                )
                
                # Fill null values with 0 for aggregated columns
                for col in agg_dict_.keys():
                    df_out = df_out.with_columns(
                        pl.col(col).fill_null(0)
                    )
                
                # Reorder columns: date_col, item_col, location_col, then others
                other_cols = [c for c in df_out.columns if c not in [date_col_, item_col_, location_col_]]
                df_out = df_out.select(
                    [pl.col(date_col_), pl.col(item_col_), pl.col(location_col_)] + [pl.col(c) for c in other_cols]
                )
            
            # Convert back to pandas
            df_pandas = df_out.to_pandas()
            
            # Reorder columns using the class method
            df_pandas = self.reorder_cols(df_pandas, first_cols=[date_col_, item_col_, location_col_])
            
        except KeyError as err:
            self.logger.exception(f'Columns for index, item or qty not found. Please check spelling: {err}')
            raise
        
        return df_pandas