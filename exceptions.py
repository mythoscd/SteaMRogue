# %% [markdown]
# # Exceptions Module
# Custom exception classes for SteamTools Auto.

# %%
class SteamToolsException(Exception):
    """Base exception class for all SteamTools Auto exceptions."""
    pass

# %%
class SteamPathNotFoundError(SteamToolsException):
    """Raised when Steam installation directory cannot be found."""
    pass

# %%
class AppIdValidationError(SteamToolsException):
    """Raised when an invalid AppID is provided by the user."""
    pass

# %%
class ManifestDownloadError(SteamToolsException):
    """Raised when download or extraction of manifest files fails."""
    pass

# %%
class VdfParseError(SteamToolsException):
    """Raised when libraryfolders.vdf parsing or modification fails."""
    pass

# %%
class BackupRestoreError(SteamToolsException):
    """Raised when backup creation or restoration fails."""
    pass
