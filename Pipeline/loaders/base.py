"""
Base class for pipe API data loaders.
"""
from interface import default, Interface


class PipelineLoader(Interface):
    """Interface for PipelineLoaders.
    """
    def load_adjusted_array(self, domain, columns, dates, sids, mask):
        """
        Load data for ``columns`` as AdjustedArrays.

        Parameters
        ----------
        domain : zipline.Pipeline.domain.Domain
            The domain of the Pipeline for which the requested data must be
            loaded.
        columns : list[zipline.Pipeline.data.dataset.BoundColumn]
            Columns for which data is being requested.
        dates : pd.DatetimeIndex
            Dates for which data is being requested.
        sids : pd.Int64Index
            Asset identifiers for which data is being requested.
        mask : np.array[ndim=2, dtype=bool]
            Boolean array of shape (len(dates), len(sids)) indicating dates on
            which we believe the requested assets were alive/tradeable. This is
            used for optimization by some loaders.

        Returns
        -------
        arrays : dict[BoundColumn -> zipline.lib.adjusted_array.AdjustedArray]
            Map from column to an AdjustedArray representing a point-in-time
            rolling view over the requested dates for the requested sids.
        """

    @default
    def validate_domain(self, domain):
        """
        Verify that a domain is supported before attempting to load it.

        This can be implemented by a loader to raise a useful error before
        performing any potentially-expensive work.

        The default implementation is a no-op.

        Parameters
        ----------
        domain : zipline.Pipeline.domain.Domain
            The domain on which a Pipeline is about to be run.
        """
        pass
