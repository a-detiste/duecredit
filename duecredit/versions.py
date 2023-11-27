# emacs: -*- mode: python; py-indent-offset: 4; tab-width: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 noet:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the duecredit package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
from __future__ import annotations

"""Module to help maintain a registry of versions for external modules etc
"""
import sys
from os import linesep
from typing import Any

from distutils.version import StrictVersion, LooseVersion

try:
    from importlib.metadata import version as metadata_version
except ImportError:
    from importlib_metadata import version as metadata_version  # type: ignore


# To depict an unknown version, which can't be compared by mistake etc
class UnknownVersion:
    """For internal use
    """

    def __str__(self) -> str:
        return "UNKNOWN"

    def __eq__(self, other: Any) -> bool:
        if other is self:
            return True
        raise TypeError("UNKNOWN version is not comparable")


class ExternalVersions:
    """Helper to figure out/use versions of the external modules.

    It maintains a dictionary of `distuil.version.StrictVersion`s to make
    comparisons easy.  If version string doesn't conform the StrictVersion
    LooseVersion will be used.  If version can't be deduced for the module,
    'None' is assigned
    """

    UNKNOWN = UnknownVersion()

    def __init__(self) -> None:
        self._versions: dict[str, StrictVersion | LooseVersion | UnknownVersion] = {}

    @classmethod
    def _deduce_version(klass, module) -> StrictVersion | LooseVersion | UnknownVersion:
        version = None
        for attr in ('__version__', 'version'):
            if hasattr(module, attr):
                version = getattr(module, attr)
                break

        if isinstance(version, tuple) or isinstance(version, list):
            #  Generate string representation
            version = ".".join(str(x) for x in version)

        if not version:
            # Try importlib.metadata
            # module name might be different, and I found no way to
            # deduce it for citeproc which comes from "citeproc-py"
            # distribution
            modname = module.__name__
            try:
                version = metadata_version(
                    {'citeproc': 'citeproc-py'}.get(modname, modname)
                )
            except Exception:
                pass  # oh well - no luck either

        if version:
            try:
                return StrictVersion(version)
            except ValueError:
                # let's then go with Loose one
                return LooseVersion(version)
        else:
            return klass.UNKNOWN

    def __getitem__(self, module: Any) -> StrictVersion | LooseVersion | UnknownVersion | None:
        # when ran straight in its source code -- fails to discover nipy's version.. TODO
        #if module == 'nipy':
        if not isinstance(module, str):
            modname = module.__name__
        else:
            modname = module
            module = None

        if modname not in self._versions:
            if module is None:
                if modname not in sys.modules:
                    try:
                        module = __import__(modname)
                    except ImportError:
                        return None
                else:
                    module = sys.modules[modname]

            self._versions[modname] = self._deduce_version(module)

        return self._versions.get(modname, self.UNKNOWN)

    def keys(self):
        """Return names of the known modules"""
        return self._versions.keys()

    def __contains__(self, item):
        return item in self._versions

    @property
    def versions(self) -> dict[str, StrictVersion | LooseVersion | UnknownVersion]:
        """Return dictionary (copy) of versions"""
        return self._versions.copy()

    def dumps(
        self,
        indent: bool | str = False,
        preamble: str = "Versions:"
    ) -> str:
        """Return listing of versions as a string

        Parameters
        ----------
        indent: bool or str, optional
          If set would instruct on how to indent entries (if just True, ' '
          is used). Otherwise returned in a single line
        preamble: str, optional
          What preamble to the listing to use
        """
        items = ["{}={}".format(k, self._versions[k]) for k in sorted(self._versions)]
        out = "%s" % preamble
        if indent:
            indent_ = ' ' if indent is True else indent
            out += (linesep + indent_).join([''] + items) + linesep
        else:
            out += " " + ' '.join(items)
        return out


external_versions = ExternalVersions()
