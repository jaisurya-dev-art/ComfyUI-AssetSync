class AssetSyncError(Exception):
    """A failure that can be shown to an artist without a traceback."""


class ValidationError(AssetSyncError):
    pass


class ConversionError(AssetSyncError):
    pass


class ReceiverError(AssetSyncError):
    pass

