from rlib.arithmetic import IntType
from rlib.erased import new_erasing_pair
from rlib.jit import JitDriver
from rlib.debug import make_sure_not_resized

from som.vmobjects.abstract_object import AbstractObject
from som.vm.globals import nilObject, falseObject, trueObject
from som.vmobjects.double import Double
from som.vmobjects.integer import Integer
from som.vmobjects.method import AbstractMethod


def put_all_obj_pl(block_method):
    assert isinstance(block_method, AbstractMethod)
    return "#putAll: (obj_strategy) %s" % block_method.merge_point_string()


def put_all_nil_pl(block_method):
    assert isinstance(block_method, AbstractMethod)
    return "#putAll: (empty_strategy) %s" % block_method.merge_point_string()


def put_all_double_pl(block_method):
    assert isinstance(block_method, AbstractMethod)
    return "#putAll: (double_strategy) %s" % block_method.merge_point_string()


def put_all_long_pl(block_method):
    assert isinstance(block_method, AbstractMethod)
    return "#putAll: (long_strategy) %s" % block_method.merge_point_string()


def put_all_bool_pl(block_method):
    assert isinstance(block_method, AbstractMethod)
    return "#putAll: (bool_strategy) %s" % block_method.merge_point_string()


put_all_obj_driver = JitDriver(
    greens=["block_method"],
    reds="auto",
    is_recursive=True,
    get_printable_location=put_all_obj_pl,
)
put_all_nil_driver = JitDriver(
    greens=["block_method"],
    reds="auto",
    is_recursive=True,
    get_printable_location=put_all_nil_pl,
)
put_all_double_driver = JitDriver(
    greens=["block_method"],
    reds="auto",
    is_recursive=True,
    get_printable_location=put_all_double_pl,
)
put_all_long_driver = JitDriver(
    greens=["block_method"],
    reds="auto",
    is_recursive=True,
    get_printable_location=put_all_long_pl,
)
put_all_bool_driver = JitDriver(
    greens=["block_method"],
    reds="auto",
    is_recursive=True,
    get_printable_location=put_all_bool_pl,
)


