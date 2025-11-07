"""
PyCasbin MongoDB Watcher

MongoDB watcher for PyCasbin that enables distributed policy synchronization
using MongoDB change streams.
"""

from .watcher import MongoWatcher, new_watcher

__all__ = ["MongoWatcher", "new_watcher"]
__version__ = "0.1.0"
