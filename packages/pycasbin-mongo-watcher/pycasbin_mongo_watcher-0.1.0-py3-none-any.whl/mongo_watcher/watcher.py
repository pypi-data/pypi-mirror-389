"""
MongoDB Watcher implementation for PyCasbin.

This module provides a watcher that uses MongoDB change streams to enable
distributed policy synchronization across multiple Casbin instances.
"""

from datetime import datetime, timezone
import logging
import threading
from pymongo import MongoClient
from pymongo.errors import PyMongoError


class MongoWatcher:
    """
    MongoDB watcher for PyCasbin.

    This watcher monitors MongoDB change streams and notifies registered
    callbacks when policy updates occur, enabling distributed policy
    synchronization.

    Args:
        dsn: MongoDB connection string
        db_name: Database name (default: "casbin")
        collection: Collection name for watcher events (default: "casbin_watcher")
    """

    def __init__(self, dsn, db_name="casbin", collection="casbin_watcher"):
        """
        Initialize MongoDB watcher.

        Args:
            dsn: MongoDB connection string
            db_name: Database name
            collection: Collection name for watcher events
        """
        self.client = MongoClient(dsn)
        self.collection = self.client[db_name][collection]
        self.callback = None
        self.running = False
        self.lock = threading.Lock()
        self.watch_thread = None
        self.logger = logging.getLogger(__name__)

    def set_update_callback(self, callback):
        """
        Set the callback function to be called when policy updates are detected.

        Args:
            callback: Callable function to be invoked on policy updates
        """
        with self.lock:
            self.callback = callback

    def update(self):
        """
        Trigger updates in other watcher instances.

        This method inserts a document into the watcher collection, which
        will be detected by other watcher instances via the change stream.
        """
        self.collection.insert_one({"created_at": datetime.now(timezone.utc)})

    def _watch_loop(self):
        """
        Internal method that runs the MongoDB change stream watch loop.

        This method continuously monitors the collection for insert operations
        and invokes the registered callback when changes are detected.
        """
        try:
            with self.collection.watch(
                [{"$match": {"operationType": {"$in": ["insert"]}}}],
                full_document="updateLookup",
            ) as stream:
                self.running = True
                for change in stream:
                    if self.running and self.callback:
                        self.callback()
        except PyMongoError as e:
            if self.running:
                self.logger.error(
                    f"Change stream error: {e}, attempting to reconnect..."
                )
                self._restart_watch()

    def _restart_watch(self):
        """
        Restart the watch loop in a new thread.

        This method is called when the watch loop encounters an error
        and needs to be restarted.
        """
        if self.watch_thread and self.watch_thread.is_alive():
            return
        self.watch_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.watch_thread.start()

    def start(self):
        """
        Start the watcher.

        This method explicitly starts the watch loop if it's not already running.
        """
        if not self.running:
            self._restart_watch()

    def stop(self):
        """
        Stop the watcher.

        This method stops the watch loop and closes the MongoDB connection.
        """
        self.running = False
        if self.watch_thread and self.watch_thread.is_alive():
            self.watch_thread.join(timeout=5)
        self.client.close()

    def close(self):
        """
        Close the watcher.

        This is an alias for stop() method for compatibility.
        """
        self.stop()


def new_watcher(dsn, db_name="casbin", collection="casbin_watcher"):
    """
    Create a new MongoDB watcher instance and start it.

    This is a convenience function that creates a MongoWatcher instance
    and automatically starts it.

    Args:
        dsn: MongoDB connection string
        db_name: Database name (default: "casbin")
        collection: Collection name for watcher events (default: "casbin_watcher")

    Returns:
        MongoWatcher: A started watcher instance
    """
    watcher = MongoWatcher(dsn, db_name, collection)
    watcher.start()
    watcher.logger.info("Mongo watcher started")
    return watcher