class _ArrayStrategy(object):
    @staticmethod
    def _set_all_with_value(array, value, size):
        if value is nilObject:
            array.storage = _empty_strategy.new_storage_for(size)
            array.strategy = _empty_strategy
        elif isinstance(value, Integer):
            int_arr = [value.get_embedded_integer()] * size
            array.storage = _long_strategy.erase(int_arr)
            array.strategy = _long_strategy
        elif isinstance(value, Double):
            double_arr = [value.get_embedded_double()] * size
            array.storage = _double_strategy.erase(double_arr)
            array.strategy = _double_strategy
        elif value is trueObject or value is falseObject:
            bool_arr = [value is trueObject] * size
            array.storage = _bool_strategy.erase(bool_arr)
            array.strategy = _bool_strategy
        else:
            obj_arr = [value] * size
            array.storage = _obj_strategy.erase(obj_arr)
            array.strategy = _obj_strategy

    @staticmethod
    def _set_all_with_block(array, block, size):
        # Handle first the empty case
        if size == 0:
            array.storage = _empty_strategy.new_storage_for(0)
            array.strategy = _empty_strategy
            return

        assert isinstance(array, Array)
        block_method = block.get_method()

        i = 0

        # we do the first iteration separately to determine our strategy
        assert i < size
        first = block_method.invoke_1(block)
        if first is nilObject:
            _ArrayStrategy._set_remaining_with_block_as_nil(array, block, size, 1)
        elif isinstance(first, Integer):
            long_store = [0] * size
            long_store[0] = first.get_embedded_integer()
            _ArrayStrategy._set_remaining_with_block_as_long(
                array, block, size, 1, long_store
            )
        elif isinstance(first, Double):
            double_store = [0.0] * size
            double_store[0] = first.get_embedded_double()
            _ArrayStrategy._set_remaining_with_block_as_double(
                array, block, size, 1, double_store
            )
        elif first is trueObject or first is falseObject:
            bool_store = [first is trueObject] * size
            _ArrayStrategy._set_remaining_with_block_as_double(
                array, block, size, 1, bool_store
            )
        else:
            obj_store = [None] * size
            obj_store[0] = first
            _ArrayStrategy._set_remaining_with_block_as_obj(
                array, block, size, 1, obj_store
            )

    @staticmethod
    def _set_remaining_with_block_as_nil(array, block, size, next_i):
        block_method = block.get_method()
        while next_i < size:
            put_all_nil_driver.jit_merge_point(block_method=block_method)
            result = block_method.invoke_1(block)
            if result is not nilObject:
                # ok, fall back, let's go straight to obj strategy
                # todo: perhaps, partially empty would be better?
                new_storage = [nilObject] * size
                new_storage[next_i] = result
                _ArrayStrategy._set_remaining_with_block_as_obj(
                    array, block, size, next_i + 1, new_storage
                )
                return
            next_i += 1
        array.strategy = _empty_strategy
        array.storage = _empty_strategy.new_storage_for(size)

    @staticmethod
    def _set_remaining_with_block_as_long(array, block, size, next_i, storage):
        block_method = block.get_method()
        while next_i < size:
            put_all_long_driver.jit_merge_point(block_method=block_method)
            result = block_method.invoke_1(block)
            if isinstance(result, Integer):
                storage[next_i] = result.get_embedded_integer()
            else:
                # something else, so, let's go to the object strategy
                new_storage = [None] * size
                for i in range(0, next_i + 1):
                    new_storage[i] = Integer(storage[i])
                _ArrayStrategy._set_remaining_with_block_as_obj(
                    array, block, size, next_i + 1, new_storage
                )
                return
            next_i += 1
        array.strategy = _long_strategy
        array.storage = _long_strategy.erase(storage)

    @staticmethod
    def _set_remaining_with_block_as_double(array, block, size, next_i, storage):
        block_method = block.get_method()
        while next_i < size:
            put_all_double_driver.jit_merge_point(block_method=block_method)
            result = block_method.invoke_1(block)
            if isinstance(result, Double):
                storage[next_i] = result.get_embedded_double()
            else:
                # something else, so, let's go to the object strategy
                new_storage = [None] * size
                for i in range(0, next_i + 1):
                    new_storage[i] = Double(storage[i])
                _ArrayStrategy._set_remaining_with_block_as_obj(
                    array, block, size, next_i + 1, new_storage
                )
                return
            next_i += 1
        array.strategy = _double_strategy
        array.storage = _double_strategy.erase(storage)

    @staticmethod
    def _set_remaining_with_block_as_bool(array, block, size, next_i, storage):
        block_method = block.get_method()
        while next_i < size:
            put_all_bool_driver.jit_merge_point(block_method=block_method)
            result = block_method.invoke_1(block)
            if result is trueObject or result is falseObject:
                storage[next_i] = result is trueObject
            else:
                # something else, so, let's go to the object strategy
                new_storage = [None] * size
                for i in range(0, next_i + 1):
                    new_storage[i] = Double(storage[i])
                _ArrayStrategy._set_remaining_with_block_as_obj(
                    array, block, size, next_i + 1, new_storage
                )
                return
            next_i += 1
        array.strategy = _bool_strategy
        array.storage = _bool_strategy.erase(storage)

    @staticmethod
    def _set_remaining_with_block_as_obj(array, block, size, next_i, storage):
        block_method = block.get_method()

        while next_i < size:
            put_all_obj_driver.jit_merge_point(block_method=block_method)
            storage[next_i] = block_method.invoke_1(block)
            next_i += 1

        array.strategy = _obj_strategy
        array.storage = _obj_strategy.erase(storage)


