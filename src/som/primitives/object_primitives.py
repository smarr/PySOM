from som.primitives.primitives import Primitives

from som.vmobjects.primitive import Primitive
from som.vmobjects.array     import Array 

class ObjectPrimitives(Primitives):
    
    def install_primitives(self):
        def _equals(ivkbl, frame, interpreter):
            op1 = frame.pop()
            op2 = frame.pop()
            if op1 is op2:
                frame.push(self._universe.trueObject)
            else:
                frame.push(self._universe.falseObject)
        self._install_instance_primitive(Primitive("==", self._universe, _equals))
        
        def _hashcode(ivkbl, frame, interpreter):
            rcvr = frame.pop()
            frame.push(self._universe.new_integer(hash(rcvr)))
        self._install_instance_primitive(Primitive("hashcode", self._universe, _hashcode))


        def _objectSize(ivkbl, frame, interpreter):
            rcvr = frame.pop()
            size = rcvr.get_number_of_fields()
            if isinstance(rcvr, Array):
                size += rcvr.get_number_of_indexable_fields()
        
            frame.push(self._universe.new_integer(size))
        self._install_instance_primitive(Primitive("objectSize", self._universe, _objectSize))

        def _perform(ivkbl, frame, interpreter):
            selector = frame.pop()
            rcvr     = frame.get_stack_element(0)

            invokable = rcvr.get_class().lookup_invokable(selector)
            invokable.invoke(frame, interpreter)
        self._install_instance_primitive(Primitive("perform:", self._universe, _perform))

        def _performInSuperclass(ivkbl, frame, interpreter):
            clazz    = frame.pop()
            selector = frame.pop()
            rcvr     = frame.get_stack_element(0)

            invokable = clazz.lookup_invokable(selector)
            invokable.invoke(frame, interpreter)
        self._install_instance_primitive(Primitive("perform:inSuperclass:", self._universe, _performInSuperclass))

        def _performWithArguments(ivkbl, frame, interpreter):
            args     = frame.pop()
            selector = frame.pop()
            rcvr     = frame.get_stack_element(0)

            for i in range(0, args.get_number_of_indexable_fields()):
                frame.push(args.get_indexable_field(i))

            invokable = rcvr.get_class().lookup_invokable(selector)
            invokable.invoke(frame, interpreter)
        self._install_instance_primitive(Primitive("perform:withArguments:", self._universe, _performWithArguments))

        def _instVarAt(ivkbl, frame, interpreter):
            idx  = frame.pop()
            rcvr = frame.pop()

            frame.push(rcvr.get_field(idx.get_embedded_integer() - 1))
        self._install_instance_primitive(Primitive("instVarAt:", self._universe, _instVarAt))

        def _instVarAtPut(ivkbl, frame, interpreter):
            val  = frame.pop()
            idx  = frame.pop()
            rcvr = frame.get_stack_element(0)

            rcvr.set_field(idx.get_embedded_integer() - 1, val)
        self._install_instance_primitive(Primitive("instVarAt:put:", self._universe, _instVarAtPut))

        def _class(ivkbl, frame, interpreter):
            rcvr = frame.pop()
            frame.push(rcvr.get_class())
        self._install_instance_primitive(Primitive("class", self._universe, _class))
