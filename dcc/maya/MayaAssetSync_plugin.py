"""Plug-in Manager loader for the MayaAssetSync package."""

from MayaAssetSync import initializePlugin, uninitializePlugin


def maya_useNewAPI():
    pass


__all__ = ["initializePlugin", "maya_useNewAPI", "uninitializePlugin"]

