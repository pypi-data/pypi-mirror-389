#----------------------------------------------------------------
# Generated CMake target import file.
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "COLA-Py" for configuration ""
set_property(TARGET COLA-Py APPEND PROPERTY IMPORTED_CONFIGURATIONS NOCONFIG)
set_target_properties(COLA-Py PROPERTIES
  IMPORTED_LOCATION_NOCONFIG "${_IMPORT_PREFIX}/lib/COLA-Py/libCOLA-Py.dylib"
  IMPORTED_SONAME_NOCONFIG "@rpath/libCOLA-Py.dylib"
  )

list(APPEND _cmake_import_check_targets COLA-Py )
list(APPEND _cmake_import_check_files_for_COLA-Py "${_IMPORT_PREFIX}/lib/COLA-Py/libCOLA-Py.dylib" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
