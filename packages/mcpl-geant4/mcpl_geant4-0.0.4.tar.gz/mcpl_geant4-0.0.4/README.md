mcpl-geant4
===========

This package faciliates the usage of Monte Carlo Particle Lists ( MCPL,
https://mctools.github.io/mcpl/ ) files with Geant4.

Usage in Geant4 (C++) code
--------------------------

The interface between MCPL and Geant4 consists of two classes, `G4MCPLGenerator`
and `G4MCPLWriter`, which users can use to either generate primary events from
the particles in an existing MCPL file (1 particle per event), or to capture the
particle state of particles entering one or more specified volumes in the
simulation geometry and write them to a new MCPL file.

Refer to https://mctools.github.io/mcpl/hooks_geant4/ and section 3.1 of the
MCPL paper (https://doi.org/10.1016/j.cpc.2017.04.012) for how to use these two
classes in a Geant4 simulation.

Usage Examples
--------------

Two complete usage examples along with the necessary CMake code is provided in
the mcpl-geant4 repository at:

* https://github.com/mctools/mcpl-geant4/tree/main/example_write
* https://github.com/mctools/mcpl-geant4/tree/main/example_read

Installation and Configuration
------------------------------

To use the MCPL-Geant4 bindings, one must:

1. Install MCPL and Geant4. Although it is possible to build both projects
   manually, it should be noted that both are available on conda-forge. If not
   using conda, note that MCPL is also available on PyPI, so assuming
   Geant4 has already been installed in another manner, it might be possible to
   simply complete the setup by a `pip install mcpl`.
2. Install mcpl-geant4. This can be done by `pip install mcpl-geant4`,
   or alternatively by cloning the repository at
   https://github.com/mctools/ncrystal-geant4 and setting the CMake
   variable `NCrystalGeant4_DIR` to point at the `src/mcpl_geant4/cmake`
   subdir of the cloned repo.
3. Edit your projects CMakeLists.txt to add a `find_package(MCPLGeant4)`
   statement, and adding the `MCPLGeant4::MCPLGeant4` target as a
   dependency of the Geant4 application you are building.
4. Edit your C++ code and include the header file(s)
   `MCPLGeant4/G4MCPLWriter.hh` and/or `MCPLGeant4/G4MCPLGenerator.hh` as
   needed. Then use the corresponding classes in your Geant4 code as needed (see
   above for usage instructions.

Scientific reference
--------------------

A substantial effort went into developing MCPL. If you use it for your work, we
would appreciate it if you would use the following reference in your work:

T. Kittelmann, et al., Monte Carlo Particle Lists: MCPL, Computer Physics
Communications, Volume 218, September 2017, Pages 17-42, ISSN 0010-4655,
https://doi.org/10.1016/j.cpc.2017.04.012
