#----------------------------------------------------------------
# Generated CMake target import file for configuration "RelWithDebInfo".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "COLA-Py" for configuration "RelWithDebInfo"
set_property(TARGET COLA-Py APPEND PROPERTY IMPORTED_CONFIGURATIONS RELWITHDEBINFO)
set_target_properties(COLA-Py PROPERTIES
  IMPORTED_LOCATION_RELWITHDEBINFO "${_IMPORT_PREFIX}/lib/COLA-Py/libCOLA-Py.dylib"
  IMPORTED_SONAME_RELWITHDEBINFO "@rpath/libCOLA-Py.dylib"
  )

list(APPEND _cmake_import_check_targets COLA-Py )
list(APPEND _cmake_import_check_files_for_COLA-Py "${_IMPORT_PREFIX}/lib/COLA-Py/libCOLA-Py.dylib" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
