FAQ
###

Can I use private methods and attributes?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, private methods and attributes (name starting with a :code:`_`) are not exposed to the remote side.

However, you can force private methods to be exposed by decorating them with :code:`@heros.inspect.force_remote`.

For attributes there is currently no straight forward way to force this.


I am observing timeouts in the HERO communication. What can I do?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If a timeout occurs, HEROS will print an error like

.. code-block:: python

   2025-10-23 17:41:47,609 heros [heros.py:70 _query_selector]: Stream interrupted when querying peer EntityGlobalId { zid: 2554c3255fd4ff7dce726aba72afd04f, eid: 0 } with arguments ('@object/heros/*/_discover',) and {'target': QueryTarget.ALL, 'timeout': 2.0}: b'Timeout'. If this error persists, consult the HEROS documentation on 'debuging'.

to the terminal. This can occure if a peer is in an unresponsive state and takes to long to respond.
To find out what is going on, the best way is to setup a zenoh router. Therefore download the newest "standalone" package for your
system `here <https://github.com/eclipse-zenoh/zenoh/releases>`_ and unpack it.

.. note::

   It does not matter on which machine you are doing this as long as it is connected to the same network as the offending peer.

Move into the unpacked folder and run

.. code-block:: bash

   RUST_LOG=DEBUG ./zenohd

in a terminal. Now the router should connect to all peers it finds on the network. For each peer it prints a line like

.. code-block:: bash

   2025-10-23T15:47:22.218912Z DEBUG acc-0 ThreadId(04) zenoh_transport::unicast::establishment::accept: New transport link accepted from 2554c3255fd4ff7dce726aba72afd04f to 2890d320dce65ff47c7ea57b87954cc6: TransportLinkUnicast { link: Link { src: tcp/[::ffff:192.168.1.130]:7447, dst: tcp/[::ffff:192.168.1.130]:54838, mtu: 49152, is_reliable: true, is_streamed: true }, config: TransportLinkUnicastConfig { direction: Inbound, batch: BatchConfig { mtu: 49152, is_streamed: true, is_compression: false }, priorities: None, reliability: None } }

Now search for the connecting :code:`zid` you obtained from the timeout error message, in this example :code:`2554c3255fd4ff7dce726aba72afd04f`. The router knows which IP address this peer runs on, here :code:`tcp/[::ffff:192.168.1.130]:7447`.

Sometimes it is enough to restart the blocking HERO, but in general it is a sign of a intermittent connection.

.. note::

   If the endpoint timing out is not :code:`_discover` but for example :code:`_@object/heros/my_hero/slow_calc`, this indicates that your function `slow_calc` takes to long to execute.
   If you require this, set the timeout in the :code:`RemoteHERO` calling this slow function in `zenoh config <https://zenoh.io/docs/manual/configuration/>`_ as a temporary solution and write
   a `feature request <https://gitlab.com/atomiq-project/heros/-/issues>`_.


Can I use Heros with ARTIQ without using Atomiq?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yes, **even if we do not recommend it an there is no real point in it other than for a temporary transitionary setup!**
Just install HEROS within your `flake.nix` (adapt the version to the latest):

.. code-block:: nix

    heros = pkgs.python3Packages.buildPythonPackage rec {
      name = "heros";
      pname = "heros";
      format = "pyproject";
      version = "0.5.0";
      nativeBuildInputs = [
        pkgs.autoPatchelfHook
        ];
      src = pkgs.python3Packages.fetchPypi {
        inherit pname version;
        sha256 = "lXvd8N1BnHRWidwESy42ZlRopEX/y/uLXv+NCnxPWwo=";
      };
      buildInputs = [ pkgs.python3Packages.cbor2 pkgs.python3Packages.hatchling pkgs.python3Packages.numpy pkgs.python3Packages.zenoh];
    };


and add :code:`heros` to the python packages loaded on shell creation.

.. note::

   If you are using Atomiq, this is all handled automatically and you can just add your HERO
   `to the components DB <https://atomiq-atomiq-project-515d34b8ff1a5c74fcf04862421f6d74a00d9de1b.gitlab.io/heros.html>`_ with the :code:`$` identifier.

To use a remote hero as a device in the device DB, you have to circumvent the device manager to be passed to the :code:`RemoteHERO` class
by creating a device like:

.. code-block:: python

  class ArtiqRemoteHERO(RemoteHERO)
    def __new__(cls, dmgr, name: str, realm: str = "heros", *args, **kwargs):
        return RemoteHERO.__new__(cls, name,realm, *args, **kwargs)

    def __init__(self, dmgr,  name: str, realm: str="heros", *args, **kwargs):
        super().__init__(name, realm, *args, **kwargs)

and adding it to the device db:

.. code-block:: python

   device_db["my_hero"] = {
      "type": "local",
      "module": "my.lib",
      "class":"ArtiqRemoteHERO",
      "arguments": {
          "name":"my_remote_hero"
          }
   }
