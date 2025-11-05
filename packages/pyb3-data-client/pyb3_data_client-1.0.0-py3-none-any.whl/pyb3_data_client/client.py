"""
B3 Data Client - Python SDK for B3 Market Data API
"""

from typing import Optional, List, Union
from datetime import date, datetime
import requests
import polars as pl
import io
from pathlib import Path

from .exceptions import (
    B3APIError,
    AuthenticationError,
    RateLimitError,
    InsufficientCreditsError,
    ValidationError
)


class B3Client:
    """
    Python client for B3 Market Data API

    Usage:
        >>> from b3_data_client import B3Client
        >>>
        >>> client = B3Client(api_key="pk_live_...")
        >>>
        >>> # Get daily data
        >>> df = client.get_daily_data(
        ...     symbols=["PETR4", "VALE3"],
        ...     start_date="2024-01-01",
        ...     end_date="2024-01-31"
        ... )
        >>>
        >>> print(df.head())
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.b3data.com",
        timeout: int = 30
    ):
        """
        Initialize B3 Data Client

        Args:
            api_key: Your API key from the dashboard
            base_url: Base URL for the API (default: https://api.b3data.com)
            timeout: Request timeout in seconds (default: 30)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': api_key,
            'User-Agent': 'b3-data-client/1.0.0'
        })

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json: Optional[dict] = None
    ) -> requests.Response:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                timeout=self.timeout
            )

            # Handle error responses
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            elif response.status_code == 402:
                raise InsufficientCreditsError("Insufficient credits")
            elif response.status_code == 400:
                error_data = response.json()
                raise ValidationError(error_data.get('detail', 'Validation error'))
            elif response.status_code >= 400:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                raise B3APIError(
                    f"API error: {response.status_code}",
                    status_code=response.status_code,
                    response=error_data
                )

            return response

        except requests.exceptions.Timeout:
            raise B3APIError("Request timeout")
        except requests.exceptions.ConnectionError:
            raise B3APIError("Connection error")

    def get_daily_data(
        self,
        symbols: Union[str, List[str]],
        start_date: Union[str, date],
        end_date: Union[str, date],
        fields: Optional[List[str]] = None,
        instrument_type: Optional[str] = None,
        format: str = "parquet"
    ) -> pl.DataFrame:
        """
        Get daily market data for specified instrument types

        Args:
            symbols: Stock symbol(s) - single string or list
            start_date: Start date (YYYY-MM-DD string or date object)
            end_date: End date (YYYY-MM-DD string or date object)
            fields: Optional list of fields to return (default: all)
            instrument_type: Filter by type - "equity", "etf", "bdr", "fii", "option" (default: all types)
            format: Response format - "json" or "parquet" (default: parquet for 50% credit discount)

        Returns:
            Polars DataFrame with daily market data

        Examples:
            >>> # Get stock data (equity only)
            >>> df = client.get_daily_data(
            ...     symbols=["PETR4", "VALE3"],
            ...     start_date="2024-01-01",
            ...     end_date="2024-01-31",
            ...     instrument_type="equity"
            ... )
            >>>
            >>> # Get ETF data in Parquet (50% credit discount!)
            >>> df = client.get_daily_data(
            ...     symbols="BOVA11",
            ...     start_date="2024-01-01",
            ...     end_date="2024-12-31",
            ...     instrument_type="etf",
            ...     format="parquet"
            ... )
            >>>
            >>> # Get FII data (Real Estate Trusts)
            >>> df = client.get_daily_data(
            ...     symbols=["HGLG11", "VISC11"],
            ...     start_date="2024-01-01",
            ...     end_date="2024-01-31",
            ...     instrument_type="fii"
            ... )
            >>>
            >>> # Get options data
            >>> df = client.get_daily_data(
            ...     symbols="PETRA123",
            ...     start_date="2024-01-01",
            ...     end_date="2024-01-31",
            ...     instrument_type="option"
            ... )
        """
        # Convert symbols to comma-separated string
        if isinstance(symbols, list):
            symbols_str = ','.join(symbols)
        else:
            symbols_str = symbols

        # Convert dates to strings
        if isinstance(start_date, date):
            start_date = start_date.strftime('%Y-%m-%d')
        if isinstance(end_date, date):
            end_date = end_date.strftime('%Y-%m-%d')

        # Build params
        params = {
            'symbols': symbols_str,
            'start_date': start_date,
            'end_date': end_date,
            'format': format
        }

        if fields:
            params['fields'] = ','.join(fields)

        if instrument_type:
            params['instrument_type'] = instrument_type

        # Make request
        response = self._request('GET', '/api/v1/cotahist/daily', params=params)

        # Parse response
        if format == 'parquet':
            # Read parquet from bytes
            return pl.read_parquet(io.BytesIO(response.content))
        else:
            # Parse JSON
            data = response.json()
            return pl.DataFrame(data['data'])

    def get_symbols(
        self,
        instrument_type: Optional[str] = None,
        is_active: bool = True
    ) -> pl.DataFrame:
        """
        Get symbol metadata

        Args:
            instrument_type: Filter by type (e.g., "equity", "option")
            is_active: Filter by active status (default: True)

        Returns:
            Polars DataFrame with symbol metadata

        Examples:
            >>> # Get all active equity symbols
            >>> symbols = client.get_symbols(instrument_type="equity")
            >>>
            >>> # Get all symbols (including inactive)
            >>> all_symbols = client.get_symbols(is_active=False)
        """
        params = {'is_active': str(is_active).lower()}

        if instrument_type:
            params['instrument_type'] = instrument_type

        response = self._request('GET', '/api/v1/symbols/', params=params)
        data = response.json()

        return pl.DataFrame(data['symbols'])

    def get_account_info(self) -> dict:
        """
        Get account information including credits and usage

        Returns:
            Dictionary with account details

        Examples:
            >>> info = client.get_account_info()
            >>> print(f"Credits remaining: {info['credits_remaining']}")
        """
        response = self._request('GET', '/api/v1/account/info')
        return response.json()

    def get_usage(
        self,
        start_date: Optional[Union[str, date]] = None,
        end_date: Optional[Union[str, date]] = None
    ) -> dict:
        """
        Get usage statistics

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary with usage statistics

        Examples:
            >>> # Get current month usage
            >>> usage = client.get_usage()
            >>>
            >>> # Get usage for specific period
            >>> usage = client.get_usage(
            ...     start_date="2024-01-01",
            ...     end_date="2024-01-31"
            ... )
        """
        params = {}

        if start_date:
            if isinstance(start_date, date):
                start_date = start_date.strftime('%Y-%m-%d')
            params['start_date'] = start_date

        if end_date:
            if isinstance(end_date, date):
                end_date = end_date.strftime('%Y-%m-%d')
            params['end_date'] = end_date

        response = self._request('GET', '/api/v1/account/usage', params=params)
        return response.json()

    def export_data(
        self,
        dataset: str,
        year: int,
        output_path: Optional[Union[str, Path]] = None
    ) -> Union[str, Path]:
        """
        Export bulk data for a year

        Args:
            dataset: Dataset name (e.g., "cotahist")
            year: Year to export
            output_path: Optional path to save file (default: current directory)

        Returns:
            Path to downloaded file

        Examples:
            >>> # Export 2023 data
            >>> file_path = client.export_data("cotahist", 2023)
            >>> print(f"Downloaded to: {file_path}")
            >>>
            >>> # Export to specific location
            >>> file_path = client.export_data(
            ...     "cotahist",
            ...     2023,
            ...     output_path="/data/cotahist_2023.parquet"
            ... )
        """
        response = self._request('GET', f'/api/v1/exports/{dataset}/{year}')
        data = response.json()

        # Get download URL
        download_url = data['download_url']

        # Download file
        file_response = requests.get(download_url, stream=True)

        # Determine output path
        if output_path is None:
            output_path = Path(f"{dataset}_{year}.parquet")
        else:
            output_path = Path(output_path)

        # Save file
        with open(output_path, 'wb') as f:
            for chunk in file_response.iter_content(chunk_size=8192):
                f.write(chunk)

        return output_path

    def to_pandas(self, df: pl.DataFrame):
        """
        Convert Polars DataFrame to Pandas

        Args:
            df: Polars DataFrame

        Returns:
            Pandas DataFrame

        Examples:
            >>> df = client.get_daily_data("PETR4", "2024-01-01", "2024-01-31")
            >>> df_pandas = client.to_pandas(df)
        """
        return df.to_pandas()

    def close(self):
        """Close the session"""
        self.session.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