class _ObjectStrategy(_ArrayStrategy):
    erase, unerase = new_erasing_pair("obj_list")
    erase = staticmethod(erase)
    unerase = staticmethod(unerase)

    def get_idx(self, storage, idx):
        store = self.unerase(storage)
        return store[idx]

    def set_idx(self, array, idx, value):
        assert isinstance(array, Array)
        store = self.unerase(array.storage)
        store[idx] = value

    def set_all(self, array, value):
        assert isinstance(array, Array)
        assert isinstance(value, AbstractObject)

        store = self.unerase(array.storage)
        # TODO: we could avoid an allocation here if value isn't something to specialize for...
        self._set_all_with_value(array, value, len(store))

    def set_all_with_block(self, array, block):
        assert isinstance(array, Array)
        store = self.unerase(array.storage)

        # TODO: perhaps we can sometimes avoid the extra allocation of the underlying storage
        self._set_all_with_block(array, block, len(store))

    def as_arguments_array(self, storage):
        return self.unerase(storage)

    def get_size(self, storage):
        return len(self.unerase(storage))

    @staticmethod
    def new_storage_for(size):
        return _ObjectStrategy.erase([nilObject] * size)

    @staticmethod
    def new_storage_with_values(values):
        assert isinstance(values, list)
        make_sure_not_resized(values)
        return _ObjectStrategy.erase(values)

    def copy(self, storage):
        store = self.unerase(storage)
        return Array(_obj_strategy, self.erase(store[:]))

    def copy_and_extend_with(self, storage, value):
        store = self.unerase(storage)
        old_size = len(store)
        new_size = old_size + 1

        new = [None] * new_size

        for i, _ in enumerate(store):
            new[i] = store[i]

        new[old_size] = value

        return Array(_obj_strategy, self.erase(new))


class _LongStrategy(_ArrayStrategy):
    erase, unerase = new_erasing_pair("int_list")
    erase = staticmethod(erase)
    unerase = staticmethod(unerase)

    def get_idx(self, storage, idx):
        store = self.unerase(storage)
        assert isinstance(store, list)
        assert isinstance(store[idx], IntType)
        return Integer(store[idx])

    def set_idx(self, array, idx, value):
        assert isinstance(array, Array)
        if isinstance(value, Integer):
            store = self.unerase(array.storage)
            store[idx] = value.get_embedded_integer()
        else:
            self._transition_to_object_array(array, idx, value)

    def _transition_to_object_array(self, array, idx, value):
        store = self.unerase(array.storage)
        new_store = [None] * len(store)
        for i, val in enumerate(store):
            new_store[i] = Integer(val)

        new_store[idx] = value
        array.storage = _ObjectStrategy.new_storage_with_values(new_store)
        array.strategy = _obj_strategy

    def set_all(self, array, value):
        assert isinstance(array, Array)

        store = self.unerase(array.storage)
        self._set_all_with_value(array, value, len(store))

        # we could avoid the allocation of the new array if value is an Integer
        # for i, _ in enumerate(store):
        #     store[i] = value.get_embedded_integer()

    def set_all_with_block(self, array, block):
        assert isinstance(array, Array)
        store = self.unerase(array.storage)

        # TODO: perhaps we can sometimes avoid the extra allocation of the underlying storage
        self._set_all_with_block(array, block, len(store))

    def as_arguments_array(self, storage):
        store = self.unerase(storage)
        return [Integer(v) for v in store]

    def get_size(self, storage):
        return len(self.unerase(storage))

    @staticmethod
    def new_storage_for(size):
        return _LongStrategy.erase([0] * size)

    @staticmethod
    def new_storage_with_values(values):
        assert isinstance(values, list)
        make_sure_not_resized(values)
        # TODO: do we guarantee this externally?
        new = [v.get_embedded_integer() for v in values]
        return _LongStrategy.erase(new)

    def copy(self, storage):
        store = self.unerase(storage)
        return Array(_long_strategy, self.erase(store[:]))

    def copy_and_extend_with(self, storage, value):
        assert isinstance(value, Integer)
        store = self.unerase(storage)
        old_size = len(store)
        new_size = old_size + 1

        new = [0] * new_size

        for i, val in enumerate(store):
            new[i] = val

        new[old_size] = value.get_embedded_integer()

        return Array(_long_strategy, self.erase(new))


