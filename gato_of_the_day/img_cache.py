from __future__ import annotations
from threading import Thread
from time import sleep
from typing import Any, Callable
from os import path, remove
from shutil import copy
from os.path import exists, isfile, isdir
from os import PathLike, listdir, mkdir
import uuid

class TempFile:
    instances = set()

    def __init__(self, file: str | PathLike):
        if not exists(file):
            raise FileNotFoundError
        
        if not isfile(file):
            raise IsADirectoryError
        
        if file in TempFile.instances:
            raise FileExistsError("File already being used as a TempFile")

        TempFile.instances.add(file)
        self.file = file

    def cancel(self):
        TempFile.instances.remove(self.file)
        self.file = None

    def __del__(self):
        if self.file is None:
            return
        
        print("Deleting " + str(self.file) + "...")
        
        TempFile.instances.remove(self.file)
        remove(self.file)

class ImageCache(Thread):
    def __init__(self, dir: str | PathLike, size: int, fn: Callable[[str], Any]) -> None:
        super().__init__()
        self.dir = dir
        self.__fn = fn
        self.caches = {}
        self.alive = False
        self.size = size

        if not exists(dir):
            mkdir(dir)
    
    def __cache_dir(self, key: str) -> PathLike:
        return path.join(self.dir, key)
    
    def init_cache(self, key: str) -> None:
        if key in self.caches:
            raise KeyError("Key Already Exists")
        
        dir = self.__cache_dir(key)

        if not exists(dir):
            mkdir(dir)

        self.caches[key] = []

        for f in listdir(dir):
            file = path.join(dir, f)
            if isfile(file):
                self.caches[key].append(TempFile(file))

    def add_file(self, key: str, file: str | PathLike) -> None:
        if not isfile(file):
            raise IsADirectoryError
        
        new_name = str(uuid.uuid4())
        extension = path.splitext(file)[1]

        new_file = path.join(self.__cache_dir(key), new_name + extension)

        copy(file, new_file)

        if key not in self.caches:
            self.caches[key] = []
        
        cache: list = self.caches[key]
        cache.append(TempFile(new_file))

    def run(self) -> None:
        print("started")
        self.alive = True
        while self.alive:
            if len(self.caches) == 0:
                return
            
            lowest = list(self.caches.keys())[0]
            for key in self.caches:
                if len(self.caches[key]) < len(self.caches[lowest]):
                    lowest = key

            if len(self.caches[lowest]) < self.size:
                self.generate_image(lowest)
            else:
                sleep(1)
        
        # Cancel tempfiles so they don't get deleted on shutdown
        for v in self.caches.values():
            for f in v:
                f: TempFile
                f.cancel()

    def kill(self) -> None:
        self.alive = False

    def generate_image(self, key: str) -> None:
        print("Generatiing " + key)
        newfile = self.__fn(key)
        self.add_file(key, newfile)
    
    def get(self, key: str) -> TempFile:
        if key not in self.caches:
            raise KeyError("Cache not initialized.")
        
        if len(self.caches[key]) > 0:
            file = self.caches[key].pop()
            return file
        else:
            # Probably the dumbest use of recursion but im lazy
            self.generate_image(key)
            return self.get(key)