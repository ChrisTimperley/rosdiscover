# -*- coding: utf-8 -*-
from typing import Dict, Iterator, Optional, Set, Sequence
import contextlib

from loguru import logger
from roswire.proxy.roslaunch.reader import LaunchFileReader
import dockerblade
import roswire

from .context import NodeContext
from .model import Model
from .summary import NodeSummary
from .parameter import ParameterServer


class Interpreter:
    @staticmethod
    @contextlib.contextmanager
    def for_image(image: str,
                  sources: Sequence[str]
                  ) -> Iterator['Interpreter']:
        """Constructs an interpreter for a given Docker image."""
        rsw = roswire.ROSWire()  # TODO don't maintain multiple instances
        with rsw.launch(image, sources) as app:
            yield Interpreter(app.files, app.shell)

    def __init__(self,
                 files: dockerblade.files.FileSystem,
                 shell: dockerblade.shell.Shell
                 ) -> None:
        self.__files = files
        self.__shell = shell
        self.__params = ParameterServer()
        self.__nodes: Set[NodeSummary] = set()

    @property
    def parameters(self) -> ParameterServer:
        """The simulated parameter server for this interpreter."""
        return self.__params

    @property
    def nodes(self) -> Iterator[NodeSummary]:
        """Returns an iterator of summaries for each ROS node."""
        yield from self.__nodes

    def launch(self, fn: str) -> None:
        """Simulates the effects of `roslaunch` using a given launch file."""
        # NOTE this method also supports command-line arguments
        reader = LaunchFileReader(shell=self.__shell,
                                  files=self.__files)

        # Workaround:
        # https://answers.ros.org/question/299232/roslaunch-python-arg-substitution-finds-wrong-package-folder-path/
        # https://github.com/ros/ros_comm/blob/e96c407c64e1c17b0dd2bb85b67f388380527097/tools/roslaunch/src/roslaunch/substitution_args.py#L141L145
        sed_command = 's#$(find xacro)/xacro #$(find xacro)/xacro.py #g'
        sed_command = f'sed -i "{sed_command}" {fn}'
        self.__shell.check_output(sed_command)

        config = reader.read(fn)

        for key, value in config.params.items():
            self.__params[key] = value

        for node in config.nodes:
            logger.debug(f"launching node: {node.name}")
            try:
                args = node.args or ''
                remappings = {old: new for (old, new) in node.remappings}
                self.load(pkg=node.package,
                          nodetype=node.typ,
                          name=node.name,
                          namespace=node.namespace,  # FIXME
                          remappings=remappings,
                          args=args)
            # FIXME this is waaay too permissive
            except Exception:
                logger.exception(f"failed to launch node: {node.name}")
                raise

    def create_nodelet_manager(self, name: str) -> None:
        """Creates a nodelet manager with a given name."""
        logger.info('launched nodelet manager: %s', name)

    def load_nodelet(self,
                     pkg: str,
                     nodetype: str,
                     name: str,
                     namespace: str,
                     remappings: Dict[str, str],
                     manager: Optional[str] = None
                     ) -> None:
        """Loads a nodelet using the provided instructions.

        Parameters:
            pkg: the name of the package to which the nodelet belongs.
            nodetype: the name of the type of nodelet that should be loaded.
            name: the name that should be assigned to the nodelet.
            namespace: the namespace into which the nodelet should be loaded.
            remappings: a dictionary of name remappings that should be applied
                to this nodelet, where keys correspond to old names and values
                correspond to new names.
            manager: the name of the manager, if any, for this nodelet. If
                this nodelet is standalone, :code:`manager` should be set to
                :code:`None`.

        Raises:
            Exception: if there is no model for the given nodelet type.
        """
        if manager:
            logger.info(f'launching nodelet [{name}] '
                        f'inside manager [{manager}]')
        else:
            logger.info(f'launching standalone nodelet [{name}]')
        return self.load(pkg, nodetype, name, namespace, remappings, '')

    def load(self,
             pkg: str,
             nodetype: str,
             name: str,
             namespace: str,
             remappings: Dict[str, str],
             args: str
             ) -> None:
        """Loads a node using the provided instructions.

        Parameters
        ----------
        pkg: str
            the name of the package to which the node belongs.
        nodetype: str
            the name of the type of node that should be loaded.
        name: str
            the name that should be assigned to the node.
        namespace: str
            the namespace into which the node should be loaded.
        remappings: Dict[str, str]
            a dictionary of name remappings that should be applied
            to this node, where keys correspond to old names and values
            correspond to new names.
        args: str
            a string containing command-line arguments to the node.

        Raises
        ------
        Exception
            if there is no model for the given node type.
        """
        args = args.strip()
        if nodetype == 'nodelet':
            if args == 'manager':
                return self.create_nodelet_manager(name)
            elif args.startswith('standalone '):
                pkg_and_nodetype = args.partition(' ')[2]
                pkg, _, nodetype = pkg_and_nodetype.partition('/')
                return self.load_nodelet(pkg, nodetype, name, namespace, remappings)
            else:
                load, pkg_and_nodetype, mgr = args.split(' ')
                pkg, _, nodetype = pkg_and_nodetype.partition('/')
                return self.load_nodelet(pkg, nodetype, name, namespace, remappings, mgr)

        if remappings:
            logger.info(f"using remappings: {remappings}")

        try:
            model = Model.find(pkg, nodetype)
        except Exception:
            m = (f"failed to find model for node type [{nodetype}] "
                 f"in package [{pkg}]")
            logger.warning(m)
            raise Exception(m)

        ctx = NodeContext(name=name,
                          namespace=namespace,
                          kind=nodetype,
                          package=pkg,
                          args=args,
                          remappings=remappings,
                          files=self.__files,
                          params=self.__params)
        model.eval(ctx)
        if hasattr(model, '__placeholder') and model.__placeholder:
            model.mark_placeholder()

        self.__nodes.add(ctx.summarize())