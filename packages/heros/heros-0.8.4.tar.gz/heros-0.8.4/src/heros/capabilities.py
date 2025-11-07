from dataclasses import dataclass, field
import inspect
from heros import __proto_version__
from heros.helper import log
from .inspect import is_hero_event
import traceback
import typing
from typing import Callable, ClassVar, Literal
from types import UnionType

if typing.TYPE_CHECKING:
    from heros.heros import LocalHERO
    from zenoh import Query


def type_to_str(annotation) -> str:
    """
    Transforms annotation given as `types` to strings.

    Args:
        annotation: The typing annotation.

    Returns:
        Annotation as string.
    """
    if annotation is not inspect.Parameter.empty:
        if isinstance(annotation, UnionType):
            return repr(annotation)
        else:
            return annotation.__name__
    else:
        return "undefined"


def build_capability(
    hero_obj: "LocalHERO", member_name: str, annotation: None | str = None
) -> "Capability | Literal[False]":
    """Build a capability object from a given member name and optional annotation to infer type.

    If no annotation is given the signature is inferred from the member itself by calling `getattr`. For callables (e.g.
    methods) this needs to be done, as the full signature is not inferable from the type annotation.

    Args:
        hero_obj: host HERO object
        member_name: name of the attribute/method to build as capability
        annotation: optional annotation to infer signature.

    Returns:
        :py:class:`Capability` object for the given member, `False` if no signature can be inferred from the given
        input.
    """
    if annotation is None:
        is_callable = callable(getattr(hero_obj, member_name))
    elif typing.get_origin(annotation) is Callable:
        is_callable = True
    else:
        is_callable = False

    if is_callable:
        # Callable typing does not contain information to build a signature from them, so we need to get the full attr.
        if is_hero_event(getattr(hero_obj, member_name)):
            log.debug(f"found event with name {member_name}!")
            return EventCapability(name=member_name)
        else:
            try:
                return MethodCapability.from_method(name=member_name, m=getattr(hero_obj, member_name))
            except ValueError:
                # this occurs if the callable cannot be inspected, we thus skip it
                log.warn(f"Skipping {getattr(hero_obj, member_name)} since the signature cannot be inferred!")
                return False

            log.debug(f"register method queryable for {hero_obj._endpoint_base_path}/{member_name}")

    else:
        if annotation is None:
            annotation = type(getattr(hero_obj, member_name))
        return AttributeCapability(name=member_name, type=type_to_str(annotation))


@dataclass
class Parameter:
    name: str
    type: str
    default: str
    kind: inspect._ParameterKind

    @staticmethod
    def from_signature_parameter(p: inspect.Parameter):
        param = Parameter(
            name=p.name,
            type=type_to_str(p.annotation),
            default=p.default if p.default is not inspect.Parameter.empty else "undefined",
            kind=p.kind,
        )
        return param

    def has_default(self):
        return self.default != "undefined"

    def to_dict(self):
        return {"name": self.name, "type": self.type, "default": self.default, "kind": self.kind}

    @staticmethod
    def from_dict(d: dict, proto_version: float = __proto_version__):
        if "name" not in d:
            raise AttributeError("required field 'name' not in dict")

        param = Parameter(
            name=d["name"],
            type=d["type"] if "type" in d else "undefined",
            default=d["default"] if "default" in d else "undefined",
            kind=d["kind"]
            if proto_version > 0.1
            else (inspect.Parameter.KEYWORD_ONLY if "default" in d else inspect.Parameter.VAR_POSITIONAL),
        )
        return param


@dataclass
class Capability:
    name: str
    flavor: ClassVar[str] = "undefined"

    def to_dict(self) -> dict:
        return {"name": self.name, "flavor": self.flavor}

    @staticmethod
    def from_dict(d: dict, proto_version: float = __proto_version__):
        if "name" not in d:
            raise AttributeError("required field 'name' not in dict")
        if "flavor" not in d:
            raise AttributeError("required field 'flavor' not in dict")

        if d["flavor"] == "attribute":
            return AttributeCapability.from_dict(d, proto_version)
        elif d["flavor"] == "method":
            return MethodCapability.from_dict(d, proto_version)
        elif d["flavor"] == "event":
            return EventCapability.from_dict(d, proto_version)
        else:
            return None

    def get_call_wrapper(self, hero_obj: "LocalHERO") -> Callable[["Query"], None] | Literal[False]:
        """Construct a callback wrapper function for the Zenoh endpoint.

        Returns:
            A wrapper function which takes exactly one input, the :py:class:`zenoh.Query` object or `False` if
            the capability does not need a wrapper function.
        """
        return False


