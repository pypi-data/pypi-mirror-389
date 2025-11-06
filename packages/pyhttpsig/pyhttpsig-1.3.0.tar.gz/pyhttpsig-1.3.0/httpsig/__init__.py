try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    # Python < 3.8
    from importlib_metadata import version, PackageNotFoundError

from .sign import Signer, HeaderSigner
from .verify import Verifier, HeaderVerifier

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    # package is not installed
    pass

__all__ = (Signer, HeaderSigner, Verifier, HeaderVerifier)
