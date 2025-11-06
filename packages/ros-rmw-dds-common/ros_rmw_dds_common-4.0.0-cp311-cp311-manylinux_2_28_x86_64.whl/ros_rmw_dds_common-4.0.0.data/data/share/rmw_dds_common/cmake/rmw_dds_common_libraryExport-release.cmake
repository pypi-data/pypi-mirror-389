#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "rmw_dds_common::rmw_dds_common_library" for configuration "Release"
set_property(TARGET rmw_dds_common::rmw_dds_common_library APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(rmw_dds_common::rmw_dds_common_library PROPERTIES
  IMPORTED_LINK_DEPENDENT_LIBRARIES_RELEASE "rcpputils::rcpputils;rosidl_runtime_c::rosidl_runtime_c"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/librmw_dds_common.so"
  IMPORTED_SONAME_RELEASE "librmw_dds_common.so"
  )

list(APPEND _cmake_import_check_targets rmw_dds_common::rmw_dds_common_library )
list(APPEND _cmake_import_check_files_for_rmw_dds_common::rmw_dds_common_library "${_IMPORT_PREFIX}/lib/librmw_dds_common.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