class _DoubleStrategy(_ArrayStrategy):
    erase, unerase = new_erasing_pair("double_list")
    erase = staticmethod(erase)
    unerase = staticmethod(unerase)

    def get_idx(self, storage, idx):
        store = self.unerase(storage)
        assert isinstance(store, list)
        assert isinstance(store[idx], float)
        return Double(store[idx])

    def set_idx(self, array, idx, value):
        assert isinstance(array, Array)
        assert isinstance(value, Double)
        store = self.unerase(array.storage)
        store[idx] = value.get_embedded_double()

    def set_all(self, array, value):
        assert isinstance(array, Array)

        store = self.unerase(array.storage)
        self._set_all_with_value(array, value, len(store))

        # we could avoid the allocation of the new array if value is an Integer
        # for i, _ in enumerate(store):
        #     store[i] = value.get_embedded_integer()

    def set_all_with_block(self, array, block):
        assert isinstance(array, Array)
        store = self.unerase(array.storage)

        # TODO: perhaps we can sometimes avoid the extra allocation of the underlying storage
        self._set_all_with_block(array, block, len(store))

    def as_arguments_array(self, storage):
        store = self.unerase(storage)
        return [Double(v) for v in store]

    def get_size(self, storage):
        return len(self.unerase(storage))

    @staticmethod
    def new_storage_for(size):
        return _DoubleStrategy.erase([0] * size)

    @staticmethod
    def new_storage_with_values(values):
        assert isinstance(values, list)
        make_sure_not_resized(values)
        # TODO: do we guarantee this externally?
        new = [v.get_embedded_double() for v in values]
        return _DoubleStrategy.erase(new)

    def copy(self, storage):
        store = self.unerase(storage)
        return Array(_double_strategy, self.erase(store[:]))

    def copy_and_extend_with(self, storage, value):
        assert isinstance(value, Double)
        store = self.unerase(storage)
        old_size = len(store)
        new_size = old_size + 1

        new = [0.0] * new_size

        for i, val in enumerate(store):
            new[i] = val

        new[old_size] = value.get_embedded_double()

        return Array(_double_strategy, self.erase(new))


class _BoolStrategy(_ArrayStrategy):
    erase, unerase = new_erasing_pair("bool_list")
    erase = staticmethod(erase)
    unerase = staticmethod(unerase)

    def get_idx(self, storage, idx):
        store = self.unerase(storage)
        assert isinstance(store, list)
        assert isinstance(store[idx], bool)
        return trueObject if store[idx] else falseObject

    def set_idx(self, array, idx, value):
        assert isinstance(array, Array)
        assert value is trueObject or value is falseObject
        store = self.unerase(array.storage)
        store[idx] = value is trueObject

    def set_all(self, array, value):
        assert isinstance(array, Array)

        store = self.unerase(array.storage)
        self._set_all_with_value(array, value, len(store))

        # we could avoid the allocation of the new array if value is an Integer
        # for i, _ in enumerate(store):
        #     store[i] = value.get_embedded_integer()

    def set_all_with_block(self, array, block):
        assert isinstance(array, Array)
        store = self.unerase(array.storage)

        # TODO: perhaps we can sometimes avoid the extra allocation of the underlying storage
        self._set_all_with_block(array, block, len(store))

    def as_arguments_array(self, storage):
        store = self.unerase(storage)
        return [trueObject if v else falseObject for v in store]

    def get_size(self, storage):
        return len(self.unerase(storage))

    @staticmethod
    def new_storage_for(size):
        return _BoolStrategy.erase([False] * size)

    @staticmethod
    def new_storage_with_values(values):
        assert isinstance(values, list)
        make_sure_not_resized(values)
        # TODO: do we guarantee this externally?
        new = [v is trueObject for v in values]
        return _BoolStrategy.erase(new)

    def copy(self, storage):
        store = self.unerase(storage)
        return Array(_bool_strategy, self.erase(store[:]))

    def copy_and_extend_with(self, storage, value):
        assert value is trueObject or value is falseObject
        store = self.unerase(storage)
        old_size = len(store)
        new_size = old_size + 1

        new = [False] * new_size

        for i, val in enumerate(store):
            new[i] = val

        new[old_size] = value is trueObject

        return Array(_bool_strategy, self.erase(new))