@dataclass
class AttributeCapability(Capability):
    """
    An attribute capability describes a single variable of the remote object.
    It is exposed under the name of the capability.

    Args:
        name: name of the capability
        type: data type. E.g. "str", "int", "float", "list", ...
        access: Read and/or write access. "r" for read, "w" for write, and "rw" for both
    """

    flavor: ClassVar[str] = "attribute"
    type: str
    access: str = "rw"

    def to_dict(self) -> dict:
        d = Capability.to_dict(self)
        d.update({"type": self.type, "access": self.access})
        return d

    @staticmethod
    def from_dict(d: dict, proto_version: float = __proto_version__) -> "AttributeCapability":
        if "name" not in d:
            raise AttributeError("required field 'type' not in dict")
        return AttributeCapability(name=d["name"], type=d["type"], access=d["access"])

    def get_call_wrapper(self, hero_obj: "LocalHERO") -> Callable[["Query"], None]:
        def wrapper(query: "Query") -> None:
            if query.payload:
                setattr(hero_obj, self.name, hero_obj._deserialize(query.payload.to_bytes()))
                log.debug(f"I should update {self.name}")
            else:
                log.debug(f"I should return value of {self.name}")

                # send back the result
                try:
                    payload = hero_obj._serialize(getattr(hero_obj, self.name))
                except AttributeError:
                    # attribute is only typed but not initialised.
                    log.warning("Call to non-initialised attribute %s", self.name)
                    payload = hero_obj._serialize(None)
                query.reply(
                    f"{hero_obj._endpoint_base_path}/{self.name}",
                    payload,
                    encoding=hero_obj._default_encoding,
                )

        return wrapper


@dataclass
class EventCapability(Capability):
    """
    An event capability describes the ability of a remote object to notify upon a certain event.
    """

    flavor: ClassVar[str] = "event"

    @staticmethod
    def from_dict(d: dict, proto_version: float = __proto_version__) -> "EventCapability":
        return EventCapability(name=d["name"])


@dataclass
class MethodCapability(Capability):
    flavor: ClassVar[str] = "method"
    parameters: list[Parameter] = field(default_factory=list)
    return_type: str = "None"

    @staticmethod
    def from_method(m: Callable, name: str | None = None) -> "MethodCapability":
        if name is None:
            name = m.__name__
        sig = inspect.signature(m)

        cap = MethodCapability(name=name)
        cap.parameters = [Parameter.from_signature_parameter(sig.parameters[pname]) for pname in sig.parameters]
        if sig.return_annotation not in (inspect.Signature.empty, None):
            cap.return_type = type_to_str(sig.return_annotation)
        return cap

    def to_signature(self) -> inspect.Signature:
        parameters = [
            inspect.Parameter(
                p.name,
                kind=p.kind,
                default=p.default if p.has_default() else inspect.Parameter.empty,
                annotation=p.type if p.type != "undefined" else inspect.Parameter.empty,
            )
            for p in self.parameters
        ]
        return inspect.Signature(parameters=parameters, return_annotation=self.return_type)

    def to_dict(self) -> dict:
        d = Capability.to_dict(self)
        d.update({"parameters": [p.to_dict() for p in self.parameters], "return_type": self.return_type})
        return d

    def get_call_wrapper(self, hero_obj: "LocalHERO") -> Callable[["Query"], None]:
        def wrapper(query: "Query") -> None:
            params = hero_obj._deserialize(query.payload.to_bytes())
            log.debug(f"I should call {self.name} with parameters {params}")

            try:
                # the actual method call
                if isinstance(params, dict):
                    return_value = getattr(hero_obj, self.name)(**params)
                    log.warning(
                        f"HERO {hero_obj._name} received a payload using protocol version 0.1 which is deprecated and will be removed in a future version"
                    )
                else:
                    return_value = getattr(hero_obj, self.name)(*params[0], **params[1])

                # send back the result
                query.reply(
                    f"{hero_obj._endpoint_base_path}/{self.name}",
                    hero_obj._serialize(return_value),
                    encoding=hero_obj._default_encoding,
                )
            except Exception as e:
                query.reply_err(
                    hero_obj._serialize(str(e) + "\n\n" + "".join(traceback.format_tb(e.__traceback__))),
                    encoding=hero_obj._default_encoding,
                )

        return wrapper

    @staticmethod
    def from_dict(d: dict, proto_version: float = __proto_version__) -> "MethodCapability":
        """
        Generate a method capabilities object from a defining dictionary.

        Args: definition of the capability according to the standard
        """
        if "parameters" not in d:
            raise AttributeError("required field 'parameters' not in dict")

        cap = MethodCapability(name=d["name"])
        cap.parameters = [Parameter.from_dict(par, proto_version) for par in d["parameters"]]
        if "return_type" in d:
            cap.return_type = d["return_type"]

        return cap

    def call_dict(self, *args, **kwargs) -> dict:
        """
        This returns a dict that assigns the given parameter to the parameters of
        ourself. It takes care that positional and keyword arguments are handled correctly

        Note:
            This function is deprecated and will be removed together with the transport protocol version 0.1

        Args:
            *args: positional arguments
            **kwargs: keyword arguments

        Returns:
            dict: dict with parameter assignments
        """
        # TODO: type checking?

        # positional arguments
        d = {self.parameters[i].name: arg for i, arg in enumerate(args)}

        # keyword arguments
        parameter_names = [p.name for p in self.parameters]
        d.update({arg_name: value for arg_name, value in kwargs.items() if arg_name in parameter_names})

        return d
