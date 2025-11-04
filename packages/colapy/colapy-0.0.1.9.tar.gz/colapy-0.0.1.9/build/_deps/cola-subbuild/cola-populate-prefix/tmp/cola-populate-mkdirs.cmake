# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file LICENSE.rst or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION ${CMAKE_VERSION}) # this file comes with cmake

# If CMAKE_DISABLE_SOURCE_CHANGES is set to true and the source directory is an
# existing directory in our source tree, calling file(MAKE_DIRECTORY) on it
# would cause a fatal error, even though it would be a no-op.
if(NOT EXISTS "/Users/artyasen/Projects/Physics/COLA-PY/build/_deps/cola-src")
  file(MAKE_DIRECTORY "/Users/artyasen/Projects/Physics/COLA-PY/build/_deps/cola-src")
endif()
file(MAKE_DIRECTORY
  "/Users/artyasen/Projects/Physics/COLA-PY/build/_deps/cola-build"
  "/Users/artyasen/Projects/Physics/COLA-PY/build/_deps/cola-subbuild/cola-populate-prefix"
  "/Users/artyasen/Projects/Physics/COLA-PY/build/_deps/cola-subbuild/cola-populate-prefix/tmp"
  "/Users/artyasen/Projects/Physics/COLA-PY/build/_deps/cola-subbuild/cola-populate-prefix/src/cola-populate-stamp"
  "/Users/artyasen/Projects/Physics/COLA-PY/build/_deps/cola-subbuild/cola-populate-prefix/src"
  "/Users/artyasen/Projects/Physics/COLA-PY/build/_deps/cola-subbuild/cola-populate-prefix/src/cola-populate-stamp"
)

set(configSubDirs )
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "/Users/artyasen/Projects/Physics/COLA-PY/build/_deps/cola-subbuild/cola-populate-prefix/src/cola-populate-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "/Users/artyasen/Projects/Physics/COLA-PY/build/_deps/cola-subbuild/cola-populate-prefix/src/cola-populate-stamp${cfgdir}") # cfgdir has leading slash
endif()