class _EmptyStrategy(_ArrayStrategy):
    # We have these basic erase/unerase methods, and then the once to be used, which
    # do also the wrapping with Integer objects of the integer value
    _erase, _unerase = new_erasing_pair("Integer")
    _erase = staticmethod(_erase)
    _unerase = staticmethod(_unerase)

    def erase(self, an_int):
        assert isinstance(an_int, int)
        return self._erase(Integer(an_int))

    def unerase(self, storage):
        return self._unerase(storage).get_embedded_integer()

    def get_idx(self, storage, idx):
        size = self.unerase(storage)
        if 0 <= idx < size:
            return nilObject
        raise IndexError()

    def set_idx(self, array, idx, value):
        size = self.unerase(array.storage)
        if 0 <= idx < size:
            if value is nilObject:
                return  # everything is nil already, avoids transition...

            assert isinstance(value, AbstractObject)
            # We need to transition to the _PartiallyEmpty strategy, because
            # we are not guaranteed to set all elements of the array.

            array.storage = _partially_empty_strategy.new_storage_with_values(
                [nilObject] * size
            )
            array.strategy = _partially_empty_strategy
            array.strategy.set_idx(array, idx, value)
        else:
            raise IndexError()

    def set_all(self, array, value):
        if value is nilObject:
            return  # easy short cut

        size = self.unerase(array.storage)
        if size > 0:
            self._set_all_with_value(array, value, size)

    def set_all_with_block(self, array, block):
        size = self.unerase(array.storage)
        self._set_all_with_block(array, block, size)

    def as_arguments_array(self, storage):
        size = self.unerase(storage)
        return [nilObject] * size

    def get_size(self, storage):
        size = self.unerase(storage)
        return size

    @staticmethod
    def new_storage_for(size):
        return _empty_strategy.erase(size)

    @staticmethod
    def new_storage_with_values(values):
        return _empty_strategy.erase(len(values))

    def copy(self, storage):
        return Array(_empty_strategy, storage)

    def copy_and_extend_with(self, storage, value):
        size = self.unerase(storage)
        if value is nilObject:
            return Array.from_size(size + 1)
        new = [nilObject] * (size + 1)
        new[-1] = value
        return Array(_obj_strategy, _ObjectStrategy.erase(new))


class _PartialStorage(object):
    _immutable_fields_ = ["storage", "size"]

    def __init__(self, storage, size, num_empty, storage_type):
        self.storage = storage
        self.size = size
        self.empty_elements = num_empty
        self.type = storage_type

    @staticmethod
    def from_obj_values(storage):
        # Currently, we support only the direct transition from empty
        # to partially empty
        assert isinstance(storage, list)
        assert isinstance(storage[0], AbstractObject)
        size = len(storage)
        return _PartialStorage(storage, size, size, None)

    @staticmethod
    def from_size(size):
        return _PartialStorage([nilObject] * size, size, size, None)


class _PartiallyEmptyStrategy(_ArrayStrategy):
    # This is an array that we expect to be slowly filled, and we have the hope
    # that it will turn out to be homogeneous
    # Thus, we track the number of empty slots left, and we track whether it
    # is homogeneous in one type

    erase, unerase = new_erasing_pair("partial_storage")
    erase = staticmethod(erase)
    unerase = staticmethod(unerase)

    def get_idx(self, storage, idx):
        store = self.unerase(storage)
        return store.storage[idx]

    def set_idx(self, array, idx, value):
        assert isinstance(array, Array)
        assert isinstance(value, AbstractObject)
        store = self.unerase(array.storage)

        if value is nilObject:
            if store.storage[idx] is nilObject:
                return
            store.storage[idx] = nilObject
            store.empty_elements += 1
            return
        if store.storage[idx] is nilObject:
            store.empty_elements -= 1

        store.storage[idx] = value

        if isinstance(value, Integer):
            if store.type is None:
                store.type = _long_strategy
            elif store.type is not _long_strategy:
                store.type = _obj_strategy
        elif isinstance(value, Double):
            if store.type is None:
                store.type = _double_strategy
            elif store.type is not _double_strategy:
                store.type = _obj_strategy
        elif value is trueObject or value is falseObject:
            if store.type is None:
                store.type = _bool_strategy
            elif store.type is not _bool_strategy:
                store.type = _obj_strategy
        else:
            store.type = _obj_strategy

        # as soon as we see it requires an object storage
        # we give up and switch to an object strategy
        if store.type is _obj_strategy or store.empty_elements == 0:
            array.strategy = store.type
            array.storage = array.strategy.new_storage_with_values(store.storage)

    def set_all(self, array, value):
        assert isinstance(array, Array)
        assert isinstance(value, AbstractObject)

        store = self.unerase(array.storage)
        self._set_all_with_value(array, value, store.size)

    def set_all_with_block(self, array, block):
        assert isinstance(array, Array)
        store = self.unerase(array.storage)
        self._set_all_with_block(array, block, store.size)

    def as_arguments_array(self, storage):
        return self.unerase(storage).storage

    def get_size(self, storage):
        return self.unerase(storage).size

    @staticmethod
    def new_storage_for(size):
        return _PartiallyEmptyStrategy.erase(_PartialStorage.from_size(size))

    @staticmethod
    def new_storage_with_values(values):
        assert isinstance(values, list)
        make_sure_not_resized(values)
        return _PartiallyEmptyStrategy.erase(_PartialStorage.from_obj_values(values))

    def copy(self, storage):
        store = self.unerase(storage)
        return Array(
            _partially_empty_strategy,
            self.erase(_PartialStorage.from_obj_values(store.storage[:])),
        )

    def copy_and_extend_with(self, storage, value):
        store = self.unerase(storage)
        old_size = store.size
        new_size = old_size + 1

        new = [nilObject] * new_size

        for i, _ in enumerate(store.storage):
            new[i] = store.storage[i]

        new_store = _PartialStorage(new, new_size, store.empty_elements + 1, store.type)
        new_arr = Array(_partially_empty_strategy, self.erase(new_store))
        new_arr.set_indexable_field(old_size, value)
        return new_arr


