#----------------------------------------------------------------
# Generated CMake target import file.
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "COLA" for configuration ""
set_property(TARGET COLA APPEND PROPERTY IMPORTED_CONFIGURATIONS NOCONFIG)
set_target_properties(COLA PROPERTIES
  IMPORTED_LOCATION_NOCONFIG "${_IMPORT_PREFIX}/lib/libCOLA.0.3.2.dylib"
  IMPORTED_SONAME_NOCONFIG "@rpath/libCOLA.0.dylib"
  )

list(APPEND _cmake_import_check_targets COLA )
list(APPEND _cmake_import_check_files_for_COLA "${_IMPORT_PREFIX}/lib/libCOLA.0.3.2.dylib" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
