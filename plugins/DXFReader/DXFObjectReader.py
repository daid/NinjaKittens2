
class DXFObject:
    def __init__(self, name):
        self._name = name
        self._data = {}

    def add(self, key, value):
        if key in self._data:
            self._data[key].append(value)
        else:
            self._data[key] = [value]

    def __repr__(self):
        return "{%s, %s}" % (self._name, self._data)

    def getName(self):
        return self._name

    def has(self, key):
        return key in self._data

    def count(self, key):
        if key in self._data:
            return len(self._data[key])
        return 0

    def get(self, key, index=0):
        return self._data[key][index]


class DXFObjectReader:
    def __init__(self, file):
        self._file = file
        self._cur_object = None

    def readObject(self):
        while True:
            group_code = self._file.readline().strip()
            value = self._file.readline().strip()
            if group_code == "":
                obj = self._cur_object
                self._cur_object = None
                return obj
            group_code = int(group_code)
            if group_code == 0:
                obj = self._cur_object
                self._cur_object = DXFObject(value)
                if obj is not None:
                    return obj
            else:
                self._cur_object.add(group_code, value)

    def __iter__(self):
        return self

    def __next__(self):
        obj = self.readObject()
        if obj is None:
            raise StopIteration
        return obj

if __name__ == "__main__":
    dxf = DXFObjectReader(open("RodCap.dxf", "rt"))
    for obj in dxf:
        print(obj)