_obj_strategy = _ObjectStrategy()
_long_strategy = _LongStrategy()
_double_strategy = _DoubleStrategy()
_bool_strategy = _BoolStrategy()
_empty_strategy = _EmptyStrategy()
_partially_empty_strategy = _PartiallyEmptyStrategy()


def _determine_strategy(values):
    is_empty = True
    only_double = True
    only_long = True
    only_bool = True
    for value in values:
        if value is None or value is nilObject:
            continue
        if isinstance(value, int) or isinstance(value, Integer):
            is_empty = False
            only_double = False
            only_bool = False
            continue
        if isinstance(value, float) or isinstance(value, Double):
            is_empty = False
            only_long = False
            only_bool = False
            continue
        if isinstance(value, bool) or value is trueObject or value is falseObject:
            is_empty = False
            only_long = False
            only_double = False
            continue
        only_long = False
        only_double = False
        only_bool = False
        is_empty = False

    if is_empty:
        return _empty_strategy
    if only_double:
        return _double_strategy
    if only_long:
        return _long_strategy
    if only_bool:
        return _bool_strategy
    return _obj_strategy


class Array(AbstractObject):
    # strategy is the strategy object
    # storage depends on the strategy, can be for instance a typed list,
    # or for the empty strategy the size as an Integer object,
    # or something more complex

    @staticmethod
    def from_size(size):
        return Array(_empty_strategy, _empty_strategy.new_storage_for(size))

    @staticmethod
    def from_values(values):
        make_sure_not_resized(values)
        suitable_strategy = _determine_strategy(values)
        return Array(
            suitable_strategy, suitable_strategy.new_storage_with_values(values)
        )

    @staticmethod
    def from_integers(ints):
        return Array(_long_strategy, _long_strategy.erase(ints))

    @staticmethod
    def from_objects(values):
        make_sure_not_resized(values)
        return Array(_obj_strategy, _obj_strategy.new_storage_with_values(values))

    def __init__(self, strategy, storage):  # pylint: disable=super-init-not-called
        self.strategy = strategy
        self.storage = storage

    def get_indexable_field(self, index):
        # Get the indexable field with the given index
        return self.strategy.get_idx(self.storage, index)

    def set_indexable_field(self, index, value):
        # Set the indexable field with the given index to the given value
        self.strategy.set_idx(self, index, value)

    def set_all(self, value):
        self.strategy.set_all(self, value)

    def set_all_with_block(self, block):
        self.strategy.set_all_with_block(self, block)

    def as_argument_array(self):
        return self.strategy.as_arguments_array(self.storage)

    def get_number_of_indexable_fields(self):
        # Get the number of indexable fields in this array
        return self.strategy.get_size(self.storage)

    def copy(self):
        return self.strategy.copy(self.storage)

    def copy_and_extend_with(self, value):
        return self.strategy.copy_and_extend_with(self.storage, value)

    def get_class(self, universe):
        return universe.array_class

    def get_object_layout(self, universe):
        return universe.array_layout
